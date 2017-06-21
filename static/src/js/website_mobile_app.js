$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

	var contract_datas = [];
	var order_datas = [];
	var to_cities = [];
	var user = {
		user_group: 'undefined',
	};
	var index_click_contract;
	var index_click_order;
	var current_au_name;

	function onclick_menu(id) {
		$('#website_mobile_app_menu_book_vehicle').removeClass('active');
		$('#website_mobile_app_menu_list_orders').removeClass('active');
		$('#website_mobile_app_menu_change_password').removeClass('active');
		$('#website_mobile_app_menu_list_contract').removeClass('active');
		$('#website_mobile_app_menu_list_shuttle').removeClass('active');
		$(id).addClass('active');
	};

	function onclick_detail_contract_menu(id) {
		$('#website_mobile_app_menu_info_contract').removeClass('active');
		$('#website_mobile_app_menu_usage_control').removeClass('active');
		$('#website_mobile_app_menu_quota_changes').removeClass('active');
		$('#website_mobile_app_menu_shuttle').removeClass('active');
		$(id).addClass('active');
    };

// BOOK VEHICLE =============================================================================================================

	$('#website_mobile_app_menu_book_vehicle').click(function() {
		onclick_menu('#website_mobile_app_menu_book_vehicle');
		$.get('/mobile_app/get_required_book_vehicle', null, function(data){
			var response = JSON.parse(data);
			var order_type = response['order_type'];
			self.to_cities = response['route_to'];
			self.user = response['user'];
			self.user['user_group'] = response['user_group'];
			self.contract_datas = response['contract_datas'];

			var fleet_vehicle_datas = [];
			var units = [];
			var route_from = [];
			if (self.contract_datas.length != 0) {
				fleet_vehicle_datas = self.contract_datas[0].fleet_vehicle;
				units = self.contract_datas[0].units;
				route_from = self.contract_datas[0].route_from;
			}

			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'user_group': self.user['user_group'],
				// Information
				'contract_datas': self.contract_datas,
				'fleet_vehicle_datas': fleet_vehicle_datas,
				'units': units,
				'order_types': order_type,
				// Route
				'from_areas': route_from,
				'to_cities': self.to_cities,
				'to_areas': self.to_cities[0].areas,
				// Passenger
				// Time
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
			}));

			$('#create_order_contract').change(function(){
				onchange_create_order_contract($(this).val());
			});

			$('#create_order_route_to_city').change(function(){
				onchange_create_order_route_to_city($(this).val());
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
		passengers = [];
		$('#passengers > tbody > tr').each(function() {
			var row = $(this);
			var name = row.find('.tbl_name').val().trim();
			var phone = row.find('.tbl_phone').val().trim();
			if(name && phone) {
				passengers.push({
					'name': name,
					'phone': phone,
					'is_orderer': row.attr("id") ? true : false,
				})
			} else {
				alert('Please complete the passengers information, name and phone number are both required!'); return false;
			}
		});

		create_order_json = {
			'contract_id': $('#create_order_info_contract').val(),
			'fleet_vehicle_id': $('#create_order_info_fleet_vehicle').val(),
			'unit_id': $('#create_order_info_unit').val(),
			'type_id': $('#create_order_info_type').val(),

			'from_area_id': $('#create_order_route_from_area').val(),
			'from_location': $('#create_order_route_from_location').val().trim(),

			'to_city_id': $('#create_order_route_to_city').val(),
			'to_area_id': $('#create_order_route_to_area').val(),
			'to_location': $('#create_order_route_to_location').val().trim(),

			'i_am_passenger': $("#ckb_i_am_passenger").prop('checked'),
			'passengers': passengers,

			'start_planned': $('#create_order_start_planned').val(),
			'finish_planned': $('#create_order_finish_planned').val(),
		};
		if (create_order_json['contract_id'] == null) {
			alert('You have no Contract!'); return;
		} else if (create_order_json['fleet_vehicle_id'] == null) {
			alert('You have no Fleet!'); return;
		} else if (!create_order_json['start_planned']) {
			alert('Please input the start planned date correctly!'); return;
		} else if (!create_order_json['finish_planned']) {
			alert('Please input the finish planned date correctly!'); return;
		} else if(self.user['user_group'] === 'booker' || self.user['user_group'] === 'approver') {
			if (create_order_json['unit_id'] == null) {
				alert('You have no Unit!'); return;
			} else if (create_order_json['type_id'] == null) {
				alert('Please select the Order Type!'); return;
			} else if (!create_order_json['from_area_id']) {
				alert('Please select the Origin Area!'); return;
			} else if (!create_order_json['from_location']) {
				alert('Please input the Origin Location!'); return;
			} else if (!create_order_json['to_city_id']) {
				alert('Please select the Destination City!'); return;
			} else if (!create_order_json['to_area_id']) {
				alert('Please select the Destination Area!'); return;
			} else if (!create_order_json['to_location']) {
				alert('Please input the Destination Location!'); return;
			}
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
	};

	function onchange_create_order_contract(contract_id) {
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == contract_id) {
				// Update fleet selection
				$('#create_order_fleet_vehicle').empty();
				$.each(contract_data.fleet_vehicle, function(index, fleet_vehicle_data) {
					$('#create_order_fleet_vehicle').append(
						'<option value=' + fleet_vehicle_data.id + '>' + fleet_vehicle_data.name + '</option>');
				});
				// Update allocation unit selection
				$('#create_order_info_unit').empty();
				$.each(contract_data.units, function(index, unit) {
					$('#create_order_info_unit').append(
						'<option value=' + unit.id + '>' + unit.name + '</option>');
				});
				// Update route_from_area selection
				$('#create_order_route_from_area').empty();
				$.each(contract_data.route_from, function(index, route) {
					$('#create_order_route_from_area').append(
						'<option value=' + route.id + '>' + route.name + '</option>');
				});
			}
		});
	};

	function onchange_create_order_route_to_city(city_id) {
		$.each(self.to_cities, function(index, city) {
			if (city.id == city_id) {
				$('#create_order_route_to_area').empty();
				$.each(city.areas, function(index, area) {
					$('#create_order_route_to_area').append(
						'<option value=' + area.id + '>' + area.name + '</option>');
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
			row += '<td><input type="text" class="tbl_name form-control" value="' + name + '"/></td>' +
                   	'<td><input type="text" class="tbl_phone form-control" value="' + phone + '"/></td>' +
                   	'<td><button type="button" class="btn_remove_passenger close" aria-label="Close">' +
							'<span aria-hidden="true">x</span>' +
						'</button></td>';
		} else {
			row += '<td><input type="text" class="tbl_name form-control" value="' + name + '" readonly/></td>' +
                   	'<td><input type="text" class="tbl_phone form-control" value="' + phone + '" readonly/></td>' +
                   	'<td></td>';
		}
		row += '</tr>';
		return row;
	};

// LIST ORDER ===============================================================================================================

	$('#website_mobile_app_menu_list_orders').click(function() {
		onclick_menu('#website_mobile_app_menu_list_orders');
		$.get('/mobile_app/fetch_orders', null, function(data){
			var response = JSON.parse(data);
			self.user = {
            	user_group: response['user_group']
            }

            classifications = {
				'Pending': 'pending',
				'Ready': 'ready',
				'Running': 'running',
				'History': 'history',
			}

			if (self.user['user_group'] === 'fullday_passenger') {
				classifications = {
					'Ready': 'ready',
					'Running': 'running',
					'History': 'history',
				}
			}
			self.order_datas = response['list_order'];
			$("#main_container", self).html(qweb.render('website_mobile_app_list_order',{
				'classifications': classifications,
				'order_datas': response['list_order'],
				'user_group' : self.user['user_group']
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

			$('#btn_approve_order').click(function(event) {
				var target = $(event.target);
				order_id = target.attr("id_order");
				onclick_button_approve_order(order_id);
				event.stopPropagation();
			});

			$('#btn_reject_order').click(function(event) {
				var target = $(event.target);
				order_id = target.attr("id_order");
				onclick_button_reject_order(order_id);
				event.stopPropagation();
			});

			$(".list_order").click(function(event) {
				var target = $(event.target);
				self.index_click_order = target.attr("index_order");
				var classifications_order = target.attr("classification_order");
				onclick_list_order_detail_order(self.index_click_order, classifications_order);
				event.stopPropagation();
			});

			$('#dialog_order_detail_container').click(function(event){
				event.stopPropagation();
			})
		});
	});

	//Order Detail ===============================================================
	function onclick_list_order_detail_order(index_order, classifications_order) {
		order = self.order_datas[classifications_order][index_order];
		//Render Dialog
		$("#dialog_order_detail_container", self).html(qweb.render('dialog_order_detail',{
			'order_name' : order.name,
		}));

		// Tampilkan Dialog
		var modal = $("#modalOrderDetail");
		modal.css("display", "block");

		// Button Close Dialog
		$(".close_dialog").click(function(event) {
			modal.css("display", "none");
		});

		// Jika Click Selain di Daerah dialog, maka tutup dialog
		window.onclick = function(event) {
			if (event.target == modal.get(0)) {
				modal.css("display", "none");
			}
		}
	};

	function onclick_button_approve_order(order_id) {
		$.ajax({
			dataType: "json",
			url: '/mobile_app/approve_order/' + order_id,
			method: 'POST',
			success: function(response) {
				if (response.status) {
					alert(response.info);
					if(response.success){
						$('#website_mobile_app_menu_list_orders').click();
					} else {}
				} else {
					alert('Server Unreachable.');
				}
			},
			error: function(XMLHttpRequest, textStatus, errorThrown) {
				alert_error(XMLHttpRequest);
			} ,
		});
	};

	function onclick_button_reject_order(order_id) {
		$.ajax({
			dataType: "json",
			url: '/mobile_app/reject_order/' + order_id,
			method: 'POST',
			success: function(response) {
				if (response.status) {
					alert(response.info);
					if(response.success){
						$('#website_mobile_app_menu_list_orders').click();
					} else {}
				} else {
					alert('Server Unreachable.');
				}
			},
			error: function(XMLHttpRequest, textStatus, errorThrown) {
				alert_error(XMLHttpRequest);
			} ,
		});
	};
// LIST SHUTTLE =============================================================================================================

	$('#website_mobile_app_menu_list_shuttle').click(function() {
		onclick_menu('#website_mobile_app_menu_list_shuttle');
		$.get('/mobile_app/fetch_contract_shuttles', null, function(data){
			self.contract_datas = JSON.parse(data);
			$("#main_container", self).html(qweb.render('website_mobile_app_list_shuttle',{
				'contract_datas': self.contract_datas,
			}));
			$('#list_shuttle_contract').change(function(){
				onchange_list_shuttle_contract($(this).val());
			});
			$('#list_shuttle_contract').change();
		});
	});

	function onchange_list_shuttle_contract(contract_id) {
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == contract_id) {
				// Update shuttle schedule
				days = {
					'Monday': '0',
					'Tuesday': '1',
					'Wednesday': '2',
					'Thursday': '3',
					'Friday': '4',
					'Saturday': '5',
					'Sunday': '6',
				}
				$("#website_mobile_app_list_shuttle_schedules", self).html(qweb.render('website_mobile_app_list_shuttle_schedules',{
					'days': days,
					'shuttle_datas': contract_data.shuttle_schedules_by_days,
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
			}
		});
	};

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
	};

// LIST CONTRACT ============================================================================================================

	$('#website_mobile_app_menu_list_contract').click(function() {
		onclick_menu('#website_mobile_app_menu_list_contract');
		$.get('/mobile_app/fetch_contracts', null, function(data){
			var response = JSON.parse(data);
			self.user = {
				user_group: response['user_group']
			}
			self.contract_datas = response['list_contract'];
			$("#main_container", self).html(qweb.render('website_mobile_app_list_contract',{
				'user_group': self.user['user_group'],
				'contract_datas': self.contract_datas,
			}));
			$(".list_contract").click(function(event) {
				var target = $(event.target);
				self.index_click_contract = target.attr("id_contract");
				$("#main_container", self).html(qweb.render('website_mobile_app_detail_contract',{
					'contract_name': self.contract_datas[self.index_click_contract].name,
					'user_group': self.user['user_group'],
					'contract_service_type': self.contract_datas[self.index_click_contract].service_type,
				}));
				setOnClickButtonMenuDetailContract();
				if(self.user['user_group'] === 'pic') {
					$('#website_mobile_app_menu_info_contract').click();
				} else {
					$('#website_mobile_app_menu_usage_control').click();
				}
			});
		});
	});

	function setOnClickButtonMenuDetailContract(){
		//Onclick menu info
		$('#website_mobile_app_menu_info_contract').click(function() {
			onclick_detail_contract_menu('#website_mobile_app_menu_info_contract');
			var contract = self.contract_datas[self.index_click_contract]
			$("#detail_contract_main_container", self).html(qweb.render('website_mobile_app_detail_contract_info',{
				'state': contract.state,
				'start_date': contract.start_date,
				'end_date': contract.end_date,
				'service_type': contract.service_type,
				'by_order_minimum_minutes': contract.by_order_minimum_minutes,
				'min_start_minutes': contract.min_start_minutes,
				'max_delay_minutes': contract.max_delay_minutes,
			}));
		});
		//Onclick menu usage control
		$('#website_mobile_app_menu_usage_control').click(function() {
			onclick_detail_contract_menu('#website_mobile_app_menu_usage_control');
			$.ajax({
				dataType: "json",
				url: '/mobile_app/get_usage_control_list/' + JSON.stringify(self.contract_datas[self.index_click_contract].id),
				method: 'POST',
				success: function(response) {
					if (response.status) {
						if(response.success){
							$("#detail_contract_main_container", self).html(qweb.render('website_mobile_app_list_control_usage',{
								'quota_list': JSON.parse(response.quota_list),
                            }));
                            quota_list = JSON.parse(response.quota_list)
							$(".list_quota_usage").click(function(){
								event.stopPropagation();
								self.current_au_name = $(this).attr("au_name");
								onclick_usage_control_quota($(this).attr("value"));
							});
							$(".quota_btn_request_change_quota").click(function(event){
								event.stopPropagation();
								onclick_button_request_change_quota($(this).attr("au_id"), $(this).attr("contract_id"));
							});
							$('#dialog_request_quota_container').click(function(event){
								event.stopPropagation();
							});
						}
					} else {
						alert('Server Unreachable.');
					}
				},
				error: function(XMLHttpRequest, textStatus, errorThrown) {
					alert_error(XMLHttpRequest);
				} ,
			});
        });

        function onclick_usage_control_quota(quota_id) {
			$.get('/mobile_app/fetch_contract_detail_usage_control_quota/' + quota_id, null, function(data){
				var quota = JSON.parse(data)
				classifications = {
					'Pending': 'pending',
					'History': 'history',
				};
				$("#detail_contract_main_container", self).html(qweb.render('website_mobile_app_detail_control_usage',{
					'user_group': self.user['user_group'],
					'classifications': classifications,
					'au_name': self.current_au_name,
					'total_usage': quota.total_usage,
					'yellow_limit': quota.yellow_limit,
					'red_limit': quota.red_limit,
					'total_request_nominal': quota.total_request_nominal,
					'total_request_time': quota.total_request_time,
					'limit_requests': quota.limit_requests,
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
				$(".limit_request_btn_approve").click(function(){
					onclick_button_change_log_approve($(this).attr("value"));
				});
				$(".limit_request_btn_reject").click(function(){
					onclick_button_change_log_reject($(this).attr("value"));
				});
			});
		};

        //Onclick menu quota changes
		$('#website_mobile_app_menu_quota_changes').click(function() {
			onclick_detail_contract_menu('#website_mobile_app_menu_quota_changes');
			$.get('/mobile_app/fetch_contract_quota_changes/' + JSON.stringify(self.contract_datas[self.index_click_contract].id), null, function(data){
				classifications = {
					'Pending': 'pending',
					'History': 'history',
				};
				$("#detail_contract_main_container", self).html(
				qweb.render('website_mobile_app_detail_contract_quota_changes',{
					'user_group': self.user['user_group'],
					'classifications': classifications,
					'quota_changes': JSON.parse(data),
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
				$(".quota_change_btn_approve").click(function(){
					onclick_button_change_log_approve($(this).attr("value"));
				});
				$(".quota_change_btn_reject").click(function(){
					onclick_button_change_log_reject($(this).attr("value"));
				});
			});
		});

		//Onclick menu shuttle
		$('#website_mobile_app_menu_shuttle').click(function() {
			$.get('/mobile_app/fetch_shuttle_schedules/' + JSON.stringify({
				'from': 'contract',
				'id': self.contract_datas[self.index_click_contract].id,
			}), null, function(data){
				onclick_detail_contract_menu('#website_mobile_app_menu_shuttle');
				shuttle_schedules_by_days = JSON.parse(data);
				days = {
					'Monday': '0',
					'Tuesday': '1',
					'Wednesday': '2',
					'Thursday': '3',
					'Friday': '4',
					'Saturday': '5',
					'Sunday': '6',
				}
				$("#detail_contract_main_container", self).html(qweb.render('website_mobile_app_list_shuttle_schedules',{
					'days': days,
					'shuttle_datas': shuttle_schedules_by_days,
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

		function onclick_button_change_log_approve(change_log_id) {
			$.ajax({
				dataType: "json",
				url: '/mobile_app/approve_quota_changes/' + change_log_id,
				method: 'POST',
				success: function(response) {
					if (response.status) {
						alert(response.info);
						if(response.success){
							$('#website_mobile_app_menu_quota_changes').click();
						} else {}
					} else {
						alert('Server Unreachable.');
					}
				},
				error: function(XMLHttpRequest, textStatus, errorThrown) {
					alert_error(XMLHttpRequest);
				} ,
			});
		};

		function onclick_button_change_log_reject(change_log_id) {
			var reject_reason = prompt("Input the reject reason:", "");
			if (reject_reason !== null && reject_reason !== "") {
				reject_change_log_data = {
					'change_log_id': change_log_id,
					'reject_reason': reject_reason,
				};
				$.ajax({
					dataType: "json",
					url: '/mobile_app/reject_quota_changes/' + JSON.stringify(reject_change_log_data),
					method: 'POST',
					success: function(response) {
						if (response.status) {
							alert(response.info);
							if(response.success){
								$('#website_mobile_app_menu_quota_changes').click();
							} else {}
						} else {
							alert('Server Unreachable.');
						}
					},
					error: function(XMLHttpRequest, textStatus, errorThrown) {
						alert_error(XMLHttpRequest);
					} ,
				});
			}
		};

		function onclick_button_request_change_quota(au_id, contract_id) {
			var red_limit = 0;
			var yellow_limit = 0;

			// Dapatkan Quota dari au_id
			$.each(quota_list, function(index, quota){
				if(quota['au_id'] == au_id){
					red_limit = quota['red_limit'];
					yellow_limit = quota['yellow_limit'];
				}
			});

			//Render Dialog
			$("#dialog_request_quota_container", self).html(qweb.render('dialog_request_change_quota',{
				'red_limit' : red_limit,
				'yellow_limit' : yellow_limit
			}));

			$("#longevity_month").prop('checked', true);
			$("#new_amount_yellow").html(yellow_limit);
			$("#new_amount_red").html(red_limit);

			// Tampilkan Dialog
			var modal = $("#modalChangeQuota");
			modal.css("display", "block");

			// Button Close Dialog
			$(".close_dialog").click(function(event) {
            	modal.css("display", "none");
			});

			// Onchange input amount yellow_limit, new = old + new_amount
			$("#amount_yellow_dialog").change(function() {
				old_amount = parseInt($("#old_amount_yellow").html());
				new_amount = parseInt($("#amount_yellow_dialog").val());
				$("#new_amount_yellow").html(new_amount + old_amount);
             });

			// Onchange input amount red_limit, new = old + new_amount
            $("#amount_red_dialog").change(function() {
				old_amount = parseInt($("#old_amount_red").html());
				new_amount = parseInt($("#amount_red_dialog").val());
				$("#new_amount_red").html(new_amount + old_amount);
			});

			// Button Request Quota Dialog
			$(".dialog_quota_change_button_request").click(function(event) {
				oldYellow = parseInt($("#old_amount_yellow").html());
				oldRed = parseInt($("#old_amount_red").html());
				newYellow = parseInt($("#new_amount_yellow").html());
				newRed = parseInt($("#new_amount_red").html());

				if (oldYellow === newYellow && oldRed === newRed) {
					alert("Please Submit At Least One Request"); return;
				} else if (newYellow <= 0) {
					alert("The new value of yellow limit can not be less nor equal zero"); return;
				} else if (newRed <= 0) {
					alert("The new value of red limit can not be less nor equal zero"); return;
				} else if (newRed == newYellow) {
					alert("Yellow and Red limit can\'t have same value"); return;
				} else if (newRed < newYellow) {
					alert("Red limit cannot be less than yellow limit"); return;
				}

				var req_longevity = 'temporary';
				if ($("#longevity_permanent").is(":checked")) {
                    req_longevity = 'permanent';
                }

				// Buat Data Untuk Request Quota
				var request_quota_json = {
					'customer_contract_id': contract_id,
					'allocation_unit_id': au_id,
					//'request_by': $('#create_order_info_unit').val(),
					'request_longevity': req_longevity,
					'new_yellow_limit': newYellow,
					'new_red_limit': newRed
				};

				// Request DataBase untuk save
                $.ajax({
					dataType: "json",
					url: '/mobile_app/request_quota_changes/' +  JSON.stringify(request_quota_json),
					method: 'POST',
					success: function(response) {
						if (response.status) {
							alert(response.info);
							if(response.success){
								modal.css("display", "none");
							}
						} else {
							alert('Server Unreachable.');
						}
					},
					error: function(XMLHttpRequest, textStatus, errorThrown) {
						alert_error(XMLHttpRequest);
					},
				});
            });

			// Jika Click Selain di Daerah dialog, maka tutup dialog
			window.onclick = function(event) {
				if (event.target == modal.get(0)) {
					modal.css("display", "none");
				}
			}
		};
	};
});
