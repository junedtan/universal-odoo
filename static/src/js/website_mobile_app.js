$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

	var contract_datas = [];

// CREATE ORDER =============================================================================================================

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

			$('#create_order_contract').change(function(){
				onchange_create_order_contract($(this).val());
			});

			$('#btn_create_order').click(function(){
				onclick_create_order_button();
			});
		});
	});

	function onclick_create_order_button() {
		create_order_json = {
			'contract_id': $('#create_order_contract').val(),
			'fleet_vehicle_id': $('#create_order_fleet_vehicle').val(),
			'start_planned': $('#create_order_start_planned').val(),
			'finish_planned': $('#create_order_finish_planned').val(),
		};
		$.ajax({
			dataType: "json",
			url: '/mobile_app/create_order/' + JSON.stringify(create_order_json),
			method: 'POST',
			success: function(response) {
				alert(response);
				alert(response.info);
				if(response.success){
					alert('success')
				}
			},
			error: function(XMLHttpRequest, textStatus, errorThrown) {
				alert_error(XMLHttpRequest);
			} ,
		});
	}

	function onchange_create_order_contract(contract_id) {
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == contract_id) {
				$('#create_order_fleet_vehicle').empty();
				$.each(contract_data.fleet_vehicle, function(index, fleet_vehicle_data) {
					$('#create_order_fleet_vehicle').append('<option value=' + fleet_vehicle_data.id + '>' + fleet_vehicle_data.name + '</option>');
				});
			}
		});
	};

// LIST ORDER ===============================================================================================================

	$('#website_mobile_app_menu_list_orders').click(function() {
		$.get('/mobile_app/fetch_orders', null, function(data){
			classifications = {
				'Pending': 'pending',
				'Ready': 'ready',
				'Running': 'running',
				'History': 'history',
			}
			console.log(JSON.parse(data));
			$("#main_container", self).html(qweb.render('website_mobile_app_list_order',{
				'classifications': classifications,
				'order_datas': JSON.parse(data),
			}));

			$(".accordion").click(function(event) {
				$(this).toggleClass("active");
				var detail = $(this).next();
				if (detail.css("maxHeight") != "0px"){
					detail.css("maxHeight", "0px");
				} else {
					detail.css("maxHeight", detail.prop("scrollHeight")+ "px");
				}
			});
		});
	});

});
