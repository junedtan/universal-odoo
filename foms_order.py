from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp import SUPERUSER_ID

import random, string

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
		'over_quota_status': fields.selection((
			('normal','Normal'),
			('yellow','Yellow Limit'),
			('warning','Over-quota with Warning'),
			('approval','Over-quota with Approval'),
		),'Over-Quota Status', required=True),
		'request_date': fields.datetime('Request Date', required=True),
		'state': fields.selection(_ORDER_STATE, 'State', required=True, track_visiblity="onchange"),
		'order_by': fields.many2one('res.users', 'Order By', ondelete='restrict'),
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
		'origin_area_id': fields.many2one('foms.order.area', 'Origin Area', ondelete='set null'),
		'origin_location': fields.char('Origin Location'),
		'dest_area_id': fields.many2one('foms.order.area', 'Destination Area', ondelete='set null'),
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
		'create_source': fields.selection((
			('app', 'Mobile App'),
			('central', 'Central'),
		), 'Create Source', readonly=True),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'request_date': lambda *a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
		'order_by': lambda self, cr, uid, ctx: uid,
		'state': 'new',
		'pause_count': 0,
		'is_lk_pp': False,
		'is_lk_inap': False,
		'create_source': 'central',
		'over_quota_status': 'normal',
	}	

# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_start_end_date','CHECK(finish_planned_date > start_planned_date)',_('Finish data must be after start date.')),
	]
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, vals['customer_contract_id'])
	# tanggal order tidak boleh lebih dari tanggal selesai 
		if contract_data.state in ['prolonged','terminated','finished']:
			raise osv.except_osv(_('Order Error'),_('Contract has already been inactive. You cannot place order under this contract anymore. Please choose another contract or contact your PIC.'))
	# untuk order by order, harus dicek dulu bahwa order harus dalam maksimal jam sebelumnya
		if vals.get('service_type', False) == 'by_order':
		# cek start date harus sudah ada
			if not vals.get('start_planned_date', False):
				raise osv.except_osv(_('Order Error'),_('Please input start date.'))
			start_date = datetime.strptime(vals['start_planned_date'],'%Y-%m-%d %H:%M:%S')
		# cek start date harus minimal n jam dari sekarang
			now = datetime.now()
			delta = float((start_date - now).days * 86400 + (start_date - now).seconds) / 3600
			if delta < contract_data.by_order_minimum_hours:
				raise osv.except_osv(_('Order Error'),_('Start date is too close to current time. There must be at least %s hours between now and start date.' % contract_data.by_order_minimum_hours))
		# kalau usage control diaktifkan, isi over_quota_status
			if contract_data.usage_control_level != 'no_control':
				quota_obj = self.pool.get('foms.contract.quota')
				current_quota = quota_obj.get_current_quota_usage(cr, uid, vals['customer_contract_id'], vals['alloc_unit_id'])
				if not current_quota:
					raise osv.except_osv(_('Order Error'),_('Quota for this month has not been set. Please contact PT Universal.'))
				over_quota_status = 'normal'
				after_usage = current_quota.balance_credit_per_usage + current_quota.current_usage
				if after_usage >= current_quota.red_limit:
					if contract_data.usage_control_level == 'warning':
						over_quota_status = 'warning'
					elif contract_data.usage_control_level == 'approval':
						over_quota_status = 'approval'
				elif after_usage >= current_quota.yellow_limit:
					over_quota_status = 'yellow'
				vals.update({
					'alloc_unit_usage': current_quota.balance_credit_per_usage,
					'over_quota_status': over_quota_status,
				})
	# bikin nomor order dulu
		if 'name' not in vals:
			vals.update({'name': 'XXX'}) # later
	# jalankan createnya
		new_id = super(foms_order, self).create(cr, uid, vals, context=context)
		new_data = self.browse(cr, uid, new_id, context=context)
	# untuk order fullday diasumsikan sudah ready karena vehicle dan drivernya pasti standby kecuali nanti diganti.
	# pula, berdasarkan order_by dan customer_contract_id, tentukan assigned_driver_id dan assigned_vehicle_id
		if new_data.service_type == 'full_day':
			fleet_data = None
			for fleet in new_data.customer_contract_id.car_drivers:
				if fleet.fullday_user_id.id == new_data.order_by.id:
					fleet_data = fleet
					break
			if fleet_data:
				self.write(cr, uid, [new_id], {
					'assigned_driver_id': fleet_data.driver_id.id,
					'assigned_vehicle_id': fleet_data.fleet_vehicle_id.id,
					'pin': fleet_data.fullday_user_id.pin,
				}) # sengaja ngga pake konteks supaya baik dari autogenerate order maupun manual via app tidak akan broadcast
			self.write(cr, uid, [new_id], {
				'state': 'ready',
			}, context=context)
	# untuk order By Order, post notification ke approver yang ada + bookernya untuk konfirmasi order sudah masuk
		if new_data.service_type == 'by_order':
			webservice_context = {
					'notification': 'order_approve',
			}
		# kalau usage control di-on-kan, ada sedikit perbedaan di notificationnya
			if new_data.customer_contract_id.usage_control_level != 'no_control':
				if new_data.over_quota_status in ['warning','approval']:
					quota_obj = self.pool.get('foms.contract.quota')
					quota_ids = quota_obj.search(cr, uid, [
						('customer_contract_id','=',new_data.customer_contract_id.id),
						('allocation_unit_id','=',new_data.alloc_unit_id.id),
						('period','=',datetime.strptime(new_data.request_date,'%Y-%m-%d %H:%M:%S').strftime('%m/%Y')),
					])
					if len(quota_ids) > 0:
						quota_data = quota_obj.browse(cr, uid, quota_ids[0])
						red_limit = quota_data.red_limit
					else:
						red_limit = 0
					webservice_context = {
						'notification': 'order_over_quota_%s' % new_data.over_quota_status,
						'order_usage': new_data.alloc_unit_usage,
						'red_limit': red_limit,
					}
			self.webservice_post(cr, uid, ['approver'], 'create', new_data, \
				webservice_context=webservice_context, context=context)
		# tetep notif ke booker bahwa ordernya udah masuk
			self.webservice_post(cr, uid, ['booker'], 'update', new_data, \
				webservice_context={
						'notification': 'order_waiting_approve',
				}, context=context)
		return new_id
	
	def write(self, cr, uid, ids, vals, context={}):
		
		context = context and context or {}
		
		orders = self.browse(cr, uid, ids)

		user_obj = self.pool.get('res.users')

	# kalau ada perubahan start_planned_date, ambil dulu planned start date aslinya
		original_start_date = {}
		if vals.get('start_planned_date', False):
			for data in orders:
				original_start_date.update({data.id: data.start_planned_date})
	
	# kalau order diconfirm dari mobile app, cek dulu apakah sudah diconfirm sebelumnya
	# ini untuk mengantisipasi kalau satu alloc unit ada beberapa approver dan pada balapan meng-approve
		if vals.get('state', False) == 'confirmed' and context.get('from_webservice') == True:
			for data in orders:
				if data.state == 'confirmed':
					context.update({
						'target_user_id': context.get('user_id', uid),
					})
					self.webservice_post(cr, uid, ['approver'], 'update', data, \
						data_columns=['state'],
						webservice_context={
								'notification': 'order_other_approved',
						}, context=context)
					return True
	
	# eksekusi write nya dan ambil ulang data hasil update
		result = super(foms_order, self).write(cr, uid, ids, vals, context=context)
		orders = self.browse(cr, uid, ids, context=context)
	# kalau ada perubahan status...
		if vals.get('state', False):
			for order_data in orders:
				contract = order_data.customer_contract_id
			# kalau status berubah menjadi ready, maka post ke mobile app
				if vals['state'] == 'ready':
				# kalau fullday karena langsung ready maka asumsinya di mobile app belum ada order itu. maka commandnya adalah create
					if order_data.service_type == 'full_day':
						self.webservice_post(cr, uid, ['pic','driver','fullday_passenger'], 'create', order_data, context=context)
				# kalau yang by order, sebelum ready order belum ada di pic dan driver, maka create
				# tapi udah ada di booker dan approver, maka update
				# driver diikutsertakan di update supaya dia muncul notifnya. di mobile app sudah ada logic bahwa kalau command = update 
				# dan data belum ada maka create. so practically utk driver ya create juga
					elif order_data.service_type == 'by_order':
						self.webservice_post(cr, uid, ['pic'], 'create', order_data, context=context)
						self.webservice_post(cr, uid, ['booker'], 'update', order_data, 
							webservice_context={
								'notification': 'order_ready_booker',
							}, context=context)
						self.webservice_post(cr, uid, ['approver'], 'update', order_data, 
							webservice_context={
								'notification': 'order_ready_approver',
							}, context=context)
						self.webservice_post(cr, uid, ['driver'], 'update', order_data, 
							webservice_context={
								'notification': 'order_ready_driver',
							}, context=context)
			# kalau state menjadi rejected dan service_type == by_order, maka post_outgoing + notif ke booker. 
				elif vals['state'] == 'rejected' and order_data.service_type == 'by_order':
					self.webservice_post(cr, uid, ['booker'], 'update', order_data, \
						data_columns=['state'], 
						webservice_context={
								'notification': 'order_reject',
						}, context=context)
			# kalau order di-confirm (khusus service type By Order)
				elif vals['state'] == 'confirmed' and order_data.service_type == 'by_order':
					user_id = context.get('user_id', uid)
				# isi data konfirmasi
					super(foms_order, self).write(cr, uid, [order_data.id], {
						'confirm_by': user_id,
						'confirm_date': datetime.now(),
					}, context=context)
				# masukin ke usage log, bila memang pakai usage control
					if contract.usage_control_level != 'no_control':
						usage_log_obj = self.pool.get('foms.contract.quota.usage.log')
						usage_log_obj.create(cr, uid, {
							'usage_date': datetime.now(),
							'order_id': order_data.id,
							'customer_contract_id': contract.id,
							'allocation_unit_id': order_data.alloc_unit_id.id,
							'period': datetime.now().strftime('%m/%Y'),
							'usage_amount': order_data.alloc_unit_usage,
						})
				# apakah source_area dan dest_area ada di bawah homebase yang sama?
				# kalo sama, langsung cariin mobil dan supir
					central_user_ids = user_obj.get_user_ids_by_group(cr, uid, 'universal', 'group_universal_central_dispatch')
					central_user_ids += [SUPERUSER_ID]
					if order_data.origin_area_id and order_data.dest_area_id and \
					order_data.origin_area_id.homebase_id.id == order_data.dest_area_id.homebase_id.id:
					# cari vehicle dan driver yang available di jam itu
						vehicle_id, driver_id = self.search_first_available_fleet(cr, uid, order_data.customer_contract_id.id, order_data.id, order_data.start_planned_date)
					# kalo ada, langsung jadi ready
					# sengaja pake self bukan super supaya kena webservice_post
						if vehicle_id and driver_id:
							self.write(cr, uid, [order_data.id], {
								'assigned_vehicle_id': vehicle_id,
								'assigned_driver_id': driver_id,
								'state': 'ready',
								'pin': self._generate_random_pin(),
							}, context=context)
					# kalau tidak ada, kirim message ke central dispatch dan notif ke booker dan approver
						else:
							self.webservice_post(cr, uid, ['booker','approver'], 'update', order_data, 
								webservice_context={
										'notification': 'order_fleet_not_ready',
								}, context=context)
							for central_user_id in central_user_ids:
								self.message_post(cr, central_user_id, order_data.id, body=_('Cannot allocate vehicle and driver for order %s. Please allocate them manually.') % order_data.name)
							return result
				# kalo beda homebase, post message 
					else:
						for central_user_id in central_user_ids:
							self.message_post(cr, central_user_id, order_data.id, body=_('New order from %s going to different homebase. Manual vehicle/driver assignment needed.') % order_data.customer_contract_id.customer_id.name)
			# kalau jadi start atau start confirmed dan actual vehicle atau driver masih kosong, maka isikan
				elif vals['state'] in ['started','start_confirmed','finished','finish_confirmed']:
					update_data = {}
					if not order_data.actual_driver_id:
						update_data.update({
							'actual_driver_id': order_data.assigned_driver_id.id,
						})
					if not order_data.actual_vehicle_id:
						update_data.update({
							'actual_vehicle_id': order_data.assigned_vehicle_id.id,
						})
					super(foms_order, self).write(cr, uid, [order_data.id], update_data, context={})
			# kalau dibatalin dan ini adalah by_order
				elif vals['state'] == 'canceled' and order_data.service_type == 'by_order':
				# kalau kontraknya pakai usage control, maka hapus dari usage log
					if contract.usage_control_level != 'no_control':
						usage_log_obj = self.pool.get('foms.contract.quota.usage.log')
						usage_log_ids = usage_log_obj.search(cr, uid, [('order_id','=',order_data.id)])
						if len(usage_log_ids) > 0:
							usage_log_obj.unlink(cr, uid, usage_log_ids, context=context)
					self.webservice_post(cr, uid, ['pic','driver','booker','approver'], 'update', order_data, context=context)
				else:
					self.webservice_post(cr, uid, ['pic','driver','fullday_passenger'], 'update', order_data, context=context)
			
	# kalau ada perubahan start_planned_date
		if vals.get('start_planned_date'):
			for order_data in orders:
			# message_post supaya kedeteksi perubahannya
				original = (datetime.strptime(original_start_date[order_data.id],'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S')
				new = (datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S')
				if context.get('from_webservice') == True:
					message_body = _("Planned start date is changed from %s to %s as requested by client.") % (original,new)
				else:
					message_body = _("Planned start date is changed from %s to %s.") % (original,new)
				self.message_post(cr, uid, order_data.id, body=message_body)
			# kalau ngubah tanggal planned, post ke pic, passenger, dan driver
				self.webservice_post(cr, uid, ['pic','fullday_passenger','driver','booker','approver'], 'update', order_data, \
					data_columns=['start_planned_date'], 
					webservice_context={
						'notification': 'order_change_date',
					}, context=context)
			
	# kalau ada perubahan pin, broadcast ke pihak ybs
		if vals.get('pin', False):
			for order_data in orders:
				self.webservice_post(cr, uid, ['pic','fullday_passenger','driver'], 'update', order_data, data_columns=['pin'], context=context)
				
	# kalau ngubah start_date atau finish_date maka post ke mobile app pic, approver, booker
		if vals.get('start_date') or vals.get('finish_date'):
			for order_data in orders:
				if user_obj.has_group(cr, context.get('user_id', uid), 'universal.group_universal_driver'):
					self.webservice_post(cr, uid, ['pic','approver','booker','fullday_passenger','driver'], 'update', order_data, \
						data_columns=['start_date','finish_date'], context=context)

	# kalau ada perubahan assigned_vehicle_id dan assigned_driver_id
		if vals.get('assigned_vehicle_id', False) and vals.get('assigned_driver_id', False):
			for order_data in orders:
			# untuk by_order yang masih new, directly ubah state menjadi ready
				if order_data.service_type == 'by_order' and order_data.state in ['new','confirmed']:
					self.write(cr, uid, [order_data.id], {
						'state': 'ready',
						'pin': self._generate_random_pin(),
					}, context=context)
					
		return result
	
	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		context = context and context or {}
		user_obj = self.pool.get('res.users')
		contract_obj = self.pool.get('foms.contract')
	# kalau diminta untuk mengambil semua order by user_id tertentu
		if context.get('by_user_id',False):
			domain = []
			user_id = context.get('user_id', uid)
			is_pic = user_obj.has_group(cr, user_id, 'universal.group_universal_customer_pic')
			is_approver = user_obj.has_group(cr, user_id, 'universal.group_universal_approver')
			is_driver = user_obj.has_group(cr, user_id, 'universal.group_universal_driver')
			is_booker = user_obj.has_group(cr, user_id, 'universal.group_universal_booker')
			is_fullday_passenger = user_obj.has_group(cr, user_id, 'universal.group_universal_passenger')
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
		# kalau passenger, ambil semua order yang order_by nya dia
			if is_fullday_passenger or is_booker:
				domain = [
					('order_by','=',user_id)
				]
		# kalau approver, ambil semua order yang allocation unit nya di bawah dia
			if is_approver:
				cr.execute("SELECT * FROM foms_alloc_unit_approvers WHERE user_id = %s" % user_id)
				approver_alloc_units = []
				for row in cr.dictfetchall():
					approver_alloc_units.append(row['alloc_unit_id'])
				domain = [
					('alloc_unit_id','in',approver_alloc_units)
				]
			if len(domain) > 0:
				args = domain + args
			else:
				return []
		return super(foms_order, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

	def webservice_handle(self, cr, uid, user_id, command, data_id, model_data, context={}):
		result = super(foms_order, self).webservice_handle(cr, uid, user_id, command, data_id, model_data, context=context)
	# ambil master cancel reason
		if command == 'cancel_reasons':
			cancel_reason_obj = self.pool.get('foms.order.cancel.reason')
			cancel_reason_ids = cancel_reason_obj.search(cr, uid, [])
			result = []
			for cancel_reason in cancel_reason_obj.browse(cr, uid, cancel_reason_ids):
				result.append({
					'id': cancel_reason.id,
					'name': cancel_reason.name,
				})
	# eksekusi cancel order
		elif command == 'cancel_order':
			model_data.update({
				'order_id': data_id,
				'cancel_by': user_id,
			})
			cancel_memory_obj = self.pool.get('foms.order.cancel.memory')
			result = cancel_memory_obj.action_execute_cancel(cr, uid, [], model_data)
			if result == True: result = 'ok'
	# list order area
		elif command == 'order_areas':
			area_obj = self.pool.get('foms.order.area')
			area_ids = area_obj.search(cr, uid, [])
			result = []
			for area in area_obj.browse(cr, uid, area_ids):
				result.append({
					'id': area.id,
					'homebase_id': area.homebase_id.id,
					'name': area.name,
				})
		return result

# METHODS ------------------------------------------------------------------------------------------------------------------

	def search_first_available_fleet(self, cr, uid, contract_id, order_id, start_planned_date):
		area_delay_obj = self.pool.get('foms.order.area.delay')
	# ambil semua order yang lagi jalan
		ongoing_order_ids = self.search(cr, uid, [
			('customer_contract_id','=',contract_id),
			('state','in',['ready', 'started', 'start_confirmed', 'paused', 'resumed', 'finished']),
			('id','!=',order_id),
		])
		vehicle_in_use_ids = []
		current_order = self.browse(cr, uid, order_id)
		for order in self.browse(cr, uid, ongoing_order_ids):
			if order.finish_planned_date >= start_planned_date: continue # udah jelas ngga available
		# perhitungkan delay dari satu area ke area lain
			if order.dest_area_id and current_order.origin_area_id:
				delay = area_delay_obj.get_delay(cr, uid, order.dest_area_id.id, current_order.origin_area_id.id)
				finish_date = datetime.strptime(order.finish_planned_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=delay)
				finish_date = finish_date.strftime('%Y-%m-%d %H:%M:%S')
				if finish_date >= start_planned_date: continue
			if order.assigned_vehicle_id: vehicle_in_use_ids.append(order.assigned_vehicle_id.id)
			if order.actual_vehicle_id: vehicle_in_use_ids.append(order.actual_vehicle_id.id)
		vehicle_in_use_ids = list(set(vehicle_in_use_ids))
	# ambil vehicle pertama yang available
		selected_fleet_line = None
		for fleet in current_order.customer_contract_id.car_drivers:
			if fleet.fleet_vehicle_id.id in vehicle_in_use_ids: continue
			selected_fleet_line = fleet
			break
		if selected_fleet_line:
			return selected_fleet_line.fleet_vehicle_id.id, selected_fleet_line.driver_id.id
		else:
			return None, None
	
	def _generate_random_pin(self):
		return (''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))).replace('0','1')
		
# ACTION -------------------------------------------------------------------------------------------------------------------

	def action_cancel(self, cr, uid, ids, context=None):
		order = self.browse(cr, uid, ids[0])
		return {
			'name': _('Cancel Order'),
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'foms.order.cancel.memory',
			'type': 'ir.actions.act_window',
			'context': {
				'default_order_id': order.id,
				'default_start_planned_date': order.start_planned_date,
				'default_finish_planned_date': order.finish_planned_date,
			},
			'target': 'new',
		}
		
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
		today = (datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
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
					print "No generate order for contract %s -------------------------------------" % contract.name
					continue
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
							'order_by': fleet.fullday_user_id.id,
							'assigned_vehicle_id': fleet.fleet_vehicle_id.id,
							'assigned_driver_id': fleet.driver_id.id,
							'pin': fleet.fullday_user_id.pin,
							'start_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['start']) - timedelta(hours=7),
							'finish_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['end']) - timedelta(hours=7),
						}, context=context)
					last_fullday = counter_date
					counter_date = counter_date + timedelta(hours=24)
					counter_date = next_workday(counter_date, working_day_keys, holidays)
					day += 1
			# update last_fullday_autogenerate_date untuk kontrak ini
				contract_obj.write(cr, uid, [contract.id], {
					'last_fullday_autogenerate_date': last_fullday
				})

