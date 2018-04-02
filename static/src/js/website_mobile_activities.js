var mobile_app_activity_definition = {

//MAIN MENU ----------------------------------------------------------------------------------------------------------------

	'univmobile_actv_main': {
		title: 'UNIVERSAL',
		back_intent_id: '',
		qweb_template_id: 'univmobile_main_menu',
		onload_callback: function(activity_data, intent_data) {
		},
	},

//CHANGE PASSWORD ----------------------------------------------------------------------------------------------------------

	'univmobile_actv_chpwd': {
		title: 'Change Password',
		back_intent_id: 'univmobile_intent_main',
		qweb_template_id: 'univmobile_chpwd',
		onload_callback: function(activity_data, intent_data) {
			mobile_app.form.initialize("#chpwd_form", {
				action: '/mobile_app/change_password/',
				validate_and_prepare: function(form_object) {
					var valid = true;
					var form_data = mobile_app.form.get_values(form_object);
				//semua field harus diisi
					if (valid && form_data['old_password'] == '' || form_data['new_password'] == 0 || form_data['new_password_retype'] == '') {
						alert("Please fill in all fields.");
						valid = false;
					}
				//password baru dan retype nya harus sama
					if (valid && form_data['new_password'] != form_data['new_password_retype']) {
						alert("New Password and Retype Password does not match.`");
						valid = false;
					}
					return {
						valid: valid,
						form_data: form_data,
					}
				},
				after_success: function(response) {
					logout();
				},
			});
		}
	},

//SHUTTLE ------------------------------------------------------------------------------------------------------------------

	'univmobile_actv_shuttle': {
		title: 'Shuttle',
		back_intent_id: 'univmobile_intent_main',
		qweb_template_id: 'univmobile_shuttle',
		onload_callback: function(activity_data, intent_data) {
		//list shuttle
			var shuttle_list_view = mobile_app.list_view({
				filter_def: {
					filter_container: ".univmobile_shuttle .filter-container",
					filter_qweb: "univmobile_shuttle_filter_form",
					filter_event: "onchange",
					on_filter: function(filter_data) {
					//data udah ada di data manager, hasil load contract shuttle yang buat 
					//filter. so kita tinggal ambil data shuttlenya dan inject ke dataset shuttle_by_day
						var selected_contract_id = parseInt(filter_data.list_shuttle_contract);
					//pisahkan data per hari berdasarkan shuttle contract yang dipilih
					//hal ini per "persyaratan" dari qweb templatnya (lihat template univmobile_shuttle_list_row)
						var shuttle_data = {
							'0': { 'day': 'Monday', 'day_value': [] },
							'1': { 'day': 'Tuesday', 'day_value': [] },
							'2': { 'day': 'Wednesday', 'day_value': [] },
							'3': { 'day': 'Thursday', 'day_value': [] },
							'4': { 'day': 'Friday', 'day_value': [] },
							'5': { 'day': 'Saturday', 'day_value': [] },
							'6': { 'day': 'Sunday', 'day_value': [] },
						};
						var contract_data = mobile_app.data_manager.get('shuttle_contracts');
						$.each(contract_data, function(index, row) {
							if (row.id == selected_contract_id) {
								$.each(row.shuttle_schedules_by_days, function(day_value, schedules) {
									shuttle_data[day_value]['day_value'] = schedules;
								})
							}
						});
					//injeeeect!!
						mobile_app.data_manager.refresh('shuttle_by_day', shuttle_data, true);
					},
				},
				container: ".univmobile_shuttle .list-container",
				row_qweb: "univmobile_shuttle_list_row",
			});
			mobile_app.data_manager.attach_view('shuttle_by_day', 'shuttle_contract_list', shuttle_list_view);
			shuttle_list_view.render_view();
		//filter contract di shuttle
			var shuttle_contract_select_view = mobile_app.select_view({
				container: ".univmobile_shuttle #list_shuttle_contract",
			//dari server ngambilnya semua kontrak, belum tentu yang shuttle. jadi harus di-"filter"
			//dulu di sini
				prepare_data: function(data) {
					var result = [];
					$.each(data, function(idx, row) {
						if (row.service_type == 'Shuttle') {
							result.push(row);
						}
					})
					return result;
				},
				after_refresh: function(data) {
					$(".univmobile_shuttle #list_shuttle_contract").change();
				}
			});
			mobile_app.data_manager.attach_view('shuttle_contracts', 'contract_filter', shuttle_contract_select_view);
		//load option filter contract
			mobile_app.data_manager.refresh('shuttle_contracts', {}, true);
		}
	},

//CONTRACT -----------------------------------------------------------------------------------------------------------------

	'univmobile_actv_contract': {
		title: 'Contracts',
		back_intent_id: 'univmobile_intent_main',
		qweb_template_id: 'univmobile_contract',
		onload_callback: function(activity_data, intent_data) {
		//list kontrak
			var contract_list_view = mobile_app.list_view({
				container: ".univmobile_contract .list-container",
				row_qweb: "univmobile_contract_list_row",
				prepare_data: function(data) {
					var new_data = [];
					$.each(data['list_contract'], function(idx, row) {
						row['user_group'] = data['user_group'];
						new_data.push(row);
					});
					return new_data;
				},
			});
			mobile_app.data_manager.attach_view('contracts', 'contract_list', contract_list_view);
			contract_list_view.render_view();
			mobile_app.data_manager.refresh('contracts', {}, true);
		}
	},

//CONTRACT DETAIL ----------------------------------------------------------------------------------------------------------

	'univmobile_actv_contract_detail': {
		title: 'Contract Detail',
		back_intent_id: 'univmobile_intent_contract',
		onload_callback: function(activity_data, intent_data) {
			var contract_id = intent_data.data_id;
			var contracts = mobile_app.data_manager.get("contracts");
			$.each(contracts.list_contract, function(idx, contract) {
				if (contract.id == contract_id) {
					mobile_app.cache['selected_contract'] = contract;
					return false;
				} 
			});
			var selected_contract = mobile_app.cache['selected_contract'];
			selected_contract.user_group = contracts.user_group;
		//view detail
			var contract_detail_view = mobile_app.detail_view({
				container: "#chjs_mobile_web_container",
				detail_qweb: "univmobile_contract_detail_form",
				after_refresh: function(data) {
				//otomatis pilih tab pertama
					$("#chjs_mobile_web_container ul.nav li a").eq(0).click();
				//view detail usage control
					if (data.service_type == 'By Order') {
						var usage_control_view = mobile_app.list_view({
							container: "#contract_detail_usage_control",
							row_qweb: "univmobile_contract_detail_usage_control_row",
							prepare_data: function(data) {
								var result = []
								$.each(data, function(idx, row) {
									row['yellow_limit_formatted'] = insert_thousand_seps(row['yellow_limit'].toString());
									row['red_limit_formatted'] = insert_thousand_seps(row['red_limit'].toString());
									row['current_usage_formatted'] = insert_thousand_seps(row['current_usage'].toString());
									row['total_request_nominal_formatted'] = insert_thousand_seps(row['total_request_nominal'].toString());
									result.push(row);
								});
								return result;
							},
						});
						mobile_app.data_manager.attach_view('contract_detail_usage_control', 'contract_detail_usage_control_list', usage_control_view);
					//load list usage control
						mobile_app.data_manager.refresh('contract_detail_usage_control', [contract_id], true);
					}
				//view detail quota changes
					if (data.service_type == 'By Order') {
						var quota_changes_view = mobile_app.list_view({
							container: "#contract_detail_quota_changes",
							row_qweb: "univmobile_contract_detail_quota_changes_row",
							prepare_data: function(data) {
								var result = {
									'pending': {
										'section': 'pending',
										'title': 'Pending',
										'data': [],
									},
									'history': {
										'section': 'history',
										'title': 'Approved/Rejected',
										'data': [],
									},
								}
								$.each(data, function(section, section_data) {
									$.each(section_data, function(idx, change_data) {
										var detail_text = openerp._t("Requested for {0} unit by {1} at {2}.");
										detail_text = detail_text.replace("{0}", change_data.name);
										detail_text = detail_text.replace("{1}", change_data.request_by);
										detail_text = detail_text.replace("{2}", change_data.request_date);
										var confirm_text;
										if (change_data.state != 'draft') {
											confirm_text = openerp._t("{0} by {1} at {2}{3}.");
											confirm_text = confirm_text.replace("{0}", (change_data.state == 'approved') ? 'Approved' : 'Rejected');
											confirm_text = confirm_text.replace("{1}", change_data.confirm_by);
											confirm_text = confirm_text.replace("{2}", change_data.confirm_date);
											confirm_text = confirm_text.replace("{3}", (change_data.state == 'rejected' && change_data.reject_reason ? ' ('+change_data.reject_reason+')' : ''));
										} else {
											confirm_text = ""
										}
										if (change_data.yellow_limit_new > 0) {
											$.extend(change_data, {
												'yellow_limit_formatted': insert_thousand_seps(change_data['yellow_limit_new'].toString()),
												'yellow_limit_old': insert_thousand_seps(change_data['yellow_limit_old'].toString()),
												'yellow_limit_final': insert_thousand_seps((change_data['yellow_limit_old'] + change_data['yellow_limit_new']).toString()),
											});
										}
										if (change_data.red_limit_new > 0) {
											$.extend(change_data, {
												'red_limit_formatted': insert_thousand_seps(change_data['red_limit_new'].toString()),
												'red_limit_old': insert_thousand_seps(change_data['red_limit_old'].toString()),
												'red_limit_final': insert_thousand_seps((change_data['red_limit_old'] + change_data['red_limit_new']).toString()),
											});
										}
										$.extend(change_data, {
											'request_detail': detail_text,
											'confirm_detail': confirm_text,
											'user_group': selected_contract.user_group,
										});
										result[section]['data'].push(change_data);
									});
								});
							//nitip: tampilin notif berisi jumlah pending di tab Quota Changes
								var pending_count = result['pending']['data'].length;
								if (pending_count > 0){
									$("#contract_detail_quota_changes_notif").html(pending_count);
								}
								return result;
							},
						});
						mobile_app.data_manager.attach_view('contract_detail_quota_changes', 'contract_detail_quota_changes', quota_changes_view);
					//load list quota changes
						mobile_app.data_manager.refresh('contract_detail_quota_changes', [contract_id], true);
					}

				},
			});
			mobile_app.data_manager.attach_view('contract_detail', 'contract_detail', contract_detail_view);
		//load option filter contract
			mobile_app.data_manager.refresh('contract_detail', selected_contract, true);
		}
	},

//CONTRACT DETAIL USAGE CONTROL --------------------------------------------------------------------------------------------

	'univmobile_actv_request_quota_change': {
		title: 'Request Quota Change',
		onload_callback: function(activity_data, intent_data) {
		//form request quota change
			var contract_request_quota_change = mobile_app.detail_view({
				container: "#chjs_mobile_modal_content",
				detail_qweb: "univmobile_request_quota_change",
				prepare_data: function(data) {
					data['yellow_limit_formatted'] = insert_thousand_seps(data['yellow_limit'].toString());
					data['red_limit_formatted'] = insert_thousand_seps(data['red_limit'].toString());
					return data;
				},
				after_refresh: function(data) {
					var form_object = $("#request_quota_change_form");
					mobile_app.form.initialize("#request_quota_change_form", {
						action: '/mobile_app/request_quota_changes/',
						validate_and_prepare: function(form_object) {
							var valid = true;
							var form_data = mobile_app.form.get_values(form_object);
						//harus isi minimal 1, jangan dua2nya kosong
							if ((form_data['new_yellow_limit'] == '' || form_data['new_yellow_limit'] == 0) && (form_data['new_red_limit'] == '' || form_data['new_red_limit'] == 0)) {
								alert("Please fill in at least the new yellow limit or the red one.");
								valid = false;
							}
						//kalau old yellow limit ditambah sama yellow limit baru jadi > dari red limit, cegah save
							var new_yellow_limit = form_data['old_amount_yellow'] + form_data['new_yellow_limit'];
							var new_red_limit = form_data['old_amount_red'] + form_data['new_red_limit'];
							if (new_yellow_limit >= new_red_limit) {
								alert("New yellow limit cannot be bigger than red limit.");
								valid = false;
							}
						//tambahin request by
							form_data['request_by'] = parseInt(mobile_app.app_data.user_id);
							return {
								valid: valid,
								form_data: form_data,
							}
						},
						after_success: function(response) {
							mobile_app.close_modal();
						//reload detail kontrak
							mobile_app.intent('univmobile_intent_contract_detail', {
								data_id: mobile_app.cache['selected_contract'].id,
							});
						},
						events: {
							"change #new_yellow_limit": function(event) {
								var form_values = mobile_app.form.get_values(form_object);
								var new_amount = form_values['old_amount_yellow'] + form_values['new_yellow_limit'];
								new_amount = insert_thousand_seps(new_amount.toString());
								$("#new_amount_yellow").html(new_amount); 
							},
							"change #new_red_limit": function(event) {
								var form_values = mobile_app.form.get_values(form_object);
								var new_amount = form_values['old_amount_red'] + form_values['new_red_limit'];
								new_amount = insert_thousand_seps(new_amount.toString());
								$("#new_amount_red").html(new_amount); 
							},
						},
					});
				}
			});
			mobile_app.data_manager.attach_view('contract_detail_request_quota_change', 'contract_detail_request_quota_change', contract_request_quota_change);
			mobile_app.data_manager.refresh('contract_detail_request_quota_change', intent_data, true);
		}
	},

	'univmobile_actv_request_quota_reject': {
		title: 'Reject Quota Change Request',
		onload_callback: function(activity_data, intent_data) {
		//form request quota change
			var contract_request_quota_reject = mobile_app.detail_view({
				container: "#chjs_mobile_modal_content",
				detail_qweb: "univmobile_request_quota_reject",
				after_refresh: function(data) {
					mobile_app.form.initialize("#request_quota_reject_form", {
						action: '/mobile_app/reject_quota_changes/',
						validate_and_prepare: function(form_object) {
							var valid = true;
							var form_data = mobile_app.form.get_values(form_object);
						//harus isi minimal 1, jangan dua2nya kosong
							if (form_data['reject_reason'] == '') {
								alert("Please fill in reject reason.");
								valid = false;
							}
							return {
								valid: valid,
								form_data: form_data,
							}
						},
						after_success: function(response) {
							mobile_app.close_modal();
						//reload detail kontrak
							mobile_app.intent('univmobile_intent_contract_detail', {
								data_id: mobile_app.cache['selected_contract'].id,
							});
						},
					});
				}
			});
			mobile_app.data_manager.attach_view('contract_detail_request_quota_reject', 'contract_detail_request_quota_reject', contract_request_quota_reject);
			mobile_app.data_manager.refresh('contract_detail_request_quota_reject', intent_data, true);
		}
	},

	'univmobile_actv_request_quota_approve': {
		title: 'Approve Quota Change Request',
		confirm_text: 'Are you sure to approve this quota change request? Users of corresponding unit will be able to book more vehicles above default monthly limits.',
		action: '/mobile_app/approve_quota_changes/',
		action_payload: function(intent_data) {
		//harus mereturn array of string. array ini nantinya akan di-join pakai /. 
		//gunakan JSON.stringify untuk data yang berupa dictionary
			return [intent_data.data_id.toString()];
		},
		is_alert_message: true,
		after_success: function(response) {
		//reload detail kontrak
			mobile_app.intent('univmobile_intent_contract_detail', {
				data_id: mobile_app.cache['selected_contract'].id,
			});
		}
	},

//ORDERS -----------------------------------------------------------------------------------------------------------------

	'univmobile_actv_order': {
		title: 'Orders',
		back_intent_id: 'univmobile_intent_main',
		qweb_template_id: 'univmobile_order',
		onload_callback: function(activity_data, intent_data) {
			//list order
			var order_list_view = mobile_app.list_view({
				container: ".univmobile_order .list-container",
				row_qweb: "univmobile_order_list_row",
				prepare_data: function(data) {
					var new_data = [];
					$.each(data['list_order'], function(idx, row) {
						row['user_group'] = data['user_group'];
						new_data.push(row);
					});
					return [new_data];
				},
			});

			function onclick_tab_order(event) {
				$('.website_mobile_app_tab_pending_order').css("background-color", "#337ab7");
				$('.website_mobile_app_tab_ready_order').css("background-color", "#337ab7");
				$('.website_mobile_app_tab_running_order').css("background-color", "#337ab7");
				$('.website_mobile_app_tab_history_order').css("background-color", "#337ab7");
				$('.' + event.target.className).css("background-color", "#286090");
			};

			$('.website_mobile_app_tab_pending_order').click(function(event) {
				onclick_tab_order(event);
				mobile_app.data_manager.attach_view('order_pending', 'order_list', order_list_view);
				mobile_app.data_manager.refresh('order_pending', {}, true);
			});
			$('.website_mobile_app_tab_ready_order').click(function(event) {
				onclick_tab_order(event);
				mobile_app.data_manager.attach_view('order_ready', 'order_list', order_list_view);
				mobile_app.data_manager.refresh('order_ready', {}, true);
			});
			$('.website_mobile_app_tab_running_order').click(function(event) {
				onclick_tab_order(event);
				mobile_app.data_manager.attach_view('order_running', 'order_list', order_list_view);
				mobile_app.data_manager.refresh('order_running', {}, true);
			});
			$('.website_mobile_app_tab_history_order').click(function(event) {
				onclick_tab_order(event);
				mobile_app.data_manager.attach_view('order_history', 'order_list', order_list_view);
				mobile_app.data_manager.refresh('order_history', {}, true);
			});
			$('.website_mobile_app_tab_pending_order').click();
			order_list_view.render_view();
		}
	},

	'univmobile_actv_book_vehicle': {
		title: 'Book Vehicle',
		back_intent_id: 'univmobile_intent_main',
		onload_callback: function(activity_data, intent_data) {
		//form request book vehicle
			var data_book_vehicle = mobile_app.detail_view({
				container: "#chjs_mobile_web_container",
				detail_qweb: "univmobile_book_vehicle",
				prepare_data: function(data) {
					mobile_app.cache['contract_datas'] = data['contract_datas'];
					mobile_app.cache['route_to'] = data['route_to'];
					mobile_app.cache['user'] = data['user'];
					mobile_app.cache['user']['user_group'] = data['user_group'];

					data['start_planned_date'] = new Date().addHours(1).toDatetimeString();
                    data['finish_planned_date'] = new Date().addHours(2).toDatetimeString();

					return data;
				},
				after_refresh: function(data) {
					var form_object = $("#book_vehicle_form");
					mobile_app.form.initialize("#book_vehicle_form", {
						action: '/mobile_app/create_edit_order/',
						validate_and_prepare: function(form_object) {
							var valid = true;
							var form_data = mobile_app.form.get_values(form_object);
							valid = is_valid_form_data_order(form_data);
							console.log(valid);
							form_data['mode_create_or_edit'] = 'create';
							return {
								valid: valid,
								form_data: form_data,
							}
						},
						after_success: function(response) {
						//reload list order
							console.log(response);
							if (response.success){
								mobile_app.intent('univmobile_intent_order', {});
							}
						},
						events: {
							"change #contract_id": function(event) {
								var contract_id = $(this).val();
								onchange_book_vehicle_contract_id(contract_id);
							},
							"change #book_vehicle_route_from_district": function(event) {
								var district_id = $(this).val();
								onchange_book_vehicle_from_district(district_id);
							},
							"change #to_city_id": function(event) {
								var city_id = $(this).val();
								onchange_book_vehicle_to_city(city_id);
							},
							"change #book_vehicle_route_to_district": function(event) {
								var district_id= $(this).val();
								onchange_book_vehicle_to_district(district_id);
							},
							"click #i_am_passenger": function(event) {
								onclick_create_order_i_am_passenger("");
							},
							"click #btn_add_passenger": function(event) {
								onclick_book_vehicle_btn_add_passenger();
							},
						},
					});
					$('#i_am_passenger').click();
					$('#i_am_passenger').click();
					$('#i_am_passenger').prop('checked', true);
				}
			});

			mobile_app.data_manager.attach_view('book_vehicle', 'book_vehicle', data_book_vehicle);
			mobile_app.data_manager.refresh('book_vehicle', {}, true);
		}
	},

	'univmobile_actv_order_detail': {
		title: 'Order Detail',
		back_intent_id: 'univmobile_intent_order',
		onload_callback: function(activity_data, intent_data) {
			var order_detail_view = mobile_app.detail_view({
				container: "#chjs_mobile_web_container",
				detail_qweb: "univmobile_order_detail",
			})
			mobile_app.cache['selected_order_id'] = intent_data['data_id'];
			mobile_app.data_manager.attach_view('order_detail', 'order_detail', order_detail_view);
			mobile_app.data_manager.refresh('order_detail', intent_data, true);
		}
	},

	'univmobile_actv_change_start_planned_time': {
		title: 'Change Start Planned Time',
		back_intent_id: 'univmobile_intent_order_detail',
		onload_callback: function(activity_data, intent_data) {
			var change_start_planned_view = mobile_app.detail_view({
				container: "#chjs_mobile_modal_content",
				detail_qweb: "univmobile_change_start_planned_time",
				after_refresh: function(data) {
					mobile_app.form.initialize("#change_start_planned_time_form", {
						action: '/mobile_app/change_planned_start_time/',
						validate_and_prepare: function(form_object) {
							var valid = true;
							var form_data = mobile_app.form.get_values(form_object);
							if (form_data['change_order_start_planned_new'] == '') {
								alert("Please fill in new start planned time.");
								valid = false;
							}
							return {
								valid: valid,
								form_data: form_data,
							}
						},
						after_success: function(response) {
							mobile_app.close_modal();
							mobile_app.intent('univmobile_intent_order_detail', {
								data_id: mobile_app.cache['selected_order_id'],
							});
						},
					});
				}
			});
			mobile_app.data_manager.attach_view('order_detail', 'order_edit', change_start_planned_view);
			mobile_app.data_manager.refresh('order_detail', intent_data, true);
		}
	},

	'univmobile_actv_edit_order': {
		title: 'Edit Order',
		back_intent_id: 'univmobile_intent_order_detail',
		onload_callback: function(activity_data, intent_data) {
			var edit_order_view = mobile_app.detail_view({
				container: "#chjs_mobile_modal_content",
				detail_qweb: "univmobile_book_vehicle",
				prepare_data: function(data) {
					console.log(data);
					mobile_app.cache['contract_datas'] = data['contract_datas'];
					mobile_app.cache['route_to'] = data['route_to'];
					mobile_app.cache['user'] = data['user'];
					mobile_app.cache['order_data'] = data['order_data'];
					mobile_app.cache['user']['user_group'] = data['user_group'];

					console.log(mobile_app.cache['order_data']);
					data['start_planned_date'] = mobile_app.cache['order_data'].start_planned_date_format_input;
					data['finish_planned_date'] = mobile_app.cache['order_data'].finish_planned_date_format_input;
					return data;
				},
				after_refresh: function(data) {
					mobile_app.form.initialize("#book_vehicle_form", {
						action: '/mobile_app/create_edit_order/',
						validate_and_prepare: function(form_object) {
							var valid = true;
							var form_data = mobile_app.form.get_values(form_object);
							valid = is_valid_form_data_order(form_data);
							form_data['mode_create_or_edit'] = 'edit';
							console.log(form_data);
							return {
								valid: valid,
								form_data: form_data,
							}
						},
						after_success: function(response) {
							if (response.success){
								mobile_app.close_modal();
								mobile_app.intent('univmobile_intent_order_detail', {
									data_id: mobile_app.cache['selected_order_id'],
								});
							}
						},
						events: {
							"change #contract_id": function(event) {
								var contract_id = $(this).val();
								onchange_book_vehicle_contract_id(contract_id);
							},
							"change #book_vehicle_route_from_district": function(event) {
								var district_id = $(this).val();
								onchange_book_vehicle_from_district(district_id);
							},
							"change #to_city_id": function(event) {
								var city_id = $(this).val();
								onchange_book_vehicle_to_city(city_id);
							},
							"change #book_vehicle_route_to_district": function(event) {
								var district_id= $(this).val();
								onchange_book_vehicle_to_district(district_id);
							},
							"click #i_am_passenger": function(event) {
								onclick_create_order_i_am_passenger("");
							},
							"click #btn_add_passenger": function(event) {
								onclick_book_vehicle_btn_add_passenger();
							},
						},
					});
					var order_data = mobile_app.cache['order_data'];
					$('#contract_id').val(""+order_data.customer_contract_id).change();
					$('#fleet_type_id').val(""+order_data.fleet_type_id).change();
					$('#unit_id').val(""+order_data.alloc_unit_id).change();
					$('#type_id').val(""+order_data.order_type_by_order).change();
					$('#book_vehicle_route_from').val(""+order_data.origin_district_id).change();
					$('#from_area_id').val(""+order_data.origin_area_id).change();
					$('#from_location').val(""+order_data.origin_location).change();
					$('#to_city_id').val(""+order_data.dest_city_id).change();
					$('#book_vehicle_route_to_district').val(""+order_data.dest_district_id).change();
					$('#to_area_id').val(""+order_data.dest_area_id).change();
					$('#to_location').val(""+order_data.dest_location).change();
					$('#purpose_id').val(""+order_data.purpose_id).change();
					$('#other_purpose').val(""+order_data.other_purpose).change();

					var ckb_i_am_passenger = $('#ckb_i_am_passenger');
					console.log(order_data.passengers);
					$.each(order_data.passengers, function(index, passenger) {
						if(!passenger.is_orderer) {
							add_passenger_to_table(passenger.name, passenger.phone_no, passenger.id);
						} else {
							$('#i_am_passenger').click();
							$('#i_am_passenger').click();
							$('#i_am_passenger').prop('checked', true);
						}
					});
				}
			});
			mobile_app.data_manager.attach_view('order_edit', 'order_edit', edit_order_view);
			mobile_app.data_manager.refresh('order_edit', intent_data, true);
		}
	},
	
	'univmobile_actv_cancel_order': {
		title: 'Cancel Order',
		confirm_text: 'Are you sure to cancel this order? This cannot be undone.',
		action: '/mobile_app/cancel_order/',
		action_payload: function(intent_data) {
			return [intent_data.data_id.toString()];
		},
		is_alert_message: true,
		after_success: function(response) {
			mobile_app.intent('univmobile_intent_order_detail', {
				data_id: mobile_app.cache['selected_order_id'],
			});
		}
	},

};

