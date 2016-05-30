$(document).ready(function () {
	$('.universal_website_attendance').each(function () {
		
		var website_attendance = this;
		
		var mode = $("#attendance_container").data("mode");
	
	//handle event di semua kemungkinan div yang muncul
		
		$(website_attendance).on("change", "#employee_contract_id", function () {
			alert('masuk');
		});
		
	//berdasarkan mode, tentukan mau ngeload konten yang mana
		switch (mode) {
			case 'employee':
				var employee_id = parseInt($("#attendance_container").data("employee"));
				console.log(employee_id);
				$.ajax({
					dataType: "html",
					url: '/hr/attendance/employee/'+employee_id,
					method: 'GET',
					success: function(response) {
						$("#attendance_container", website_attendance).html(response);
					},
				})
				break;
			case 'customer':
				$.ajax({
					dataType: "html",
					url: '/hr/attendance/customer',
					method: 'GET',
					success: function(response) {
						$("#attendance_container", website_attendance).html(response);
					},
				})
				break;
		}
	});
});