# SYNCRONIZER MOBILE APP ---------------------------------------------------------------------------------------------------

	def webservice_post(self, cr, uid, targets, command, order_data, webservice_context={}, data_columns=[], context={}):
		sync_obj = self.pool.get('chjs.webservice.sync.bridge')
		user_obj = self.pool.get('res.users')
	# user spesifik
		target_user_ids = context.get('target_user_id', [])
		if target_user_ids:
			if isinstance(target_user_ids, (int, long)): target_user_ids = [target_user_ids]
	# massal tergantung target
		else:
			if 'pic' in targets:
				target_user_ids += user_obj.search(cr, uid, [('partner_id','=',order_data.customer_contract_id.customer_contact_id.id)])
			if 'driver' in targets:
				if order_data.assigned_driver_id:
					target_user_ids += [order_data.assigned_driver_id.user_id.id]
			if 'approver' in targets:
				if order_data.confirm_by:
					target_user_ids += [order_data.confirm_by.id]
				else:
					alloc_unit_id = order_data.alloc_unit_id and order_data.alloc_unit_id.id or None
					if alloc_unit_id:
						cr.execute("SELECT * FROM foms_alloc_unit_approvers WHERE alloc_unit_id = %s" % alloc_unit_id)
						for row in cr.dictfetchall():
							target_user_ids.append(row['user_id'])
			if 'booker' in targets or 'fullday_passenger' in targets:
				if order_data.order_by:
					target_user_ids += [order_data.order_by.id]
		if len(target_user_ids) > 0:
			for user_id in target_user_ids:
				print "======================================================================================"
				print command
				print order_data.id
				print user_id
				print webservice_context
				sync_obj.post_outgoing(cr, user_id, 'foms.order', command, order_data.id, data_columns=data_columns, data_context=webservice_context)

