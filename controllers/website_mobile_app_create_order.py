from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.osv import osv, fields
from openerp.http import request
from datetime import datetime, date, timedelta

from openerp.addons.website.models.website import slug

import json

import pytz
from datetime import datetime, date

class website_mobile_app_create_order(http.Controller):
	
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
		handler_obj = http.request.env['universal.website.mobile_app.create_order.handler']
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
		handler_obj = http.request.env['universal.website.mobile_app.create_order.handler']
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


class website_mobile_app_create_order_handler(osv.osv):
	_name = 'universal.website.mobile_app.create_order.handler'
	_description = 'Model for handling website-based requests'
	_auto = False
	
	def search_contract(self, cr, uid, param_context):
		contract_obj = self.pool.get('foms.contract');
		contract_ids = contract_obj.search(cr, uid, [], context=param_context)
		return contract_obj.browse(cr, uid, contract_ids)
	
	def create_order(self, domain, context={}):
		# stock_opname_inject = self.env['stock.opname.inject']
		# product_obj = self.env['product.product']
		# product_ids = product_obj.search([
		# 	('name', '=ilike', domain.get('product_name', '')),
		# 	('type', '=', 'product')
		# ])
		# if len(product_ids) > 0:
		# 	priority = domain.get('priority', '').strip()
		# 	priority = priority.encode('ascii', 'ignore')
		# 	return stock_opname_inject.create({
		# 		'product_id': product_ids[0],
		# 		'priority': int(priority),
		# 	})
		# else:
			return False
