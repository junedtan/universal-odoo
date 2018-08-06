from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp import SUPERUSER_ID
from . import SERVER_TIMEZONE
from . import datetime_to_server
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

try:
	import Queue as Q  # ver. < 3.0
except ImportError:
	import queue as Q

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
				if row.actual_driver_id.mobile_phone3: phones.append(row.actual_driver_id.mobile_phone3)
			elif row.assigned_driver_id:
				if row.assigned_driver_id.phone: phones.append(row.assigned_driver_id.phone)
				if row.assigned_driver_id.mobile_phone2: phones.append(row.assigned_driver_id.mobile_phone2)
				if row.assigned_driver_id.mobile_phone3: phones.append(row.assigned_driver_id.mobile_phone3)
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
		'origin_district_id': fields.many2one('chjs.region', 'Origin District', domain=[('type','=','district')]),
		'origin_area_id': fields.many2one('foms.order.area', 'Origin Area', ondelete='set null'),
		'origin_location': fields.char('Origin Location'),
		'dest_district_id': fields.many2one('chjs.region', 'Destination District', domain=[('type','=','district')]),
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
		'purpose_id' : fields.many2one('foms.booking.purpose', 'Booking Purpose', ondelete='SET NULL'),
		'other_purpose': fields.text('Other Purpose'),
		'start_odometer': fields.float('Start Odometer', track_visibility="onchange"),
		'finish_odometer': fields.float('Finish Odometer', track_visibility="onchange"),
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

	_sql_constraints = [
		('const_start_end_date','CHECK(finish_planned_date > start_planned_date)',_('Finish data must be after start date.')),
	]

# OVERRIDES ----------------------------------------------------------------------------------------------------------------

	def create(self, cr, uid, vals, context={}):
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, vals['customer_contract_id'])
		
		service_type = vals.get('service_type', False)
		if not service_type:
			service_type = contract_data.service_type
			vals['service_type'] = contract_data.service_type

		user_obj = self.pool.get('res.users')
		
	# cek dahulu apakah contractnya masih active
		if vals.get('customer_contract_id', False):
			self._cek_contract_is_active(cr,uid, [vals['customer_contract_id']], context)
		
	#cek apakah ada order by
		if not vals.get('order_by', False):
			raise osv.except_osv(_('Order Error'),_('Please input order by.'))

	# untuk order by order, harus dicek dulu bahwa order harus dalam maksimal jam sebelumnya
		if service_type == 'by_order':
		# cek start date harus sudah ada
			if not vals.get('start_planned_date', False):
				raise osv.except_osv(_('Order Error'),_('Please input start date.'))
		# cek start date harus minimal n jam dari sekarang
			start_date = datetime.strptime(vals['start_planned_date'],'%Y-%m-%d %H:%M:%S')
			self._cek_min_hour_for_type_by_order(cr, uid, start_date, contract_data.by_order_minimum_minutes, context)

		# kalau usage control diaktifkan, isi over_quota_status
			if contract_data.usage_control_level != 'no_control':
				quota_per_usage, over_quota_status = self.determine_over_quota_status(cr, uid, vals['customer_contract_id'], vals['alloc_unit_id'], vals['fleet_type_id'])
				vals.update({
					'alloc_unit_usage': quota_per_usage,
					'over_quota_status': over_quota_status,
				})

	# cek bahwa request_date harus di dalam order hours, alias user hanya bisa mesen di jam2 tertentu TERLEPAS dari mesennya
	# buat hari apa dan jam berapa
	# cek juga bahwa ga boleh order di hari libur
	# kalau shuttle atau dari cron, babat langsung ngga usah dicek
		if service_type in ['full_day','by_order'] and context.get('source', False) != 'cron':
			self._cek_request_date(cr, uid, vals['request_date'], contract_data)

	# bikin nomor order dulu
	# format: (Tanggal)(Bulan)(Tahun)(4DigitPrefixCustomer)(4DigitNomorOrder) Cth: 23032017BNPB0001
		if not vals.get('name', False):
			order_date = vals.get('request_date', None)
			if not order_date: order_date = datetime.now()
			if isinstance(order_date, (str,unicode)):
				order_date = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S')
			prefix = "%s%s" % (order_date.strftime('%d%m%Y'), contract_data.customer_id.partner_code.upper())
			order_ids = self.search(cr, uid, [('name','=like',prefix+'%')], order='request_date DESC, name DESC')
			if len(order_ids) == 0:
				last_number = 1
			else:
				order_data = self.browse(cr, uid, order_ids[0])
				last_number = int(order_data.name[-4:]) + 1
			vals.update({'name': "%s%04d" % (prefix,last_number)}) # later
		
	# kalau udah di-assign mobil, cek apakah ada vehicle bentrok dengan start dan finish planned date 
	# order lain
		if vals.get('assigned_vehicle_id', False):
		# cek apakah ada vehicle bentrok dengan start dan finish planned date order lain
			if not context.get('source', False) or context.get('source', False) == 'form':
				self._cek_vehicle_clash(cr, uid, vals['assigned_vehicle_id'], vals['start_planned_date'], vals['finish_planned_date'], 0, context)
			
	# jalankan createnya
		new_id = super(foms_order, self).create(cr, uid, vals, context=context)
		new_data = self.browse(cr, uid, new_id, context=context)

	# untuk order fullday diasumsikan sudah ready karena vehicle dan drivernya pasti standby kecuali nanti diganti.
	# pula, berdasarkan order_by dan customer_contract_id, tentukan assigned_driver_id dan assigned_vehicle_id
		if service_type == 'full_day':
			fleet_data = None
			for fleet in new_data.customer_contract_id.car_drivers:
				if vals.get('assigned_vehicle_id', False):
					if fleet.fullday_user_id.id == new_data.order_by.id and fleet.fleet_vehicle_id.id == vals.get('assigned_vehicle_id', False):
						fleet_data = fleet
						break
				else:
					if fleet.fullday_user_id.id == new_data.order_by.id:
						fleet_data = fleet
						break
			if fleet_data:
				self.write(cr, uid, [new_id], {
					'assigned_driver_id': fleet_data.driver_id.id,
					'assigned_vehicle_id': fleet_data.fleet_vehicle_id.id,
					'pin': fleet_data.fullday_user_id.pin,
					'state': 'ready',
				})
			self.webservice_post(cr, uid, ['fullday_passenger'], 'create', new_data, \
				webservice_context={}, context=context)
	# untuk order By Order
		elif service_type == 'by_order':
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
				is_over_quota = False
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
						is_over_quota = True
					
			#kalau yang memesan adalah approver dan tidak over quota, maka state menjadi confirmed
				is_approver = user_obj.has_group(cr, new_data.order_by.id, 'universal.group_universal_approver')
				if not is_over_quota and is_approver:
					self.write(cr, uid, [new_id], {
						'state': 'confirmed',
					}, context=context)
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
		elif service_type == 'shuttle':
			self.write(cr, uid, [new_id], {
				'state': 'confirmed',
			}, context=context)

		return new_id

	def write(self, cr, uid, ids, vals, context={}):
		orders = self.browse(cr, uid, ids)
		# Escalation Privilege (Insecure Direct Object References)
		if 'user_id' in context: uid = context['user_id']
		if uid != SUPERUSER_ID:
			accessible_order_ids = self.search(cr, uid, [], offset=0, limit=None, order=None, context={
				'by_user_id': True,
				'user_id': uid
			}, count=False)
			for id in ids:
				if id not in accessible_order_ids:
					raise osv.except_osv(_('Order Error'),_('You cannot access this order!'))
		
		context = context and context or {}
		source = context.get('source', False)

	#apabila ada perubahan contract cek dahulu apakah contractnya masih active
		if vals.get('customer_contract_id', False):
			self._cek_contract_is_active(cr,uid, [vals['customer_contract_id']], context)
		
	#cek dahulu apakah ada perubahan start_planned_date, kalau ada cek apakah kosong
		if 'start_planned_date' in vals:
			if not vals.get('start_planned_date', False):
				raise osv.except_osv(_('Order Error'),_('Please input start date.'))
		
	# kalau ada perubahan start_planned_date, ambil dulu planned start date aslinya
		original_start_date = {}
		if vals.get('start_planned_date', False):
			start_date = datetime.strptime(vals['start_planned_date'],'%Y-%m-%d %H:%M:%S')
			for data in orders:
			# cek start date harus minimal n jam dari sekarang
				self._cek_min_hour_for_type_by_order(cr, uid, start_date, data.customer_contract_id.by_order_minimum_minutes, context)
				original_start_date.update({data.id: data.start_planned_date})
				if start_date > datetime.strptime(data.finish_planned_date,'%Y-%m-%d %H:%M:%S'):
					raise osv.except_osv(_('Order Error'),_('Start date cannot be greater than end date.'))
		
	# cek apakah bentrok waktu sama order lain
		if vals.get('assigned_vehicle_id', False) or vals.get('start_planned_date', False):
		# ambil nilai lama dahulu apabila ternyata hanya terjadi 1 perubahan
			for data in orders:
				assigned_vehicle = data.assigned_vehicle_id.id
				start_planned_date = data.start_planned_date
				finish_planned_date = data.finish_planned_date
			# apabila ada perubahan, gunakan nilai yang baru
				if vals.get('assigned_vehicle_id', False):
					assigned_vehicle = vals.get('assigned_vehicle_id', False)
				if vals.get('start_planned_date', False):
					start_planned_date = vals.get('start_planned_date', False)
				if vals.get('finish_planned_date', False):
					finish_planned_date = vals.get('finish_planned_date', False)
			# cek ada yang beririsan ga
				if assigned_vehicle and (not source or source == 'form'):
					self._cek_vehicle_clash(cr, uid, assigned_vehicle, start_planned_date, finish_planned_date, data.id, context)
		
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

	# kalau ada perubahan odometer, cek finish harus > start
	# kenapa ngga pake constraint? karena isi keduanya bisa 0
		if vals.get('start_odometer', False) or vals.get('finish_odometer', False):
			for data in orders:
				start_odo = vals.get('start_odometer', data.start_odometer)
				finish_odo = vals.get('finish_odometer', data.finish_odometer)
				if finish_odo > 0 and finish_odo <= start_odo:
					raise osv.except_osv(_('Order Error'),_('Finish odometer must be larger than start odometer (%s). Please check again your input.') % start_odo)

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
						
				# apabila order sudah mempunyai vehicle dan driver maka ubah statenya menjadi ready, apabila tidak coba gunakan autoplot
					if order_data.assigned_vehicle_id and order_data.assigned_driver_id:
						self.write(cr, uid, [order_data.id], {
							'state': 'ready',
							'pin': self._generate_random_pin(),
						}, context=context)
				# apakah source_area dan dest_area ada di bawah homebase yang sama?
				# kalo sama, langsung cariin mobil dan supir
					else:
						if order_data.origin_area_id and order_data.dest_area_id and \
						order_data.origin_area_id.homebase_id.id == order_data.dest_area_id.homebase_id.id:
						# sebelum cariin mobil dan supir, cek dulu di luar jam kerja ngga ini order
						# kalau iya, jangan autoplot
							autoplot = False
							start_planned_date = datetime.strptime(order_data.start_planned_date,"%Y-%m-%d %H:%M:%S")
							weekday = start_planned_date.weekday()
							order_time = start_planned_date.time()
							order_time = order_time.hour + (order_time.minute / 60.0)
							for working_day in order_data.customer_contract_id.working_time_id.attendance_ids:
								if weekday == int(working_day.dayofweek) and \
								(order_time >= working_day.hour_from - SERVER_TIMEZONE and order_time <= working_day.hour_to - SERVER_TIMEZONE):
									autoplot = True
									break
						# jika order di dalam hari kerja, maka autoplot
							if autoplot:
							# cari vehicle dan driver yang available di jam itu
								vehicle_id, driver_id = self.search_first_available_fleet(cr, uid, order_data.customer_contract_id.id, order_data.id, order_data.fleet_type_id.id, order_data.start_planned_date)
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
									self._message_dispacther(cr, uid, order_data.id,
										_('Cannot allocate vehicle and driver for order %s. Please allocate them manually.') % order_data.name )
									return result
						# jika order di luar hari kerja, jangan autoplot, kirim notif ke dispatcher untuk mengingatkan agar manual assign
							else:
								partner_ids = []
								self._message_dispacther(cr, uid, order_data.id,
									_('Order %s were booked outside working day. Please assign the vehicle and the driver manually.') % order_data.name )
					# kalo beda homebase, post message
						else:
							partner_ids = []
							self._message_dispacther(cr, uid, order_data.id,
								_('New order from %s going to different homebase. Manual vehicle/driver assignment needed.') % order_data.customer_contract_id.customer_id.name )
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
				# Kalau state berubah jadi start confirmed, cek apakah dia order pertama start_planned_date di hari tersebut bukan
					if vals['state'] in ['start_confirmed']:
						order_ids = self.search(cr, uid, [
							('actual_driver_id', '=', order_data.actual_driver_id.id),
							('start_planned_date', '>=', datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d 00:00:00")),
							('start_planned_date', '<', order_data.start_planned_date),
						])
						if len(order_ids) == 0:
						# liat di hari tersebut ada clockin tidak?
							clock_in, clock_out = self._get_clock_in_clock_out_driver_at_date(cr, uid, order_data.actual_driver_id.id, datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S'))
							if clock_in:
								self._write_attendance(cr, uid, clock_in.id, order_data.start_planned_date, order_data.customer_contract_id.id, order_data.id)
							else:
								self._create_attendance(cr, uid, order_data.actual_driver_id.id, order_data.customer_contract_id.id,
									'sign_in', order_data.start_planned_date, order_data.id)
				# Kalau state berubah jadi finish confirmed, cek apakah dia order terakhir finish_confirm_date di hari tersebut bukan
					if vals['state'] in ['finish_confirmed']:
						order_ids = self.search(cr, uid, [
							('actual_driver_id', '=', order_data.actual_driver_id.id),
							('finish_confirm_date', '<=', datetime.strptime(order_data.finish_confirm_date,'%Y-%m-%d %H:%M:%S').strftime("%Y-%m-%d 23:59:59")),
							('finish_confirm_date', '>', order_data.finish_confirm_date),
						])
						if len(order_ids) == 0:
							# liat di hari tersebut ada clockin tidak?
							clock_in, clock_out = self._get_clock_in_clock_out_driver_at_date(cr, uid, order_data.actual_driver_id.id, datetime.strptime(order_data.finish_confirm_date,'%Y-%m-%d %H:%M:%S'))
							if clock_out:
							# kalau order nanggung, create. Kl order biasa, write
								date_start = datetime.strptime(clock_out.order_id.start_planned_date, DEFAULT_SERVER_DATETIME_FORMAT)
								date_finish = datetime.strptime(clock_out.order_id.finish_confirm_date, DEFAULT_SERVER_DATETIME_FORMAT)
								if date_start.date() != date_finish.date():
									self._create_attendance(cr, uid, order_data.actual_driver_id.id, order_data.customer_contract_id.id,
										'sign_out', order_data.finish_confirm_date, order_data.id)
								else:
									self._write_attendance(cr, uid, clock_out.id, order_data.finish_confirm_date, order_data.customer_contract_id.id, order_data.id)
							else:
								self._create_attendance(cr, uid, order_data.actual_driver_id.id, order_data.customer_contract_id.id,
									'sign_out', order_data.finish_confirm_date, order_data.id)
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
		if context == None: context = {}
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
			context = {}
			model_data.update({
				'order_id': data_id,
				'cancel_by': user_id,
			})
			context.update(model_data)
			cancel_memory_obj = self.pool.get('foms.order.cancel.memory')
			result = cancel_memory_obj.action_execute_cancel(cr, uid, [], context)
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
					'district_id': area.district_id.id,
					'name': area.name,
				})
	# list booking purpose
		elif command == 'booking_purpose':
			purpose_obj = self.pool.get('foms.booking.purpose')
			purpose_ids = purpose_obj.search(cr, uid, [])
			result = []
			for purpose in purpose_obj.browse(cr, uid, purpose_ids):
				result.append({
					'id': purpose.id,
					'name': purpose.name,
				})
		return result