# ==========================================================================================================================

class foms_order_area(osv.osv):

	_name = "foms.order.area"
	_description = 'Order Area'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'homebase_id': fields.many2one('chjs.region', 'Homebase', required=True, ondelete='restrict'),
		'name': fields.char('Area Name', required=True),
	}		
	
# ==========================================================================================================================

class foms_order_area_delay(osv.osv):

	_name = "foms.order.area.delay"
	_description = 'Order Area Delay'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'area_from_id': fields.many2one('foms.order.area', 'From Area', required=True, ondelete='set null'),
		'area_to_id': fields.many2one('foms.order.area', 'To Area', required=True, ondelete='set null'),
		'delay': fields.integer('Delay (minutes)', required=True),
	}
	
	_sql_constraints = [
		('const_area_from_to','UNIQUE(area_from_id,area_to_id)',_('A From-To Area pair cannot be set more than once.')),
	]
	
# METHODS ------------------------------------------------------------------------------------------------------------------

	def get_delay(self, cr, uid, area_from_id, area_to_id, context={}):
		if not area_from_id or not area_to_id: return 0
		delay_ids = self.search(cr, uid, [('area_from_id','=',area_from_id),('area_to_id','=',area_to_id)])
		if len(delay_ids) == 0:
			return 0
		else:
			delay_data = self.browse(cr, uid, delay_ids[0])
			return delay_data.delay
	
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
	