// Function For Book / Edit Order -------------------------------------------------------------------------------------------------------------------

function onchange_book_vehicle_contract_id(contract_id){
	$.each(mobile_app.cache['contract_datas'], function(index, contract_data) {
		if (contract_data.id == contract_id) {
			// Update fleet selection
			$('#fleet_type_id').empty();
			$.each(contract_data.fleet_type, function(index, fleet_type_data) {
				$('#fleet_type_id').append(
					'<option value=' + fleet_type_data.id + '>' + fleet_type_data.name + '</option>');
			});
			// Update allocation unit selection
			$('#unit_id').empty();
			$.each(contract_data.units, function(index, unit) {
				$('#unit_id').append(
					'<option value=' + unit.id + '>' + unit.name + '</option>');
			});
			// Update route_from_disctrict selection
			$('#create_order_route_from_district').empty();
			$.each(contract_data.districts, function(index, district) {
				$('#create_order_route_from_district').append(
					'<option value=' + district.id + '>' + district.name + '</option>');
			});
		}
	});
};

function onchange_book_vehicle_from_district(district_id){
	var contract_id = $('#contract_id').val();
	$.each(mobile_app.cache['contract_datas'], function(index, contract_data) {
		if (contract_data.id == contract_id) {
			console.log(contract_data.districts);
			$.each(contract_data.districts, function(index, district) {
				if (district.id == district_id) {
					$('#from_area_id').empty();
					$.each(district.areas, function(index, area) {
						$('#from_area_id').append(
							'<option value=' + area.id + '>' + area.name + '</option>');
					});
				}
			});
		}
	});
};