# METHODS ------------------------------------------------------------------------------------------------------------------
	
	def determine_over_quota_status(self, cr, uid, customer_contract_id, allocation_unit_id, fleet_type_id, add_credit_per_usage=True):
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
		if add_credit_per_usage:
			after_usage = credit_per_usage + current_quota.current_usage
		else:
			after_usage = current_quota.current_usage
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
		
		current_order = self.browse(cr, uid, order_id)
		driver_in_use_ids = []  # ongoing vehicle that can't be used
		for order in self.browse(cr, uid, ongoing_order_ids):
			if order.finish_planned_date >= start_planned_date:  # udah jelas ngga available
				if order.assigned_vehicle_id: driver_in_use_ids.append(order.assigned_driver_id.id)
				if order.actual_vehicle_id: driver_in_use_ids.append(order.actual_driver_id.id)
				continue
		# perhitungkan delay dari satu area ke area lain
			if order.dest_area_id and current_order.origin_area_id:
				delay = area_delay_obj.get_delay(cr, uid, order.dest_area_id.id, current_order.origin_area_id.id)
				finish_date = datetime.strptime(order.finish_planned_date, '%Y-%m-%d %H:%M:%S') + timedelta(minutes=delay)
				finish_date = finish_date.strftime('%Y-%m-%d %H:%M:%S')
				if finish_date >= start_planned_date:
					if order.assigned_vehicle_id: driver_in_use_ids.append(order.assigned_driver_id.id)
					if order.actual_vehicle_id: driver_in_use_ids.append(order.actual_driver_id.id)
					continue
		driver_in_use_ids = list(set(driver_in_use_ids))
		
		current_time = datetime.now()
		nearest_billing_month = current_time.month
		if current_time.day - current_order.customer_contract_id.billing_cycle < 0:
			nearest_billing_month -= 1
		nearest_billing_time = datetime(current_time.year, nearest_billing_month,
			current_order.customer_contract_id.billing_cycle, 0, 0, 0)
		
		q_vehicle_in_use_ids = Q.PriorityQueue()  # ongoing vehicle that can't be used with each total working time as priority
		
	# ambil fleet-fleet yang mungkin digunakan
		possible_fleet_line_ids = []
		for fleet in current_order.customer_contract_id.car_drivers:
			if fleet.driver_id.id in driver_in_use_ids or fleet.fleet_type_id.id != fleet_type_id: continue
		# jika ada vehicle di contract tsb dengan fleet type yg sama
		# dan tidak sedang digunakan, maka append ke possible_fleet_line
			if fleet.id not in possible_fleet_line_ids:
				possible_fleet_line_ids.append(fleet.id)
				driver_order_ids = self.search(cr, uid, [
					'&', ('start_date', '!=', False),
					'&', ('finish_date', '!=', False),
					'&', ('start_date', '>=', str(nearest_billing_time)),
					'&', ('start_date', '<=', str(current_time)),
					'|', ('assigned_driver_id', '=', fleet.driver_id.id),
							('actual_driver_id', '=', fleet.driver_id.id),
				])
				total_priority_driver = 0
				for driver_order_id in driver_order_ids:
					driver_order = self.browse(cr, uid, driver_order_id)
					total_priority_driver += self._calculate_total_working_time_priority(cr, uid,
												driver_order.start_date, driver_order.finish_date,
												driver_order.customer_contract_id.working_time_id.attendance_ids)
				q_vehicle_in_use_ids.put((total_priority_driver, fleet))
			
	# ambil vehicle pertama yang available untuk jenis mobil yang diminta
		if not q_vehicle_in_use_ids.empty():
			selected_fleet = q_vehicle_in_use_ids.get()
			return selected_fleet[1].fleet_vehicle_id.id, selected_fleet[1].driver_id.id
		else:
			return None, None

	def _calculate_total_working_time_priority(self, cr, uid, val_start_confirm_date, val_finish_confirm_date, attendance_ids):
		"""
		Untuk menghitung berapa bobot waktu kerja supir dalam sebuah kontrak.
		Perhitungan bobot sama dengan total jam normal + 1.5*total jam lembur.
		Digunakan untuk order tipe by_order.
		:param cr:
		:param uid:
		:param val_start_confirm_date: value dari start_confirm_date yang ingin dihitung
		:param val_finish_confirm_date: value dari finish_confirm_date yang ingin dihitung
		:param attendance_ids: working_time attendance_ids sebuah order data
		:return: total bobot
		"""
		working_normal_time = 0
		working_overtime = 0
		if val_start_confirm_date and val_finish_confirm_date:
		# Get waktu start dan finish
			start_confirm_date = datetime.strptime(val_start_confirm_date,"%Y-%m-%d %H:%M:%S")
			start_confirm_weekday = start_confirm_date.weekday()
			start_confirm_time = start_confirm_date.time()
			start_confirm_time = start_confirm_time.hour + (start_confirm_time.minute / 60.0)
			finish_confirm_date = datetime.strptime(val_finish_confirm_date,"%Y-%m-%d %H:%M:%S")
			finish_confirm_weekday = finish_confirm_date.weekday()
			finish_confirm_time = finish_confirm_date.time()
			finish_confirm_time = finish_confirm_time.hour + (finish_confirm_time.minute / 60.0)
			working_days = (finish_confirm_date.day - start_confirm_date.day) + 1
			
		# Get working time supaya tidak usah looping berkali-kali jika start dan finish tidak dalam hari yg sama
			working_time = {
				'0': {'hour_from': 0, 'hour_to': 0, },
				'1': {'hour_from': 0, 'hour_to': 0, },
				'2': {'hour_from': 0, 'hour_to': 0, },
				'3': {'hour_from': 0, 'hour_to': 0, },
				'4': {'hour_from': 0, 'hour_to': 0, },
				'5': {'hour_from': 0, 'hour_to': 0, },
				'6': {'hour_from': 0, 'hour_to': 0, },
			}
		# jika ada hari yang sama, misal Senin 7-9, 10-14,
		# maka working_time untuk hari itu dimulai dari 7 sampai 14
		# jam kosong 9-10 tidak dihitung sebagai jam lembur
			for working_day in attendance_ids:
				if working_time[working_day.dayofweek]['hour_from'] == working_time[working_day.dayofweek]['hour_to']:
					working_time[working_day.dayofweek]['hour_from'] = working_day.hour_from - SERVER_TIMEZONE
					working_time[working_day.dayofweek]['hour_to'] = working_day.hour_to - SERVER_TIMEZONE
				else:
					working_time[working_day.dayofweek]['hour_from'] = min(working_day.hour_from - SERVER_TIMEZONE,
						working_time[working_day.dayofweek]['hour_from'])
					working_time[working_day.dayofweek]['hour_to'] = max(working_day.hour_to - SERVER_TIMEZONE,
						working_time[working_day.dayofweek]['hour_to'])
				
		# Hitung lama kerja dan lembur
			w = 1
			current_weekday_int = start_confirm_weekday
			current_weekday = str(current_weekday_int)
			while w <= working_days:
				if w == 1: current_start_time = start_confirm_time
				else: current_start_time = 0
				if w == working_days: current_end_time = finish_confirm_time
				else: current_end_time = 24
				
				if current_start_time < working_time[current_weekday]['hour_from']:
					if current_end_time < working_time[current_weekday]['hour_from']:
						working_overtime += (current_end_time - current_start_time)
					elif current_end_time > working_time[current_weekday]['hour_to']:
						working_overtime += (working_time[current_weekday]['hour_from'] - current_start_time)
						working_normal_time += (working_time[current_weekday]['hour_to'] -
												working_time[current_weekday]['hour_from'])
						working_overtime += (current_end_time - working_time[current_weekday]['hour_to'])
					else:
						working_overtime += (working_time[current_weekday]['hour_from'] - current_start_time)
						working_normal_time += (current_end_time - working_time[current_weekday]['hour_from'])
				elif current_start_time > working_time[current_weekday]['hour_to']:
					working_overtime += (current_end_time - current_start_time)
				else:
					if current_end_time > working_time[current_weekday]['hour_to']:
						working_normal_time += (working_time[current_weekday]['hour_to'] - current_start_time)
						working_overtime += (current_end_time - working_time[current_weekday]['hour_to'])
					else:
						working_normal_time += (current_end_time - current_start_time)
				w += 1
				current_weekday_int = (current_weekday_int+1) % 7
				current_weekday = str(current_weekday_int)
		return working_normal_time + (1.5 * working_overtime)

	_central_dispatch_partners = []
	
	def _message_dispacther(self, cr, uid, data_id, message):
		if not self._central_dispatch_partners:
			user_obj = self.pool.get('res.users')
			self._central_partner_ids = user_obj.get_partner_ids_by_group(cr, SUPERUSER_ID, 'universal', 'group_universal_dispatcher')
		partner_ids = []
		for partner_id in self._central_partner_ids:
			partner_ids.append((4,partner_id))
		self.message_post(cr, SUPERUSER_ID, data_id, message, partner_ids=partner_ids)

	def _generate_random_pin(self):
		return (''.join(random.choice(string.digits) for _ in range(6))).replace('0','1')

	def _cek_contract_is_active(self, cr, uid, customer_contact_ids, context=None):
		contract_object = self.pool.get('foms.contract')
		contract_ids = contract_object.browse(cr, uid, customer_contact_ids)
		for contract_id in contract_ids:
			if contract_id.state in ['prolonged', 'terminated', 'finished']:
				raise osv.except_osv(_('Order Error'),_('Contract has already been inactive. You cannot place order under this contract anymore. Please choose another contract or contact your PIC.'))

	def _cek_request_date(self, cr, uid, request_date, contract_data):
		book_in_hours = False
		if type(request_date) is unicode:
			request_date = request_date.encode('ascii', 'ignore')
		if type(request_date) is string or type(request_date) is str:
			request_date = datetime.strptime(request_date, "%Y-%m-%d %H:%M:%S")
		order_day = request_date.weekday()
		order_time = request_date.time()
		order_time = order_time.hour + (order_time.minute/60.0)
		for order_hours in contract_data.order_hours:
			if order_day == int(order_hours.dayofweek) and (order_time >= order_hours.time_from - SERVER_TIMEZONE and order_time <= order_hours.time_to - SERVER_TIMEZONE):
				book_in_hours = True
				break
		if not book_in_hours:
			raise osv.except_osv(_('Order Error'),_('You are booking outside of order hours. Please contact your PIC or Administrator for allowable order hours.'))
		if not contract_data.working_time_id:
			raise osv.except_osv(_('Order Error'),_('Working time for this order\'s contract is not set. Please contact PT. Universal.'))
		book_in_holiday = False
		for holiday in contract_data.working_time_id.leave_ids:
			if request_date >= datetime.strptime(holiday.date_from, "%Y-%m-%d %H:%M:%S") \
					and request_date <= datetime.strptime(holiday.date_to, "%Y-%m-%d %H:%M:%S"):
				book_in_holiday = True
				break
		if book_in_holiday:
			raise osv.except_osv(_('Order Error'),_('You are booking in holiday. We are sorry we cannot serve you on holidays.'))

	def _cek_min_hour_for_type_by_order(self, cr, uid, start_date, order_minimum_minutes , context=None):
		now = datetime.now()
		delta = float((start_date - now).days * 86400 + (start_date - now).seconds) / 60
		if delta < order_minimum_minutes:
			raise osv.except_osv(_('Order Error'),_('Start date is too close to current time, or is in the past. There must be at least %s minutes between now and start date.' % order_minimum_minutes))
	
