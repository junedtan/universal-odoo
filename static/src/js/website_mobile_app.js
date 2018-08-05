
function intersperse(str, indices, separator) {
	separator = separator || '';
	var result = [], last = str.length;

	for(var i=0; i<indices.length; ++i) {
		var section = indices[i];
		if (section === -1 || last <= 0) { break; }
		else if(section === 0 && i === 0) { break; }
		else if (section === 0) { section = indices[--i]; }
		result.push(str.substring(last-section, last));
		last -= section;
	}
	var s = str.substring(0, last);
	if (s) { result.push(s); }
	return result.reverse().join(separator);
}

function insert_thousand_seps(num) {
	var l10n = openerp._t.database.parameters;
	var negative = num[0] === '-';
	num = (negative ? num.slice(1) : num);

	if (l10n.grouping.length == 0) {
		l10n.grouping = [3,0];
	}

	return (negative ? '-' : '') + intersperse(
		num, l10n.grouping, l10n.thousands_sep);
}

function currency_to_str(price) {
	var l10n = openerp._t.database.parameters;
	var precision = 2;
	/*
	if ($(".decimal_precision").length) {
		var dec_precision = $(".decimal_precision").first().data('precision');
		//MAth.log10 is not implemented in phantomJS
		dec_precision = Math.round(Math.log(1/parseFloat(dec_precision))/Math.log(10));
		if (!isNaN(dec_precision)) {
			precision = dec_precision;
		}
	}
	*/
	var formatted = _.str.sprintf('%.' + precision + 'f', price).split('.');
	formatted[0] = insert_thousand_seps(formatted[0]);
	var ret = formatted.join(l10n.decimal_point);
	return ret;
}



$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;

//new version

	try {
		if (mobile_web == true) {
			$(".navbar-static-top").hide();
			qweb.add_template('/universal/static/src/xml/website_mobile_app.xml?'+$.now(), function() {
				mobile_app.init(mobile_app_activity_definition, mobile_app_intent_definition);
				mobile_app.data_manager.attach_data_sources(mobile_app_data_sources, true);
			});

			return;
		}
	} catch(e) {

	}

