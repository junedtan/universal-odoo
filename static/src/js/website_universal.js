
Number.prototype.formatMoney = function(c, d, t){
var n = this, 
    c = isNaN(c = Math.abs(c)) ? 2 : c, 
    d = d == undefined ? "." : d, 
    t = t == undefined ? "," : t, 
    s = n < 0 ? "-" : "", 
    i = parseInt(n = Math.abs(+n || 0).toFixed(c)) + "", 
    j = (j = i.length) > 3 ? j % 3 : 0;
   return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
};

function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}

function alert_error(XMLHttpRequest, errorThrown) {
	response = XMLHttpRequest.responseText;
	console.log(response);
	index_start = response.indexOf("except_orm: ");
	index_end = response.indexOf("</pre>", index_start);
	exception_string = response.substring(index_start, index_end);

	index_start = exception_string.indexOf(", u'") + 4;
	index_end = exception_string.length-3;
	exception_string = exception_string.substring(index_start, index_end);
	if (exception_string.length == 0) {
		alert(errorThrown);
	} else {
		alert(exception_string);
	}
}

Date.prototype.toDatetimeString = function() {
    var currentdate = this;
    return pad(currentdate.getFullYear(),4) + "-"
		+ pad((currentdate.getMonth()+1),2)  + "-"
		+ pad(currentdate.getDate(),2) + "T"
		+ pad(currentdate.getHours(),2) + ":"
		+ pad(currentdate.getMinutes(),2) + ":"
		+ pad(currentdate.getSeconds(),2);
};

Date.prototype.addHours = function(h) {
   this.setTime(this.getTime() + (h*60*60*1000));
   return this;
}

function logout() {
	window.location.href = "/web/session/logout?redirect=/";
}