# untuk assigned_vehicle_id yang diminta, tentukan apakah bentrok dengan order yang lagi jalan
# ini untuk kasus di mana ada perubahan/setting ulang/pengisian assigned vehicle id di sebuah 
# order
	"""
	JUNED: ini seharusnya udah ngga ada. dipertahankan supaya kalian dapet contoh pemanggilan _message_dispacther
	kalau caranya udah ketangkep, hapus aja bagian ini
	def _cek_order_assigning_vehicle(self, cr, uid, assigned_vehicle_id, start_planned_date, order_id, context=None):
		temp_date = datetime.strptime(start_planned_date, "%Y-%m-%d %H:%M:%S")
		order_ids = self.search(cr, uid, [
			('start_date','<',  datetime.strftime(temp_date, "%Y-%m-%d %H:%M:%S")),
			('finish_confirm_date','=', False),
			('actual_vehicle_id','=', assigned_vehicle_id),
		])
		if len(order_ids) > 0:
			for order in self.browse(cr, uid, order_ids):
				self._message_dispacther(cr, uid, order.id, 
					_('Order %s still not finish but same vehicle assigned to this order.') % order.name )
	"""

	def _cek_vehicle_clash(self, cr, uid, assigned_vehicle_id, start_planned_date, finish_planned_date, new_id, context=None):
		# Cek Order ga boleh bentrok sama order laen yg vehicle nya sama
		# 	'id' === new_id
		# AND
		# (
		# 	('actual_vehicle_id' == assigned_vehicle_id)
		# OR
		# 	('actual_vehicle_id' == None AND 'assigned_vehicle_id' == assigned_vehicle_id)
		# )
		# AND
		# 	state NOT IN ['finish_confirmed', 'canceled', 'finished', 'rejected']
		# AND (
		# 		('start_planned_date' <= start_planned_date AND 'finish_planned_date' >= start_planned_date)
		# 	OR
		# 		('start_planned_date' <= finish_planned_date AND 'finish_planned_date' >= finish_planned_date)
		# )
		
		if finish_planned_date:
			order_ids = self.search(cr, uid, [
				'&',('id', '!=', new_id),
				'&','|',('actual_vehicle_id', '=', assigned_vehicle_id),
					'&',('actual_vehicle_id', '=', None),
						('assigned_vehicle_id', '=', assigned_vehicle_id),
				'&',('state', 'not in', ['finish_confirmed', 'canceled', 'finished', 'rejected']),
					'|','&',('start_planned_date', '<=', start_planned_date),
						('finish_planned_date', '>=', start_planned_date),
					'|','&',('start_planned_date', '<=', finish_planned_date),
						('finish_planned_date', '>=', finish_planned_date),
						'&',('start_planned_date', '>=', start_planned_date),
						('finish_planned_date', '<=', finish_planned_date),
			])
		else:
			order_ids = self.search(cr, uid, [
				'&',('id', '!=', new_id),
				'&','|',('actual_vehicle_id', '=', assigned_vehicle_id),
					'&',('actual_vehicle_id', '=', None),
						('assigned_vehicle_id', '=', assigned_vehicle_id),
				'&',('state', 'not in', ['finish_confirmed', 'canceled', 'finished', 'rejected']),
					'&',('start_planned_date', '<=', start_planned_date),
					('finish_planned_date', '>=', start_planned_date)
			])
		if new_id:
			new_order = self.browse(cr, uid, new_id)
			new_order_contract_id = new_order.customer_contract_id.id
		else:
			new_order_contract_id = None
		if len(order_ids) > 0:
			for order_data in self.browse(cr, uid, order_ids):
				raise osv.except_osv(_('Order Error'),_('Assigned vehicle clash with order %s with start planned date %s and finish planned date. %s'
					% (order_data[0].name, datetime_to_server(order_data[0].start_planned_date), datetime_to_server(order_data[0].finish_planned_date))))
			
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
	def cron_driver_attendances(self, cr, uid, context=None):
		employee_obj = self.pool.get('hr.employee')
		fleet_obj = self.pool.get('foms.contract.fleet')
		attendance_obj = self.pool.get('hr.attendance')
		data_obj = self.pool.get('ir.model.data')
		# Pool drivers
		driver_job_id = data_obj.get_object(cr, uid, 'universal', 'hr_job_driver').id
		driver_ids = employee_obj.search(cr, uid, [('job_id', '=', driver_job_id)])
		drivers = employee_obj.browse(cr, uid, driver_ids)
		yesterday = datetime.now() - timedelta(hours=24)
		for driver in drivers:
			first_order, last_order = self._get_days_first_last_order(cr, uid, driver.id, yesterday)
		# Dapatkan pasangan clock in dan clock kemarin
			first_clock_in, last_clock_out = self._get_clock_in_clock_out_driver_at_date(cr, uid, driver.id, yesterday)
		# Jika tidak ada order pertama di hari itu, maka cek apakah driver itu sedang menjalani order lintas hari, jika tidak maka dia tidak absen
			if len(first_order) == 0:
				order_pass_day = self._get_running_multiday_orders(cr, uid, driver.id, yesterday)
				if len(order_pass_day) > 0:
					working_time = self._get_contract_working_time(order_pass_day.customer_contract_id, yesterday)
				#dapetin working time
					date_clock_in, date_clock_out = self._determine_clock_datetimes(cr, uid, None, None, yesterday,
						working_time.working_time_type, True, working_time.hour_from, working_time.hour_to, working_time.max_hour)
					if len(first_clock_in) == 0 and date_clock_in is not None:
						self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id, 'sign_in', date_clock_in, last_order.id)
					if len(last_clock_out) == 0 and date_clock_out is not None:
						self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id, 'sign_out', date_clock_out, last_order.id)
			else:
				working_time = self._get_contract_working_time(first_order.customer_contract_id, yesterday)
			# Kalau libur, return
				if working_time is None:
					return
			#dapetin working time
				date_clock_in, date_clock_out = self._determine_clock_datetimes(cr, uid, first_order, last_order, yesterday, 
						working_time.working_time_type, False, working_time.hour_from, working_time.hour_to, working_time.max_hour)
				if date_clock_in is not None:
					if len(first_clock_in) == 0:
						self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id, 'sign_in', date_clock_in, last_order.id)
					else:
						self._write_attendance(cr, uid, first_clock_in.id, date_clock_in, last_order.customer_contract_id.id, last_order.id)
				if date_clock_out is not None:
					if len(last_clock_out) == 0:
						self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id, 'sign_out', date_clock_out, last_order.id)
					else:
						self._write_attendance(cr, uid, last_clock_out.id, date_clock_out, last_order.customer_contract_id.id, last_order.id)

	def action_finish(self, cr, uid, ids, context=None):
		order = self.browse(cr, uid, ids[0])
		return self.write(cr, uid, ids, {
			'state': 'finish_confirmed',
			'finish_date': order.finish_planned_date,
			'finish_confirm_date': order.finish_planned_date,
			'finish_confirm_by': uid,
			'finish_from': 'central',
		})
	
	# def cron_compute_driver_attendances(self, cr, uid, context=None):
	# 	employee_obj = self.pool.get('hr.employee')
	# 	fleet_obj = self.pool.get('foms.contract.fleet')
	# 	attendance_obj = self.pool.get('hr.attendance')
	# 	data_obj = self.pool.get('ir.model.data')
	# 	# Pool drivers
	# 	driver_job_id = data_obj.get_object(cr, uid, 'universal', 'hr_job_driver').id
	# 	driver_ids = employee_obj.search(cr, uid, [('job_id', '=', driver_job_id)])
	# 	drivers = employee_obj.browse(cr, uid, driver_ids)
	# 	today = datetime.now()
	# 	for driver in drivers:
	# 		first_order, first_finished_order, last_order = self._get_first_and_last_order_times_today(cr, uid, driver.id,
	# 			today)
	# 		if len(first_order) == 0 and len(last_order) == 0:
	# 			continue
	# 		start_working_time, end_working_time = self._get_driver_order_workingtime(first_order, last_order, today)
	# 		first_order_clock_in, first_order_clock_out_in = self._determine_clock_datetime(cr, uid, start_working_time,
	# 			end_working_time, first_order, today)
	# 		first_finished_order_clock_in, first_finished_order_clock_out = self._determine_clock_datetime(cr, uid,
	# 			start_working_time, end_working_time, first_finished_order, today)
	# 		last_order_clock_in, last_order_clock_out = self._determine_clock_datetime(cr, uid, start_working_time,
	# 			end_working_time, last_order, today)
	#
	# 		first_clock_in = first_order_clock_in
	# 		first_clock_out = first_finished_order_clock_out
	# 		last_clock_out = last_order_clock_out
	#
	# 		today_clock_in_id = attendance_obj.search(cr, uid, [
	# 			('name', '>=', today.strftime('%Y-%m-%d 00:00:00')),
	# 			('name', '<=', today.strftime('%Y-%m-%d 23:59:59')),
	# 			('action', '=', 'sign_in'),
	# 		])
	# 		today_clock_out_id = attendance_obj.search(cr, uid, [
	# 			('name', '>=', today.strftime('%Y-%m-%d 00:00:00')),
	# 			('name', '<=', today.strftime('%Y-%m-%d 23:59:59')),
	# 			('action', '=', 'sign_out'),
	# 		])
	#
	# 	# Jika ada first_clock_in
	# 		if first_clock_in:
	# 		# Jika sudah ada db_clock_in
	# 			if today_clock_in_id: # update db_clock_in
	# 				self._write_attendance(cr, uid, today_clock_in_id, first_clock_in, first_order.customer_contract_id.id, first_order.id)
	# 		# else belum ada db_clock_in
	# 			else: # create db_clock_in
	# 				self._create_attendance(cr, uid, driver.id, first_order.customer_contract_id.id, 'sign_in',
	# 					first_clock_in, first_order.id)
	# 		# Jika ada first_clock_out
	# 			if first_clock_out:
	# 			# Jika first_clock_out <= first_clock_in
	# 				if first_clock_out <= first_clock_in:
	# 				# ambil start_planned nya si clock_out
