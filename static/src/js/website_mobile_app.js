$(document).ready(function () {

	var self = this;
	var instance = openerp;
	var qweb = openerp.qweb;
	qweb.add_template('/universal/static/src/xml/website_mobile_app.xml');

// EVENT HANDLER ============================================================================================================

	$("#website_mobile_app_menu_book_vehicle").click(function() {
		$("#main_container", self).html(qweb.render('website_mobile_app_create_order',{
			'user_group': 'fullday_passenger'
		}));
	});

});