# ==========================================================================================================================

class foms_order_cancel_memory(osv.osv_memory):

	_name = "foms.order.cancel.memory"
	_description = 'Order Cancel Input Memory'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'order_id': fields.many2one('foms.order', 'Order'),
		'start_planned_date': fields.datetime('Start Date'),
		'finish_planned_date': fields.datetime('Finish Date'),
		'cancel_reason': fields.many2one('foms.order.cancel.reason', 'Cancel Reason'),
		'cancel_reason_other': fields.text('Other Cancel Reason'),
	}		
	
	def action_execute_cancel(self, cr, uid, ids, context={}):
	# kalao ids berisi [] berarti dari mobile app, karena formnya di sono dan dia manggil langsung execute nya
		if ids == []:
			order_id = context.get('order_id')
			cancel_reason = context.get('cancel_reason')
			cancel_reason_other = context.get('cancel_reason_other')
			cancel_by = context.get('cancel_by')
	# kalo ada ids nya maka dari memory form Odoo
		else:
			form_data = self.browse(cr, uid, ids[0])
			order_id = form_data.order_id.id
			cancel_reason = form_data.cancel_reason.id
			cancel_reason_other = form_data.cancel_reason_other
			cancel_by = uid
	# cancel lah is ordernya
		order_obj = self.pool.get('foms.order')
		order_data = order_obj.browse(cr, uid, order_id, context=context)
	# state harus belum start
		if order_data.state not in ['new','rejected','confirmed','ready']:
			raise osv.except_osv(_('Order Error'),_('Order has already ongoing or finished, so it cannot be canceled.'))
	# entah cancel reason atau cancel reason other harus diisi
		if not cancel_reason and not cancel_reason_other:
			raise osv.except_osv(_('Order Error'),_('Please choose Cancel Reason or type in Other Reason.'))
		return order_obj.write(cr, uid, [order_id], {
			'state': 'canceled',
			'cancel_reason': cancel_reason,
			'cancel_reason_other': cancel_reason_other,
			'cancel_date': datetime.now(),
			'cancel_by': cancel_by,
			'cancel_previous_state': order_data.state,
		})
	
	
