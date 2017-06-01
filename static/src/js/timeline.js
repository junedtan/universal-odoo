
openerp.universal = function(instance) {
	var QWeb = instance.web.qweb;
	QWeb.add_template('/universal/static/src/xml/timeline.xml');
	var _t = instance.web._t, _lt = instance.web._lt;

	instance.web.client_actions.add('universal.timeline_by_date','instance.universal.TimelineByDate');
	instance.web.client_actions.add('universal.timeline_by_driver','instance.universal.TimelineByDriver');

// TIMELINE BY DATE =========================================================================================================

	instance.universal.TimelineByDate = instance.web.Widget.extend({

		QWeb: QWeb,
		_t: _t,
		_lt: _lt,
		instance: instance,
		className: 'oe_universal_timeline_by_date',

		events: {
			'click #button_filter': 'onclick_filter_button',
		},

// FUNDAMENTAL FUNCTION -----------------------------------------------------------------------------------------------------

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

// METHODS ------------------------------------------------------------------------------------------------------------------

		onclick_filter_button: function(){
			var filter_date = new Date($('#filter_date').val());
			var year = filter_date.getFullYear();
			var month = filter_date.getMonth()+1;
			var day = filter_date.getDate();
			this.render_table(day, month, year);
		},

		render_table: function(day, month, year) {
			var self = this;
			new this.instance.web.Model('universal.timeline')
        		.call('get_timeline_by_date', {
        			 'day' : day,
        			 'month' : month,
        			 'year': year,
        		}).done(function(response) {
        			console.log(response);
        			if (response.status) {
						$('#div_main').html(self.QWeb.render("universal_timeline_by_date_table",{
							'drivers': response.drivers,
							'hours': response.hours,
						}));
					} else {
						alert('Server Unreachable.')
					}
        		});
		},

		pad: function(num, size){
			var s = num+"";
			while (s.length < size) s = "0" + s;
			return s;
		},

	});

// TIMELINE BY DRIVER =======================================================================================================

	instance.universal.TimelineByDriver = instance.web.Widget.extend({

		QWeb: QWeb,
		_t: _t,
		_lt: _lt,
		instance: instance,
		className: 'oe_universal_timeline_by_driver',
		driver_id: 0,

		events: {
			'click #button_filter': 'onclick_filter_button',
		},

// FUNDAMENTAL FUNCTION -----------------------------------------------------------------------------------------------------

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
			var self = this;
			new self.instance.web.Model('universal.timeline')
        		.call('get_drivers').done(function(response) {
        			console.log(response);
        			if (response.status) {
						self.$el.html(self.QWeb.render("universal_timeline_by_driver",{
							'drivers': response.drivers,
						}));
						var today = new Date();
						var date_string = self.pad(today.getFullYear(),4) + "-" + self.pad((today.getMonth()+1),2)  + "-" + self.pad(today.getDate(),2);
						$('#filter_start_date').val(date_string);
						$('#filter_end_date').val(date_string);

					  	$('#filter_driver').on('input',function() {
							var opt = $('option[value="'+$(this).val()+'"]');
							self.driver_id = (opt.length ? parseInt(opt.attr('id')) : 0);
					 	 });

						self.onclick_filter_button();
					} else {
						alert('Server Unreachable.')
					}
        		});
		},

// METHODS ------------------------------------------------------------------------------------------------------------------

		onclick_filter_button: function(){
			var self = this;
			var filter_start_date = new Date($('#filter_start_date').val());
			var filter_end_date = new Date($('#filter_end_date').val());
			var start_date = filter_start_date.getFullYear() + '-' + (filter_start_date.getMonth()+1) + '-' + filter_start_date.getDate();
			var end_date = filter_end_date.getFullYear() + '-' + (filter_end_date.getMonth()+1) + '-' + filter_end_date.getDate();
			this.render_table(self.driver_id, start_date, end_date);
		},

		render_table: function(driver_id, start_date, end_date) {
			var self = this;
			new this.instance.web.Model('universal.timeline')
        		.call('get_timeline_by_driver', {
        			 'driver_id' : driver_id,
        			 'start_date_string' : start_date,
        			 'end_date_string': end_date,
        		}).done(function(response) {
        			console.log(response);
        			if (response.status) {
						$('#div_main').html(self.QWeb.render("universal_timeline_by_driver_table",{
							'driver_name': response.driver_name,
							'dates': response.dates,
							'hours': response.hours,
						}));
					} else {
						alert('Server Unreachable.')
					}
        		});
		},

		pad: function(num, size){
			var s = num+"";
			while (s.length < size) s = "0" + s;
			return s;
		},

	});

};
