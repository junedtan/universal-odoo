from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from datetime import datetime, date, timedelta

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
		contract_obj = http.request.env['foms.contract']
		contract_datas = contract_obj.website_mobile_app_search({
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