from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta

_ORDER_STATE = [
	('new','New'),
	('rejected','Rejected'),
	('confirmed','Confirmed'),
	('ready','Ready'),
	('started','Started'),
	('start_confirmed','Start Confirmed'),
	('paused','Paused'),
	('resumed','Resumed'),
	('finished','Finished'),
	('finish_confirmed','Finish Confirmed'),
	('canceled','Canceled')
]



class foms_order(osv.osv):

	_name = 'foms.order'
	_description = 'Forms Order'
	
	_inherit = ['mail.thread','chjs.base.webservice']

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Order #', required=True),
		'customer_contract_id': fields.many2one('foms.contract', 'Customer Contract', required=True, ondelete='restrict'),
		'service_type': fields.selection([
			('full_day','Full-day Service'),
			('by_order','By Order'),
			('shuttle','Shuttle')], 'Service Type', required=True),
		'request_date': fields.datetime('Request Date', required=True),
		'state': fields.selection(_ORDER_STATE, 'State', required=True, track_visiblity="onchange"),
		'order_by': fields.many2one('res.users', 'Order By', required=True, ondelete='restrict'),
		'confirm_date': fields.datetime('Confirm Date'),
		'confirm_by': fields.many2one('res.users', 'Confirm By', ondelete='restrict'),
		'cancel_reason': fields.many2one('foms.order.cancel.reason', 'Cancel Reason'),
		'cancel_reason_other': fields.text('Other Cancel Reason'),
		'cancel_date': fields.datetime('Cancel Date'),
		'cancel_by': fields.many2one('res.users', 'Cancel By', ondelete='restrict'),
		'cancel_previous_state': fields.selection(_ORDER_STATE, 'Previous State'),
		'alloc_unit_id': fields.many2one('foms.contract.alloc.unit', 'Alloc Unit', ondelete='restrict'),
		'alloc_unit_usage': fields.float('Allocation Unit Usage'),
		'route_id': fields.many2one('res.partner.route', 'Route', ondelete='cascade'),
		'origin_location_id': fields.many2one('res.partner.location', 'Origin Location', ondelete='set null'),
		'origin_location': fields.char('Origin Location'),
		'dest_location_id': fields.many2one('res.partner.location', 'Destination Location', ondelete='set null'),
		'dest_location': fields.char('Destination Location'),
		'order_type_by_order': fields.selection([
			('one_way_drop_off','One-way Drop Off'),
			('one_way_pickup','One-way Pick-up'),
			('two_way','Two Way')], 'Order Type by Order'),
		'passenger_count': fields.integer('Passenger Count'),
		'is_orderer_passenger': fields.boolean('Orderer Is Passenger?'),
		'passengers': fields.one2many('foms.order.passenger', 'header_id', 'Passengers'),
		'assigned_vehicle_id': fields.many2one('fleet.vehicle', 'Assigned Vehicle', ondelete='restrict'),
		'assigned_driver_id': fields.many2one('hr.employee', 'Assigned Driver', ondelete='restrict'),
		'actual_vehicle_id': fields.many2one('fleet.vehicle', 'Actual Vehicle', ondelete='restrict'),
		'actual_driver_id': fields.many2one('hr.employee', 'Actual Driver', ondelete='restrict'),
		'pin': fields.char('PIN'),
		'start_planned_date': fields.datetime('Start Planned Date'),
		'finish_planned_date': fields.datetime('Finish Planned Date'),
		'start_date': fields.datetime('Start Date'),
		'start_confirm_date': fields.datetime('Start Confirm Date'),
		'start_confirm_by': fields.many2one('res.users', 'Start Confirm By', ondelete='set null'),
		'start_from': fields.selection([
			('mobile','Mobile App'),
			('central','Central Dispatch'),], 'Start From'),
		'finish_date': fields.datetime('Finish Date'),
		'finish_confirm_date': fields.datetime('Finish Confirm Date'),
		'finish_confirm_by': fields.many2one('res.users', 'Finish Confirm By', ondelete='set null'),
		'finish_from': fields.selection([
			('mobile','Mobile App'),
			('central','Central Dispatch'),], 'Finish From'),
		'pause_count': fields.integer('Pause Count'),
		'is_lk_pp': fields.boolean('Luar Kota PP?'),
		'is_lk_inap': fields.boolean('Luar Kota Menginap?'),
		
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'request_date': lambda *a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
		'order_by': lambda self, cr, uid, ctx: uid,
		'state': 'new',
		'pause_count': 0,
		'is_lk_pp': False,
		'is_lk_inap': False,
	}	

# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context=None):
		new_id = super(foms_order, self).create(cr, uid, vals, context=context)
		new_data = self.browse(cr, uid, new_id, context=context)
	# untuk order fullday diasumsikan sudah ready karena vehicle dan drivernya pasti standby kecuali nanti diganti
		if new_data.service_type == 'full_day':
			self.write(cr, uid, [new_id], {
				'state': 'ready',
			})
		return new_id
	
	def write(self, cr, uid, ids, vals, context=None):
		result = super(foms_order, self).write(cr, uid, ids, vals, context=context)
		orders = self.browse(cr, uid, ids, context=context)
	# kalau status berubah menjadi ready, maka post ke mobile app
		if vals.get('state', False) == 'ready':
			for order_data in orders:
			# kalau fullday karena langsung ready maka asumsinya di mobile app belum ada order itu. maka commandnya adalah create
				if order_data.service_type == 'full_day':
					self.webservice_post(cr, uid, ['pic','driver'], 'create', order_data, context=context)
			# untuk by order ... (dilanjut nanti)
		if context.get('from_webservice') == True:
			sync_obj = self.pool.get('chjs.webservice.sync.bridge')
			user_id = context.get('user_id', uid)
		# kalau ngubah start_date atau finish_date dan dari webservice, maka post ke mobile app pic, approver, booker
			if vals.get('start_date') or vals.get('finish_date'):
				for order_data in orders:
				# kalau yang ngupdate driver maka perintahkan update juga ke pic
					if user_obj.has_group(cr, user_id, 'universal.group_universal_driver'):
						self.webservice_post(cr, uid, ['pic','approver','booker'], 'update', order_data, context=context)
		return result
	
	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		user_obj = self.pool.get('res.users')
		contract_obj = self.pool.get('contract')
	# kalau diminta untuk mengambil semua kontrak by user_id tertentu
		if context.get('by_user_id',False):
			domain = []
			user_id = context.get('user_id', uid)
			is_pic = user_obj.has_group(cr, user_id, 'universal.group_universal_customer_pic')
			is_approver = user_obj.has_group(cr, user_id, 'universal.group_universal_approver')
			is_driver = user_obj.has_group(cr, user_id, 'universal.group_universal_driver')
			is_booker = user_obj.has_group(cr, user_id, 'universal.group_universal_booker')
		# kalau pic, domainnya menjadi semua order dengan contract yang pic nya adalah partner terkait
			if is_pic:
				user_data = user_obj.browse(cr, uid, user_id)
				if user_data.partner_id:
					contract_ids = contract_obj.search(cr, uid, [('customer_contact_id','=',user_data.partner_id.id)])
					domain.append(('customer_contract_id','in',contract_ids))
		# kalau driver, domainnya menjadi semua order yang di-assign ke dia, atau actual nya dia
			if is_driver:
				employee_obj = self.pool.get('hr.employee')
				employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
				if len(employee_ids) > 0:
					domain = [
						'|',
						('assigned_driver_id','=',employee_ids[0]),
						('actual_driver_id','=',employee_ids[0]),
					]
			if len(domain) > 0:
				args = domain + args
			else:
				return []
		return super(foms_contract, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
		
# CRON ---------------------------------------------------------------------------------------------------------------------

	def cron_autogenerate_fullday(self, cr, uid, context=None):
		
		def get_contract_workdays(contract_data):
		# return dict of workday dengan key=workday (0,1,2,3,4 - senin selasa rabu, dst) dan value {start, finish}
			if not contract_data.working_time_id: return {}
			working_days = {}
			for working_time in contract_data.working_time_id.attendance_ids:
				if working_time.working_time_type == 'duration':
					start = working_time.hour_from
					end = working_time.hour_to
				elif working_time.working_time_type == 'max_hour':
					start = working_time.hour_from
					end = working_time.hour_from + working_time.max_hour
				working_days.update({int(working_time.dayofweek): {
					'start': start,
					'end': end,
				}})
		# nanti dulu
			holidays = []
			for holiday in contract_data.working_time_id.leave_ids:
				date_from = (datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)).replace(hour=0,minute=0,second=0)
				date_to = (datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S") + timedelta(hours=7)).replace(hour=23,minute=59,second=59)
				day = date_from
				while day < date_to:
					holidays.append(day)
					day = day + timedelta(hours=24)
			return working_days, holidays
		
		def next_workday(work_date, working_day_keys, holidays):
			while work_date in holidays: work_date = work_date + timedelta(hours=24)
			while work_date.weekday() not in working_day_keys: work_date = work_date + timedelta(hours=24)
			return work_date
			
		contract_obj = self.pool.get('foms.contract')
		order_obj = self.pool.get('foms.order')
	# bikin order fullday untuk n hari ke depan secara berkala
	# set tanggal2
		today = (datetime.now() - timedelta(hours=7)).replace(hour=0, minute=0, second=0, microsecond=0)
		next_day = today + timedelta(hours=24)
		next7days = today + timedelta(hours=24*7)
	# ambil contract yang baru aktif (last_fullday_autogenerate_date kosong)
		contract_ids = contract_obj.search(cr, uid, [
			('service_type','=','full_day'),('state','in',['active','planned']),
			('start_date','<=',next7days.strftime('%Y-%m-%d'))
		])
		if len(contract_ids) > 0:
			for contract in contract_obj.browse(cr, uid, contract_ids):
			# ambil working days dan holidays
				working_days, holidays = get_contract_workdays(contract)
				working_day_keys = working_days.keys()
				contract_start_date = datetime.strptime(contract.start_date,"%Y-%m-%d")
				last_fullday_autogenerate = contract.last_fullday_autogenerate_date and datetime.strptime(contract.last_fullday_autogenerate_date,'%Y-%m-%d') or None
			# tentukan first order date dan mau berapa banyak bikin ordernya
				last_order_date = last_fullday_autogenerate or datetime.strptime('1970-01-01','%Y-%m-%d') + timedelta(hours=24)
				if not contract.last_fullday_autogenerate_date:
					first_order_date = max([contract_start_date, last_order_date, today])
					max_orders = 7
				else:
					first_order_date = last_order_date + timedelta(hours=24)
					max_orders = 1 # kalo udah pernah autogenerate maka cukup generate satu hari berikutnya
				first_order_date = next_workday(first_order_date, working_day_keys, holidays)
			# kalo last generatenya masih kejauhan (lebih dari 7 hari) maka ngga usah generate dulu, bisi kebanyakan
				if last_fullday_autogenerate and first_order_date > next7days: 
					print "No generate -------------------------------------"
					return
			# mulai bikin order satu2
				day = 1
				counter_date = first_order_date
				while day <= max_orders:
					for fleet in contract.car_drivers:
						new_id = order_obj.create(cr, uid, {
							'name': 'XXX',
							'customer_contract_id': contract.id,
							'service_type': contract.service_type,
							'request_date': counter_date,
							'order_by': uid,
							'assigned_vehicle_id': fleet.fleet_vehicle_id.id,
							'assigned_driver_id': fleet.driver_id.id,
							'pin': contract.default_pin,
							'start_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['start']) - timedelta(hours=7),
							'finish_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['end']) - timedelta(hours=7),
						}, context=context)
					last_fullday = counter_date
					counter_date = counter_date + timedelta(hours=24)
					counter_date = next_workday(counter_date, working_day_keys, holidays)
					day += 1
			# update last_fullday_autogenerate_date untuk kontrak ini
				print "Last fullday: %s" % last_fullday
				contract_obj.write(cr, uid, [contract.id], {
					'last_fullday_autogenerate_date': last_fullday
				})

# SYNCRONIZER MOBILE APP ---------------------------------------------------------------------------------------------------

	def webservice_post(self, cr, uid, targets, command, order_data, context=None):
		sync_obj = self.pool.get('chjs.webservice.sync.bridge')
		user_obj = self.pool.get('res.users')
		if 'pic' in targets:
			pic_user_ids = user_obj.search(cr, uid, [('partner_id','=',order_data.customer_contract_id.customer_contact_id.id)])
			if len(pic_user_ids) > 0:
				sync_obj.post_outgoing(cr, pic_user_ids[0], 'foms.order', command, order_data.id)
		if 'driver' in targets:
			if order_data.assigned_driver_id:
				driver_user_id = order_data.assigned_driver_id.user_id.id
				sync_obj.post_outgoing(cr, driver_user_id, 'foms.order', command, order_data.id)
		if 'approver' in targets:
			if order_data.confirm_by:
				approver_user_id = order_data.confirm_by.id
				sync_obj.post_outgoing(cr, approver_user_id, 'foms.order', command, order_data.id)
		if 'booker' in targets:
			if order_data.order_by:
				booker_user_id = order_data.order_by.id
				sync_obj.post_outgoing(cr, booker_user_id, 'foms.order', command, order_data.id)
			

# ==========================================================================================================================

class foms_order_passenger(osv.osv):

	_name = "foms.order.passenger"
	_description = 'Forms Order Passenger'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.order', 'Forms Order', required=True, ondelete='cascade'),
		'name': fields.char('Name'),
		'phone_no': fields.char('Phone No.'),
		'is_orderer': fields.boolean('Is Orderer'),
	}		
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'is_orderer': False,
	}	
	

# ==========================================================================================================================

class foms_order_cancel_reason(osv.osv):

	_name = "foms.order.cancel.reason"
	_description = 'Forms Order Cancel Reason'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Name'),
	}		
	
# ==========================================================================================================================

class foms_order_mass_input_memory(osv.osv_memory):

	_name = "foms.order.mass.input.memory"
	_description = 'Forms Order Mass Input Memory'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('foms.contract', 'Contract'),
		'customer_id': fields.many2one('res.partner', 'Customer'),
		'order_details': fields.one2many('foms.order.mass.input.memory.line', 'order_id', 'Order'),
	}		
	
# ==========================================================================================================================

class foms_order_mass_input_memory_line(osv.osv_memory):

	_name = "foms.order.mass.input.memory.line"
	_description = 'Forms Order Mass Input Memory Line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'order_id': fields.many2one('foms.order', 'Order'),
		'alloc_unit_id': fields.many2one('foms.contract.alloc.unit', 'Allocation Unit', required=True, ondelete='restrict'),
		'start_date': fields.datetime('Start Date'),
		'finish_date': fields.datetime('Finish Date'),
	}		
	
	
	