# 					previous_start_planned_date = datetime.strptime(first_finished_order.start_planned_date, '%Y-%m-%d %H:%M:%S')
	# 					previous_clock_out_id = attendance_obj.search(cr, uid, [
	# 						('name', '>=', previous_start_planned_date.date().strftime('%Y-%m-%d 00:00:00')),
	# 						('name', '<=', previous_start_planned_date.date().strftime('%Y-%m-%d 23:59:59')),
	# 						('action', '=', 'sign_out'),
	# 					])
	# 				# Jika yg sblmnya sudah ada db_clock_out
	# 					if len(previous_clock_out_id) > 0: # update db_clock_out si hari sebelum2nya
	# 						self._write_attendance(cr, uid, previous_clock_out_id, first_clock_out, first_finished_order.customer_contract_id.id, first_finished_order.id)
	# 				# else yg sblmnya belum ada db_clock_out
	# 					else: # create db_clock_out si hari sebelum2nya
	# 						self._create_attendance(cr, uid, driver.id, first_finished_order.customer_contract_id.id,
	# 							'sign_out', first_clock_out, first_finished_order.id)
	#
	# 				# Jika first_clock_out != last_clock_out
	# 					if first_clock_out != last_clock_out:
	# 					# Jika db_clock_out sudah ada
	# 						if today_clock_out_id: # update db_clock_out dgn last_clock_out
	# 							self._write_attendance(cr, uid, today_clock_out_id, last_clock_out, last_order.customer_contract_id.id, last_order.id)
	# 					# else db_clock_out belum ada
	# 						else: # create db_clock_out dgn last_clock_out
	# 							self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id,
	# 								'sign_out', last_clock_out, last_order.id)
	# 			# else first_clock_out dan last_clock_out pasti lebih besar dari first_clock_in
	# 				else:
	# 				# Jika db_clock_out sudah ada
	# 					if today_clock_out_id: # update db_clock_out dgn last_clock_out
	# 						self._write_attendance(cr, uid, today_clock_out_id, last_clock_out, last_order.customer_contract_id.id, last_order.id)
	# 				# else db_clock_out belum ada
	# 					else: # create db_clock_out dgn last_clock_out
	# 						self._create_attendance(cr, uid, driver.id, last_order.customer_contract_id.id, 'sign_out',
	# 							last_clock_out, last_order.id)
	# 		# else tidak ada first_clock_out, ga usah ngapa2in
	# 	# else tidak ada first_clock_in
	# 		else:
	# 		# Jika ada first_clock_out
	# 			if first_clock_out:
	# 			# ambil start_planned nya si clock_out
	# 				previous_start_planned_date = datetime.strptime(first_finished_order.start_planned_date, '%Y-%m-%d %H:%M:%S')
	# 				previous_clock_out_id = attendance_obj.search(cr, uid, [
	# 					('name', '>=', previous_start_planned_date.date().strftime('%Y-%m-%d 00:00:00')),
	# 					('name', '<=', previous_start_planned_date.date().strftime('%Y-%m-%d 23:59:59')),
	# 					('action', '=', 'sign_out'),
	# 				])
	# 			# Jika yg sblmnya sudah ada db_clock_out
	# 				if len(previous_clock_out_id) > 0: # update db_clock_out si hari sebelum2nya
	# 					self._write_attendance(cr, uid, previous_clock_out_id, first_clock_out, first_finished_order.customer_contract_id.id, first_finished_order.id)
	# 			# else yg sblmnya belum ada db_clock_out
	# 				else: # create db_clock_out si hari sebelum2nya
	# 					self._create_attendance(cr, uid, driver.id, first_finished_order.customer_contract_id.id,
	# 						'sign_out', first_clock_out, first_finished_order.id)
	# 		# else tidak ada first_clock_out, ga usah ngapa2in
	# 		pass
	# 	pass
	
	def _create_attendance(self, cr, uid, driver_id, customer_contract_id, clock_type, clock_datetime, order_id):
		attendance_obj = self.pool.get('hr.attendance')
		attendance_obj.create(cr, uid, {
			'employee_id': driver_id,
			'contract_id': customer_contract_id,
			'action': clock_type,
			'name': clock_datetime,
			'order_id': order_id,
		})
		
	def _write_attendance(self, cr, uid, id, clock_datetime, customer_contract_id, order_id):
		attendance_obj = self.pool.get('hr.attendance')
		attendance_obj.write(cr, uid, id, {
			'name': clock_datetime,
			'contract_id': customer_contract_id,
			'order_id': order_id,
		})
		
	def _get_clock_in_clock_out_driver_at_date(self, cr, uid, driver_id, calculated_date):
		attendance_obj = self.pool.get('hr.attendance')
		calculated_date = calculated_date.replace(hour=0, minute=0, second=0, microsecond=0)
		calculated_date_from = calculated_date - timedelta(hours=SERVER_TIMEZONE)
		calculated_date_to = calculated_date_from + timedelta(hours=24)
	# Get date's attendance clock in
		clock_in_ids = attendance_obj.search(cr, uid, [
			('employee_id', '=', driver_id),
			('name', '>=', calculated_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('name', '<=', calculated_date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('action', '=', 'sign_in'),
		], limit=1, order="name asc")
		clock_in = attendance_obj.browse(cr, uid, clock_in_ids)
	# Get today's last order
		clock_out_ids = attendance_obj.search(cr, uid, [
			('employee_id', '=', driver_id),
			('name', '>=', calculated_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('name', '<=', calculated_date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('action', '=', 'sign_out'),
		], limit=1, order="name desc")
		clock_out = attendance_obj.browse(cr, uid, clock_out_ids)
		return clock_in, clock_out

	def _get_contract_working_time(self, contract, calculated_date):
		"""
		Returns the given contract workingtime
		:param contract: recordset of contract (foms.contract)
		:param calculated_date: calculated_date: datetime of the date of intended working time
		:return: recordset of working time (resource.calendar.attendance)
		"""
		result = None
		working_times = contract.working_time_id.attendance_ids
		for working_time in working_times:
			if str(calculated_date.weekday()) == working_time.dayofweek:
				result = working_time
		return result
		
	def _get_running_multiday_orders(self, cr, uid, driver_id, calculated_datetime):
		# dapetin order lintas hari
		calculated_datetime = calculated_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
		calculated_datetime = calculated_datetime - timedelta(hours=SERVER_TIMEZONE)
		calculated_datetime_tomorrow = calculated_datetime + timedelta(hours=24)
		order_running_ids = self.search(cr, uid, [
			('actual_driver_id', '=', driver_id),
			('start_planned_date', '<=', calculated_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('finish_planned_date', '>=', calculated_datetime_tomorrow.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('state', 'in', ['started', 'start_confirmed', 'paused', 'resumed', 'finished', 'finish_confirmed'])
		], limit=1, order="start_planned_date desc")
		order_running = self.browse(cr, uid, order_running_ids)
		return order_running
	
	# def _get_first_and_last_order_today(self, cr, uid, driver_id, today):
	# 	# Get today's first order
	# 	first_order_ids = self.search(cr, uid, [
	# 		('actual_driver_id', '=', driver_id),
	# 		('start_planned_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
	# 		('start_planned_date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
	# 	], limit=1, order="start_planned_date asc")
	# 	first_order = self.browse(cr, uid, first_order_ids)
	# 	# Get today's last order
	# 	last_order_ids = self.search(cr, uid, [
	# 		('actual_driver_id', '=', driver_id),
	# 		('finish_confirm_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
	# 		('finish_confirm_date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
	# 	], limit=1, order="finish_confirm_date desc")
	# 	last_order = self.browse(cr, uid, last_order_ids)
	# 	return first_order, last_order
	
	def _determine_clock_datetimes(self, cr, uid, first_order, last_finished_order, calculated_date, working_type,
			is_multi_day=False, start_working_time=None, end_working_time=None, working_time_duration=None):
		"""
		Determines clock-in and clock-out datetime from the given orders and working time.
		:param first_order: recordset of first order of the day
		:param last_finished_order: recordset of last finish confirmed order of the day, may be None
		:param calculated_date: datetime of the date of intended clock in and clock out
		:param working_type: string of working type, max_hour or duration
		:param is_multi_day: boolean. If True, first_order and last_finished_order will be ignored. clock_in, clock_out will
			be calculated from working time
		:param start_working_time: floattime of start working time, ignored if working type is duration
		:param end_working_time: floattime of end working time, ignored if working type is duration
		:param working_time_duration: floattime of working time duration, ignored if working type is max_hour
		:return: tuple of two datetime objects; (clock_in and clock_out)
		"""
		clock_in = None
		clock_out = None
		calculated_date = calculated_date - timedelta(hours=SERVER_TIMEZONE)
	# If there are no working time, then there are no clockin and clockout time
		if (working_type == 'duration' and (start_working_time is None or end_working_time is None)) \
				or (working_type == 'max_hour' and working_time_duration is None):
			return clock_in, clock_out
		
	# Pool start_planned_date
		if first_order is not None:
			if first_order.start_planned_date:
				start_planned_date = datetime.strptime(first_order.start_planned_date, DEFAULT_SERVER_DATETIME_FORMAT)
			else:
				raise Exception('No start planned date found on order')
		else:
			start_planned_date = None
		
	# Pool finish_planned_date
		if last_finished_order is not None:
			if last_finished_order.finish_confirm_date:
				finish_confirm_date = datetime.strptime(last_finished_order.finish_confirm_date,
					DEFAULT_SERVER_DATETIME_FORMAT)
			else:
				raise Exception('No finish planned date found on order')
		else:
			finish_confirm_date = None
			
	# Pool start_working_date and end_working_date
		if working_type == 'duration':
			if not is_multi_day:
				start_working_date = start_planned_date + timedelta(hours=SERVER_TIMEZONE)
				start_working_date = start_working_date.replace(hour=0, minute=0, second=0, microsecond=0)
				start_working_date += timedelta(seconds=(start_working_time - SERVER_TIMEZONE) * 60 * 60)
				# start_working_date = start_working_date - timedelta(hours=SERVER_TIMEZONE)
				
				end_working_date = calculated_date + timedelta(hours=SERVER_TIMEZONE)
				end_working_date = end_working_date.replace(hour=0, minute=0, second=0, microsecond=0)
				end_working_date += timedelta(seconds=(end_working_time - SERVER_TIMEZONE) * 60 * 60)
				# end_working_date = end_working_date - timedelta(hours=SERVER_TIMEZONE)
			else:
				start_working_date = calculated_date + timedelta(hours=SERVER_TIMEZONE)
				start_working_date = start_working_date.replace(hour=0, minute=0, second=0, microsecond=0)
				start_working_date += timedelta(seconds=(start_working_time - SERVER_TIMEZONE) * 60 * 60)
				# start_working_date = start_working_date - timedelta(hours=SERVER_TIMEZONE)
				
				end_working_date = calculated_date + timedelta(hours=SERVER_TIMEZONE)
				end_working_date = end_working_date.replace(hour=0, minute=0, second=0, microsecond=0)
				end_working_date += timedelta(seconds=(end_working_time - SERVER_TIMEZONE) * 60 * 60)
				# end_working_date = end_working_date - timedelta(hours=SERVER_TIMEZONE)
		elif working_type == 'max_hour':
			if not is_multi_day:
				start_working_date = start_planned_date
			else:
				# Force set start working date time to 0800
				start_working_date = calculated_date + timedelta(hours=SERVER_TIMEZONE)
				start_working_date = start_working_date.replace(hour=8 + SERVER_TIMEZONE, minute=0, second=0, microsecond=0)
				# start_working_date = start_working_date - timedelta(hours=SERVER_TIMEZONE)
			end_working_date = start_working_date + timedelta(seconds=(working_time_duration) * 60 * 60)
		else:
			raise Exception('Invalid working type')
			
	# Calculate clock_in and clock_out
		if not is_multi_day:
			clock_in = start_working_date if start_planned_date > start_working_date else start_planned_date
			clock_out = end_working_date if finish_confirm_date < end_working_date else finish_confirm_date
		else:
			clock_in = start_working_date
			clock_out = end_working_date
		return clock_in, clock_out
	
	def _determine_clock_datetime(self, cr, uid, start_working_time, end_working_time, order, order_day):
	# Kalau start atau end workingtimenya None, pake start_planned_date atau finish_confirm_date
		if start_working_time is None:
			clock_in = order.start_planned_date
		else:
			start_working_date = order_day.replace(hour=0, minute=0, second=0, microsecond=0)
			start_working_date += timedelta(seconds=(start_working_time - SERVER_TIMEZONE) * 60 * 60)
			if order.start_planned_date and datetime.strptime(order.start_planned_date, '%Y-%m-%d %H:%M:%S') > start_working_date:
				clock_in = start_working_date
			else:
				clock_in = datetime.strptime(order.start_planned_date, '%Y-%m-%d %H:%M:%S')
		if end_working_time is None:
			clock_out = order.finish_confirm_date
		else:
			end_working_date = order_day.replace(hour=0, minute=0, second=0, microsecond=0)
			end_working_date += timedelta(seconds=(end_working_time - SERVER_TIMEZONE) * 60 * 60)
			if order.finish_confirm_date and datetime.strptime(order.finish_confirm_date, '%Y-%m-%d %H:%M:%S') < end_working_date:
				clock_out = end_working_date
			else:
				clock_out = datetime.strptime(order.finish_confirm_date, '%Y-%m-%d %H:%M:%S')
		return clock_in, clock_out
		
	def _get_days_first_last_order(self, cr, uid, driver_id, calculated_date):
		calculated_date = calculated_date.replace(hour=0, minute=0, second=0, microsecond=0)
		calculated_date_from = calculated_date - timedelta(hours=SERVER_TIMEZONE)
		calculated_date_to = calculated_date_from + timedelta(hours=24)
		calculated_date_tommorow_to = calculated_date_to + timedelta(hours=23, minutes=59, seconds=59)
		# Get date's first order
		calculated_date = calculated_date - timedelta(hours=SERVER_TIMEZONE)
		first_order_ids = self.search(cr, uid, [
			('actual_driver_id', '=', driver_id),
			('start_planned_date', '>=', calculated_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('start_planned_date', '<=', calculated_date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('state', 'in', ['started', 'start_confirmed', 'paused', 'resumed', 'finished', 'finish_confirmed'])
		], limit=1, order="start_planned_date asc")
		first_order = self.browse(cr, uid, first_order_ids)
		# Get date's last order
		last_order_ids = self.search(cr, uid, [
			('actual_driver_id', '=', driver_id),
			('finish_confirm_date', '>=', calculated_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('finish_confirm_date', '<=', calculated_date_tommorow_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('start_planned_date', '>=', calculated_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('start_planned_date', '<=', calculated_date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
			('state', '=', 'finish_confirmed')
		], limit=1, order="finish_confirm_date desc")
		last_order = self.browse(cr, uid, last_order_ids)
			# Get date's first finished order
			# first_finished_order_ids = self.search(cr, uid, [
				# ('actual_driver_id', '=', driver_id),
				# ('finish_confirm_date', '>=', date.strftime('%Y-%m-%d 00:00:00')),
				# ('finish_confirm_date', '<=', date.strftime('%Y-%m-%d 23:59:59')),
				# ('state', 'in', ['ready', 'started', 'start_confirmed', 'paused', 'resumed', 'finished', 'finish_confirmed'])
			# ], limit=1, order="finish_confirm_date desc")
			# first_finished_order = self.browse(cr, uid, first_finished_order_ids)
		return first_order, last_order
	
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
			#date_from = (datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S")).replace(hour=0,minute=0,second=0)
			#date_to = (datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S")).replace(hour=23,minute=59,second=59)
			date_from = (datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S") + timedelta(hours=SERVER_TIMEZONE)).replace(hour=0,minute=0,second=0)
			date_to = (datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S") + timedelta(hours=SERVER_TIMEZONE)).replace(hour=23,minute=59,second=59)
			day = date_from
			while day < date_to:
				holidays.append(day)
				day = day + timedelta(hours=24)
		return working_days, holidays

	def _next_workday(self, work_date, working_day_keys, holidays):
		while work_date in holidays: 
			work_date = work_date + timedelta(hours=24)
		while work_date.weekday() not in working_day_keys: work_date = work_date + timedelta(hours=24)
		return work_date
	
# ini akan menjadi legacy Anton di kode Universal: nama method paling panjang!
# :D :D :D jangan dihapus, this is so hilarious!
	def cron_cek_order_still_running_at_1_hour_before_other_order_start(self, cr, uid, context=None):
	# cron untuk cek apakah ada order yg sudah diplot ke mobil x tapi 1 jam sblm nya order sebelumnya ternyata belom selesai
		now = datetime.now()
	# kenapa 65 (menit) bukan 60? mengantisipasi cronnya jalan cukup lambat sehingga setelah 5 menit 
	# masih belum beres
		temp_date = datetime.strftime(now + timedelta(minutes=65), '%Y-%m-%d %H:%M:%S')
		order_ids_ready = self.search(cr, uid, [
			('state','=',"ready"),
			('start_planned_date','<=',temp_date),
		])
	# untuk semua order statenya masih ready, cari order yang masih running dengan actual_vehicle_id yang sama
	# dan order yang masih running tersebut masih running dengan jeda 1 jam sebelum start planned order yang ready		
		for order_ready in self.browse(cr, uid, order_ids_ready):
			order_ids_running = self.search(cr, uid, [
				('start_confirm_date','!=',False),
				('finish_confirm_date','=',False),
				('actual_vehicle_id','=',order_ready.assigned_vehicle_id.id),
			])
		# kalau ternyata order tersebut belum selesai dengan beda waktu 60 sblm order ready start_planned_date, meesage ke dispatcher
			if len(order_ids_running) > 0:
				for order in self.browse(cr, uid, order_ids_running):
					self._message_dispacther(cr, uid, order.id, 
						_('Order %s still is still running but in one hour another order should have been started.') % order.name)

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
			now = datetime.now - timedelta(hours=SERVER_TIMEZONE)
			start = datetime.strptime(order.start_planned_date,'%Y-%m-%d %H:%M:%S')
			if start + timedelta(minutes=order.customer_contract_id.max_delay_minutes) < now:
				self.write(cr, uid, [order.id], {
					'state': 'canceled',
					'cancel_date': datetime.now(),
					'cancel_by': SUPERUSER_ID,
					'cancel_previous_state': order.state,
				}, context={'delay_exceeded': True})
	
	def cron_autocancel_fullday_orders(self, cr, uid, context=None):
		# ambil semua order yang by_order dan belum start (new, confirmed, ready)
		order_ids = self.search(cr, uid, [
			('service_type','=','full_day'),('state','in',['new','confirmed','ready'])
		])
		if len(order_ids) == 0: return
		# untuk setiap order itu
		for order in self.browse(cr, uid, order_ids):
			# kalau waktu sekarang sudah melewati batas delay, maka cancel si order
			start = datetime.strptime(order.start_planned_date,'%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0, microsecond=0)
			now = datetime.strptime(datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S').replace(hour=0, minute=0, second=0, microsecond=0)
			if now > start :
				self.write(cr, uid, [order.id], {
					'state': 'canceled',
					'cancel_date': datetime.now(),
					'cancel_by': SUPERUSER_ID,
					'cancel_previous_state': order.state,
				}, context={'delay_exceeded': True})

	def cron_autogenerate_fullday(self, cr, uid, context={}):

		contract_obj = self.pool.get('foms.contract')
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
				working_days, holidays = self._get_contract_workdays(contract)
				working_day_keys = working_days.keys()
				contract_start_date = datetime.strptime(contract.start_date,"%Y-%m-%d")
				last_fullday_autogenerate = contract.last_fullday_autogenerate_date and datetime.strptime(contract.last_fullday_autogenerate_date,'%Y-%m-%d') or None
			# tentukan first order date dan mau berapa banyak bikin ordernya
				last_order_date = last_fullday_autogenerate or datetime.strptime('1970-01-01','%Y-%m-%d') + timedelta(hours=24)
				if not contract.last_fullday_autogenerate_date or last_order_date < today:
					#first_order_date = max([contract_start_date, last_order_date, today])
					first_order_date = max([contract_start_date, last_order_date])
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
						context.update({'source': 'cron'})
						new_id = self.create(cr, uid, {
							'customer_contract_id': contract.id,
							'service_type': contract.service_type,
							'request_date': counter_date,
							'order_by': fleet.fullday_user_id.id,
							'assigned_vehicle_id': fleet.fleet_vehicle_id.id,
							'assigned_driver_id': fleet.driver_id.id,
							'pin': fleet.fullday_user_id.pin,
							'start_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['start']) - timedelta(hours=SERVER_TIMEZONE),
							'finish_planned_date': counter_date + timedelta(hours=working_days[counter_date.weekday()]['end']) - timedelta(hours=SERVER_TIMEZONE),
						}, context=context)
					last_fullday = counter_date
					counter_date = counter_date + timedelta(hours=24)
					counter_date = self._next_workday(counter_date, working_day_keys, holidays)
					day += 1
			# update last_fullday_autogenerate_date untuk kontrak ini
				contract_obj.write(cr, uid, [contract.id], {
					'last_fullday_autogenerate_date': last_fullday
				})

	def cron_autogenerate_shuttle(self, cr, uid, context={}):

		print "mulai cron shuttle"

		contract_obj = self.pool.get('foms.contract')
	# bikin order shuttle untuk n hari ke depan secara berkala
	# set tanggal2
		today = (datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
		next_day = today + timedelta(hours=24)
		next7days = today + timedelta(hours=24*1)
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
							'order_by': uid,
							'assigned_vehicle_id': schedule['fleet_vehicle_id'],
							'assigned_driver_id': fleet_drivers[schedule['fleet_vehicle_id']],
							'start_planned_date': counter_date + timedelta(hours=schedule['departure_time']) - timedelta(hours=SERVER_TIMEZONE),
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
	# filter pilihan order origin district
		region_obj = self.pool.get('chjs.region')
		district_ids = region_obj.search(cr, uid, [('parent_id','=',contract_data.homebase_id.id)])
	# filter pilihan order origin area
		area_obj = self.pool.get('foms.order.area')
		area_ids = area_obj.search(cr, uid, [('homebase_id','=',contract_data.homebase_id.id)])
	# filter pilihan allocation unit
		allocation_unit_ids = []
		for alloc in contract_data.allocation_units:
			allocation_unit_ids.append(alloc.id)
	# filter pilihan assigned dan actual vehicle serta assigned dan actual driver
		fleet_ids = []
		driver_ids = []
		for fleet in contract_data.car_drivers:
			fleet_ids.append(fleet.fleet_vehicle_id.id)
			driver_ids.append(fleet.driver_id.id)
	# bila fullday maka harus dipilih Order by (yaitu penumpang fullday), jangan default=uid
		value = {}
		value['service_type'] = contract_data.service_type
		if contract_data.service_type == 'full_day':
			value['order_by'] = ''
		return {
			'value': value,
			'domain': {
				'fleet_type_id': [('id','in',fleet_type_ids)],
				'origin_district_id': [('id','in',district_ids)],
				'origin_area_id': [('id','in',area_ids)],
				'alloc_unit_id': [('id','in',allocation_unit_ids)],
				'assigned_vehicle_id': [('id','in',fleet_ids)],
				'actual_vehicle_id': [('id','in',fleet_ids)],
				'assigned_driver_id': [('id','in',driver_ids)],
				'actual_driver_id': [('id','in',driver_ids)],
			}
		}
	
	def onchange_origin_district_id(self, cr, uid, ids, customer_contract_id, origin_district_id, context=None):
		if not customer_contract_id: return {}
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
	# filter pilihan order origin area
		area_obj = self.pool.get('foms.order.area')
		if origin_district_id:
			area_ids = area_obj.search(cr, uid, [
				('homebase_id','=',contract_data.homebase_id.id),
				('district_id','=',origin_district_id)
			])
		else:
			area_ids = area_obj.search(cr, uid, [
				('homebase_id','=',contract_data.homebase_id.id),
			])
		return {
			'domain': {
				'origin_area_id': [('id','in',area_ids)],
			}
		}
	
	def onchange_dest_district_id(self, cr, uid, ids, dest_district_id, context=None):
	# filter pilihan order dest area
		area_obj = self.pool.get('foms.order.area')
		if not dest_district_id: return {}
		area_ids = area_obj.search(cr, uid, [
			('district_id','=',dest_district_id)
		])
		return {
			'domain': {
				'dest_area_id': [('id','in',area_ids)],
			}
		}

	def onchange_service_type(self, cr, uid, ids, customer_contract_id, fleet_type_id, service_type, start_planned_date):
		result = {'domain': {}, 'value': {}}
		result['domain'].update(self._domain_filter_vehicle(cr, uid, ids, customer_contract_id, fleet_type_id, service_type))
		return result
	
	def onchange_request_by(self, cr, uid, ids, service_type, customer_contract_id, order_by_id, start_planned_date, context=None):
		if service_type not in ['full_day']: return {}
		contract_obj = self.pool('foms.contract')
		customer_contract = contract_obj.browse(cr, uid, customer_contract_id)
		car_drivers = customer_contract.car_drivers
		fleet_data = None
		for fleet in car_drivers:
			if fleet.fullday_user_id.id == order_by_id:
				fleet_data = fleet
				break
		if fleet_data and context.get('source', False) == 'form':
			return { 'value': {
				'assigned_driver_id': fleet_data.driver_id.id,
				'assigned_vehicle_id': fleet_data.fleet_vehicle_id.id,
				'pin': fleet_data.fullday_user_id.pin,
			}}
	
	def this_order_not_in_working_time(self, cr, uid, customer_contract_id, start_planned_date):
		contract_obj = self.pool('foms.contract')
		customer_contracts = contract_obj.browse(cr, uid, customer_contract_id)
		for customer_contract in customer_contracts:
			for holiday in customer_contract.working_time_id.leave_ids:
				date_from_holiday = datetime.strftime((datetime.strptime(holiday.date_from,"%Y-%m-%d %H:%M:%S")).replace(hour=0,minute=0,second=0),"%Y-%m-%d %H:%M:%S")
				date_to_holiday =  datetime.strftime((datetime.strptime(holiday.date_to,"%Y-%m-%d %H:%M:%S")).replace(hour=23,minute=59,second=59),"%Y-%m-%d %H:%M:%S")
				if start_planned_date >= date_from_holiday and start_planned_date <= date_to_holiday:
					return True
		return False
		
	def _domain_filter_vehicle(self, cr, uid, ids, customer_contract_id, fleet_type_id, service_type):
		if not fleet_type_id: return {}
		# filter kendaraan yang dipilih
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, customer_contract_id)
		fleet_ids = []
		# cuman yang di bawah kontrak ini,
		for vehicle in contract_data.car_drivers:
			if vehicle.fleet_type_id.id == fleet_type_id:
				fleet_ids.append(vehicle.fleet_vehicle_id.id)
			#... plus semua yang tidak sedang ada di bawah kontrak aktif bila ordernya bukan by-order
		if service_type != 'by_order':
			vehicle_obj = self.pool.get('fleet.vehicle')
			vehicle_ids = vehicle_obj.search(cr, uid, [])
			for vehicle in vehicle_obj.browse(cr, uid, vehicle_ids):
				if vehicle.model_id.id != fleet_type_id: continue
				if vehicle.current_contract_id == None or vehicle.current_contract_id.state not in ['active','planned']:
					fleet_ids.append(vehicle.id)
		return {
			'assigned_vehicle_id': [('id','in',fleet_ids)]
		}
	
	def onchange_fleet_type(self, cr, uid, ids, customer_contract_id, fleet_type_id, service_type):
		result = {'domain': {}}
		result['domain'].update(self._domain_filter_vehicle(cr, uid, ids, customer_contract_id, fleet_type_id, service_type))
		return result

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
		'homebase_id': fields.many2one('chjs.region', 'Homebase', required=True, ondelete='restrict', domain=[('type','=','city')]),
		'district_id': fields.many2one('chjs.region', 'District', required=True, ondelete='restrict', domain=[('type','=','district')]),
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

class foms_order_area_set_delay_memory(osv.osv_memory):

	_name = "foms.order.area.set.delay.memory"
	_description = 'Set Order Area Delay Wizard'

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'homebase_id': fields.many2one('chjs.region', 'Homebase', required=True, domain=[('type','=','city')]),
		'district_id': fields.many2one('chjs.region', 'District', required=True, domain=[('type','=','district')]),
		'area_from_id': fields.many2one('foms.order.area', 'From Area', required=True),
		'delay_lines': fields.one2many('foms.order.area.set.delay.line.memory', 'header_id', 'Delays'),
	}

	def onchange_area_from(self, cr, uid, ids, area_from_id):
		if not area_from_id: return {}
	# ambil semua data yang area_from nya sesuai yang dipilih
		area_delay_obj = self.pool.get('foms.order.area.delay')
		area_delay_ids = area_delay_obj.search(cr, uid, [('area_from_id','=',area_from_id)])
		if len(area_delay_ids) == 0: return {}
		lines = []
		for area_delay in area_delay_obj.browse(cr, uid, area_delay_ids):
			lines.append([0,False,{
				'delay_id': area_delay.id,
				'area_to_id': area_delay.area_to_id.id,
				'delay': area_delay.delay,
				}])
		return {
			'value': {
				'delay_lines': lines,
			}
		}

	def action_set_delays(self, cr, uid, ids, context={}):
		form_data = self.browse(cr, uid, ids[0])
		area_delay_obj = self.pool.get('foms.order.area.delay')
		for line in form_data.delay_lines:
			if line.delay_id:
				print "masuk write"
				area_delay_obj.write(cr, uid, [line.delay_id.id], {
					'area_to_id': line.area_to_id.id,
					'delay': line.delay,
					})
			else:
				print "masuk create"
				area_delay_obj.create(cr, uid, {
					'area_from_id': form_data.area_from_id.id,
					'area_to_id': line.area_to_id.id,
					'delay': line.delay,
					})
		return True

class foms_order_area_set_delay_line_memory(osv.osv_memory):

	_name = "foms.order.area.set.delay.line.memory"
	_description = 'Set Order Area Delay Wizard Lines'

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.order.area.set.delay.memory', 'Header'),
		'delay_id': fields.many2one('foms.order.area.delay', 'Existing Delay ID'),
		'area_to_id': fields.many2one('foms.order.area', 'To Area', required=True),
		'delay': fields.integer('Delay (minutes)', required=True),
	}

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
		# kalau dari mobile app dan cancel reason nya kosong, maka itu berarti order dicancel karena delay exceeded
			if not (cancel_reason or cancel_reason_other):
				model_obj = self.pool.get('ir.model.data')
				model, reason_id = model_obj.get_object_reference(cr, uid, 'universal', 'foms_cancel_reason_delay_exceeded')
				cancel_reason = reason_id
	# kalo ada ids nya maka dari memory form Odoo
		else:
			form_data = self.browse(cr, uid, ids[0])
			order_id = form_data.order_id.id
			cancel_reason = form_data.cancel_reason.id
			cancel_reason_other = form_data.cancel_reason_other
			cancel_by = uid

		order_obj = self.pool.get('foms.order')
		order_data = order_obj.browse(cr, uid, order_id, context=context)
	# state harus belum start
		if order_data.state not in ['new','rejected','confirmed','ready']:
			raise osv.except_osv(_('Order Error'),_('Order has already ongoing or finished, so it cannot be canceled.'))
	# entah cancel reason atau cancel reason other harus diisi
		if not cancel_reason and not cancel_reason_other:
			raise osv.except_osv(_('Order Error'),_('Please choose Cancel Reason or type in Other Reason.'))
	# kalau tipe kontrak adalah by_order dan sudah mencapai limit cancel before start
	# maka ngga boleh cancel
		if order_data.customer_contract_id.service_type == 'by_order' and order_data.customer_contract_id.max_cancel_minutes:
			now = datetime.now() - timedelta(hours=SERVER_TIMEZONE)
			start_planned_date = datetime.strptime(order_data.start_planned_date, DEFAULT_SERVER_DATETIME_FORMAT)
			time_diff = start_planned_date - now
			temp = divmod(time_diff.total_seconds(), 60)
			if time_diff.total_seconds() < 0 or temp[0] < order_data.customer_contract_id.max_cancel_minutes:
				raise osv.except_osv(_('Order Error'),_('This order is too close to its planned start date and thus cannot be canceled.'))
	# go with the calcellation
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
		'replaced_vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle to be Replaced', required=True),
		'replacement_vehicle_id': fields.many2one('fleet.vehicle', 'Replacement Vehicle', required=True),
		'replacement_date': fields.datetime('Effective Since', required=True),
		'replacement_reason': fields.text('Replacement Reason'),
	}
	
# CONSTRAINT ---------------------------------------------------------------------------------------------------------------
	
	def _constraint_vehicle_same_type(self, cr, uid, ids, context=None):
	# Cek apakah vehiclenya yang direplace setipe
		for replace_vehicles in self.browse(cr, uid, ids, context):
			for replace_vehicle in replace_vehicles:
				if replace_vehicle.replaced_vehicle_id.model_id.id != replace_vehicle.replacement_vehicle_id.model_id.id:
					return False
		return True
	
	def _constraint_replacement_vehicle_use_in_other_contract(self, cr, uid, ids, context=None):
		# Cek apakah vehiclenya yang mereplace ada di contract lain
		contract_fleet_obj = self.pool.get('foms.contract.fleet')
		for replace_vehicles in self.browse(cr, uid, ids, context):
			for replace_vehicle in replace_vehicles:
				args = [
					('header_id.state', 'in', ['active']),
					('fleet_vehicle_id','=',replace_vehicle.replacement_vehicle_id.id),
				]
				contract_fleet_ids = contract_fleet_obj.search(cr, uid, args)
				if len(contract_fleet_ids)>0:
					return False
		return True

	_constraints = [
		(_constraint_vehicle_same_type, _('Vehicles must be in the same type.'), ['replaced_vehicle_id', 'replacement_vehicle_id']),
		(_constraint_replacement_vehicle_use_in_other_contract, _('This car is being used in other contracts.'), ['replaced_vehicle_id', 'replacement_vehicle_id']),
	]
	
# OVERRIDES ---------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		new_replace_vehicle_id = super(foms_order_replace_vehicle, self).create(cr, uid, vals, context=context)
		self._replace_on_orders(cr, uid, [new_replace_vehicle_id])
		self._replace_on_contracts(cr, uid, [new_replace_vehicle_id])
		return new_replace_vehicle_id
	
# METHODS -----------------------------------------------------------------------------------------------------------------
	
	def _replace_on_orders(self, cr, uid, replace_vehicle_ids):
		order_obj = self.pool.get('foms.order')
		for replace_vehicle in self.browse(cr, uid, replace_vehicle_ids):
		# Ambil order yang statenya berikut ini
			args = [ 
				('state', 'in', ['new','confirmed','ready']),
				('start_planned_date','>=',replace_vehicle.replacement_date),
				('assigned_vehicle_id','=',replace_vehicle.replaced_vehicle_id.id),
			]
		# Update data vehicle di order
			order_ids = order_obj.search(cr, uid, args)
			order_obj.write(cr, uid, order_ids, {
				'assigned_vehicle_id': replace_vehicle.replacement_vehicle_id.id,
			})
	
	def _replace_on_contracts(self, cr, uid, replace_vehicle_ids):
		contract_fleet_obj = self.pool.get('foms.contract.fleet')
		for replace_vehicle in self.browse(cr, uid, replace_vehicle_ids):
		# Ambil order yang statenya berikut ini
			args = [ 
				('header_id.state', 'not in', ['terminated', 'finished']),
				('header_id.start_date', '<=', replace_vehicle.replacement_date),
				('header_id.end_date', '>=', replace_vehicle.replacement_date),
				('fleet_vehicle_id','=',replace_vehicle.replaced_vehicle_id.id),
			]
		# Update data vehicle fleet planning si contract
			contract_fleet_ids = contract_fleet_obj.search(cr, uid, args)
			contract_fleet_obj.write(cr, uid, contract_fleet_ids, {
				'fleet_vehicle_id': replace_vehicle.replacement_vehicle_id.id,
			})
				
# ==========================================================================================================================

class foms_order_replace_driver(osv.osv):

	_name = "foms.order.replace.driver"
	_description = 'Order Replace Driver'

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'replaced_driver_id': fields.many2one('hr.employee', 'Driver to be Replaced', required=True),
		'replacement_driver_id': fields.many2one('hr.employee', 'Replacement Driver', required=True),
		'replacement_date': fields.datetime('Effective Since', required=True),
		'replacement_reason': fields.text('Replacement Reason'),
	}
	
	def _constraint_replacement_driver_use_in_other_contract(self, cr, uid, ids, context=None):
		# Cek apakah driver yang mereplace ada di contract lain
		contract_fleet_obj = self.pool.get('foms.contract.fleet')
		for replace_drivers in self.browse(cr, uid, ids, context):
			for replace_driver in replace_drivers:
				args = [
					('header_id.state', 'in', ['active']),
					('driver_id','=',replace_driver.replacement_driver_id.id),
				]
				contract_fleet_ids = contract_fleet_obj.search(cr, uid, args)
				if len(contract_fleet_ids)>0:
					return False
		return True

	_constraints = [
		(_constraint_replacement_driver_use_in_other_contract, _('Driver is being used in other contracts.'), ['replaced_driver_id', 'replacement_driver_id']),
	]

# OVERRIDES ---------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		new_replace_driver_id = super(foms_order_replace_driver, self).create(cr, uid, vals, context=context)
		self._replace_on_orders(cr, uid, [new_replace_driver_id])
		self._replace_on_contracts(cr, uid, [new_replace_driver_id])
		return new_replace_driver_id
	
# METHODS -----------------------------------------------------------------------------------------------------------------
	
	def _replace_on_orders(self, cr, uid, replace_driver_ids):
		order_obj = self.pool.get('foms.order')
		for replace_driver in self.browse(cr, uid, replace_driver_ids):
		# Ambil order yang statenya berikut ini
			args = [ 
				('state', 'in', ['new', 'confirmed', 'ready']),
				('start_planned_date', '>=', replace_driver.replacement_date),
				('assigned_driver_id','=',replace_driver.replaced_driver_id.id),
			]
			order_ids = order_obj.search(cr, uid, args)
			order_obj.write(cr, uid, order_ids, {
				'assigned_driver_id': replace_driver.replacement_driver_id.id,
			})
	
	def _replace_on_contracts(self, cr, uid, replace_driver_ids):
		contract_fleet_obj = self.pool.get('foms.contract.fleet')
		for replace_driver in self.browse(cr, uid, replace_driver_ids):
		# Ambil order yang statenya berikut ini
			args = [ 
				('header_id.state', 'not in', ['terimnated', 'finished']),
				('header_id.start_date', '<=', replace_driver.replacement_date),
				('header_id.end_date', '>=', replace_driver.replacement_date),
				('driver_id','=',replace_driver.replaced_driver_id.id),
			]
			contract_fleet_ids = contract_fleet_obj.search(cr, uid, args)
			contract_fleet_obj.write(cr, uid, contract_fleet_ids, {
				'driver_id': replace_driver.replacement_driver_id.id,
			})
		
class foms_order_try_cron(osv.osv_memory):

	_name = 'foms.order.try.cron'
	_description = 'Testing buat cron'

	_columns = {
		'cron': fields.selection((
			('cron_autogenerate_fullday','Autogenerate fullday'),
			('cron_sync_gps_data','Sync GPS data'),
		), 'Cron Name')
	}

	def action_execute(self, cr, uid, ids, context={}):
		form_data = self.browse(cr, uid, ids[0])
		order_obj = self.pool.get('foms.order')
		gps_obj = self.pool.get('foms.gps.sync')
		if form_data.cron == 'cron_autogenerate_fullday':
			order_obj.cron_autogenerate_fullday(cr, uid, context)
			raise osv.except_osv('test','test')
		elif form_data.cron == 'cron_sync_gps_data':
			gps_obj.cron_sync_gps_data(cr, uid, context)

# ==========================================================================================================================

class foms_booking_purpose(osv.osv):
	
	_name = "foms.booking.purpose"
	_description = 'Foms booking purpose'
	
	# COLUMNS ------------------------------------------------------------------------------------------------------------------
	
	_columns = {
		'name': fields.char('Purpose', size=64, required=True)
	}
