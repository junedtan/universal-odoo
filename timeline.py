import json
from datetime import datetime, date, timedelta
from openerp.osv import osv
from openerp import SUPERUSER_ID
from openerp.tools.translate import _, translate
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from . import SERVER_TIMEZONE

# warna berdasarkan status. RGB diset di timeline.js
STATE_COLORS = {
	'new': 'pending',
	'confirmed': 'pending',
	'ready': 'ready',
	'started': 'ready',
	'start_confirmed': 'running',
	'paused': 'running',
	'resumed': 'running',
	'finished': 'running',
	'finish_confirmed': 'finished',
}


class universal_timeline(osv.osv):
	_name = 'universal.timeline'
	_description = 'Timeline Controller'
	_auto = False

# versi oktober 2018. list timeline langsung diambil dari order, terlepas dari 
# kontrak manapun
	def get_timeline_by_date(self, cr, uid, date_string, customer_name, service_type):
		user_obj = self.pool.get('res.users');
		order_obj = self.pool.get('foms.order');
		contract_fleet_obj = self.pool.get('foms.contract.fleet');

		date = datetime.strptime(date_string,'%m/%d/%Y')
		tomorrow_date = date + timedelta(days=1)

	# search actual orders
		domain = [
			('customer_contract_id.customer_id.name', 'ilike', customer_name),
			('customer_contract_id.service_type', 'ilike', service_type),
			('state', 'not in', ['canceled', 'rejected','new','confirmed']),
			('start_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
			'|',('finish_date', '>=', (date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")), ('finish_date', '=', False),
		]
		actual_order_ids = order_obj.search(cr, uid, domain, order='start_date ASC')
		actual_orders = order_obj.browse(cr, uid, actual_order_ids) if len(actual_order_ids) > 0 else []

	# search planned orders
		domain = [
			('customer_contract_id.customer_id.name', 'ilike', customer_name),
			('customer_contract_id.service_type', 'ilike', service_type),
			('state', 'not in', ['canceled', 'rejected','new','confirmed']),
			('start_planned_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
			('finish_planned_date', '>=', (date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
		]
		planned_order_ids = order_obj.search(cr, uid, domain, order='start_planned_date ASC')
		planned_orders = order_obj.browse(cr, uid, planned_order_ids) if len(planned_order_ids) > 0 else []

		drivers_ids = []
	# extract driver_id dari actual dan planned orders
		for order in actual_orders:
			drivers_ids.append(order.actual_driver_id.user_id.id)
		for order in planned_orders:
			drivers_ids.append(order.assigned_driver_id.user_id.id)
	# tambahkan id-id driver dari fleet planning kontrak yang masih aktif
	# ini supaya driver yang terikat kontrak tapi belum dapet order tetap muncul di list
		fleet_ids = contract_fleet_obj.search(cr, uid, [
			('header_id.state', '=', 'active'),
			('header_id.customer_id.name', 'ilike', customer_name),
		])
		contract_fleets = contract_fleet_obj.browse(cr, uid, fleet_ids)
		for fleet in contract_fleets:
			drivers_ids.append(fleet.driver_id.user_id.id)
	# di titik ini list userid para driver sudah lengkap. unikkan list driver supaya
	# ngga dobel ngambil pas browse di bawah
		drivers_ids = list(set(drivers_ids))
	# mulai isi baris, driver by driver
		result = []
		for driver_data in user_obj.browse(cr, uid, drivers_ids):
		# isi actual
			daily_actual_orders = []
			finish_before = 0
			license_plate = ""
			vehicle_type = ""
			for actual_order in actual_orders:
			# hanya untuk yang actual drivernya adalah driver ini
				if actual_order.actual_driver_id.user_id.id != driver_data.id: continue
			# isi license plate. di actual sengaja license plate ditimpa terus sampe 
			# actual order terakhir, supaya dapet yang terbaru
				if actual_order.assigned_vehicle_id:
					license_plate = actual_order.assigned_vehicle_id.license_plate
					vehicle_type = actual_order.assigned_vehicle_id.model_id.modelname
				elif actual_order.actual_vehicle_id:
					license_plate = actual_order.actual_vehicle_id.license_plate
					vehicle_type = actual_order.actual_vehicle_id.model_id.modelname
			# isi start dan finish untuk order ini
				start = datetime.strptime(actual_order.start_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				if actual_order.finish_date:
					finish = datetime.strptime(actual_order.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				else:
					now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
					if now >= date and now <= tomorrow_date:
						finish = now
					elif now >= tomorrow_date:
						finish = tomorrow_date
					else:
						finish = date
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				if finish_minute - start_minute != 0:
			# tambahin ke actual orders
					daily_actual_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
						'color': STATE_COLORS.get(actual_order.state,'none'),
					})
				finish_before = finish_minute
		# isi planned
			daily_planned_orders = []
			finish_before = 0
			for planned_order in planned_orders:
			# hanya untuk yang assigned drivernya adalah driver ini
				if planned_order.assigned_driver_id.user_id.id != driver_data.id: continue
				print "masuk: %s" % planned_order.name
			# isi license plate. hanya kalau kosong saja (kalau udah keisi di actual di atas
			# ya ga usah ditimpa lagi)
				if not license_plate and planned_order.assigned_vehicle_id:
					license_plate = planned_order.assigned_vehicle_id.license_plate
					vehicle_type = planned_order.assigned_vehicle_id.model_id.modelname
			# tentuin waktu mulai dan selesai. waktu selesai untuk order yang sudah selesai
			# ngikut ke actual finish
				start = datetime.strptime(planned_order.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				if planned_order.state in ['finished','finish_confirmed']:
					finish = datetime.strptime(planned_order.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				else:
					finish = datetime.strptime(planned_order.finish_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
			# tambahin ke planned order
				if finish_minute - start_minute != 0:
					daily_planned_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
						'color': STATE_COLORS.get(planned_order.state,'none'),
					})
				finish_before = finish_minute
		# now ("garis" vertikal penanda jam sekarang)
			now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
			now_time = []
			if now >= date and now <= tomorrow_date:
				now_time.append({
					'start': now.hour * 60,
					'finish': 60,
				})
		# kalo license plate masih kosong, ambil dari assignment kontraknya
			if not license_plate:
				for fleet in contract_fleets:
					if fleet.driver_id.user_id.id == driver_data.id:
						license_plate = fleet.fleet_vehicle_id.license_plate
						vehicle_type = fleet.fleet_vehicle_id.model_id.modelname
						break
		# tentukan sorting nomor plat. kondisikan supaya nomor plat menjadi B BOL 1025
		# dari B 1025 BOL
			temp = license_plate.split(" ")
			try:
				sort = "%s %s %s" % (temp[0],temp[2],temp[1])
			except IndexError:
				sort = license_plate
		# gabungkan semuanya!
			result.append({
				'driver_id': driver_data.id,
				'driver_name': driver_data.name,
				'license_plates': [license_plate],
				'vehicle_type': vehicle_type,
				'sort': sort,
				'planned_orders': daily_planned_orders,
				'actual_orders': daily_actual_orders,
				'has_order': len(daily_planned_orders) > 0 or len(daily_actual_orders) > 0,
				'now_time': now_time,
			})
	# urutkan result berdasarkan nama supir
		result = sorted(result, key=lambda k: k['sort'])
	# akhirnya...
		hours = []
		for hour in range(0, 24):
			#hours.append(str(hour).zfill(2) + ':00')
			hours.append(str(hour).zfill(2))
		return {
			'status': 'ok',
			'drivers': result,
			'hours': hours,
		}



	"""
	Versi pre-Oktober 2018. list mobil diambil dari fleet contract dan driver
	diambil dari pasangan mobil. Hal ini menyebabkan driver pengganti ngga akan
	masuk ke list.
	def get_timeline_by_date(self, cr, uid, date_string, customer_name, service_type):
		user_obj = self.pool.get('res.users');
		order_obj = self.pool.get('foms.order');
		contract_fleet_obj = self.pool.get('foms.contract.fleet');
		date = datetime.strptime(date_string,'%m/%d/%Y')
		tomorrow_date = date + timedelta(days=1)
		
		drivers_ids = user_obj.get_user_ids_by_group(cr, SUPERUSER_ID, 'universal', 'group_universal_driver')
		result = []
		for driver_data in user_obj.browse(cr, uid, drivers_ids):
		# GET LICENSE PLATE
			fleet_ids = contract_fleet_obj.search(cr, uid, [
				('header_id.state', '=', 'active'),
				('header_id.customer_id.name', 'ilike', customer_name),
				('driver_id.user_id', '=', driver_data.id),
			])
			license_plates = []
			for fleet_data in contract_fleet_obj.browse(cr, uid, fleet_ids):
				if fleet_data.fleet_vehicle_id.license_plate:
					license_plates.append(fleet_data.fleet_vehicle_id.license_plate)
		# GET PLANNED AND ACTUAL ORDER
			domain =  [
				('customer_contract_id.customer_id.name', 'ilike', customer_name),
				('customer_contract_id.service_type', 'ilike', service_type),
				('state', 'not in', ['canceled', 'rejected']),
				('assigned_driver_id.user_id', '=', driver_data.id),
				('start_planned_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
				('finish_planned_date', '>=', (date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
			]
			planned_order_ids = order_obj.search(cr, uid, domain, order='start_planned_date ASC')
		
			domain = [
				('customer_contract_id.customer_id.name', 'ilike', customer_name),
				('customer_contract_id.service_type', 'ilike', service_type),
				('state', 'not in', ['canceled', 'rejected']),
				('actual_driver_id.user_id', '=', driver_data.id),
				('start_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
				'|',('finish_date', '>=', (date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")), ('finish_date', '=', False),
			]
			actual_order_ids = order_obj.search(cr, uid, domain, order='start_date ASC')
		# ACTUAL ORDER
			actual_orders = []
			finish_before = 0
			for order_actual in order_obj.browse(cr, uid, actual_order_ids):
				start = datetime.strptime(order_actual.start_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				if order_actual.finish_date:
					finish = datetime.strptime(order_actual.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				else:
					now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
					if now >= date and now <= tomorrow_date:
						finish = now
					elif now >= tomorrow_date:
						finish = tomorrow_date
					else:
						finish = date
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				if finish_minute - start_minute != 0:
					actual_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
					})
				finish_before = finish_minute
		# PLANNED ORDER
			planned_orders = []
			finish_before = 0
			for order_planned in order_obj.browse(cr, uid, planned_order_ids):
				start = datetime.strptime(order_planned.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				finish = datetime.strptime(order_planned.finish_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				if finish_minute - start_minute != 0:
					planned_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
					})
				finish_before = finish_minute
		# NOW
			now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
			now_time = []
			if now >= date and now <= tomorrow_date:
				now_time.append({
					'start': now.hour * 60,
					'finish': 60,
				})
		# ADD TO RESULT
			if len(fleet_ids) != 0:
				result.append({
					'driver_id': driver_data.id,
					'driver_name': driver_data.name,
					'license_plates': license_plates,
					'planned_orders': planned_orders,
					'actual_orders': actual_orders,
					'now_time': now_time,
				})
		hours = []
		for hour in range(0, 24):
			hours.append(str(hour).zfill(2) + ':00')
		return {
			'status': 'ok',
			'drivers': result,
			'hours': hours,
		}
	"""
	
	def get_timeline_by_driver(self, cr, uid, driver_id, start_date_string, end_date_string, customer_name, service_type):
		user_obj = self.pool.get('res.users')
		order_obj = self.pool.get('foms.order')
		start_date = datetime.strptime(start_date_string,'%m/%d/%Y')
		end_date = datetime.strptime(end_date_string,'%m/%d/%Y')
		
		driver_data = user_obj.browse(cr, uid, driver_id)
		result = []
		while start_date <= end_date:
			tomorrow_date = start_date + timedelta(days=1)
		# GET PLANNED AND ACTUAL ORDER
			planned_order_ids = order_obj.search(cr, uid, [
				('customer_contract_id.customer_id.name', 'ilike', customer_name),
				('customer_contract_id.service_type', 'ilike', service_type),
				('state', 'not in', ['canceled', 'rejected']),
				('assigned_driver_id.user_id', '=', driver_data.id),
				('start_planned_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
				('finish_planned_date', '>=', (start_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
			], order='start_planned_date ASC')
			actual_order_ids = order_obj.search(cr, uid, [
				('customer_contract_id.customer_id.name', 'ilike', customer_name),
				('customer_contract_id.service_type', 'ilike', service_type),
				('state', 'not in', ['canceled', 'rejected']),
				('actual_driver_id.user_id', '=', driver_data.id),
				('start_date', '<', (tomorrow_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")),
				'|',('finish_date', '>=', (start_date - timedelta(hours=SERVER_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")), ('finish_date', '=', False),
			], order='start_date ASC')
		# ACTUAL ORDER
			actual_orders = []
			finish_before = 0
			now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
			for order_actual in order_obj.browse(cr, uid, actual_order_ids):
				start = datetime.strptime(order_actual.start_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				if order_actual.finish_date:
					finish = datetime.strptime(order_actual.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				else:
					finish = now
				start_minute = 0
				finish_minute = 24 * 60
				if start > start_date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				if start_date > now:
					finish_minute = 0
				if finish_minute - start_minute != 0:
					actual_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
					})
				finish_before = finish_minute
		# PLANNED ORDER
			planned_orders = []
			finish_before = 0
			for order_planned in order_obj.browse(cr, uid, planned_order_ids):
				start = datetime.strptime(order_planned.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				finish = datetime.strptime(order_planned.finish_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=SERVER_TIMEZONE)
				start_minute = 0
				finish_minute = 24 * 60
				if start > start_date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				if finish_minute - start_minute != 0:
					planned_orders.append({
						'start': start_minute - finish_before,
						'finish': finish_minute - start_minute,
					})
				finish_before = finish_minute
		# NOW
			now = datetime.now() + timedelta(hours=SERVER_TIMEZONE)
			now_time = []
			if now >= start_date and now <= tomorrow_date:
				now_time.append({
					'start': now.hour * 60,
					'finish': 60,
				})
		# ADD TO RESULT
			result.append({
				'date_string': start_date.strftime("%d-%m-%Y"),
				'planned_orders': planned_orders,
				'actual_orders': actual_orders,
				'now_time': now_time,
			})
			start_date += timedelta(days=1);
		hours = []
		for hour in range(0, 24):
			hours.append(str(hour).zfill(2) + ':00')
		return {
			'status': 'ok',
			'driver_name': driver_data.name,
			'dates': result,
			'hours': hours,
		}
	
	def get_required_datas(self, cr, uid):
		user_obj = self.pool.get('res.users')
		contract_obj = self.pool.get('foms.contract')
		
	# DRIVER
		driver_ids = user_obj.get_user_ids_by_group(cr, SUPERUSER_ID, 'universal', 'group_universal_driver')
		drivers = []
		for driver_data in user_obj.browse(cr, uid, driver_ids):
			drivers.append({
				'id': driver_data.id,
				'name': driver_data.name,
			})
		drivers = sorted(drivers, key=lambda driver: driver['name'])
		
	# CUSTOMER
		contract_ids = contract_obj.search(cr, uid, [])
		customers = []
		customers_existing_ids = []
		for contract_data in contract_obj.browse(cr, uid, contract_ids):
			customer_id = contract_data.customer_id.id
			if customer_id not in customers_existing_ids:
				customers_existing_ids.append(customer_id)
				customers.append({
					'id': customer_id,
					'name': contract_data.customer_id.name,
				})
		customers = sorted(customers, key=lambda customer: customer['name'])
		
		return {
			'status': 'ok',
			'drivers': drivers,
			'customers': customers
		}