//old version

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
	var my_id;
	var page_stack = [];
	$('#button_back').hide();

	function onclick_menu(id, page_title) {
		page_stack.push(id);
		$('#panel_title').text(page_title);
		$('#menu_container').hide();
		$('#main_container').show();
		$('#button_back').show();
	};

	function onclick_change_password_button(event) {
		old_password = $('#change_password_old').val();
		new_password = $('#change_password_new').val();
		retype_password = $('#change_password_retype').val();

		if(new_password != retype_password) {
			alert('New Password and Retype Password does not match.');
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

	$('#button_back').click(function() {
		page_stack.pop();
		if(page_stack.length == 0) {
			$('#panel_title').text('UNIVERSAL');
			$('#menu_container').show();
			$('#main_container').hide();
			$('#button_back').hide();
		} else {
			var page = page_stack.pop();
			$(page).click();
			if(page == '.list_contract') {
				page_stack.pop();
			}
		}
	});

	function onclick_usage_control() {
		$('#menu_detail_contract_container').hide();
		$('#detail_contract_main_container').show();
	}

	function onclick_detail_contract_menu(id) {
		$('#website_mobile_app_menu_info_contract').css("background-color", "#337ab7");
		$('#website_mobile_app_menu_usage_control').css("background-color", "#337ab7");
		$('#website_mobile_app_menu_quota_changes').css("background-color", "#337ab7");
		$('#website_mobile_app_menu_shuttle').css("background-color", "#337ab7");
		$(id).css("background-color", "#d3d3d3");
	};
	
	function onclick_tab_order(id) {
		$('#website_mobile_app_tab_pending_order').css("background-color", "#337ab7");
		$('#website_mobile_app_tab_ready_order').css("background-color", "#337ab7");
		$('#website_mobile_app_tab_running_order').css("background-color", "#337ab7");
		$('#website_mobile_app_tab_history_order').css("background-color", "#337ab7");
		$(id).css("background-color", "#d3d3d3");
	};

	function onclick_tab_detail_au(id) {
		$('#website_mobile_app_tab_usage_control_information').css("background-color", "#337ab7");
		$('#website_mobile_app_tab_usage_control_request_history').css("background-color", "#337ab7");
		$(id).css("background-color", "#d3d3d3");
	}

	function intersperse(str, indices, separator) {
		separator = separator || '';
		var result = [], last = str.length;

		for(var i=0; i<indices.length; ++i) {
			var section = indices[i];
			if (section === -1 || last <= 0) { break; }
			else if(section === 0 && i === 0) { break; }
			else if (section === 0) { section = indices[--i]; }
			result.push(str.substring(last-section, last));
			last -= section;
		}
		var s = str.substring(0, last);
		if (s) { result.push(s); }
		return result.reverse().join(separator);
	}
	
	function insert_thousand_seps(num) {
		var l10n = instance._t.database.parameters;
		var negative = num[0] === '-';
		num = (negative ? num.slice(1) : num);

		return (negative ? '-' : '') + intersperse(
			num, l10n.grouping, l10n.thousands_sep);
	}

	function currency_to_str(price) {
		var l10n = instance._t.database.parameters;
		var precision = 2;
		/*
		if ($(".decimal_precision").length) {
			var dec_precision = $(".decimal_precision").first().data('precision');
			//MAth.log10 is not implemented in phantomJS
			dec_precision = Math.round(Math.log(1/parseFloat(dec_precision))/Math.log(10));
			if (!isNaN(dec_precision)) {
				precision = dec_precision;
			}
		}
		*/
		var formatted = _.str.sprintf('%.' + precision + 'f', price).split('.');
		formatted[0] = insert_thousand_seps(formatted[0]);
		var ret = formatted.join(l10n.decimal_point);
		return ret;
	}

// BOOK VEHICLE =============================================================================================================

	$('#website_mobile_app_menu_book_vehicle').click(function() {
		onclick_menu('#website_mobile_app_menu_book_vehicle', 'Book Vehicle');
		$.get('/mobile_app/get_required_book_vehicle', null, function(data){
			var response = JSON.parse(data);
			var order_type = response['order_type'];
			self.to_cities = response['route_to'];
			self.user = response['user'];
			self.user['user_group'] = response['user_group'];
			self.contract_datas = response['contract_datas'];

			var fleet_type_datas = [];
			var units = [];
			var district_from = [];
			var route_from = [];
			if (self.contract_datas.length != 0) {
				fleet_type_datas = self.contract_datas[0].fleet_type;
				units = self.contract_datas[0].units;
				district_from = self.contract_datas[0].districts;
				if (self.contract_datas[0].districts.length != 0) {
					route_from = self.contract_datas[0].districts[0].areas;
				}
			}
			var to_areas = [];
			if (self.to_cities[0].districts.length != 0) {
				to_areas = self.to_cities[0].districts[0].areas;
			}

			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'user_group': self.user['user_group'],
				// Information
				'contract_datas': self.contract_datas,
				'fleet_type_datas': fleet_type_datas,
				'units': units,
				'order_types': order_type,
				// Route
				'from_districts': district_from,
				'from_areas': route_from,
				'to_cities': self.to_cities,
				'to_districts': self.to_cities[0].districts,
				'to_areas': to_areas,
				// Passenger
				// Time
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
				'create_mode': true,
			}));

			$('#create_order_contract').change(function(){
				onchange_create_order_contract($(this).val());
			});

			$('#create_order_route_from_district').change(function(){
				onchange_create_order_route_from_district($(this).val());
			});

			$('#create_order_route_to_city').change(function(){
				onchange_create_order_route_to_city($(this).val());
			});

			$('#create_order_route_to_district').change(function(){
				onchange_create_order_route_to_district($(this).val());
			});

			$('#btn_create_order').click(function(){
				onclick_create_order_button('create', 0);
			});

			var ckb_i_am_passenger = $('#ckb_i_am_passenger');
			ckb_i_am_passenger.click(function(){
				onclick_create_order_i_am_passenger("");
			});
			ckb_i_am_passenger.click();
			onclick_create_order_i_am_passenger("");

			$('#btn_add_passenger').click(function(){
				onclick_create_order_add_passenger();
			});
		});
	});

	function onclick_create_order_button(mode, order_id) {
		create_order_json = {
			'mode_create_or_edit': (mode === 'create') ? 'create' : 'edit',
			'contract_id': $('#create_order_info_contract').val(),
			'fleet_type_id': $('#create_order_info_fleet_type').val(),
			'unit_id': $('#create_order_info_unit').val(),
			'type_id': $('#create_order_info_type').val(),
			'start_planned': $('#create_order_start_planned').val(),
			'finish_planned': $('#create_order_finish_planned').val(),
		};
		if(self.user['user_group'] !== 'fullday_passenger') {
			passengers = [];
			$('#passengers > tbody > tr').each(function() {
				var row = $(this);
				var name = row.find('.tbl_name').val().trim();
				var phone = row.find('.tbl_phone').val().trim();
				var passenger_info;
				if(name && phone) {
					passenger_info = {
						'name': name,
						'phone_no': phone,
					}
					if(row.attr("id") === self.my_id) {
						passenger_info['is_orderer'] = true;
					} else {
						passenger_info['is_orderer'] = false;
					}
					if(row.attr("exist_id") && (row.attr("exist_id").trim() !== false || row.attr("exist_id").trim() !== '')) {
						passenger_info['exist_id'] = row.attr("exist_id");
					}
					passengers.push(passenger_info);
				} else {
					alert('Please complete the passengers information, name and phone number are both required!'); return false;
				}
			});

			create_order_json['from_area_id'] = $('#create_order_route_from_area').val();
			create_order_json['from_location'] = $('#create_order_route_from_location').val().trim();
	
			create_order_json['to_city_id'] = $('#create_order_route_to_city').val();
			create_order_json['to_area_id'] = $('#create_order_route_to_area').val();
			create_order_json['to_location'] = $('#create_order_route_to_location').val().trim();
	
			create_order_json['i_am_passenger'] = $("#ckb_i_am_passenger").prop('checked');
			create_order_json['passengers'] = passengers;
		}

		if(mode === 'edit') {
			create_order_json['order_id'] = order_id;
		}
		if (create_order_json['contract_id'] == null) {
			alert('You have no Contract!'); return;
		} else if (create_order_json['fleet_type_id'] == null) {
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
			url: '/mobile_app/create_edit_order/' + JSON.stringify(create_order_json),
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
				$('#create_order_fleet_type').empty();
				$.each(contract_data.fleet_type, function(index, fleet_type_data) {
					$('#create_order_fleet_type').append(
						'<option value=' + fleet_type_data.id + '>' + fleet_type_data.name + '</option>');
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

	function onchange_create_order_route_from_district(district_id) {
		var contract_id = $('#create_order_info_contract').val();
		$.each(self.contract_datas, function(index, contract_data) {
			if (contract_data.id == contract_id) {
				$.each(contract_data.districts, function(index, district) {
					if (district.id == district_id) {
						$('#create_order_route_from_area').empty();
						$.each(district.areas, function(index, area) {
							$('#create_order_route_from_area').append(
								'<option value=' + area.id + '>' + area.name + '</option>');
						});
					}
				});
			}
		});
	};

	function onchange_create_order_route_to_city(city_id) {
		$.each(self.to_cities, function(index, city) {
			if (city.id == city_id) {
				$('#create_order_route_to_district').empty();
				$('#create_order_route_to_area').empty();
				$.each(city.districts, function(index, district) {
					$('#create_order_route_to_district').append(
						'<option value=' + district.id + '>' + district.name + '</option>');
				});
				$('#create_order_route_to_district').change();
			}
		});
	};

	function onchange_create_order_route_to_district(district_id) {
		city_id = $('#create_order_route_to_city').val();
		$.each(self.to_cities, function(index, city) {
			if (city.id == city_id) {
				$.each(city.districts, function(index, district) {
					if (district.id == district_id) {
						$('#create_order_route_to_area').empty();
						$.each(district.areas, function(index, area) {
							$('#create_order_route_to_area').append(
								'<option value=' + area.id + '>' + area.name + '</option>');
						});
					}
				});
			}
		});
	};

	function onclick_create_order_i_am_passenger(exist_id) {
		var checkbox = $("#ckb_i_am_passenger");
		self.my_id = "passenger_me";
		if(checkbox.prop('checked')) {
			var table_passengers = $("#passengers");
			table_passengers.prepend(get_row_string_passenger(self.user.name,
				self.user.phone === false ? '-' : self.user.phone, self.my_id, exist_id, false));
		} else {
			$("#"+self.my_id).remove();
		}
	};

	function onclick_create_order_add_passenger() {
		var table_passengers = $("#passengers");
		table_passengers.append(get_row_string_passenger("", "", "", "", true));
		$(".btn_remove_passenger").click(function(){
			onclick_create_order_remove_passenger(this);
		});
	};

	function add_passenger_to_table(name, phone, exist_id) {
		var table_passengers = $("#passengers");
		table_passengers.append(get_row_string_passenger(name, phone, '', exist_id, true));
		$(".btn_remove_passenger").click(function(){
			onclick_create_order_remove_passenger(this);
		});
	};

	function onclick_create_order_remove_passenger(button_remove) {
		button_remove.closest('tr').remove();
	};

	function get_row_string_passenger(name, phone, id, exist_id, removable) {
		if(id === "") {
			if(exist_id === "") {
				var row = '<tr>';
			} else {
				var row = '<tr exist_id="' + exist_id + '">';
			}
		} else {
			if(exist_id === "") {
				var row = '<tr id="' + id + '">';
			} else {
				var row = '<tr id="' + id + '" exist_id="' + exist_id + '">';
			}
		}
		if(removable === true) {
			row += '<td><input type="text" class="tbl_name form-control" value="' + name + '"/></td>' +
					'<td><input type="text" class="tbl_phone form-control" value="' + phone + '"/></td>' +
					'<td><button type="button" class="btn_remove_passenger form-control btn btn-default" aria-label="Close">' +
							'<span class="fa fa-close"></span>' +
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
		onclick_menu('#website_mobile_app_menu_list_orders', 'Orders');
		$.get('/mobile_app/fetch_orders/' + JSON.stringify({}), null, function(data){
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

			// AUTO COMPLETE FILTER ORDER
			var order_names = [];
			var order_bookers = [];
			var order_drivers = [];
			var order_vehicles = [];
			$.each(self.order_datas, function(key,value){
				for(var i=0; i<value.length; i++) {
					if ($.inArray(value[i].name, order_names) == -1 && value[i].name) {
						order_names.push(value[i].name);
					}
					if ($.inArray(value[i].order_by_name, order_bookers) == -1 && value[i].order_by_name) {
						order_bookers.push(value[i].order_by_name);
					}
					if ($.inArray(value[i].assigned_driver_name, order_drivers) == -1 && value[i].assigned_driver_name) {
						order_drivers.push(value[i].assigned_driver_name);
					}
					if ($.inArray(value[i].assigned_vehicle_name, order_vehicles) == -1 && value[i].assigned_vehicle_name) {
						order_vehicles.push(value[i].assigned_vehicle_name);
					}
				}
			});
			$("#main_container", self).html(qweb.render('website_mobile_app_list_order',{
				'user_group' : self.user['user_group'],
				'order_names': order_names,
				'order_bookers': order_bookers,
				'order_drivers': order_drivers,
				'order_vehicles': order_vehicles,
			}));

			$("#website_mobile_app_tab_pending_order").click(function(event) {
				onclick_tab_order('#website_mobile_app_tab_pending_order');
				$("#container_order_list", self).html(qweb.render('website_mobile_app_list_order_classification',{
					'classifications': 'pending',
					'order_datas': self.order_datas['pending'],
					'user_group' : self.user['user_group']
				}));
				addEventListOrder();
			});
			
			$("#website_mobile_app_tab_ready_order").click(function(event) {
				onclick_tab_order('#website_mobile_app_tab_ready_order');
				$("#container_order_list", self).html(qweb.render('website_mobile_app_list_order_classification',{
					'classifications': 'ready',
					'order_datas': self.order_datas['ready'],
					'user_group' : self.user['user_group']
				}));
				addEventListOrder();
			});
			
			$("#website_mobile_app_tab_running_order").click(function(event) {
				onclick_tab_order('#website_mobile_app_tab_running_order');
				$("#container_order_list", self).html(qweb.render('website_mobile_app_list_order_classification',{
					'classifications': 'running',
					'order_datas': self.order_datas['running'],
					'user_group' : self.user['user_group']
				}));
				addEventListOrder();
			});
			
			$("#website_mobile_app_tab_history_order").click(function(event) {
				onclick_tab_order('#website_mobile_app_tab_history_order');
				$("#container_order_list", self).html(qweb.render('website_mobile_app_list_order_classification',{
					'classifications': 'history',
					'order_datas': self.order_datas['history'],
					'user_group' : self.user['user_group']
				}));
				addEventListOrder();
			});
			$("#website_mobile_app_tab_pending_order").click();
			initOrderFilter();
		});
	});

	function initOrderFilter() {
		$(".accordion").click(function(event) {
			$(this).toggleClass("active");
			var detail = $(this).next();
			if (detail.css("maxHeight") != "0px"){
				detail.css("maxHeight", "0px");
			} else {
				detail.css("maxHeight", detail.prop("scrollHeight")+ "px");
			}
		});

		$('#button_filter').click(function(event) {
			var order_number = $('#filter_order_number').val();
			var booker_name = $('#filter_booker').val();
			var driver_name = $('#filter_driver').val();
			var vehicle_name = $('#filter_vehicle').val();
			$.get('/mobile_app/fetch_orders/' + JSON.stringify({
				'order_name': order_number,
				'booker_name': booker_name,
				'driver_name': driver_name,
				'vehicle_name': vehicle_name,
			}), null, function(data){
				var response = JSON.parse(data);
				self.order_datas = response['list_order'];
				$("#website_mobile_app_tab_pending_order").click();
			});
		});
	};

	function addEventListOrder() {
		$('.btn_approve_order').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			order_id = target.attr("id_order");
			onclick_button_approve_order(order_id);
		});

		$('.btn_reject_order').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			order_id = target.attr("id_order");
			onclick_button_reject_order(order_id);
		});

		$(".list_order").click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			self.index_click_order = target.attr("index_order");
			var classifications_order = target.attr("classification_order");
			onclick_list_order_detail_order(self.index_click_order, classifications_order);
		});

		$('#dialog_order_detail_container').click(function(event){
			event.stopPropagation();
		});

		$('.btn_add_quota').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			au_id = target.attr("id_au");
			contract_id = target.attr("id_contract");
			yellow_limit = target.attr("yellow_limit");
			red_limit = target.attr("red_limit");
			onclick_button_request_change_quota(au_id, contract_id, yellow_limit, red_limit);
		});
	};

	//Order Detail ===============================================================
	function onclick_list_order_detail_order(index_order, classifications_order) {
		order_data = self.order_datas[classifications_order][index_order];
		//Render Dialog
		$("#dialog_order_detail_container", self).html(qweb.render('dialog_order_detail',{
			'user_group': self.user['user_group'],
			'classification_value': classifications_order,
			'id': order_data.id,
			'name': order_data.name,
			'state': order_data.state,
			'pin': order_data.pin,
			'state_name': order_data.state_name,
			'request_date':  order_data.request_date,
			'order_by_name':  order_data.order_by_name,
			'start_planned_date': order_data.start_planned_date,
			'finish_planned_date':  order_data.finish_planned_date,
			'assigned_vehicle_name': order_data.assigned_vehicle_name,
			'assigned_driver_name': order_data.assigned_driver_name,
			'origin_location': order_data.origin_location,
			'origin_area_name': order_data.origin_area_name,
			'dest_location': order_data.dest_location,
			'dest_area_name': order_data.dest_area_name,
			'service_type': order_data.service_type,
			'service_type_name': order_data.service_type_name,
			'order_by_name': order_data.order_by_name,
			'over_quota_status': order_data.over_quota_status,
			'order_usage': order_data.alloc_unit_usage,
			'red_limit': order_data.red_limit,
			'yellow_limit': order_data.yellow_limit,
			'maintained_by': order_data.maintained_by,
			'au_id': order_data.au_id,
			'au_name': order_data.au_name,
			'list_passenger' : order_data.list_passenger,
			'contract_id': order_data.contract_id,
			'contract_name': order_data.contract_name,
			'type': order_data.type,
			'type_name': order_data.type_name,
		}));

		// Tampilkan Dialog
		var modal = $("#modalOrderDetail");
		modal.css("display", "block");

		// Button Close Dialog
		$(".close_dialog").click(function(event) {
			modal.css("display", "none");
		});

		$('.btn_change_planned_start_time').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			order_id = target.attr("id_order");
			onclick_button_change_planned_start_time(order_id, self.order_datas);
		});
		$('.btn_edit_order').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			order_id = target.attr("id_order");
			onclick_button_edit_order(order_id);
		});
		$('.btn_cancel_order').click(function(event) {
			event.stopPropagation();
			var target = $(event.target);
			order_id = target.attr("id_order");
			onclick_button_cancel_order(order_id);
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

	function onclick_button_change_planned_start_time(order_id, order_datas) {
		filtered_order_datas = [];
		filtered_order_datas.push.apply(filtered_order_datas, order_datas['pending']);
		filtered_order_datas.push.apply(filtered_order_datas, order_datas['ready']);
		$.each(filtered_order_datas, function(index, order_data) {
			if(parseInt(order_data['id']) === parseInt(order_id)) {
				$("#change_planned_start_time", self).html(qweb.render('dialog_change_planned_start_time',{
					'order_id': order_id,
					'planned_start_time_old': new Date().addHours(1).toDatetimeString(),
				}));
				// Tampilkan Dialog
				var modal = $("#dialog_change_planned_start_time");
				modal.css("display", "block");

				// Button Close Dialog
				$(".close_dialog").click(function(event) {
					modal.css("display", "none");
				});

				$('#dialog_change_planned_start_time').click(function(event){
					event.stopPropagation();
				})

				$('.btn_save_change_order').click(function(event) {
					var target = $(event.target);
					order_id = target.attr("id_order");
					onclick_button_save_change_planned_start_time(order_id);
				});
				$('.btn_cancel_change_order').click(function(event) {
					modal.css("display", "none");
				});
				return false;
			}
		});
	};

	function onclick_button_edit_order(order_id) {
		$.get('/mobile_app/get_required_edit_order/' + JSON.stringify({
			'order_id': parseInt(order_id),
		}), null, function(data){
			var response = JSON.parse(data);
			var order_type = response['order_type'];
			self.to_cities = response['route_to'];
			self.user = response['user'];
			self.user['user_group'] = response['user_group'];
			self.contract_datas = response['contract_datas'];

			var fleet_type_datas = [];
			var units = [];
			var district_from = [];
			var route_from = [];
			if (self.contract_datas.length != 0) {
				fleet_type_datas = self.contract_datas[0].fleet_type;
				units = self.contract_datas[0].units;
				district_from = self.contract_datas[0].districts;
				if (self.contract_datas[0].districts.length != 0) {
					route_from = self.contract_datas[0].districts[0].areas;
				}
			}
			var to_areas = [];
			if (self.to_cities[0].districts.length != 0) {
				to_areas = self.to_cities[0].districts[0].areas;
			}

			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'order_id': order_id,
				'user_group': self.user['user_group'],
				// Information
				'contract_datas': self.contract_datas,
				'fleet_type_datas': fleet_type_datas,
				'units': units,
				'order_types': order_type,
				// Route
				'from_districts': district_from,
				'from_areas': route_from,
				'to_cities': self.to_cities,
				'to_districts': self.to_cities[0].districts,
				'to_areas': to_areas,
				// Passenger
				// Time
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
				'create_mode': false,
			}));

			$('#create_order_contract').change(function(){
				onchange_create_order_contract($(this).val());
			});

			$('#create_order_route_from_district').change(function(){
				onchange_create_order_route_from_district($(this).val());
			});

			$('#create_order_route_to_city').change(function(){
				onchange_create_order_route_to_city($(this).val());
			});

			$('#create_order_route_to_district').change(function(){
				onchange_create_order_route_to_district($(this).val());
			});

			$('#btn_create_order').click(function(){
				onclick_create_order_button('create', 0);
			});

			$('#btn_add_passenger').click(function(){
				onclick_create_order_add_passenger();
			});

			var order_data = response['order_data'];
			$('#create_order_contract').val(""+order_data.customer_contract_id).change();
			$('#create_order_info_fleet_type').val(""+order_data.fleet_type_id).change();
			$('#create_order_info_unit').val(""+order_data.alloc_unit_id).change();
			$('#create_order_info_type').val(""+order_data.order_type_by_order).change();
			$('#create_order_route_from_district').val(""+order_data.origin_district_id).change();
			$('#create_order_route_from_area').val(""+order_data.origin_area_id).change();
			$('#create_order_route_from_location').val(""+order_data.origin_location).change();
			$('#create_order_route_to_city').val(""+order_data.dest_city_id).change();
			$('#create_order_route_to_district').val(""+order_data.dest_district_id).change();
			$('#create_order_route_to_area').val(""+order_data.dest_area_id).change();
			$('#create_order_route_to_location').val(""+order_data.dest_location).change();

			me_exist = false;
			var ckb_i_am_passenger = $('#ckb_i_am_passenger');
			$.each(order_data.passengers, function(index, passenger) {
				if(!passenger.is_orderer) {
					add_passenger_to_table(passenger.name, passenger.phone_no, passenger.id);
				} else {
					if(order_data.is_orderer_passenger) {
						ckb_i_am_passenger.click(function(){
							onclick_create_order_i_am_passenger("");
						});
						ckb_i_am_passenger.click();
						onclick_create_order_i_am_passenger(passenger.id);
					}
				}
			});

			if(!me_exist) {
				ckb_i_am_passenger.click(function(){
					onclick_create_order_i_am_passenger("");
				});
			}

			$('.btn_save_edit_order').click(function(event) {
				var target = $(event.target);
				order_id = target.attr("id_order");
				onclick_create_order_button('edit', order_id);
			});
			$('.btn_cancel_edit_order').click(function(event) {
				$('#website_mobile_app_menu_list_orders').click();
			});
		});
	};

	function onclick_button_cancel_order(order_id) {
		var confirmation = confirm('Are you sure to cancel this order?');
		if(confirmation === true) {
			$.ajax({
				dataType: "json",
				url: '/mobile_app/cancel_order/' + order_id,
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
		}
	};

	function onclick_button_save_change_planned_start_time(order_id) {
		var new_planned_start_time = $('#change_order_start_planned_new').val();
		$.ajax({
			dataType: "json",
			url: '/mobile_app/change_planned_start_time/' + JSON.stringify({
				'order_id': order_id,
				'new_planned_start_time': new_planned_start_time,
			}),
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
		onclick_menu('#website_mobile_app_menu_list_shuttle', 'Shuttle');
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
		onclick_menu('#website_mobile_app_menu_change_password', 'Change Password');
		$("#main_container", self).html(qweb.render('website_mobile_app_change_password'));
		$('#btn_change_password').click(function(){
			onclick_change_password_button();
		});
	});

// LIST CONTRACT ============================================================================================================

	$('#website_mobile_app_menu_list_contract').click(function() {
		onclick_menu('#website_mobile_app_menu_list_contract', 'Contracts');
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
				onclick_menu('.list_contract', self.contract_datas[self.index_click_contract].name);
				$("#detail_contract_container", self).html(qweb.render('website_mobile_app_detail_contract',{
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
		$("#list_contract_container").hide();
		$("#detail_contract_container").show();
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
							$(".list_quota_usage").click(function(event){
								event.stopPropagation();
								onclick_usage_control();
								self.current_au_name = $(this).attr("au_name");
								onclick_menu('.list_quota_usage', self.current_au_name);
								onclick_usage_control_quota($(this).attr("value"));
							});
							$(".quota_btn_request_change_quota").click(function(event){
								event.stopPropagation();
								var au_id = $(this).attr("au_id");
								// Dapatkan Quota dari au_id
								$.each(quota_list, function(index, quota){
									if(quota['au_id'] == au_id){
										red_limit = quota['red_limit'];
										yellow_limit = quota['yellow_limit'];
									}
								});
								onclick_button_request_change_quota(au_id, $(this).attr("contract_id"), yellow_limit, red_limit);
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

				$("#detail_contract_main_container", self).html(qweb.render('website_mobile_app_detail_control_usage', {
					'au_name': self.current_au_name,
				}));
				
				$("#website_mobile_app_tab_usage_control_information", self).click(function(event) {
					onclick_tab_detail_au("#website_mobile_app_tab_usage_control_information");
					$(".usage_control_container", self).html(qweb.render('website_mobile_app_usage_control_information',{
						'au_name': self.current_au_name,
						'total_usage': quota.total_usage,
						'yellow_limit': quota.yellow_limit,
						'red_limit': quota.red_limit,
						'total_request_nominal': quota.total_request_nominal,
						'total_request_time': quota.total_request_time,
						}));
				});
				
				$("#website_mobile_app_tab_usage_control_request_history", self).click(function(event) {
					onclick_tab_detail_au("#website_mobile_app_tab_usage_control_request_history");
					$(".usage_control_container", self).html(qweb.render('website_mobile_app_usage_control_request_history',{
						'user_group': self.user['user_group'],
						'classifications': classifications,
						'limit_requests': quota.limit_requests,
					}));
					event_limit_request_list();
				});

				$("#website_mobile_app_tab_usage_control_information", self).click();
			});
		};
		
		function event_limit_request_list() {
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
		}

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
	};

	function onclick_button_request_change_quota(au_id, contract_id, yellow_limit, red_limit) {
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

// LOG OUT ============================================================================================================

	$('#website_mobile_app_menu_log_out').click(function() {
		var pathname = window.location.pathname;
		var url      = window.location.href;
		url = url.replace(pathname, '');
		url += "/web/session/logout?redirect=/";
		window.location.replace(url);
	});
});
