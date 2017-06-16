from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.osv import osv, fields
from openerp.http import request
from datetime import datetime, date, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

from openerp.addons.website.models.website import slug

import json

import pytz
from datetime import datetime, date

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

_ORDER_TYPE = [
	('one_way_drop_off','One-way Drop Off'),
	('one_way_pickup','One-way Pick-up'),
	('two_way','Two Way')
]

_SERVICE_TYPE = [
	('full_day','Full-day Service'),
	('by_order','By Order'),
	('shuttle','Shuttle')
]

class website_mobile_app(http.Controller):

	@http.route('/mobile_app', type='http', auth="user", website=True)
	def mobile_app(self, **kwargs):
		response = self.mobile_app_get_user_group()
		data = json.loads(response.data)
		return request.render("universal.website_mobile_app_main_menu", {
			'user_group': data['user_group'],
		})
	
	@http.route('/mobile_app/get_user_group', type='http', auth="user", website=True)
	def mobile_app_get_user_group(self, **kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		user_obj = env['res.users']
		is_fullday_passenger = user_obj.has_group('universal.group_universal_passenger')
		is_booker = user_obj.has_group('universal.group_universal_booker')
		is_pic = user_obj.has_group('universal.group_universal_customer_pic')
		is_approver = user_obj.has_group('universal.group_universal_approver')
		# is_driver = user_obj.has_group('universal.group_universal_driver')
		user_group = ''
		if is_fullday_passenger:
			user_group = 'fullday_passenger'
		elif is_booker:
			user_group = 'booker'
		elif is_pic:
			user_group = 'pic'
		elif is_approver:
			user_group = 'approver'
		# elif is_driver:
		# 	user_group = 'driver'
		return json.dumps({
			'user_group': user_group
		})
	
	@http.route('/mobile_app/get_required_book_vehicle', type='http', auth="user", website=True)
	def mobile_app_get_required_book_vehicle(self, **kwargs):
		# User
		response_user_group = self.mobile_app_get_user_group()
		data_user_group = json.loads(response_user_group.data)
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		data_users = handler_obj.get_user_data({})
		user = {
			'name': '',
			'phone': '',
		}
		for data_user in data_users:
			user = {
				'name': data_user.name,
				'phone': data_user.phone,
			}
			break
		# Contract
		response_fetch_contract = self.mobile_app_fetch_contracts()
		data_fetch_contract = json.loads(response_fetch_contract.data)
		# Order Type
		order_type_arr = []
		for order_type in _ORDER_TYPE:
			order_type_arr.append({
				'id': order_type[0],
				'name': order_type[1],
			})
		# Route Area To
		route_city_arr = []
		regions = handler_obj.search_region({})
		for region in regions:
			areas = handler_obj.search_order_area({
				'homebase_id': region.id
			})
			route_area_arr = []
			for area in areas:
				route_area_arr.append({
					'id': area.id,
					'name': area.name,
				})
			route_city_arr.append({
				'id': region.id,
				'name': region.name,
				'areas': route_area_arr,
			})
		
		return json.dumps({
			'user_group': data_user_group['user_group'],
			'contract_datas': data_fetch_contract,
			'user': user,
			'order_type': order_type_arr,
			'route_to': route_city_arr,
		})
	
	@http.route('/mobile_app/fetch_contracts', type='http', auth="user", website=True)
	def mobile_app_fetch_contracts(self, **kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		contract_datas = handler_obj.search_contract({
			'by_user_id': True,
			'user_id': uid,
		})
		result = [];
		for contract_data in contract_datas:
			# Fleet
			fleet_vehicle_arr = []
			for fleet_data in contract_data.car_drivers:
				if fleet_data.fullday_user_id.id == uid:
					fleet_vehicle_arr.append({
						'id': fleet_data.fleet_vehicle_id.id,
						'name': fleet_data.fleet_vehicle_id.name,
					})
			# Unit
			unit_arr = []
			for allocation_unit in contract_data.allocation_units:
				if uid in allocation_unit.booker_ids.ids:
					unit_arr.append({
						'id': allocation_unit.id,
						'name': allocation_unit.name,
					})
			# Order Area From
			order_areas = handler_obj.search_order_area({
				'homebase_id': contract_data.homebase_id.id,
			})
			route_from_arr = []
			for area in order_areas:
				route_from_arr.append({
					'id': area.id,
					'name': area.name,
				})
			# Shuttle
			shuttle_arr = []
			for shuttle_schedule in contract_data.shuttle_schedules:
				driver_name = ''
				for fleet_data in contract_data.car_drivers:
					if fleet_data.fleet_vehicle_id.id == shuttle_schedule.fleet_vehicle_id.id:
						driver_name = fleet_data.driver_id.name
				shuttle_arr.append({
					'id': shuttle_schedule.id,
					'name': shuttle_schedule.route_id.name,
					'dayofweek': shuttle_schedule.dayofweek,
					'departure_time': shuttle_schedule.departure_time,
					# 'arrival_time': shuttle_schedule.arrival_time,
					'assigned_driver_name': driver_name,
					'assigned_vehicle_name': shuttle_schedule.fleet_vehicle_id.name,
				})
			# Appending data
			result.append({
				'id': contract_data.id,
				'name': contract_data.name,
				'fleet_vehicle': fleet_vehicle_arr,
				'units': unit_arr,
				'shuttle_schedules': shuttle_arr,
				'route_from': route_from_arr,
				'state': contract_data.state,
				'start_date': datetime.strptime(contract_data.start_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
				'end_date': datetime.strptime(contract_data.end_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
				'service_type': dict(_SERVICE_TYPE).get(contract_data.service_type, ''),
				'min_start_minutes': contract_data.min_start_minutes,
				'max_delay_minutes': contract_data.max_delay_minutes,
				'by_order_minimum_minutes' : contract_data.by_order_minimum_minutes,
			});
		result = sorted(result, key=lambda contract: contract['name'])
		return json.dumps(result)
	
	@http.route('/mobile_app/create_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_create_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		try:
			result = handler_obj.create_order(json.loads(data))
		except Exception, e:
			response = {
				'status': 'ok',
				'info': str(e.value),
				'success' : False,
			}
		else:
			if result:
				response = {
					'status': 'ok',
					'info': _('Create Order Success'),
					'success' : True,
				}
			else:
				response = {
					'status': 'ok',
					'info': _('Create Order Failed'),
					'success' : False,
				}
		return json.dumps(response)
	
	@http.route('/mobile_app/fetch_orders', type='http', auth="user", website=True)
	def mobile_app_fetch_orders(self, **kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		order_datas = handler_obj.search_order({
			'by_user_id': True,
			'user_id': uid,
		})
		result = {
			'pending': [],
			'ready'  : [],
			'running': [],
			'history': [],
		};
		for order_data in order_datas:
			if order_data.state in ['new', 'confirmed']:
				classification = 'pending'
			elif order_data.state in ['ready', 'started']:
				classification = 'ready'
			elif order_data.state in ['start_confirmed', 'paused', 'resumed', 'finished']:
				classification = 'running'
			else:
				classification = 'history'
			result[classification].append({
				'id': order_data.id,
				'name': order_data.name,
				'state': dict(_ORDER_STATE).get(order_data.state, ''),
				'request_date':  datetime.strptime(order_data.request_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'start_planned_date': datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'finish_planned_date':  datetime.strptime(order_data.finish_planned_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'assigned_vehicle_name': order_data.assigned_vehicle_id.name,
				'assigned_driver_name': order_data.assigned_driver_id.name,
				'origin_location': order_data.origin_location,
				'dest_location': order_data.dest_location,
			});
		result['pending'] = sorted(result['pending'], key=lambda order: order['request_date'], reverse=True)
		result['ready']   = sorted(result['ready'],   key=lambda order: order['request_date'], reverse=True)
		result['running'] = sorted(result['running'], key=lambda order: order['request_date'], reverse=True)
		result['history'] = sorted(result['history'], key=lambda order: order['request_date'], reverse=True)
		return json.dumps(result)
	
	@http.route('/mobile_app/fetch_contract_shuttles', type='http', auth="user", website=True)
	def mobile_app_fetch_contract_shuttles(self, **kwargs):
		response_fetch_contract = self.mobile_app_fetch_contracts()
		data_fetch_contract = json.loads(response_fetch_contract.data)
		contract_datas = data_fetch_contract
		for contract_data in contract_datas:
			contract_shuttle_days = {
				'0': [], '1': [], '2': [], '3': [], '4': [], '5': [], '6': [],
			};
			for shuttle_schedule in contract_data['shuttle_schedules']:
				if shuttle_schedule['dayofweek'] == 'A':
					for day_number in contract_shuttle_days:
						contract_shuttle_days[day_number].append(shuttle_schedule)
				else:
					contract_shuttle_days[shuttle_schedule['dayofweek']].append(shuttle_schedule)
			contract_data['shuttle_schedules_by_days'] = contract_shuttle_days
		return json.dumps(contract_datas)
	
	@http.route('/mobile_app/fetch_contract_quota_changes/<string:data>', type='http', auth="user", website=True)
	def mobile_app_fetch_contract_quota_changes(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		quota_changes = handler_obj.search_all_quota_changes(int(data))
		# Quota Changes by Pending/History
		quota_pending_history = {
			'pending': [], 'history': [],
		}
		for quota_change in quota_changes:
			classification = 'history'
			if quota_change.state == 'draft':
				classification = 'pending'
			quota_pending_history[classification].append({
				'id': quota_change.id,
				'name': quota_change.allocation_unit_id.name,
				'request_date': quota_change.request_date,
				'request_by': quota_change.request_by,
				'request_type': quota_change.request_longevity,
				'yellow_limit_old': quota_change.old_yellow_limit,
				'yellow_limit_new': quota_change.new_yellow_limit,
				'red_limit_old': quota_change.old_red_limit,
				'red_limit_new': quota_change.new_red_limit,
				'respond_date': quota_change.fleet_vehicle_id.name,
				'state': quota_change.fleet_vehicle_id.name,
				'reason': quota_change.reject_reason,
			})
		return json.dumps(quota_pending_history)
	
	@http.route('/mobile_app/get_usage_control_list/<string:data>', type='http', auth="user", website=True)
	def mobile_app_get_usage_control_list(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		quota_list = handler_obj.search_all_au_contract_quota_usage(int(data))
		return json.dumps({
			'status': 'ok',
			'quota_list': json.dumps(quota_list),
			'success' : True,
		})
	
	@http.route('/mobile_app/change_password/<string:data>', type='http', auth="user", website=True)
	def mobile_app_change_password(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.change_password(json.loads(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Change Password Success'),
				'success' : True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Old Password is not correct.'),
				'success' : False,
			})

class website_mobile_app_handler(osv.osv):
	_name = 'universal.website.mobile_app.handler'
	_description = 'Model for handling website-based requests'
	_auto = False
	
	def get_user_data(self, cr, uid, param_context):
		user_obj = self.pool.get('res.users')
		user = user_obj.browse(cr, uid, uid)
		return user.partner_id
	
	def search_order(self, cr, uid, param_context):
		order_obj = self.pool.get('foms.order');
		order_ids = order_obj.search(cr, uid, [], context=param_context)
		return order_obj.browse(cr, uid, order_ids)
	
	def search_order_area(self, cr, uid, param_context):
		order_area_obj = self.pool.get('foms.order.area');
		order_area_ids = order_area_obj.search(cr, uid, [('homebase_id', '=', param_context['homebase_id'])], context=param_context)
		return order_area_obj.browse(cr, uid, order_area_ids)
	
	def search_region(self, cr, uid, param_context):
		region_obj = self.pool.get('chjs.region');
		region_ids = region_obj.search(cr, uid, [])
		return region_obj.browse(cr, uid, region_ids)
	
	def search_contract(self, cr, uid, param_context):
		contract_obj = self.pool.get('foms.contract');
		contract_ids = contract_obj.search(cr, uid, [], context=param_context)
		return contract_obj.browse(cr, uid, contract_ids)
	
	def create_order(self, cr, uid, domain, context={}):
		order_obj = self.pool.get('foms.order')
		contract_id = domain.get('contract_id', '')
		contract_id = int(contract_id.encode('ascii', 'ignore'))
		fleet_vehicle_id = domain.get('fleet_vehicle_id', '')
		fleet_vehicle_id = int(fleet_vehicle_id.encode('ascii', 'ignore'))
		unit_id = domain.get('unit_id', '')
		unit_id = int(unit_id.encode('ascii', 'ignore'))
		type_id = domain.get('type_id', '')
		
		from_area_id = domain.get('from_area_id', '')
		from_area_id = int(from_area_id.encode('ascii', 'ignore'))
		from_location = domain.get('from_location', '')
		
		# to_city_id = domain.get('to_city_id', '')
		# to_city_id = int(to_city_id.encode('ascii', 'ignore'))
		to_area_id = domain.get('to_area_id', '')
		to_area_id = int(to_area_id.encode('ascii', 'ignore'))
		to_location = domain.get('to_location', '')
		
		is_orderer_passenger = domain.get('i_am_passenger', '')
		passengers = []
		for passenger in domain.get('passengers', []):
			passengers.append([0,False,passenger])
		
		start_planned = domain.get('start_planned', '')
		start_planned = datetime.strptime(start_planned, '%Y-%m-%dT%H:%M:%S')
		finish_planned = domain.get('finish_planned', '')
		finish_planned = datetime.strptime(finish_planned, '%Y-%m-%dT%H:%M:%S')
		
		return order_obj.create(cr, SUPERUSER_ID, {
			'customer_contract_id': contract_id,
			'order_by': uid,
			'assigned_vehicle_id': fleet_vehicle_id,
			'alloc_unit_id': unit_id,
			'order_type_by_order': type_id,
			
			'origin_area_id': from_area_id,
			'origin_location': from_location,
			# 'dest_city_id': to_city_id,
			'dest_area_id': to_area_id,
			'dest_location': to_location,
			
			'is_orderer_passenger': is_orderer_passenger,
			'passengers': passengers,
			
			'start_planned_date': start_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'finish_planned_date': finish_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'request_date': datetime.now(),
		})
	
	def change_password(self, cr, uid, domain, context={}):
		user_obj = self.pool.get('res.users')
		old_password = domain.get('old_password', '').encode('ascii', 'ignore')
		new_password = domain.get('new_password', '').encode('ascii', 'ignore')
		result = False
		try:
			result = user_obj.change_password(cr, uid, old_password, new_password)
		finally:
			return result
	
	def search_all_au_contract_quota_usage(self, cr, uid, id_contract, context={}):
		quota_obj = self.pool.get('foms.contract.quota')
		quota_ids = quota_obj.search(cr, uid, [('customer_contract_id', '=', id_contract)])
		quota_list = []
		if len(quota_ids) > 0:
			quota_list = quota_obj.browse(cr, uid, quota_ids)
		return quota_list

	def search_all_quota_changes(self, cr, uid, id_contract, context={}):
		quota_obj = self.pool.get('foms.contract.quota.change.log')
		quota_ids = quota_obj.search(cr, uid, [('customer_contract_id', '=', id_contract)])
		return quota_obj.browse(cr, uid, quota_ids)