$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

// EVENT HANDLER ============================================================================================================

	$("#website_mobile_app_menu_book_vehicle").click(function() {
		$.get('/mobile_app/fetch_contracts', null, function(data){
			$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
				'user_group': 'fullday_passenger',
				'contract_datas': JSON.parse(data),
				'start_planned_default': new Date().addHours(1).toDatetimeString(),
				'finish_planned_default': new Date().addHours(2).toDatetimeString(),
			}));
		});
	});

});
