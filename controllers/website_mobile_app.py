from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.osv import osv, fields
from openerp.http import request
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.addons.universal import datetime_to_server

from openerp.addons.website.models.website import slug

import json
import locale

import pytz
from datetime import datetime, date

_CONTRACT_STATE = [
	('proposed','Proposed'),
	('confirmed','Confirmed'),
	('planned','Planned'),
	('active','Active'),
	('prolonged','Prolonged'),
	('terminated','Terminated'),
	('finished','Finished')
]

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

_REQUEST_LONGEVITY = [
	('temporary','Temporary'),
	('permanent','Permanent'),
]

class website_mobile_app(http.Controller):

	@http.route('/mobile_app', type='http', auth="user", website=True)
	def mobile_app(self, **kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		uid = env.uid
		response = self.mobile_app_get_user_group()
		data_user = json.loads(response.data)
		return request.render("universal.website_mobile_app_main_menu", {
			'user_group': data_user['user_group'],
			'user_name': data_user['user_name'],
			'homebase': handler_obj.get_homebase()
		})

	@http.route('/mobile_app_new', type='http', auth="user", website=True)
	def mobile_app_new(self, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		return handler_obj.render_main(request, {
			'homebases': handler_obj.get_homebase(),
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
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		partner_data = handler_obj.get_user_data({})
		user_name = ""
		if len(partner_data) != 0:
			user_name = partner_data[0].name
		return json.dumps({
			'user_group': user_group,
			'user_name': user_name
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
			districts = handler_obj.search_order_district({
				'homebase_id': region.id
			})
			route_district_arr = []
			for district in districts:
				areas = handler_obj.search_order_area({
					'homebase_id': region.id,
					'district_id': district.id
				})
				route_area_arr = []
				for area in areas:
					route_area_arr.append({
						'id': area.id,
						'name': area.name,
					})
				route_district_arr.append({
					'id': district.id,
					'name': district.name,
					'areas': route_area_arr,
				})
			route_city_arr.append({
				'id': region.id,
				'name': region.name,
				'districts': route_district_arr,
			})
		
		return json.dumps({
			'user_group': data_user_group['user_group'],
			'contract_datas': data_fetch_contract['list_contract'],
			'user': user,
			'order_type': order_type_arr,
			'route_to': route_city_arr,
		})
	
	@http.route('/mobile_app/get_required_edit_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_get_required_edit_order(self, data, **kwargs):
		loaded_data = json.loads(data)
		# Required book vehicle
		response_book_vehicle = self.mobile_app_get_required_book_vehicle()
		data_book_vehicle = json.loads(response_book_vehicle.data)
		# Get order current info
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		order_data = handler_obj.get_order(loaded_data['order_id'])
		
		passenger_arr = []
		for passenger in order_data.passengers:
			passenger_arr.append({
				'id': passenger.id,
				'name': passenger.name,
				'phone_no': passenger.phone_no,
				'is_orderer': passenger.is_orderer,
			})
		
		return json.dumps({
			'user_group': data_book_vehicle['user_group'],
			'contract_datas': data_book_vehicle['contract_datas'],
			'user': data_book_vehicle['user'],
			'order_type': data_book_vehicle['order_type'],
			'route_to': data_book_vehicle['route_to'],
			'order_data': {
				'is_orderer_passenger': order_data.is_orderer_passenger,
				'customer_contract_id': order_data.customer_contract_id.id,
				'fleet_type_id': order_data.fleet_type_id.id,
				'alloc_unit_id': order_data.alloc_unit_id.id,
				'order_type_by_order': order_data.order_type_by_order,
				'origin_district_id': order_data.origin_area_id.district_id.id,
				'origin_area_id': order_data.origin_area_id.id,
				'origin_location': order_data.origin_location,
				'dest_city_id': order_data.dest_area_id.homebase_id.id,
				'dest_district_id': order_data.dest_area_id.district_id.id,
				'dest_area_id': order_data.dest_area_id.id,
				'dest_location': order_data.dest_location,
				'passengers': passenger_arr,
				'start_planned_date': order_data.start_planned_date,
				'finish_planned_date': order_data.finish_planned_date,
			},
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
			fleet_type_arr = []
			for fleet_data in contract_data.car_drivers:
				if contract_data.service_type != 'full_day' or fleet_data.fullday_user_id.id == uid:
					fleet_type_arr.append({
						'id': fleet_data.fleet_type_id.id,
						'name': fleet_data.fleet_type_id.name,
					})
			# Unit
			unit_arr = []
			for allocation_unit in contract_data.allocation_units:
				if uid in allocation_unit.booker_ids.ids or uid in allocation_unit.approver_ids.ids:
					unit_arr.append({
						'id': allocation_unit.id,
						'name': allocation_unit.name,
					})
			# Order District and Area From
			districts = handler_obj.search_order_district({
				'homebase_id': contract_data.homebase_id.id
			})
			district_from_arr = []
			for district in districts:
				areas = handler_obj.search_order_area({
					'homebase_id': contract_data.homebase_id.id,
					'district_id': district.id
				})
				route_from_arr = []
				for area in areas:
					route_from_arr.append({
						'id': area.id,
						'name': area.name,
					})
				district_from_arr.append({
					'id': district.id,
					'name': district.name,
					'areas': route_from_arr,
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
				'fleet_type': fleet_type_arr,
				'units': unit_arr,
				'shuttle_schedules': shuttle_arr,
				'districts': district_from_arr,
				# 'route_from': route_from_arr,
				'state': contract_data.state,
				'state_name': dict(_CONTRACT_STATE).get(contract_data.state, ''),
				'start_date': datetime.strptime(contract_data.start_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
				'end_date': datetime.strptime(contract_data.end_date,'%Y-%m-%d').strftime('%d-%m-%Y'),
				'service_type': dict(_SERVICE_TYPE).get(contract_data.service_type, ''),
				'min_start_minutes': contract_data.min_start_minutes,
				'max_delay_minutes': contract_data.max_delay_minutes,
				'by_order_minimum_minutes' : contract_data.by_order_minimum_minutes,
			});
		result = sorted(result, key=lambda contract: contract['name'])
		# User
		response_user_group = self.mobile_app_get_user_group()
		data_user_group = json.loads(response_user_group.data)
		return json.dumps({
			'user_group': data_user_group['user_group'],
			'list_contract': result,
		})
	
	@http.route('/mobile_app/create_edit_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_create_edit_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		loaded_data = json.loads(data)
		try:
			result = handler_obj.create_edit_order(loaded_data)
		except Exception as e:
			response = {
				'status': 'ok',
				'info': _("Error: %s") % e,
				'success' : False,
			}
		else:
			mode = loaded_data.get('mode_create_or_edit', '')
			if isinstance(result, basestring):
				response = {
					'status': 'ok',
					'info': result,
					'success' : False,
				}
			else :
				if result:
					info = _('Create Order Success') if mode == 'create' else _('Edit Order Success')
					response = {
						'status': 'ok',
						'info': info,
						'success' : True,
					}
				else:
					info = _('Create Order Failed') if mode == 'create' else _('Edit Order Failed')
					response = {
						'status': 'ok',
						'info': info,
						'success' : False,
					}
		return json.dumps(response)
	
	@http.route('/mobile_app/fetch_orders/<string:data>', type='http', auth="user", website=True)
	def mobile_app_fetch_orders(self, data,**kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		loaded_data = json.loads(data)
		order_datas = handler_obj.search_order(loaded_data, {
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
			yellow_limit = 0
			red_limit = 0
			if order_data.over_quota_status in ['warning','approval']:
				dictionary_quota = handler_obj.search_au_contract_quota_usage(order_data.customer_contract_id.id, [order_data.alloc_unit_id.id])
				if len(dictionary_quota) > 0:
					quota_data = dictionary_quota.get(str(order_data.alloc_unit_id.id), False)
					red_limit = quota_data.red_limit
					yellow_limit = quota_data.yellow_limit
			maintained_by = order_data.customer_contract_id.usage_allocation_maintained_by
			
			list_passenger = []
			for passenger in order_data.passengers:
				list_passenger.append({'name':passenger.name, 'phone' : passenger.phone_no})
			
			result[classification].append({
				'id': order_data.id,
				'name': order_data.name,
				'state': order_data.state,
				'pin': order_data.pin,
				'state_name': dict(_ORDER_STATE).get(order_data.state, ''),
				'request_date':  datetime.strptime(order_data.request_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'order_by_name': order_data.order_by.name,
				'start_planned_date': datetime.strptime(order_data.start_planned_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'finish_planned_date':  datetime.strptime(order_data.finish_planned_date,'%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M'),
				'assigned_vehicle_name': order_data.assigned_vehicle_id.name,
				'assigned_driver_name': order_data.assigned_driver_id.name,
				'origin_location': order_data.origin_location,
				'origin_area_name': order_data.origin_area_id.name,
				'dest_location': order_data.dest_location,
				'dest_area_name': order_data.dest_area_id.name,
				'service_type': order_data.service_type,
				'service_type_name': dict(_SERVICE_TYPE).get(order_data.service_type, ''),
				'order_by_name': order_data.order_by.name,
				'over_quota_status': order_data.over_quota_status,
				'order_usage': order_data.alloc_unit_usage,
				'red_limit': red_limit,
				'yellow_limit': yellow_limit,
				'maintained_by': maintained_by,
				'au_id': order_data.alloc_unit_id.id,
				'au_name': order_data.alloc_unit_id.name,
				'list_passenger' : list_passenger,
				'contract_id': order_data.customer_contract_id.id,
				'contract_name': order_data.customer_contract_id.name,
				'type': order_data.order_type_by_order,
				'type_name': dict(_ORDER_TYPE).get(order_data.order_type_by_order, ''),
			});
		result['pending'] = sorted(result['pending'], key=lambda order: order['request_date'], reverse=True)
		result['ready']   = sorted(result['ready'],   key=lambda order: order['request_date'], reverse=True)
		result['running'] = sorted(result['running'], key=lambda order: order['request_date'], reverse=True)
		result['history'] = sorted(result['history'], key=lambda order: order['request_date'], reverse=True)
		
		# User
		response_user_group = self.mobile_app_get_user_group()
		data_user_group = json.loads(response_user_group.data)
		return json.dumps({
			'user_group': data_user_group['user_group'],
			'list_order': result,
		})
	
	@http.route('/mobile_app/approve_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_approve_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.approve_order(int(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Order Approved'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Approving Order Failed'),
				'success': False,
			})
	
	@http.route('/mobile_app/reject_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_reject_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.reject_order(int(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Order Rejected'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Rejecting Order Failed'),
				'success': False,
			})
	
	@http.route('/mobile_app/change_planned_start_time/<string:data>', type='http', auth="user", website=True)
	def mobile_app_change_planned_start_time(self, data, **kwargs):
		order_data = json.loads(data)
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		datetime_format = '%Y-%m-%dT%H:%M:%S'
		if order_data['new_planned_start_time'].count(':') == 1:
			datetime_format = '%Y-%m-%dT%H:%M'
		new_start_date = datetime.strptime(order_data['new_planned_start_time'], datetime_format)
		result = handler_obj.change_planned_start_time(int(order_data['order_id']), new_start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Planned Start Time Changed'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Changing Planned Start Time Failed'),
				'success': False,
			})
	
	@http.route('/mobile_app/edit_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_edit_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.edit_order(int(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Order Edited'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Editing Order Failed'),
				'success': False,
			})
	
	@http.route('/mobile_app/cancel_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_cancel_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.cancel_order(int(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Order Canceled'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Canceling Order Failed'),
				'success': False,
			})
		
	@http.route('/mobile_app/fetch_contract_shuttles', type='http', auth="user", website=True)
	def mobile_app_fetch_contract_shuttles(self, **kwargs):
		"""
		dummy
		return json.dumps([{
			'id': 27,
			'name': '170346',
			'service_type': 'Shuttle',
			'shuttle_schedules_by_days': {
				'0': [{'name': 'IP-TSM', 'departure_time': '08:00', 'assigned_vehicle_name': 'B 1234 XX', 'assigned_driver_name': 'Baskoro'}],
				'1': [{'name': 'IP-TSM', 'departure_time': '08:00', 'assigned_vehicle_name': 'B 1234 XX', 'assigned_driver_name': 'Baskoro'}],
			}
		}])
		"""
		response_fetch_contract = self.mobile_app_fetch_contracts()
		data_fetch_contract = json.loads(response_fetch_contract.data)
		contract_datas = data_fetch_contract['list_contract']
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
	
	@http.route('/mobile_app/fetch_shuttle_schedules/<string:data>', type='http', auth="user", website=True)
	def mobile_app_fetch_shuttle_schedules(self, data, **kwargs):
		parameters = json.loads(data)
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		shuttle_schedules = handler_obj.get_shuttle_schedules(parameters['id'])
		contract_shuttle_days = {
			'0': [], '1': [], '2': [], '3': [], '4': [], '5': [], '6': [],
		};
		for shuttle_schedule in shuttle_schedules:
			driver_name = ''
			for fleet_data in shuttle_schedule.header_id.car_drivers:
				if fleet_data.fleet_vehicle_id.id == shuttle_schedule.fleet_vehicle_id.id:
					driver_name = fleet_data.driver_id.name
			shuttle_schedule_detail = {
				'id': shuttle_schedule.id,
				'name': shuttle_schedule.route_id.name,
				'dayofweek': shuttle_schedule.dayofweek,
				'departure_time': shuttle_schedule.departure_time,
				# 'arrival_time': shuttle_schedule.arrival_time,
				'assigned_driver_name': driver_name,
				'assigned_vehicle_name': shuttle_schedule.fleet_vehicle_id.name,
			}
			if shuttle_schedule['dayofweek'] == 'A':
				for day_number in contract_shuttle_days:
					contract_shuttle_days[day_number].append(shuttle_schedule_detail)
			else:
				contract_shuttle_days[shuttle_schedule['dayofweek']].append(shuttle_schedule_detail)
		return json.dumps(contract_shuttle_days)
	
	@http.route('/mobile_app/fetch_contract_quota_changes/<string:data>', type='http', auth="user", website=True)
	def mobile_app_fetch_contract_quota_changes(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		quota_changes = handler_obj.search_all_quota_changes(int(data))
		# Quota Changes by Pending/History
		quota_pending_history = {
			'pending': [], 'history': [],
		}
		#locale.setlocale( locale.LC_ALL, locale= "id_ID.utf8")
		for quota_change in quota_changes:
			classification = 'history'
			if quota_change.state == 'draft':
				classification = 'pending'
			quota_pending_history[classification].append({
				'id': quota_change.id,
				'name': quota_change.allocation_unit_id.name,
				'request_date': datetime_to_server(quota_change.request_date),
				'request_by': quota_change.request_by and quota_change.request_by.name or quota_change.create_uid.name,
				'request_type': dict(_REQUEST_LONGEVITY).get(quota_change.request_longevity, ''),
				'confirm_by': quota_change.confirm_by and quota_change.confirm_by.name or None,
				'confirm_date': quota_change.confirm_date and datetime_to_server(quota_change.confirm_date) or None,
				'reject_reason': quota_change.reject_reason,
				'yellow_limit_old': quota_change.old_yellow_limit,
				'yellow_limit_new': quota_change.new_yellow_limit,
				'red_limit_old': quota_change.old_red_limit,
				'red_limit_new': quota_change.new_red_limit,
				'respond_date': quota_change.confirm_date,
				'state': quota_change.state,
				'reason': quota_change.reject_reason,
			})
		return json.dumps(quota_pending_history)
	
	@http.route('/mobile_app/approve_quota_changes/<string:data>', type='http', auth="user", website=True)
	def mobile_app_approve_quota_changes(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.approve_quota_change(int(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Quota change approval is successfully saved.'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('System fails to save the quota change approval. Please try again later.'),
				'success': False,
			})
	
	@http.route('/mobile_app/reject_quota_changes/<string:data>', type='http', auth="user", website=True)
	def mobile_app_reject_quota_changes(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.reject_quota_change(json.loads(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Quota change rejection is successfully saved.'),
				'success': True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('System fails to save the quota change rejection. Please try again later.'),
				'success': False,
			})
	
	@http.route('/mobile_app/get_usage_control_list/<string:data>', type='http', auth="user", website=True)
	def mobile_app_get_usage_control_list(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		allocation_unit_list, au_ids = handler_obj.search_all_au_contract(int(data))
		quota_from_arr = []
		dictionary_quota = handler_obj.search_au_contract_quota_usage(int(data), au_ids)
		for au in allocation_unit_list:
			total_nominal, total_count = handler_obj.search_total_request_nominal_count_quota_changes(au.header_id.id, au.id)
			quota = dictionary_quota.get(str(au.id), False)
			plural = 'time'
			status = 'OK'
			response_user_group = self.mobile_app_get_user_group()
			data_user_group = json.loads(response_user_group.data)
			if quota and quota.red_limit and quota.current_usage:
				if quota.current_usage > quota.red_limit:
					status = 'Overlimit'
				elif quota.current_usage > quota.yellow_limit:
					status = 'Warning'
			#locale.setlocale(locale.LC_ALL, locale= "id_ID.utf8")
			if total_count > 1:
				plural = 'times'
			button_change_exist = 'hide'
			if data_user_group['user_group'] == 'approver' and au and \
					au.header_id.service_type == 'by_order' and \
					au.header_id.usage_allocation_maintained_by == 'customer' and \
					au.header_id.usage_control_level != 'no_control':
				button_change_exist = 'show'
			quota_from_arr.append({
				'user_group': data_user_group['user_group'],
				'id': quota.id if quota else 0,
				'au_id': au.id,
				'contract_id': au.header_id.id,
				'yellow_limit': quota.yellow_limit if quota else 0,
				'red_limit': quota.red_limit if quota else 0,
				'allocation_unit_name': au.name,
				'control_level': au.header_id.usage_control_level,
				#'total_request_nominal': locale.currency(total_nominal, grouping= True),
				'total_request_nominal': total_nominal,
				'total_request_count': total_count,
				'current_usage': quota.current_usage if quota and quota.current_usage else 0,
				'red_limit': quota.red_limit if quota and quota.red_limit else 0,
				'plural': plural,
				'status': status,
				'progress_exist': 'show' if quota and quota.red_limit and quota.current_usage else 'hide',
				'button_change_exist': button_change_exist,
			})
		return json.dumps({
			'status': 'ok',
			'quota_list': json.dumps(quota_from_arr),
			'data': json.dumps(quota_from_arr), # ditambahkan untuk framework baru. quota_list tetap dipertahankan sampai framework baru jalan semua
			'success' : True,
		})
	
	@http.route('/mobile_app/fetch_contract_detail_usage_control_quota/<string:data>', type='http', auth="user", website=True)
	def mobile_app_fetch_contract_detail_usage_control_quota(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		quota_id = int(data)
		quota = handler_obj.get_quota_data(quota_id)
		# Quota Changes by Pending/History
		limit_request_pending_history = {
			'pending': [], 'history': [],
		}
		for limit_request in quota['limit_requests']:
			classification = 'history'
			if limit_request.state == 'draft':
				classification = 'pending'
			limit_request_pending_history[classification].append({
				'id': limit_request.id,
				'name': limit_request.allocation_unit_id.name,
				'request_date': limit_request.request_date,
				'request_by': limit_request.create_uid.name,
				'request_type': dict(_REQUEST_LONGEVITY).get(limit_request.request_longevity, ''),
				'yellow_limit_old': limit_request.old_yellow_limit,
				'yellow_limit_new': limit_request.new_yellow_limit,
				'red_limit_old': limit_request.old_red_limit,
				'red_limit_new': limit_request.new_red_limit,
				'respond_date': limit_request.confirm_date,
				'state': limit_request.state,
				'reason': limit_request.reject_reason,
			})
		quota_detail = {
			'total_usage': quota['total_usage'],
			'yellow_limit': quota['yellow_limit'],
			'red_limit': quota['red_limit'],
			'total_request_nominal': quota['total_request_nominal'],
			'total_request_time': quota['total_request_time'],
			'limit_requests': limit_request_pending_history,
		}
		return json.dumps(quota_detail)
	
	@http.route('/mobile_app/change_password/<string:data>', type='http', auth="user", website=True)
	def mobile_app_change_password(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.change_password(json.loads(data))
		if result:
			return json.dumps({
				'status': 'ok',
				'info': _('Change password is successful.'),
				'success' : True,
			})
		else:
			return json.dumps({
				'status': 'ok',
				'info': _('Old Password is not correct.'),
				'success' : False,
			})
	
	@http.route('/mobile_app/request_quota_changes/<string:data>', type='http', auth="user", website=True)
	def mobile_app_request_quota_changes(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		try:
			result = handler_obj.request_quota_change(json.loads(data))
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
					'info': _('Your quota change request has been succesfully submitted.'),
					'success' : True,
				}
			else:
				response = {
					'status': 'ok',
					'info': _('System fails to save your quota change request. Please try again later.'),
					'success' : False,
				}
		return json.dumps(response)

class website_mobile_app_handler(osv.osv):
	_name = 'universal.website.mobile_app.handler'
	_description = 'Model for handling website-based requests'
	_auto = False

	def render_main(self, cr, uid, request, additional_data={}):
		mobile_web_obj = self.pool.get('chjs.mobile.web.app')
		return mobile_web_obj.render_main(cr, uid, request, 'univmobile', additional_data=additional_data)

	def get_user_data(self, cr, uid, param_context):
		user_obj = self.pool.get('res.users')
		user = user_obj.browse(cr, SUPERUSER_ID, uid)
		return user.partner_id
	
	def search_order(self, cr, uid, domain, param_context):
		order_obj = self.pool.get('foms.order');
		name_order = domain.get('order_name', '')
		booker_name = domain.get('booker_name', '')
		driver_name = domain.get('driver_name', '')
		vehicle_name = domain.get('vehicle_name', '')
		
		filter_domain = [('start_planned_date', '>=', (datetime.now() - relativedelta(months=+2)).strftime(DEFAULT_SERVER_DATETIME_FORMAT))]
		
		if name_order:
			filter_domain.append(('name', 'ilike', name_order))
		if booker_name:
			filter_domain.append(('order_by.name', 'ilike', booker_name))
		if driver_name:
			filter_domain.append(('assigned_driver_id.name', 'ilike', driver_name))
		if vehicle_name:
			filter_domain.append(('assigned_vehicle_id.name', 'ilike', vehicle_name))
		
		order_ids = order_obj.search(cr, SUPERUSER_ID, filter_domain, context=param_context)
		return order_obj.browse(cr, SUPERUSER_ID, order_ids)
	
	def search_quota(self, cr, uid, param_context):
		order_obj = self.pool.get('foms.order');
		order_ids = order_obj.search(cr, SUPERUSER_ID, [
		
		], context=param_context)
		return order_obj.browse(cr, SUPERUSER_ID, order_ids)
	
	def search_order_district(self, cr, uid, param_context):
		region_obj = self.pool.get('chjs.region');
		district_ids = region_obj.search(cr, SUPERUSER_ID, [
			('parent_id', '=', param_context['homebase_id'])
		], context=param_context)
		return region_obj.browse(cr, SUPERUSER_ID, district_ids)
	
	def search_order_area(self, cr, uid, param_context):
		order_area_obj = self.pool.get('foms.order.area');
		order_area_ids = order_area_obj.search(cr, SUPERUSER_ID, [
			('homebase_id', '=', param_context['homebase_id']),
			('district_id', '=', param_context['district_id'])
		], context=param_context)
		return order_area_obj.browse(cr, SUPERUSER_ID, order_area_ids)
	
	def search_region(self, cr, uid, param_context):
		region_obj = self.pool.get('chjs.region');
		region_ids = region_obj.search(cr, SUPERUSER_ID, [('type','=','city')])
		return region_obj.browse(cr, SUPERUSER_ID, region_ids)
	
	def search_contract(self, cr, uid, param_context):
		contract_obj = self.pool.get('foms.contract');
		contract_ids = contract_obj.search(cr, SUPERUSER_ID, [], context=param_context)
		return contract_obj.browse(cr, SUPERUSER_ID, contract_ids)
	
	def  create_edit_order(self, cr, uid, domain, context={}):
		order_obj = self.pool.get('foms.order')
		order_passenger_obj = self.pool.get('foms.order.passenger')
		user_obj = self.pool.get('res.users')
		is_fullday_passenger = user_obj.has_group(cr, uid, 'universal.group_universal_passenger')
		
		mode = domain.get('mode_create_or_edit', '')
		contract_id = domain.get('contract_id', '')
		contract_id = int(contract_id.encode('ascii', 'ignore'))
		fleet_type_id = domain.get('fleet_type_id', '')
		fleet_type_id = int(fleet_type_id.encode('ascii', 'ignore'))
		
		start_planned = domain.get('start_planned', '')
		start_planned = datetime.strptime(start_planned, '%Y-%m-%dT%H:%M' if start_planned.count(':') == 1 else '%Y-%m-%dT%H:%M:%S')
		finish_planned = domain.get('finish_planned', '')
		finish_planned = datetime.strptime(finish_planned, '%Y-%m-%dT%H:%M' if finish_planned.count(':') == 1 else '%Y-%m-%dT%H:%M:%S')
		order_data = {
			'customer_contract_id': contract_id,
			'order_by': uid,
			'fleet_type_id': fleet_type_id,
			'start_planned_date': start_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'finish_planned_date': finish_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'request_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
		}
		
		if not is_fullday_passenger:
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
				passenger_data = {
					'name': passenger['name'],
					'phone_no': passenger['phone_no'],
					'is_orderer': passenger['is_orderer'],
				}
				passengers.append([0, False, passenger_data])
				
			if len(passengers) == 0:
				return "there is no passenger, please add 1 passenger at least"
			
			order_data['alloc_unit_id'] = unit_id
			order_data['order_type_by_order'] = type_id
			
			order_data['origin_area_id'] = from_area_id
			order_data['origin_location'] = from_location
			# order_data['dest_city_id'] = to_city_id
			order_data['dest_area_id'] = to_area_id
			order_data['dest_location'] = to_location
			
			order_data['is_orderer_passenger'] = is_orderer_passenger
			order_data['passengers'] = passengers
		if mode == 'create':
			return order_obj.create(cr, SUPERUSER_ID, order_data)
		else:
			order_id = domain.get('order_id', '')
			order_id = int(order_id.encode('ascii', 'ignore'))
			order_passenger_obj.unlink(cr, uid, order_passenger_obj.search(cr, SUPERUSER_ID, [('header_id', '=', order_id)]))
			return order_obj.write(cr, SUPERUSER_ID, [order_id], order_data)
			
	
	def request_quota_change(self, cr, uid, domain, context={}):
		change_log = self.pool.get('foms.contract.quota.change.log')
		contract_id = domain.get('customer_contract_id', '')
		contract_id = int(contract_id.encode('ascii', 'ignore'))
		au_id = domain.get('allocation_unit_id', '')
		au_id = int(au_id.encode('ascii', 'ignore'))
		new_yellow_limit = domain.get('new_yellow_limit', '')
		new_red_limit = domain.get('new_red_limit', '')
		request_longevity = domain.get('request_longevity', '')
		request_by = domain.get('request_by', SUPERUSER_ID)
		
		now = datetime.now()
		period = "%02d/%04d" % (now.month ,now.year)
		
		return change_log.create(cr, SUPERUSER_ID, {
			'customer_contract_id': contract_id,
			'allocation_unit_id': au_id,
			'new_yellow_limit': new_yellow_limit,
			'new_red_limit': new_red_limit,
			'request_longevity': request_longevity,
			'period': period,
			'state': 'draft',
			'request_date': now,
			'request_by': request_by,
		}, context = {'from_webservice' : 1})
	
	def change_password(self, cr, uid, domain, context={}):
		user_obj = self.pool.get('res.users')
		old_password = domain.get('old_password', '').encode('ascii', 'ignore')
		new_password = domain.get('new_password', '').encode('ascii', 'ignore')
		result = False
		try:
			result = user_obj.change_password(cr, uid, old_password, new_password)
		finally:
			return result
	
	def search_au_contract_quota_usage(self, cr, uid, contract_id, allocation_unit_ids,context={}):
		quota_obj = self.pool.get('foms.contract.quota')
		now = datetime.now()
		period = "%02d/%04d" % (now.month ,now.year)
		quota_ids = quota_obj.search(cr, SUPERUSER_ID, [('customer_contract_id', '=', contract_id),
											('allocation_unit_id', 'in', allocation_unit_ids),
											('period', '=', period)])
	# Bikin dictionary dengan key berupa allocation_id, dengan demikian untuk mencari quota dengan au id x tinggal lookup ke dictionary
		res = {}
		for quota in quota_obj.browse(cr, SUPERUSER_ID, quota_ids):
			res[str(quota.allocation_unit_id.id)] = quota
		return res
	
	def search_all_au_contract(self, cr, uid, contract_id, context={}):
		au_obj = self.pool.get('foms.contract.alloc.unit')
		au_ids = au_obj.search(cr, SUPERUSER_ID, [('header_id', '=', contract_id)])
		return au_obj.browse(cr, SUPERUSER_ID, au_ids), au_ids

	def get_quota_data(self, cr, uid, quota_id, context={}):
		quota_obj = self.pool.get('foms.contract.quota')
		quota_change_obj = self.pool.get('foms.contract.quota.change.log')
		quota = quota_obj.browse(cr, SUPERUSER_ID, [quota_id])
		au = quota.allocation_unit_id
		quota_change_ids = quota_change_obj.search(cr, SUPERUSER_ID, [('allocation_unit_id', '=', au.id)])
		quota_changes = quota_change_obj.browse(cr, SUPERUSER_ID, quota_change_ids)
		if quota.customer_contract_id.id and au.id:
			total_nominal, total_count = self.search_total_request_nominal_count_quota_changes(cr, uid, quota.customer_contract_id.id, au.id)
		else:
			total_nominal = 0
			total_count = 0
		return {
			'total_usage': quota.current_usage if quota.current_usage else 0,
			'yellow_limit': quota.yellow_limit if quota.yellow_limit else 0,
			'red_limit': quota.red_limit if quota.red_limit else 0,
			'total_request_nominal': total_nominal if total_nominal else 0,
			'total_request_time': total_count if total_count else 0,
			'plural': 'time' if total_count > 1 else 'times',
			'limit_requests': quota_changes if quota_changes else [],
		}

	def search_all_quota_changes(self, cr, uid, id_contract, context={}):
		quota_obj = self.pool.get('foms.contract.quota.change.log')
		quota_ids = quota_obj.search(cr, SUPERUSER_ID, [('customer_contract_id', '=', id_contract)])
		return quota_obj.browse(cr, SUPERUSER_ID, quota_ids)
	
	def search_total_request_nominal_count_quota_changes(self, cr, uid, contract_id, allocation_unit_id, context={}):
		quota_change_obj = self.pool.get('foms.contract.quota.change.log')
		now = datetime.now()
		period = "%02d/%04d" % (now.month ,now.year)
		quota_change_log_ids = quota_change_obj.search(cr, SUPERUSER_ID, [('customer_contract_id', '=', contract_id),
												('allocation_unit_id', '=', allocation_unit_id),
												('state', '=', 'approved'),
												('period', '=', period)])
		result_nominal = 0
		for quota_change in quota_change_obj.browse(cr, SUPERUSER_ID, quota_change_log_ids):
			if quota_change.new_red_limit != 0 and quota_change.new_red_limit != quota_change.old_red_limit:
				result_nominal += quota_change.new_red_limit
			elif quota_change.new_yellow_limit != 0 and quota_change.new_yellow_limit != quota_change.old_yellow_limit:
				result_nominal += quota_change.new_yellow_limit
		return result_nominal, len(quota_change_log_ids)
	
	def approve_quota_change(self, cr, uid, change_log_id, context={}):
		quota_obj = self.pool.get('foms.contract.quota.change.log')
		return quota_obj.write(cr, SUPERUSER_ID, [change_log_id], {
			'state': 'approved',
			'confirm_by': uid,
			'confirm_date': datetime.now(),
		}, context=context)
	
	def reject_quota_change(self, cr, uid, domain, context={}):
		quota_obj = self.pool.get('foms.contract.quota.change.log')
		change_log_id = int(domain.get('change_log_id', '').encode('ascii', 'ignore'))
		reject_reason = domain.get('reject_reason', '').encode('ascii', 'ignore')
		return quota_obj.write(cr, SUPERUSER_ID, [change_log_id], {
			'state': 'rejected',
			'reject_reason': reject_reason,
			'confirm_by': uid,
			'confirm_date': datetime.now(),
		}, context=context)
	
	def approve_order(self, cr, uid, order_id, context={}):
		order_obj = self.pool.get('foms.order')
		return order_obj.action_confirm(cr, SUPERUSER_ID, [order_id], context=context)
	
	def reject_order(self, cr, uid, order_id, context={}):
		order_obj = self.pool.get('foms.order')
		return order_obj.write(cr, SUPERUSER_ID, [order_id], {
			'state': 'rejected',
		}, context=context)
	
	def change_planned_start_time(self, cr, uid, order_id, new_start_planned_date, context={}):
		order_obj = self.pool.get('foms.order')
		return order_obj.write(cr, SUPERUSER_ID, [order_id], {
			'start_planned_date': new_start_planned_date,
		}, context=context)
	
	def get_order(self, cr, uid, order_id, context={}):
		order_obj = self.pool.get('foms.order')
		return order_obj.browse(cr, SUPERUSER_ID, order_id);
	
	def cancel_order(self, cr, uid, order_id, context={}):
		order_obj = self.pool.get('foms.order')
		return order_obj.write(cr, SUPERUSER_ID, [order_id], {
			'state': 'canceled',
		}, context=context)
	
	def get_shuttle_schedules(self, cr, uid, contract_id):
		shuttle_schedule_obj = self.pool.get('foms.contract.shuttle.schedule')
		shuttle_schedule_ids = shuttle_schedule_obj.search(cr, SUPERUSER_ID, [('header_id','=',contract_id)])
		return shuttle_schedule_obj.browse(cr, SUPERUSER_ID, shuttle_schedule_ids)
	
	def get_homebase(self, cr, uid):
		homebase_obj = self.pool.get('chjs.region')
		homebase_ids = []
		contract_datas = self.search_contract(cr, SUPERUSER_ID, {
			'by_user_id': True,
			'user_id': uid,
		})
		for contract_data in contract_datas:
			if contract_data.homebase_id.id not in homebase_ids:
				homebase_ids.append(contract_data.homebase_id.id)
		result = []
		for homebase in homebase_obj.browse(cr, SUPERUSER_ID, homebase_ids):
			result.append({
				'id': homebase.id,
				'name': homebase.name,
				'emergency_number': homebase.emergency_number,
			})
		return result
