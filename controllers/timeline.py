import json
from datetime import datetime
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
		tomorrow_date = datetime(year=year, month=month, day=day+1)
		
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
				planned_orders.append({
					'start_planned_date': order_data.start_planned_date,
					'finish_planned_date': order_data.finish_planned_date,
				})
		# GET ACTUAL ORDERS FOR DRIVER
			actual_order_ids = order_obj.search(cr, uid, [
				('actual_driver_id.user_id', '=', driver_data.id),
				('start_date', '<', tomorrow_date.strftime("%Y-%m-%d")),
				('finish_date', '>=', date.strftime("%Y-%m-%d")),
			])
			actual_orders = []
			for order_data in order_obj.browse(cr, uid, actual_order_ids):
				actual_orders.append({
					'start_date': order_data.start_date,
					'finish_date': order_data.finish_date,
				})
			result.append({
				'driver_id': driver_data.id,
				'driver_name': driver_data.name,
				'planned_orders': planned_orders,
				'actual_orders': actual_orders,
			})
		return result