$(document).ready(function () {
	
	var message_timer;
	function display_message(container, message, type='info', timeout=5) { //timeout dalam detik
		var type_to_class = {
			'info': 'oe_callout_info',
			'error': 'oe_callout_danger',
		}
		var type_to_text = {
			'info': 'Info',
			'error': 'Error',
		}
		container.html(
			'<div class="oe_callout '+type_to_class[type]+'">'+
				'<h4>'+type_to_text[type]+'</h4>'+
				'<p>'+message+'</p>'+
			'</div>'
		).fadeIn();
		$("html, body").animate({scrollTop: 0}, 500);
		if (timeout > 0) {
			message_timer = setTimeout(function() {
				clear_message(container);
			},timeout*1000);
		}
	}
	
	function clear_message(container) {
		container.fadeOut().html('');
	}
	
	function daily_expense_change() {
		var expenses_total = 0;
		$("tr.expense_line").each(function() {
			var line = $(this);
			var qty = parseFloat(line.find("input[name='qty[]']").val());
			var unit_price = parseFloat(line.find("input[name='unit_price[]']").val());
			if (isNaN(qty) || !qty) qty = 0;
			if (isNaN(unit_price) || !unit_price) unit_price = 0;
			var subtotal = (qty * unit_price).formatMoney(0, ',', '.');
			line.prev().find('.expense_subtotal').html(subtotal);
			expenses_total += qty * unit_price;
		});
		$(".expenses_total").html(expenses_total.formatMoney(0, ',', '.'));
	}
	
	function daily_expense_serialize() {
		var product_id_hiddens = $("input[name='product_id[]']");
		var qty_inputs = $("input[name='qty[]']");
		var unit_price_inputs = $("input[name='unit_price[]']");
		var product_ids = [], qtys = [], unit_prices = [];
		qty_inputs.each(function(idx, dummy) {
			var qty = $.trim($(this).val());
			if (qty) {
				qtys.push(qty);
				unit_prices.push($(unit_price_inputs[idx]).val());
				product_ids.push($(product_id_hiddens[idx]).val());
			}
		});
		if ((product_ids.length) > 0 && (qtys.length) > 0) {
			product_ids = product_ids.join('|');
			qtys = qtys.join('|');
			unit_prices = unit_prices.join('|');
			return product_ids + '@' + qtys + '@' + unit_prices;
		} else {
			return '-';
		}
		
	}
	
//start/stop baik untuk driver maupun customer
	
	$('.universal_website_attendance').each(function () {
		
		var website_attendance = this;
		var message_container = $("#message_container");
		
		var mode = $("#attendance_container").data("mode");
		
		function attendance_scan() {
			var employee_id = parseInt($("#attendance_container").data("employee"));
			if (isNaN(employee_id)) employee_id = 0;
			var customer_id = parseInt($("#attendance_container").data("customer"));
			if (isNaN(customer_id)) customer_id = 0;
			console.log(customer_id);
			if (employee_id || customer_id) {
				$.ajax({
					dataType: "html",
					url: '/hr/attendance/scan/'+employee_id+'/'+customer_id,
					method: 'GET',
					success: function(response) {
						console.log(response);
						$("#attendance_container", website_attendance).html(response);
						$("input[name='qty[]']").eq(0).change();
					},
				});
			}
		}
		
		function employee_start() {
			var employee_id = parseInt($("#attendance_container").data("employee"));
			var contract_id = parseInt($("#employee_contract_id").val());
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/employee/start/'+employee_id+'/'+contract_id,
				method: 'POST',
				success: function(response) {
					if (response.error) {
						display_message(message_container, response.error, "error", 0);
					}
					if (response.info) {
						display_message(message_container, response.info, "info");
					}
					attendance_scan();
				},
			});
		}
	
		function employee_finish() {
			var employee_id = parseInt($("#attendance_container").data("employee"));
			var contract_id = parseInt($("#attendances_table").data("contract"));
			var out_of_town = $("#out_of_town_div input[type='radio'][name='out_of_town']:checked").val();
			var expense = daily_expense_serialize();
			var routes = $("#routes").val();
			if (!routes) {
				routes = '-';
			}
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/employee/finish/'+employee_id+'/'+contract_id+'/'+out_of_town+'/'+expense+'/'+routes,
				method: 'POST',
				success: function(response) {
					if (response.error) {
						display_message(message_container, response.error, "error", 0);
					}
					if (response.info) {
						display_message(message_container, response.info, "info");
					}
					attendance_scan();
				},
			});
		}
	
		function customer_confirm() {
			var attendance_id = parseInt($("#attendances_table").data("attendance"));
			var time = $("#confirm_time").val();
			var regex = /([01]\d|2[0-3]):([0-5]\d)/;
			if (!regex.test(time)) {
				display_message($("#message_container"), 'Invalid time. Please input time in format of HH:MM (24 hour) e.g. 08:30, 17:40.', "error", 0);
				return;
			}
			var expense_id = parseInt($("#expenses_table").data("expense"));
			if (isNaN(expense_id)) expense_id = 0;
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/customer/confirm/'+attendance_id+'/'+time+'/'+expense_id,
				method: 'POST',
				success: function(response) {
					if (response.error) {
						display_message(message_container, response.error, "error", 0);
					}
					if (response.info) {
						display_message(message_container, response.info, "info");
					}
					attendance_scan();
				},
			});
		}
	
		function customer_reject() {
			var attendance_id = parseInt($("#attendances_table").data("attendance"));
			var expense_id = parseInt($("#expenses_table").data("expense"));
			if (isNaN(expense_id)) expense_id = 0;
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/customer/reject/'+attendance_id+'/'+expense_id,
				method: 'POST',
				success: function(response) {
					if (response.error) {
						display_message(message_container, response.error, "error", 0);
					}
					if (response.info) {
						display_message(message_container, response.info, "info");
					}
					attendance_scan();
				},
			});
		}
	
	//handle event di semua kemungkinan div yang muncul
		
		$(website_attendance).on("click", "#btn_start", function () {
			employee_start();
		});
		
		$(website_attendance).on("click", "#btn_recheck", function () {
			$("#btn_recheck", website_attendance).html('Rechecking...');
			attendance_scan();
		});
		
		$(website_attendance).on("click", "#btn_stop", function () {
			employee_finish();
		});
		
		$(website_attendance).on("click", "#btn_confirm", function () {
			customer_confirm();
		});
		
		$(website_attendance).on("click", "#btn_reject", function () {
			customer_reject();
		});
		
		$(website_attendance).on("change", ".expense_line input", function() {
			daily_expense_change();
		});
		
	//berdasarkan mode, tentukan mau ngeload konten yang mana
		attendance_scan();
	});
});
