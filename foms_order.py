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

# FIELD FUNCTION METHOD ----------------------------------------------------------------------------------------------------

	def _driver_mobile(self, cr, uid, ids, field_name, arg, context={}):
		result = {}
		for row in self.browse(cr, uid, ids, context):
			phones = []
			if row.actual_driver_id:
				if row.actual_driver_id.phone: phones.append(row.actual_driver_id.phone)
				if row.actual_driver_id.mobile_phone2: phones.append(row.actual_driver_id.mobile_phone2)
			elif row.assigned_driver_id:
				if row.assigned_driver_id.phone: phones.append(row.assigned_driver_id.phone)
				if row.assigned_driver_id.mobile_phone2: phones.append(row.assigned_driver_id.mobile_phone2)
			result[row.id] = ",".join(phones)
		return result

	def _customer_name(self, cr, uid, ids, field_name, arg, context):
		result = {}
		for row in self.browse(cr, uid, ids, context):
			result[row.id] = row.customer_contract_id.customer_id.name
		return result

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Order #'),
		'customer_contract_id': fields.many2one('foms.contract', 'Customer Contract', required=True, ondelete='restrict'),
		'customer_name': fields.function(_customer_name, type="char", string="Customer"),
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
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Vehicle Type', ondelete='restrict'),
		'request_date': fields.datetime('Request Date', required=True),
		'state': fields.selection(_ORDER_STATE, 'State', required=True, track_visibility="onchange"),
		'order_by': fields.many2one('res.users', 'Order By', ondelete='restrict'),
		'confirm_date': fields.datetime('Confirm Date'),
		'confirm_by': fields.many2one('res.users', 'Confirm By', ondelete='restrict'),
		'cancel_reason': fields.many2one('foms.order.cancel.reason', 'Cancel Reason'),
		'cancel_reason_other': fields.text('Other Cancel Reason'),
		'cancel_date': fields.datetime('Cancel Date'),
		'cancel_by': fields.many2one('res.users', 'Cancel By', ondelete='restrict'),
		'cancel_previous_state': fields.selection(_ORDER_STATE, 'Previous State'),
		'alloc_unit_id': fields.many2one('foms.contract.alloc.unit', 'Unit', ondelete='restrict'),
		'alloc_unit_usage': fields.float('Unit Usage'),
		'route_id': fields.many2one('res.partner.route', 'Route', ondelete='set null'),
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
		'driver_mobile': fields.function(_driver_mobile, type="char", method=True, string="Driver Phone"),
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
		'pause_minutes': fields.float('Pause Minutes'),
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
		user_obj = self.pool.get('res.users')
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
			delta = float((start_date - now).days * 86400 + (start_date - now).seconds) / 60
			if delta < contract_data.by_order_minimum_minutes:
				raise osv.except_osv(_('Order Error'),_('Start date is too close to current time, or is in the past. There must be at least %s minutes between now and start date.' % contract_data.by_order_minimum_minutes))
		# kalau usage control diaktifkan, isi over_quota_status
			if contract_data.usage_control_level != 'no_control':
				quota_per_usage, over_quota_status = self.determine_over_quota_status(cr, uid, vals['customer_contract_id'], vals['alloc_unit_id'], vals['fleet_type_id'])
				vals.update({
					'alloc_unit_usage': quota_per_usage,
					'over_quota_status': over_quota_status,
				})
	# dicek dahulu apakah waktu order tidak berada di hari libur yang sudah ditentukan di kontrak sebelumnya
		for holiday in contract_data.working_time_id.leave_ids:
			date_from_holiday = datetime.strftime((datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S")).replace(hour=0,minute=0,second=0),"%Y-%m-%d %H:%M:%S")
			date_to_holiday =  datetime.strftime((datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S")).replace(hour=23,minute=59,second=59),"%Y-%m-%d %H:%M:%S")
			if vals.get('start_planned_date', False) and vals['start_planned_date'] >= date_from_holiday and vals['start_planned_date'] <= date_to_holiday:
				raise osv.except_osv(_('Order Error'),_('Cannot create order because today is not in working time.'))
			
	# bikin nomor order dulu
	# format: (Tanggal)(Bulan)(Tahun)(4DigitPrefixCustomer)(4DigitNomorOrder) Cth: 23032017BNPB0001
		if not vals.get('name', False):
			order_date = vals.get('request_date', None)
			if not order_date: order_date = datetime.now()
			if isinstance(order_date, (str,unicode)):
				order_date = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S')
			prefix = "%s%s" % (order_date.strftime('%d%m%Y'), contract_data.customer_id.partner_code.upper())
			order_ids = self.search(cr, uid, [('name','=like',prefix+'%')], order='request_date DESC')
			if len(order_ids) == 0:
				last_number = 1
			else:
				order_data = self.browse(cr, uid, order_ids[0])
				last_number = int(order_data.name[-4:]) + 1
			vals.update({'name': "%s%04d" % (prefix,last_number)}) # later
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
			#kalau dibuat manual dari form, jangan assign driver dan vehicle
				if context.get('source', False) and context['source']=='form':
					self.write(cr, uid, [new_id], {
						'pin': fleet_data.fullday_user_id.pin,
					})
					self.write(cr, uid, [new_id], {
						'state': 'new',
					}, context=context)
				else:
					self.write(cr, uid, [new_id], {
						'assigned_driver_id': fleet_data.driver_id.id,
						'assigned_vehicle_id': fleet_data.fleet_vehicle_id.id,
						'pin': fleet_data.fullday_user_id.pin,
					})
					vals = {'state': 'ready'}
				# Kalau belum ada driver dan vehiclenya, statenya jangan sampai ready
					if not fleet_data.driver_id.id and not fleet_data.fleet_vehicle_id.id:
						vals['state'] = 'new'
					self.write(cr, uid, [new_id], vals, context=context)
	# untuk order By Order
		elif new_data.service_type == 'by_order':
		# cek apakah unit ini punya approver?
			alloc_unit_id = new_data.alloc_unit_id.id
			has_approver = False
			if alloc_unit_id:
				for alloc_unit in new_data.customer_contract_id.allocation_units:
					if alloc_unit.id == alloc_unit_id and len(alloc_unit.approver_ids) > 0:
						has_approver = True
						break
		# kalau allocation unit punya approver
			if has_approver:
			# post notification ke approver yang ada + bookernya untuk konfirmasi order sudah masuk
				webservice_context = {
						'notification': ['order_approve'],
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
							'notification': ['order_over_quota_%s' % new_data.over_quota_status],
							'order_usage': new_data.alloc_unit_usage,
							'red_limit': red_limit,
						}
				self.webservice_post(cr, uid, ['approver'], 'create', new_data, \
					webservice_context=webservice_context, context=context)
			# tetep notif ke booker bahwa ordernya udah masuk
				self.webservice_post(cr, uid, ['booker'], 'update', new_data, \
					webservice_context={
							'notification': ['order_waiting_approve'],
					}, context=context)
		# kalau allocation unit tidak punya approver
			else:
			# langsung confirm order ini
				self.write(cr, uid, [new_id], {
					'state': 'confirmed',
				}, context=context)
		elif new_data.service_type == 'shuttle':
			self.write(cr, uid, [new_id], {
				'state': 'confirmed',
			}, context=context)
		
		#cek apakah ada order yg sudah diplot ke mobil x tapi 1 jam sblm nya order sebelumnya ternyata belom selesai
		if vals.get('service_type', False) in ['full_day', 'by_order'] and vals.get('assigned_vehicle_id', False):
			order_ids = self.search(cr, uid, [
				('state','not in', ['finish_confirmed', 'canceled', 'new', 'rejected', 'confirmed']),
				('assigned_vehicle_id','=', vals.get('assigned_vehicle_id', False)),
			])
			if len(order_ids) > 0:
				order_data = self.browse(cr, uid, order_ids)
				central_partner_ids = user_obj.get_partner_ids_by_group(cr, uid, 'universal', 'group_universal_dispatcher')
				for order in order_data:
					start_planned_date_another_order = datetime.strptime(order.start_planned_date,"%Y-%m-%d %H:%M:%S")
					start_planned_date_self_order    = datetime.strptime(vals.get('start_planned_date', False),"%Y-%m-%d %H:%M:%S")
					delta = float((start_planned_date_self_order - start_planned_date_another_order).days * 86400 + (start_planned_date_self_order - start_planned_date_another_order).seconds) / 60
					partner_ids = []
					if delta < 60:
						for partner_id in central_partner_ids: partner_ids.append((4,partner_id))
						self.message_post(cr, SUPERUSER_ID, order.id,
							body=_('Order %s still not finish and vehicle assigned to this order.') % vals.get('name', False) ,
							partner_ids=partner_ids)
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
								'notification': ['order_other_approved'],
						}, context=context)
					return True

	# kalau order dicancel karena delay excceded, maka isi alasannya sbg delay exceeded
		if vals.get('state', False) == 'canceled' and context.get('delay_exceeded') == True:
		# ambil id untuk alasan pembatalan "Delay time exceeded"
			model_obj = self.pool.get('ir.model.data')
			model, reason_id = model_obj.get_object_reference(cr, uid, 'universal', 'foms_cancel_reason_delay_exceeded')
		# tambahkan cancel reason
			vals.update({
				'cancel_reason': reason_id,
				})

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
								'notification': ['order_ready_booker'],
							}, context=context)
						self.webservice_post(cr, uid, ['approver'], 'update', order_data,
							webservice_context={
								'notification': ['order_ready_approver'],
							}, context=context)
						self.webservice_post(cr, uid, ['driver'], 'update', order_data,
							webservice_context={
								'notification': ['order_ready_driver'],
							}, context=context)
				# kalau shuttle, cukup push data order ini ke app driver
					elif order_data.service_type == 'shuttle':
						self.webservice_post(cr, uid, ['driver'], 'create', order_data, context=context)
			# kalau state menjadi rejected dan service_type == by_order, maka post_outgoing + notif ke booker.
				elif vals['state'] == 'rejected' and order_data.service_type == 'by_order':
					self.webservice_post(cr, uid, ['booker'], 'update', order_data, \
						data_columns=['state'],
						webservice_context={
								'notification': ['order_reject'],
						}, context=context)
					self.webservice_post(cr, uid, ['approver'], 'update', order_data, data_columns=['state'], context=context)
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
					central_partner_ids = user_obj.get_partner_ids_by_group(cr, uid, 'universal', 'group_universal_dispatcher')
					if order_data.origin_area_id and order_data.dest_area_id and \
					order_data.origin_area_id.homebase_id.id == order_data.dest_area_id.homebase_id.id:
					# cari vehicle dan driver yang available di jam itu
						vehicle_id, driver_id = self.search_first_available_fleet(cr, uid, order_data.customer_contract_id.id, order_data.id, order_data.start_planned_date, order_data.fleet_type_id.id)
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
										'notification': ['order_fleet_not_ready'],
								}, context=context)
							partner_ids = []
							for partner_id in central_partner_ids: partner_ids.append((4,partner_id))
							self.message_post(cr, SUPERUSER_ID, order_data.id,
								body=_('Cannot allocate vehicle and driver for order %s. Please allocate them manually.') % order_data.name,
								partner_ids=partner_ids)
							return result
				# kalo beda homebase, post message
					else:
						partner_ids = []
						for partner_id in central_partner_ids: partner_ids.append((4,partner_id))
						self.message_post(cr, SUPERUSER_ID, order_data.id,
							body=_('New order from %s going to different homebase. Manual vehicle/driver assignment needed.') % order_data.customer_contract_id.customer_id.name,
							partner_ids=partner_ids)
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
					if order_data.service_type == 'full_day':
						self.webservice_post(cr, uid, ['pic','driver','fullday_passenger'], 'update', order_data, context=context)
					elif order_data.service_type == 'by_order':
						self.webservice_post(cr, uid, ['pic','approver','booker'], 'update', order_data, context=context)
			# kalau dibatalin
				elif vals['state'] == 'canceled':
				# kalau kontraknya pakai usage control, maka hapus dari usage log
					if order_data.service_type == 'by_order' and contract.usage_control_level != 'no_control':
						usage_log_obj = self.pool.get('foms.contract.quota.usage.log')
						usage_log_ids = usage_log_obj.search(cr, uid, [('order_id','=',order_data.id)])
						if len(usage_log_ids) > 0:
							usage_log_obj.unlink(cr, uid, usage_log_ids, context=context)
					if order_data.service_type == 'full_day':
						targets = ['pic','driver','fullday_passenger']
					elif order_data.service_type == 'by_order':
						targets = ['pic','driver','booker','approver']
					self.webservice_post(cr, uid, targets, 'update', order_data,
						webservice_context={
							'notification': ['order_canceled'],
						}, context=context)
				else:
					if order_data.service_type == 'full_day':
						self.webservice_post(cr, uid, ['pic','driver','fullday_passenger'], 'update', order_data, context=context)
					elif order_data.service_type == 'by_order':
						self.webservice_post(cr, uid, ['pic','booker','approver','driver'], 'update', order_data, context=context)

	# kalau ada perubahan data, lakukan proses khusus tergantung data apa yang berubah, dan broadcast perubahannya
	# ke semua pihak
	# ini sengaja dipisahkan dari yang perubahan status, karena yang perubahan status begitu kompleks
	# memang benar, konsekuensinya bisa ada dua kali broadcast ke user yang sama untuk proses write yang sama
		for order_data in orders:
		# reset variabel broadcast
			broadcast_data_columns = []
			broadcast_notifications = {
				'all': [], 'pic': [], 'fullday_passenger': [], 'driver': [], 'booker': [], 'approver': [],
			}

		# kalau ada perubahan tanggal mulai
			if vals.get('start_planned_date', False):
			# message_post supaya kesimpen perubahannya
				original = (datetime.strptime(original_start_date[order_data.id],'%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M:%S')
				new = (datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M:%S')
				if context.get('from_webservice') == True:
					message_body = _("Planned start date is changed from %s to %s as requested by client.") % (original,new)
				else:
					message_body = _("Planned start date is changed from %s to %s.") % (original,new)
				self.message_post(cr, uid, order_data.id, body=message_body)
			# broadcast
				broadcast_data_columns.append('start_planned_date')
				broadcast_notifications['all'].append('order_change_date')

		# kalau ada perubahan pin, broadcast ke pihak ybs
		# asumsi: untuk by_order PIN tidak bisa diganti
			if vals.get('pin', False):
				broadcast_data_columns.append('pin')

		# kalau ngubah start_date atau finish_date maka broadcast
			if vals.get('start_date') or vals.get('finish_date'):
				broadcast_data_columns += ['start_date','finish_date']

		# kalau ada perubahan assigned_vehicle_id dan assigned_driver_id
			if vals.get('assigned_vehicle_id', False) and vals.get('assigned_driver_id', False):
			# untuk by_order yang masih new, directly ubah state menjadi ready
				if order_data.service_type == 'by_order' and order_data.state in ['new','confirmed']:
					self.write(cr, uid, [order_data.id], {
						'state': 'ready',
						'pin': self._generate_random_pin(),
					}, context=context)
				elif order_data.service_type == 'full_day' and order_data.state in ['new','confirmed']:
					self.write(cr, uid, [order_data.id], {
						'state': 'ready',
					}, context=context)

		# kalau ada perubahan di over_quota_status, kasih tau ke pic dan approver
			if vals.get('over_quota_status', False):
				if order_data.service_type == 'by_order':
					broadcast_data_columns += ['over_quota_status','alloc_unit_usage']

		# finally, broadcast perubahan
			targets = []
			if order_data.service_type == 'full_day':
				targets = ['pic','fullday_passenger','driver']
			elif order_data.service_type == 'by_order':
				targets = ['pic','booker','approver','driver']
			for target in targets:
				notif = broadcast_notifications[target]
				if broadcast_notifications['all']: notif += broadcast_notifications['all']
				self.webservice_post(cr, uid, [target], 'update', order_data, \
					data_columns=broadcast_data_columns,
					webservice_context={
						'notification': notif,
					}, context=context)

	# kalau ada perubahan tanggal mulai
		"""
		if vals.get('start_planned_date'):
			for order_data in orders:
			# message_post supaya kesimpen perubahannya
				original = (datetime.strptime(original_start_date[order_data.id],'%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M:%S')
				new = (datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S')).strftime('%d/%m/%Y %H:%M:%S')
				if context.get('from_webservice') == True:
					message_body = _("Planned start date is changed from %s to %s as requested by client.") % (original,new)
				else:
					message_body = _("Planned start date is changed from %s to %s.") % (original,new)
				self.message_post(cr, uid, order_data.id, body=message_body)
			# kalau ngubah tanggal planned, post ke pic, passenger, dan driver
				self.webservice_post(cr, uid, ['pic','fullday_passenger','driver','booker','approver'], 'update', order_data, \
					data_columns=['start_planned_date'],
					webservice_context={
						'notification': ['order_change_date'],
					}, context=context)
			
	# kalau ada perubahan pin, broadcast ke pihak ybs
	# asumsi: untuk by_order PIN tidak bisa diganti
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
				if order_data.service_type in ['by_order','shuttle'] and order_data.state in ['new','confirmed']:
					self.write(cr, uid, [order_data.id], {
						'state': 'ready',
						'pin': self._generate_random_pin(),
					}, context=context)

	# kalau ada perubahan di over_quota_status, kasih tau ke pic dan approver
		if vals.get('over_quota_status', False):
			for order_data in orders:
				if order_data.service_type == 'by_order':
					self.webservice_post(cr, uid, ['pic','approver'], 'update', order_data, \
						data_columns=['over_quota_status','alloc_unit_usage'], context=context)
		"""
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
			result = cancel_memory_obj.action_execute_cancel(cr, uid, [], model_data, context=context)
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

	def determine_over_quota_status(self, cr, uid, customer_contract_id, allocation_unit_id, fleet_type_id):
		quota_obj = self.pool.get('foms.contract.quota')
		contract_obj = self.pool.get('foms.contract')
	# ambil quota saat ini
		current_quota = quota_obj.get_current_quota_usage(cr, uid, customer_contract_id, allocation_unit_id)
		if not current_quota:
			raise osv.except_osv(_('Order Error'),_('Quota for this month has not been set. Please contact PT Universal.'))
	# untuk kontrak dan kendaraan jenis ini, berapa sih balance per usage nya?
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
		credit_per_usage = -1
		for usage_per_vehicle in contract_data.vehicle_balance_usage:
			if usage_per_vehicle.fleet_vehicle_model_id.id == fleet_type_id:
				credit_per_usage = usage_per_vehicle.credit_per_usage
				break
		if credit_per_usage == -1:
			raise osv.except_osv(_('Order Error'),_('Credit per usage for this type of vehicle has not been set for this contract.'))
	# tentukan status overquota
		over_quota_status = 'normal'
		after_usage = credit_per_usage + current_quota.current_usage
		if after_usage >= current_quota.red_limit:
			if contract_data.usage_control_level == 'warning':
				over_quota_status = 'warning'
			elif contract_data.usage_control_level == 'approval':
				over_quota_status = 'approval'
		elif after_usage >= current_quota.yellow_limit:
			over_quota_status = 'yellow'
		return credit_per_usage, over_quota_status
		
	def search_first_available_fleet(self, cr, uid, contract_id, order_id, fleet_type_id, start_planned_date):
		area_delay_obj = self.pool.get('foms.order.area.delay')
	# ambil semua order yang lagi jalan untuk jenis mobil terpilih
		ongoing_order_ids = self.search(cr, uid, [
			('customer_contract_id','=',contract_id),
			('state','in',['ready', 'started', 'start_confirmed', 'paused', 'resumed', 'finished']),
			('fleet_type_id','=',fleet_type_id),
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
	# ambil vehicle pertama yang available untuk jenis mobil yang diminta
		selected_fleet_line = None
		for fleet in current_order.customer_contract_id.car_drivers:
			if fleet.fleet_vehicle_id.id in vehicle_in_use_ids or fleet.fleet_type_id.id != fleet_type_id: continue
			selected_fleet_line = fleet
			break
		if selected_fleet_line:
			return selected_fleet_line.fleet_vehicle_id.id, selected_fleet_line.driver_id.id
		else:
			return None, None
	
	def _generate_random_pin(self):
		return (''.join(random.choice(string.digits) for _ in range(6))).replace('0','1')
		
# ACTION -------------------------------------------------------------------------------------------------------------------
	
	def action_confirm(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {
			'state': 'confirmed',
			'confirm_by': uid,
			'confirm_date': datetime.now(),
			})

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

	def _get_contract_workdays(self, contract_data):
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
			date_from = (datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S")).replace(hour=0,minute=0,second=0)
			date_to = (datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S")).replace(hour=23,minute=59,second=59)
			day = date_from
			while day < date_to:
				holidays.append(day)
				day = day + timedelta(hours=24)
		return working_days, holidays
	
	def _next_workday(self, work_date, working_day_keys, holidays):
		while work_date in holidays: work_date = work_date + timedelta(hours=24)
		while work_date.weekday() not in working_day_keys: work_date = work_date + timedelta(hours=24)
		return work_date
	
	def cron_autocancel_byorder_orders(self, cr, uid, context=None):
	# ambil semua order yang by_order dan belum start (new, confirmed, ready)
		order_ids = self.search(cr, uid, [
			('service_type','=','by_order'),('state','in',['new','confirmed','ready'])
		])
		if len(order_ids) == 0: return
	# untuk setiap order itu
		for order in self.browse(cr, uid, order_ids):
		# apakah di kontrak ybs setting max_delay_minutes diisi? bila tidak ya sudah ngga usah cancel2an
			if order.customer_contract_id.max_delay_minutes <= 0: continue
		# kalau waktu sekarang sudah melewati batas delay, maka cancel si order
			start = datetime.strptime(order.start_planned_date,'%Y-%m-%d %H:%M:%S')
			if start + timedelta(minutes=order.customer_contract_id.max_delay_minutes) < datetime.now():
				self.write(cr, uid, [order.id], {
					'state': 'canceled',
					'cancel_date': datetime.now(),
					'cancel_by': SUPERUSER_ID,
					'cancel_previous_state': order.state,
					}, context={'delay_exceeded': True})

	def cron_autogenerate_fullday(self, cr, uid, context=None):
		
		contract_obj = self.pool.get('foms.contract')
	# bikin order fullday untuk n hari ke depan secara berkala
	# set tanggal2
		today = (datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
		next_day = today + timedelta(hours=24)
		next7days = today + timedelta(hours=24*1)
	# ambil contract yang baru aktif (last_fullday_autogenerate_date kosong)
		contract_ids = contract_obj.search(cr, uid, [
			('service_type','=','full_day'),('state','in',['active','planned']),
			('start_date','<=',next7days.strftime('%Y-%m-%d'))
		])
		if len(contract_ids) > 0:
			for contract in contract_obj.browse(cr, uid, contract_ids):
			# ambil working days dan holidays
				working_days, holidays = self._get_contract_workdays(contract)
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
				first_order_date = self._next_workday(first_order_date, working_day_keys, holidays)
			# kalo last generatenya masih kejauhan (lebih dari 7 hari) maka ngga usah generate dulu, bisi kebanyakan
				if last_fullday_autogenerate and first_order_date > next7days:
					print "No generate order for contract %s -------------------------------------" % contract.name
					continue
			# mulai bikin order satu2
				day = 1
				counter_date = first_order_date
				while day <= max_orders:
					for fleet in contract.car_drivers:
						new_id = self.create(cr, uid, {
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
					counter_date = self._next_workday(counter_date, working_day_keys, holidays)
					day += 1
			# update last_fullday_autogenerate_date untuk kontrak ini
				contract_obj.write(cr, uid, [contract.id], {
					'last_fullday_autogenerate_date': last_fullday
				})

	def cron_autogenerate_shuttle(self, cr, uid, context=None):
		
		print "mulai cron shuttle"
		
		contract_obj = self.pool.get('foms.contract')
	# bikin order shuttle untuk n hari ke depan secara berkala
	# set tanggal2
		today = (datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
		next_day = today + timedelta(hours=24)
		next7days = today + timedelta(hours=24*7)
	# ambil contract yang baru aktif (last_fullday_autogenerate_date kosong)
		contract_ids = contract_obj.search(cr, uid, [
			('service_type','=','shuttle'),('state','in',['active','planned']),
			('start_date','<=',next7days.strftime('%Y-%m-%d'))
		])
		if len(contract_ids) > 0:
			for contract in contract_obj.browse(cr, uid, contract_ids):
			# ambil working days dan holidays
				working_days, holidays = self._get_contract_workdays(contract)
				working_day_keys = working_days.keys()
				contract_start_date = datetime.strptime(contract.start_date,"%Y-%m-%d")
				last_shuttle_autogenerate = contract.last_shuttle_autogenerate_date and datetime.strptime(contract.last_shuttle_autogenerate_date,'%Y-%m-%d') or None
			# tentukan first order date dan mau berapa banyak bikin ordernya
				last_order_date = last_shuttle_autogenerate or datetime.strptime('1970-01-01','%Y-%m-%d') + timedelta(hours=24)
				if not contract.last_shuttle_autogenerate_date:
					first_order_date = max([contract_start_date, last_order_date, today])
					max_orders = 3
				else:
					first_order_date = last_order_date + timedelta(hours=24)
					max_orders = 1 # kalo udah pernah autogenerate maka cukup generate satu hari berikutnya
				first_order_date = self._next_workday(first_order_date, working_day_keys, holidays)
			# kalo last generatenya masih kejauhan (lebih dari 7 hari) maka ngga usah generate dulu, bisi kebanyakan
				if last_shuttle_autogenerate and first_order_date > next7days:
					print "No generate shuttle order for contract %s -------------------------------------" % contract.name
					continue
			# harus bikin buat hari apa aja?
				schedule_days = {}
				for schedule in contract.shuttle_schedules:
					if schedule.dayofweek == 'A':
						for i in range(0,7):
							key = str(i)
							if key not in schedule_days: schedule_days.update({key: []})
							schedule_days[key].append({
								'sequence': schedule.sequence,
								'route_id': schedule.route_id.id,
								'fleet_vehicle_id': schedule.fleet_vehicle_id.id,
								'departure_time': schedule.departure_time,
								# 'arrival_time': schedule.arrival_time,
							})
					else:
						if schedule.dayofweek not in schedule_days: schedule_days.update({schedule.dayofweek: []})
						schedule_days[schedule.dayofweek].append({
							'sequence': schedule.sequence,
							'route_id': schedule.route_id.id,
							'fleet_vehicle_id': schedule.fleet_vehicle_id.id,
							'departure_time': schedule.departure_time,
							# 'arrival_time': schedule.arrival_time,
						})
			# ambil pasangan fleet - driver, buat di bawah
				fleet_drivers = {}
				for fleet in contract.car_drivers:
					fleet_drivers.update({fleet.fleet_vehicle_id.id: fleet.driver_id.id})
			# mulai bikin order satu2
				day = 1
				counter_date = first_order_date
				while day <= max_orders:
					date_schedule = None
					for dayofweek in schedule_days.keys():
						if int(dayofweek) == counter_date.weekday():
							date_schedule = schedule_days[dayofweek]
							break
					if not date_schedule: continue
					for schedule in date_schedule:
						new_id = self.create(cr, uid, {
							'customer_contract_id': contract.id,
							'service_type': contract.service_type,
							'request_date': counter_date,
							'assigned_vehicle_id': schedule['fleet_vehicle_id'],
							'assigned_driver_id': fleet_drivers[schedule['fleet_vehicle_id']],
							'start_planned_date': counter_date + timedelta(hours=schedule['departure_time']) - timedelta(hours=7),
							# 'finish_planned_date': counter_date + timedelta(hours=schedule['arrival_time']) - timedelta(hours=7),
							'route_id': schedule['route_id'],
						}, context=context)
					last_fullday = counter_date
					counter_date = counter_date + timedelta(hours=24)
					counter_date = self._next_workday(counter_date, working_day_keys, holidays)
					day += 1
			# update last_fullday_autogenerate_date untuk kontrak ini
				contract_obj.write(cr, uid, [contract.id], {
					'last_shuttle_autogenerate_date': last_fullday
				})

# ONCHANGE -----------------------------------------------------------------------------------------------------------------

	def onchange_customer_contract_id(self, cr, uid, ids, customer_contract_id, context=None):
		if not customer_contract_id: return {}
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
		if not contract_data: return {}
	# filter pilihan fleet type
		fleet_type_ids = []
		for fleet in contract_data.fleet_types:
			fleet_type_ids.append(fleet.fleet_type_id.id)
	# filter piliha order origin area
		area_obj = self.pool.get('foms.order.area')
		area_ids = area_obj.search(cr, uid, [('homebase_id','=',contract_data.homebase_id.id)])
	# filter pilihan allocation unit
		allocation_unit_ids = []
		for alloc in contract_data.allocation_units:
			allocation_unit_ids.append(alloc.id)
		return {
			'value': {
				'service_type': contract_data.service_type,
			},
			'domain': {
				'fleet_type_id': [('id','in',fleet_type_ids)],
				'origin_area_id': [('id','in',area_ids)],
				'alloc_unit_id': [('id','in',allocation_unit_ids)],
			}
		}

	def onchange_fleet_type(self, cr, uid, ids, customer_contract_id, fleet_type_id):
		if not fleet_type_id: return {}
	# filter kendaraan yang dipilih
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
		fleet_ids = []
	# cuman yang di bawah kontrak ini,
		for vehicle in contract_data.car_drivers:
			if vehicle.fleet_type_id.id == fleet_type_id:
				fleet_ids.append(vehicle.fleet_vehicle_id.id)
	#... plus semua yang tidak sedang ada di bawah kontrak aktif
		vehicle_obj = self.pool.get('fleet.vehicle')
		vehicle_ids = vehicle_obj.search(cr, uid, [])
		for vehicle in vehicle_obj.browse(cr, uid, vehicle_ids):
			if vehicle.model_id.id != fleet_type_id: continue
			print vehicle.current_contract_id
			if vehicle.current_contract_id == None or vehicle.current_contract_id.state not in ['active','planned']:
				fleet_ids.append(vehicle.id)
		return {
			'domain': {
				'assigned_vehicle_id': [('id','in',fleet_ids)]
			}
		}


	def onchange_assigned_vehicle(self, cr, uid, ids, customer_contract_id, assigned_vehicle_id):
		if not assigned_vehicle_id: return {}
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
		if not contract_data: return {}
	# kalau vehicle ada di bawah kontrak ybs, maka otomatis isi supir "pasangan" nya
		assigned_driver_id = None
		for vehicle in contract_data.car_drivers:
			if vehicle.fleet_vehicle_id.id == assigned_vehicle_id and vehicle.driver_id:
				assigned_driver_id = vehicle.driver_id.id
				break
		if assigned_driver_id:
			return {
				'value': {
					'assigned_driver_id': assigned_driver_id,
				}
			}
		else:
			return {}


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
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------

	_sql_constraints = [
		('unique_name','UNIQUE(homebase_id,name)',_('Name must be unique for each homebase.')),
	]
	
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
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------

	_sql_constraints = [
		('unique_name','UNIQUE(name)',_('Name must be unique.')),
	]
	
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
		'alloc_unit_id': fields.many2one('foms.contract.alloc.unit', 'Unit', required=True, ondelete='restrict'),
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
		}, context=context)

# ==========================================================================================================================

class foms_order_replace_vehicle(osv.osv):

	_name = "foms.order.replace.vehicle"
	_description = 'Order Replace Vehicle'

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'replaced_vehicle_id': fields.many2one('fleet.vehicle', 'Replaced Vehicle'),
		'replacement_vehicle_id': fields.many2one('fleet.vehicle', 'Replacement Vehicle'),
		'replacement_date': fields.datetime('Replacement Date'),
		'replacement_reason': fields.text('foms.order.cancel.reason', 'Replacement Reason'),
	}

# ==========================================================================================================================

class foms_order_replace_driver(osv.osv):
	
	_name = "foms.order.replace.driver"
	_description = 'Order Replace Driver'
	
	# COLUMNS ------------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'replaced_driver_id': fields.many2one('hr.employee', 'Replaced Driver'),
		'replacement_driver_id': fields.many2one('hr.employee', 'Replacement Driver'),
		'replacement_date': fields.datetime('Replacement Date'),
		'replacement_reason': fields.text('foms.order.cancel.reason', 'Replacement Reason'),
	}