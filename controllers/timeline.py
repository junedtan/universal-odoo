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
		date = datetime(year=year, month=month, day=day)
		tomorrow_date = date + timedelta(days=1)
		
		drivers_ids = user_obj.get_user_ids_by_group(cr, SUPERUSER_ID, 'universal', 'group_universal_driver')
		result = []
		for driver_data in user_obj.browse(cr, uid, drivers_ids):
		# GET PLANNED ORDERS FOR DRIVER
			planned_order_ids = order_obj.search(cr, uid, [
				('assigned_driver_id.user_id', '=', driver_data.id),
				('start_planned_date', '<', tomorrow_date.strftime("%Y-%m-%d")),
				('finish_planned_date', '>=', date.strftime("%Y-%m-%d")),
			])
			planned_orders = []
			for order_data in order_obj.browse(cr, uid, planned_order_ids):
				start = datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				start_minute = 0
				if start > date:
					start_minute = start.hour * 60 + start.minute
				finish = datetime.strptime(order_data.finish_planned_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				finish_minute = 24 * 60
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				planned_orders.append({
					'start': start_minute,
					'finish': finish_minute,
				})
		# GET ACTUAL ORDERS FOR DRIVER
			actual_order_ids = order_obj.search(cr, uid, [
				('actual_driver_id.user_id', '=', driver_data.id),
				('start_date', '<', tomorrow_date.strftime("%Y-%m-%d")),
				('finish_date', '>=', date.strftime("%Y-%m-%d")),
			])
			actual_orders = []
			for order_data in order_obj.browse(cr, uid, actual_order_ids):
				start = datetime.strptime(order_data.start_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				start_minute = 0
				if start > date:
					start_minute = start.hour * 60 + start.minute
				finish = datetime.strptime(order_data.finish_date,'%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
				finish_minute = 24 * 60
				if finish < tomorrow_date:
					finish_minute = finish.hour * 60 + finish.minute
				actual_orders.append({
					'start': start_minute,
					'finish': finish_minute,
				})
			result.append({
				'driver_id': driver_data.id,
				'driver_name': driver_data.name,
				'planned_orders': planned_orders,
				'actual_orders': actual_orders,
			})
		hours = []
		for hour in range(0, 24):
			hours.append(str(hour).zfill(2) + ':00')
		return {
			'status': 'ok',
			'drivers': result,
			'hours': hours,
		}