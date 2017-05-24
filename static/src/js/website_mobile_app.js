$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

	var contract_datas = [];

// EVENT HANDLER ============================================================================================================

	$('#website_mobile_app_menu_book_vehicle').click(function() {
		$.get('/mobile_app/fetch_contracts', null, function(data){
			self.contract_datas = JSON.parse(data);
			var fleet_vehicle_datas = []
			if (self.contract_datas.length != 0) {
				fleet_vehicle_datas = self.contract_datas[0].fleet_vehicle
			}
			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'user_group': 'fullday_passenger',
				'contract_datas': self.contract_datas,
				'fleet_vehicle_datas': fleet_vehicle_datas,
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
			}));
		});
	});

	$('#create_order_contract').on('change', function() {
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == this.value) {
				$('#create_order_fleet_vehicle').empty();
				$.each(contract_data.fleet_vehicle, function(index, fleet_vehicle_data) {
					$('#create_order_fleet_vehicle').append('<option value=' + fleet_vehicle_data.id + '">' + fleet_vehicle_data.name + '</option>');
				});
			}
		});
	});

});
