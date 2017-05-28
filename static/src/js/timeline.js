
openerp.universal = function(instance) {
	var QWeb = instance.web.qweb;
	QWeb.add_template('/universal/static/src/xml/timeline.xml');
	var _t = instance.web._t, _lt = instance.web._lt;

	instance.web.client_actions.add('universal.timeline_by_date','instance.universal.TimelineByDate');
	instance.web.client_actions.add('universal.timeline_by_driver','instance.universal.TimelineByDriver');
	instance.universal.TimelineByDate = instance.web.Widget.extend({

		QWeb: QWeb,
		_t: _t,
		_lt: _lt,
		instance: instance,
		className: 'oe_universal_timeline_by_date',

		events: {
			'click #button_filter': 'onclick_filter_button',
		},

//Fundamental Function ==================================================================================================================

		init: function(parent) {
			this._super(parent);
			var context = arguments[1]['context'];
			this.force_readonly = (context['force_readonly'] === 1);
			if (context['hide_sidebar']) {
				$('.oe_leftbar').hide();
			}
		},

		destroy: function() {
			this._super();
			$('.oe_leftbar').show();
		},

		start: function() {
			this.$el.html(this.QWeb.render("universal_timeline_by_date"));
			var today = new Date();
			var date_string = this.pad(today.getFullYear(),4) + "-" + this.pad((today.getMonth()+1),2)  + "-" + this.pad(today.getDate(),2);
			$('#filter_date').val(date_string);
			this.onclick_filter_button();
		},

		onclick_filter_button: function(){
			this.render_timeline();
		},

		render_timeline: function() {
			$('#div_main').html(this.QWeb.render("universal_timelie_by_date_table",{

			}));
		},

// UTILITY ==================================================================================================================

		pad: function(num, size){
			var s = num+"";
			while (s.length < size) s = "0" + s;
			return s;
		},

	});

};
