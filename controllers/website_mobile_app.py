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

class website_mobile_app(http.Controller):
	
	@http.route('/mobile_app', type='http', auth="user", website=True)
	def mobile_app(self, **kwargs):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
	# tentukan apakah yang login ini fullday-passennger. di luar itu ngga bisa diakses
		partner_obj = env['res.partner']
		user_obj = env['res.users']
		return request.render("universal.website_mobile_app_main_menu", {
			'user_group': 'fullday_passenger'
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
			fleet_vehicle_arr = []
			for fleet_data in contract_data.car_drivers:
				if fleet_data.fullday_user_id.id == uid:
					fleet_vehicle_arr.append({
						'id': fleet_data.fleet_vehicle_id.id,
						'name': fleet_data.fleet_vehicle_id.name,
					})
			result.append({
				'id': contract_data.id,
				'name': contract_data.name,
				'fleet_vehicle': fleet_vehicle_arr,
			});
		result = sorted(result, key=lambda contract: contract['name'])
		return json.dumps(result)
	
	@http.route('/mobile_app/create_order/<string:data>', type='http', auth="user", website=True)
	def mobile_app_create_order(self, data, **kwargs):
		handler_obj = http.request.env['universal.website.mobile_app.handler']
		result = handler_obj.create_order(json.loads(data))
		if result:
			response = {
				'status': 'ok',
				'info': _('Save Success'),
				'success' : True,
			}
		else:
			response = {
				'status': 'ok',
				'info': _('Save Failed'),
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
				'request_date': order_data.request_date,
			});
		result['pending'] = sorted(result['pending'], key=lambda order: order['request_date'])
		result['ready'] = sorted(result['ready'], key=lambda order: order['request_date'])
		result['running'] = sorted(result['running'], key=lambda order: order['request_date'])
		result['history'] = sorted(result['history'], key=lambda order: order['request_date'])
		return json.dumps(result)

class website_mobile_app_handler(osv.osv):
	_name = 'universal.website.mobile_app.handler'
	_description = 'Model for handling website-based requests'
	_auto = False
	
	def search_order(self, cr, uid, param_context):
		order_obj = self.pool.get('foms.order');
		order_ids = order_obj.search(cr, uid, [], context=param_context)
		return order_obj.browse(cr, uid, order_ids)
	
	def search_contract(self, cr, uid, param_context):
		contract_obj = self.pool.get('foms.contract');
		contract_ids = contract_obj.search(cr, uid, [], context=param_context)
		return contract_obj.browse(cr, uid, contract_ids)
	
	def create_order(self, domain, context={}):
		env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
		uid = env.uid
		order_obj = self.env['foms.order']
		contract_id = domain.get('contract_id', '')
		contract_id = int(contract_id.encode('ascii', 'ignore'))
		fleet_vehicle_id = domain.get('fleet_vehicle_id', '')
		fleet_vehicle_id = int(fleet_vehicle_id.encode('ascii', 'ignore'))
		start_planned = domain.get('start_planned', '')
		start_planned = datetime.strptime(start_planned, '%Y-%m-%dT%H:%M:%S')
		finish_planned = domain.get('finish_planned', '')
		finish_planned = datetime.strptime(finish_planned, '%Y-%m-%dT%H:%M:%S')
		return order_obj.create({
			'customer_contract_id': contract_id,
			'order_by': uid,
			'assigned_vehicle_id': fleet_vehicle_id,
			'start_planned_date': start_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'finish_planned_date': finish_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
			'request_date': datetime.now(),
		})
