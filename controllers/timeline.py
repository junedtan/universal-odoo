import json
from datetime import datetime, date, timedelta
from openerp.osv import osv
from openerp import SUPERUSER_ID
from openerp.tools.translate import _, translate
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class universal_timeline(osv.osv):
	_name = 'universal.timeline'
	_description = 'Timeline Controller'
	_auto = False
	
	def get_timeline_by_date(self, cr, uid, day, month, year):
		user_obj = self.pool.get('res.users');
		order_obj = self.pool.get('foms.order');
		contract_fleet_obj = self.pool.get('foms.contract.fleet');
		date = datetime(year=year, month=month, day=day)
		tomorrow_date = date + timedelta(days=1)
		
		drivers_ids = user_obj.get_user_ids_by_group(cr, SUPERUSER_ID, 'universal', 'group_universal_driver')
		result = []
		for driver_data in user_obj.browse(cr, uid, drivers_ids):
		# GET LICENSE PLATE
			fleet_ids = contract_fleet_obj.search(cr, uid, [
				('header_id.state', '=', 'active'),
				('driver_id.user_id', '=', driver_data.id),
			])
			license_plates = []
			for fleet_data in contract_fleet_obj.browse(cr, uid, fleet_ids):
				if fleet_data.fleet_vehicle_id.license_plate:
					license_plates.append(fleet_data.fleet_vehicle_id.license_plate)
		# GET PLANNED AND ACTUAL ORDER
			planned_order_ids = order_obj.search(cr, uid, [
				('state', 'not in', ['canceled', 'rejected']),
				('assigned_driver_id.user_id', '=', driver_data.id),
				('start_planned_date', '<', (tomorrow_date - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")),
				('finish_planned_date', '>=', (date - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")),
			], order='start_planned_date ASC')
			actual_order_ids = order_obj.search(cr, uid, [
				('state', 'not in', ['canceled', 'rejected']),
				('actual_driver_id.user_id', '=', driver_data.id),
				('start_date', '<', (tomorrow_date - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")),
				'|',('finish_date', '>=', (date - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")), ('finish_date', '=', False),
			], order='start_date ASC')
		# ACTUAL ORDER
			actual_orders = []
			finish_before = 0
			for order_actual in order_obj.browse(cr, uid, actual_order_ids):
				start = datetime.strptime(order_actual.start_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				if order_actual.finish_date:
					finish = datetime.strptime(order_actual.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				else:
					finish = datetime.now()
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				actual_orders.append({
					'mode': 'actual',
					'start': start_minute - finish_before,
					'finish': finish_minute - start_minute,
				})
				finish_before = finish_minute
		# PLANNED ORDER
			planned_orders = []
			finish_before = 0
			for order_planned in order_obj.browse(cr, uid, planned_order_ids):
				start = datetime.strptime(order_planned.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				finish = datetime.strptime(order_planned.finish_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				start_minute = 0
				finish_minute = 24 * 60
				if start > date:
					start_minute = start.hour * 60 + start.minute
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				planned_orders.append({
					'mode': 'planned',
					'start': start_minute - finish_before,
					'finish': finish_minute - start_minute,
				})
				finish_before = finish_minute
		# ADD TO RESULT
			result.append({
				'driver_id': driver_data.id,
				'driver_name': driver_data.name,
				'license_plates': license_plates,
				'planned_orders': planned_orders,
				'actual_orders': actual_orders
			})
		hours = []
		for hour in range(0, 24):
			hours.append(str(hour).zfill(2) + ':00')
		return {
			'status': 'ok',
			'drivers': result,
			'hours': hours,
		}