$(document).ready(function () {
	
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
		);
		if (timeout > 0) {
			setTimeout(function() {
				clear_message(container);
			},timeout*1000);
		}
	}
	
	function clear_message(container) {
		container.html('');
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
			if (employee_id || customer_id) {
				$.ajax({
					dataType: "html",
					url: '/hr/attendance/scan/'+employee_id+'/'+customer_id,
					method: 'GET',
					success: function(response) {
						$("#attendance_container", website_attendance).html(response);
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
			console.log(out_of_town);
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/employee/finish/'+employee_id+'/'+contract_id+'/'+out_of_town,
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
			$.ajax({
				dataType: "json",
				url: '/hr/attendance/customer/confirm/'+attendance_id+'/'+time,
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
		
	//berdasarkan mode, tentukan mau ngeload konten yang mana
		attendance_scan();
	});
});