function onchange_book_vehicle_to_city(city_id){
	$.each(mobile_app.cache['route_to'], function(index, city) {
		if (city.id == city_id) {
			$('#book_vehicle_route_to_district').empty();
			$('#to_area_id').empty();
			$.each(city.districts, function(index, district) {
				$('#book_vehicle_route_to_district').append(
					'<option value=' + district.id + '>' + district.name + '</option>');
			});
			$('#book_vehicle_route_to_district').change();
		}
	});
};

function onchange_book_vehicle_to_district(district_id){
	var city_id = $('#to_city_id').val();
	$.each(mobile_app.cache['route_to'], function(index, city) {
		if (city.id == city_id) {
			$.each(city.districts, function(index, district) {
				if (district.id == district_id) {
					$('#to_area_id').empty();
					$.each(district.areas, function(index, area) {
						$('#to_area_id').append(
							'<option value=' + area.id + '>' + area.name + '</option>');
					});
				}
			});
		}
	});
};

function onclick_create_order_i_am_passenger(exist_id) {;
	var checkbox = $("#i_am_passenger");
	mobile_app.cache['my_id'] = "passenger_me";
	if(checkbox.prop('checked')) {
		var table_passengers = $("#passengers");
		table_passengers.prepend(get_row_string_passenger(mobile_app.cache['user'].name,
			mobile_app.cache['user'].phone === false ? '-' : mobile_app.cache['user'].phone, mobile_app.cache['my_id'], exist_id, false));
	} else {
		$("#"+mobile_app.cache['my_id']).remove();
	}
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

function onclick_book_vehicle_btn_add_passenger(){
	var table_passengers = $("#passengers");
	table_passengers.append(get_row_string_passenger("", "", "", "", true));
	$(".btn_remove_passenger").click(function(){
		onclick_create_order_remove_passenger(this);
	});
}

function is_valid_form_data_order(form_data){
	var valid = true;
	if(mobile_app.cache['user']['user_group'] !== 'fullday_passenger') {
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
				if(row.attr("id") === mobile_app.cache['my_id']) {
					passenger_info['is_orderer'] = true;
				} else {
					passenger_info['is_orderer'] = false;
				}
				if(row.attr("exist_id") && (row.attr("exist_id").trim() !== false || row.attr("exist_id").trim() !== '')) {
					passenger_info['exist_id'] = row.attr("exist_id");
				}
				passengers.push(passenger_info);
			} else {
				alert('Please complete the passengers information, name and phone number are both required!');
				valid = false;
			}
		});

		form_data['passengers'] = passengers;
	}
	if (form_data['contract_id'] == '') {
		alert('You have no Contract!');
		valid = false;
	} else if (form_data['fleet_type_id'] == '') {
		alert('You have no Fleet!');
		valid = false;
	} else if (form_data['start_planned'] == '') {
		alert('Please input the start planned date correctly!');
		valid = false;
	} else if (form_data['finish_planned'] == '') {
		alert('Please input the finish planned date correctly!');
		valid = false;
	}

	if(mobile_app.cache['user']['user_group'] === 'booker' || mobile_app.cache['user']['user_group'] === 'approver') {
		if (!form_data['unit_id']) {
			alert('You have no Unit!');
			valid = false;
		} else if (!form_data['type_id']) {
			alert('Please select the Order Type!');
			valid = false;
		} else if (!form_data['from_area_id']) {
			alert('Please select the Origin Area!');
			valid = false;
		} else if (!form_data['from_location']) {
			alert('Please input the Origin Location!');
			valid = false;
		} else if (!form_data['to_city_id']) {
			alert('Please select the Destination City!');
			valid = false;
		} else if (!form_data['to_area_id']) {
			alert('Please select the Destination Area!');
			valid = false;
		} else if (!form_data['to_location']) {
			alert('Please input the Destination Location!');
			valid = false;
		}
	}
	return valid;
};

function add_passenger_to_table(name, phone, exist_id) {
	var table_passengers = $("#passengers");
	table_passengers.append(get_row_string_passenger(name, phone, '', exist_id, true));
	$(".btn_remove_passenger").click(function(){
		onclick_create_order_remove_passenger(this);
	});
};


