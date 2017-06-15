$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

	var contract_datas = [];
	var user = {};

	function onclick_menu(id) {
		$('#website_mobile_app_menu_book_vehicle').removeClass('active');
		$('#website_mobile_app_menu_list_orders').removeClass('active');
		$('#website_mobile_app_menu_change_password').removeClass('active');
		$('#website_mobile_app_menu_list_contract').removeClass('active');
		$('#website_mobile_app_menu_list_shuttle').removeClass('active');
		$(id).addClass('active');
	}

// BOOK VEHICLE =============================================================================================================

	$('#website_mobile_app_menu_book_vehicle').click(function() {
		onclick_menu('#website_mobile_app_menu_book_vehicle');
		$.get('/mobile_app/get_required_book_vehicle', null, function(data){
			var response = JSON.parse(data);
			console.log(response);
			var user_group = response['user_group'];
			var order_type = response['order_type'];
			self.user = response['user'];
			self.contract_datas = response['contract_datas'];

			var fleet_vehicle_datas = [];
			var units = [];
			if (self.contract_datas.length != 0) {
				fleet_vehicle_datas = self.contract_datas[0].fleet_vehicle;
				units = self.contract_datas[0].units;
			}

			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'user_group': user_group,
				// Information
				'contract_datas': self.contract_datas,
				'fleet_vehicle_datas': fleet_vehicle_datas,
				'units': units,
				'order_types': order_type,
				// Route
//				'from_area': ,
//				'to_city': ,
//				'to_area': ,
				// Passenger
				// Time
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
			}));

			$('#create_order_contract').change(function(){
				onchange_create_order_contract($(this).val());
			});

			$('#btn_create_order').click(function(){
				onclick_create_order_button();
			});

			var ckb_i_am_passenger = $('#ckb_i_am_passenger');
			ckb_i_am_passenger.click(function(){
				onclick_create_order_i_am_passenger();
			});
			ckb_i_am_passenger.click();
			onclick_create_order_i_am_passenger();

			$('#btn_add_passenger').click(function(){
				onclick_create_order_add_passenger();
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
		if (create_order_json['contract_id'] == null) {
			alert('You have no Contract!');
			return;
		} else if (create_order_json['fleet_vehicle_id'] == null) {
			alert('You have no Fleet!');
			return;
		} else if (!create_order_json['start_planned']) {
			alert('Please input the start planned date correctly!');
			return;
		} else if (!create_order_json['finish_planned']) {
			alert('Please input the finish planned date correctly!');
			return;
		}
		$.ajax({
			dataType: "json",
			url: '/mobile_app/create_order/' + JSON.stringify(create_order_json),
			method: 'POST',
			success: function(response) {
				if (response.status) {
					alert(response.info);
					if(response.success){
						$('#website_mobile_app_menu_list_orders').click();
					}
				} else {
					alert('Server Unreachable.');
				}
			},
			error: function(XMLHttpRequest, textStatus, errorThrown) {
				alert_error(XMLHttpRequest, errorThrown);
			} ,
		});
	}

	function onchange_create_order_contract(contract_id) {
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == contract_id) {
				$('#create_order_fleet_vehicle').empty();
				$.each(contract_data.fleet_vehicle, function(index, fleet_vehicle_data) {
					$('#create_order_fleet_vehicle').append(
						'<option value=' + fleet_vehicle_data.id + '>' + fleet_vehicle_data.name + '</option>');
				});
			}
		});
	};

	function onclick_create_order_i_am_passenger() {
		var checkbox = $("#ckb_i_am_passenger");
		my_id = "passenger_me";
		if(checkbox.prop('checked')) {
			var table_passengers = $("#passengers");
			table_passengers.prepend(get_row_string_passenger(self.user.name,
				self.user.phone === false ? '-' : self.user.phone, my_id, false));
		} else {
			$("#"+my_id).remove();
		}
	};

	function onclick_create_order_add_passenger() {
		var table_passengers = $("#passengers");
		table_passengers.append(get_row_string_passenger("", "", "", true));
		$(".btn_remove_passenger").click(function(){
			onclick_create_order_remove_passenger(this);
		});
	};

	function onclick_create_order_remove_passenger(button_remove) {
		button_remove.closest('tr').remove();
	};

	function get_row_string_passenger(name, phone, id, removable) {
		if(id === "") {
			var row = '<tr>';
		} else {
			var row = '<tr id="' + id + '">';
		}
		if(removable === true) {
			row += '<td><input type="text" class="form-control" value="' + name + '"/></td>' +
                   	'<td><input type="text" class="form-control" value="' + phone + '"/></td>' +
                   	'<td><button type="button" class="btn_remove_passenger close" aria-label="Close">' +
							'<span aria-hidden="true">x</span>' +
						'</button></td>';
		} else {
			row += '<td><input type="text" class="form-control" value="' + name + '" readonly/></td>' +
                   	'<td><input type="text" class="form-control" value="' + phone + '" readonly/></td>' +
                   	'<td></td>';
		}
		row += '</tr>';
		return row;
	};

// LIST ORDER ===============================================================================================================

	$('#website_mobile_app_menu_list_orders').click(function() {
		onclick_menu('#website_mobile_app_menu_list_orders');
		$.get('/mobile_app/fetch_orders', null, function(data){
			classifications = {
				'Pending': 'pending',
				'Ready': 'ready',
				'Running': 'running',
				'History': 'history',
			}
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

// CHANGE PASSWORD ==========================================================================================================

	$('#website_mobile_app_menu_change_password').click(function() {
		onclick_menu('#website_mobile_app_menu_change_password');
		$("#main_container", self).html(qweb.render('website_mobile_app_change_password'));
		$('#btn_change_password').click(function(){
			onclick_change_password_button();
		});
	});

	function onclick_change_password_button() {
		old_password = $('#change_password_old').val();
		new_password = $('#change_password_new').val();
		retype_password = $('#change_password_retype').val();

		if(new_password != retype_password) {
			alert('New Password and Retype Password doesn\'t match.');
			$('#change_password_new').val('');
			$('#change_password_retype').val('')
		} else if(old_password.length == 0){
			alert('Old Password may not be empty.');
		}  else if(new_password.length == 0){
			alert('New Password may not be empty.');
		} else {
			change_password_json = {
				'old_password': old_password,
				'new_password': new_password,
			};
			$.ajax({
				dataType: "json",
				url: '/mobile_app/change_password/' + JSON.stringify(change_password_json),
				method: 'POST',
				success: function(response) {
					if (response.status) {
						alert(response.info);
						if(response.success){
							logout();
						}else {
							$('#change_password_old').val('');
						}
					} else {
						alert('Server Unreachable.');
					}
				},
				error: function(XMLHttpRequest, textStatus, errorThrown) {
					alert_error(XMLHttpRequest);
				} ,
			});
		}
	}

// LIST CONTRACT ============================================================================================================

	$('#website_mobile_app_menu_list_contract').click(function() {

	});

});
