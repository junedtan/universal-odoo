# ==========================================================================================================================

class forms_contract(osv.osv):

	_name = "forms.contract"
	_inherit = ['mail.thread']
	_description = 'Forms Contract'
	
	# PRIVATE METHOD ------------------------------------------------------------------------------------------------------------------

	def _get_fee_gapok(self, cr, uid, ids, field_name, arg, context):
		res = {}
		gapok_fee_obj = self.pool.get('res.partner.gapok.fee')
		for row in self.browse(cr, uid, ids, context):
			gapok_fee_ids = gapok_fee_obj.search(cr, uid, [('header_id',=,row.customer_id.id),('homebase_id','='row.homebase_id.id)])
			if len(gapok_fee_ids) > 0:
				gapok_fee_data = gapok_fee_obj.browse(cr, uid, gapok_fee_ids[0])
				res[row.id] = gapok_fee_data.gapok_fee
		return res
	
	_columns = {
		'name': fields.char('Name', required=True),
		'contract_date': fields.date('Contract Date', required=True),
		'homebase_id' : fields.many2one('chjs.region', 'Homebase'),
    'customer_id' : fields.many2one('res.partner', 'Customer', required=True, domain=[('customer','=',True),('is_company','=',True)], ondelete='restrict'),
    'customer_contract_id' : fields.many2one('res.partner', 'PIC Customer', required=True, domain=[('customer','=',True),('is_company','=',False)], ondelete='restrict'),
		'start_date': fields.date('Start Date'),
		'end_date': fields.date('End Date'),
		'service_type': fields.selection([
			('full_day','Full-day Service'),
			('by_order','By Order'),
			('shuttle','Shuttle')], 'Service Type', required=True),
		'fee_calculation_type': fields.selection([
			('monthly','Monthly'),
			('order_based','Order Based')], 'Fee Calculation Type'),
		'fee_structure_id' : fields.many2one('hr.payroll.structure', 'Fee Structure', domain=[('is_customer_contract','=',True)], ondelete='restrict'),
		'state': fields.selection([
			('proposed','Proposed'),
			('confirmed','Confirmed'),
			('planned','Planned'),
			('active','Active'),
			('prolonged','Prolonged'),
			('terminated','Terminated'),
			('finished','Finished')], 'State', required=True),
		'termination_reason': fields.text('Termination Reason'),
		'default_pin': fields.char('Default PIN', help="Default PIN for full-day service and shuttle order."),
		'overtime_id' : fields.many2one('hr.overtime', 'Overtime', ondelete='restrict'),
		'working_time_id' : fields.many2one('resource.calendar', 'Working Time', ondelete='restrict'),
    'fleet_types': fields.one2many('forms.contract.fleet.type', 'header_id', 'Fleet Types'),
    'car_drivers': fields.one2many('forms.contract.fleet', 'header_id', 'Car Drivers'),
    'shuttle_schedules': fields.one2many('forms.contract.shuttle.schedule', 'header_id', 'Shuttle Schedules'),
    'allocation_units': fields.one2many('forms.contract.alloc.unit', 'header_id', 'Allocation Units'),
		'extended_contract_id' : fields.many2one('forms.contract', 'Extended Contract'),
    'fee_premature_termination': fields.float('Fee Premature Termination'),
		'fee_gapok': fields.function(_get_fee_gapok, method=True, type='float', string="Fee Gapok"),
		'fee_varpok': fields.float('Fee Varpok'),
		'fee_makan': fields.float('Fee Makan'),
		'fee_pulsa': fields.float('Fee Pulsa'),
		'fee_hadir': fields.float('Fee Hadir'),
		'fee_seragam': fields.float('Fee Seragam'),
		'fee_bpjs_tk': fields.float('Fee BPJS Ketenagakerjaan'),
		'fee_bpjs_ks': fields.float('Fee BPJS Kesehatan'),
		'fee_insurance': fields.float('Fee Insurance'),
		'fee_cuti': fields.float('Fee Cuti'),
		'fee_mcu': fields.float('Fee MCU'),
		'fee_training': fields.float('Fee Training'),
		'fee_lk_pp': fields.float('Fee Luar Kota PP'),
		'fee_lk_inap': fields.float('Fee Luar Kota Menginap'),
		'fee_holiday_allowance': fields.float('Fee Holiday Allowance'),
		'fee_management': fields.float('Fee Management'),
		'fee_ot1': fields.float('Fee Overtime 1'),
		'fee_ot2': fields.float('Fee Overtime 2'),
		'fee_ot3': fields.float('Fee Overtime 3'),
		'fee_ot4': fields.float('Fee Overtime 4'),
		'fee_ot_flat': fields.float('Fee Overtime Flat'),
		'usage_control_level': fields.selection([
			('no_control','No Control'),
			('warning','Limit with Warning'),
			('approval','Limit with Approval')], 'Usage Control Level'),
		'is_global_usage_setting': fields.boolean('Is Global Setting?'),
		'usage_allocation_maintained_by': fields.selection([
			('customer','Customer'),
			('universal','Universal')], 'Usage Allocation Maintained By'),
		'global_yellow_limit': fields.float('Yellow Limit (Rp)'),	
		'global_red_limit': fields.float('Red Limit (Rp)'),	
		'global_balance_credit_per_usage': fields.float('Balance Credit per Usage'),	
		'is_order_replacement_vehicle': fields.boolean('Is Order Replacement Vehicle?'),
		'last_fullday_autogenerate_date': fields.date('Last Fullday Autogenerate Date'),
		'last_shuttle_autogenerate_date': fields.date('Last Shuttle Autogenerate Date'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'state': 'proposed',
		'usage_control_level': 'no_control',
		'is_global_usage_setting': True,
		'usage_allocation_maintained_by': 'customer',
		'fee_varpok': 0,
		'fee_makan': 0,
		'fee_pulsa': 0,
		'fee_hadir': 0,
		'fee_seragam': 0,
		'fee_bpjs_tk': 0,
		'fee_bpjs_ks': 0,
		'fee_insurance': 0,
		'fee_cuti': 0,
		'fee_mcu': 0,
		'fee_training': 0,
		'fee_lk_pp': 0,
		'fee_lk_inap': 0,
		'fee_holiday_allowance': 0,
		'fee_management': 0,
		'fee_ot1': 0,
		'fee_ot2': 0,
		'fee_ot3': 0,
		'fee_ot4': 0,
		'fee_ot_flat': 0,
	}	
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_constraints = [
		(_const_start_end_date, _('Start date must'), ['shipper_id']),
	]
	
	_sql_constraints = [
		('const_start_end_date','CHECK(end_date > start_date)','End date must be after start date.'),
		('const_premature1', 'CHECK(fee_premature_termination >= 0)', _('Premature termination must be greater than or equal to zero.')),
		('const_premature2', 'CHECK(fee_premature_termination <= 100)', _('Premature termination must be less than or equal to 100.')),
		('const_bpjs_tk1', 'CHECK(fee_bpjs_tk >= 0)', _('BPJS Ketenagakerjaan must be greater than or equal to zero.')),
		('const_bpjs_tk2', 'CHECK(fee_bpjs_tk <= 100)', _('BPJS Ketenagakerjaan must be less than or equal to 100.')),
		('const_bpjs_ks1', 'CHECK(fee_bpjs_ks >= 0)', _('BPJS Kesehatan must be greater than or equal to zero.')),
		('const_bpjs_ks2', 'CHECK(fee_bpjs_ks <= 100)', _('BPJS Kesehatan must be less than or equal to 100.')),
		('const_management1', 'CHECK(fee_management >= 0)', _('Fee management must be greater than or equal to zero.')),
		('const_management2', 'CHECK(fee_management <= 100)', _('Fee management must be less than or equal to 100.')),
		('const_varpok', 'CHECK(fee_varpok >= 0)', _('Fee varpok must be greater than or equal to zero.')),
		('const_makan', 'CHECK(fee_makan >= 0)', _('Fee makan must be greater than or equal to zero.')),
		('const_pulsa', 'CHECK(fee_pulsa >= 0)', _('Fee pulsa must be greater than or equal to zero.')),
		('const_hadir', 'CHECK(fee_hadir >= 0)', _('Fee hadir must be greater than or equal to zero.')),
		('const_seragam', 'CHECK(fee_seragam >= 0)', _('Fee seragam must be greater than or equal to zero.')),
		('const_insurance', 'CHECK(fee_insurance >= 0)', _('Fee insurance must be greater than or equal to zero.')),
		('const_cuti', 'CHECK(fee_cuti >= 0)', _('Fee cuti must be greater than or equal to zero.')),
		('const_mcu', 'CHECK(fee_mcu >= 0)', _('Fee MCU must be greater than or equal to zero.')),
		('const_training', 'CHECK(fee_training >= 0)', _('Fee training must be greater than or equal to zero.')),
		('const_lk_pp', 'CHECK(fee_lk_pp >= 0)', _('Fee Luar Kota PP must be greater than or equal to zero.')),
		('const_lk_inap', 'CHECK(fee_lk_inap >= 0)', _('Fee Luar Kota Menginap must be greater than or equal to zero.')),
		('const_holiday_allowance', 'CHECK(fee_holiday_allowance >= 0)', _('Fee holiday allowance must be greater than or equal to zero.')),
		('const_ot1', 'CHECK(fee_ot1 >= 0)', _('Fee overtime 1 must be greater than or equal to zero.')),
		('const_ot2', 'CHECK(fee_ot2 >= 0)', _('Fee overtime 2 must be greater than or equal to zero.')),
		('const_ot3', 'CHECK(fee_ot3 >= 0)', _('Fee overtime 3 must be greater than or equal to zero.')),
		('const_ot4', 'CHECK(fee_ot4 >= 0)', _('Fee overtime 4 must be greater than or equal to zero.')),
		('const_ot_flat', 'CHECK(fee_ot_flat >= 0)', _('Fee overtime flat must be greater than or equal to zero.')),
	]		
	

# ==========================================================================================================================

class forms_contract_fleet_type(osv.osv):

	_name = "forms.contract.fleet.type"
	_description = 'Forms Contract Fleet Type'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('forms.contract', 'Forms Contract', ondelete='cascade'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type', required=True, ondelete='restrict'),
		'number': fields.integer('Number', required=True),
	}
	
	
# ==========================================================================================================================

class forms_contract_fleet(osv.osv):

	_name = "forms.contract.fleet"
	_description = 'Forms Contract Fleet'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('forms.contract', 'Forms Contract', ondelete='cascade'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type', required=True, ondelete='restrict'),
		'fleet_vehicle_id': fields.many2one('fleet.vehicle', 'Fleet Vehicle', required=True, ondelete='restrict'),
		'driver_id': fields.many2one('hr.employee', 'Driver', required=True, ondelete='restrict'),
	}
	
	
	
	
# ==========================================================================================================================

class forms_contract_shuttle_schedule(osv.osv):

	_name = "forms.contract.shuttle.schedule"
	_description = 'Forms Contract Shuttle Schedule'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('forms.contract', 'Forms Contract', ondelete='cascade'),
		'dayofweek': fields.selection([
			('0','Monday'),
			('1','Tuesday'),
			('2','Wednesday'),
			('3','Thursday'),
			('4','Friday'),
			('5','Saturday'),
			('6','Sunday'),], 'Day of Week', required=True),
		'sequence': fields.integer('Sequence', required=True),
		'route_id': fields.many2one('res.partner.route', 'Route', ondelete='restrict'),
		'fleet_vehicle_id': fields.many2one('fleet.vehicle', 'Fleet Vehicle', required=True, ondelete='restrict'),
		'departure_time': fields.float('Departure Time'),	
		'arrival_time': fields.float('Arrival Time'),	
	}		
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_departure_arrival', 'CHECK(arrival_time > departure_time)', _('Arrival time must be greater than departure time.')),
	]
	
# ORDER -------------------------------------------------------------------------------------------------------------------------

	_order = 'header_id, dayofweek, sequence'


	
# ==========================================================================================================================

class forms_contract_alloc_unit(osv.osv):

	_name = "forms.contract.alloc.unit"
	_description = 'Forms Contract Allocation Unit'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('forms.contract', 'Forms Contract', ondelete='cascade'),
		'name': fields.char('Name', required=True),
		'yellow_limit': fields.float('Yellow Limit'),
		'red_limit': fields.float('Red Limit'),
		'balance_credit_per_usage': fields.float('Balance Credit Per Usage'),
	}		
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'yellow_limit': -1,
		'red_limit': -1,
		'name': 'General',
	}	
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_contract_alloc_unit', 'UNIQUE(header_id,name)', _('Please input unique contract allocation unit.')),
	]	
	

# ==========================================================================================================================

class forms_contract_quota(osv.osv):

	_name = "forms.contract.quota"
	_description = 'Forms Contract Quota'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'customer_contract_id': fields.many2one('forms.contract', 'Forms Contract', required=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('forms.contract.alloc.unit', 'Alloc Unit', required=True, ondelete='cascade'),
		'period': fields.char('Period', required=True),
		'yellow_limit': fields.float('Yellow Limit'),
		'red_limit': fields.float('Red Limit'),
	}		
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_contract_alloc_period', 'UNIQUE(customer_contract_id,allocation_unit_id,period)', _('Please input unique contract, allocation unit, and period.')),
	]	
	

# ==========================================================================================================================

class forms_contract_quota_change_log(osv.osv):

	_name = "forms.contract.quota.change.log"
	_description = 'Forms Contract Quota Change Log'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'customer_contract_id': fields.many2one('forms.contract', 'Forms Contract', required=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('forms.contract.alloc.unit', 'Alloc Unit', required=True, ondelete='cascade'),
		'state': fields.selection([
			('draft','Draft'),
			('approved','Approved'),
			('rejected','Rejected'),], 'State'),
		'request_by': fields.many2one('res.users', 'Request By', ondelete='restrict'),
		'request_date': fields.datetime('Request Date', required=True),
		'period': fields.char('Period', required=True),
		'request_longevity': fields.selection([
			('temporary','Temporary'),
			('permanent','Permanent'),], 'Request Longevity'),
		'old_yellow_limit': fields.float('Old Yellow Limit', readonly=True),
		'old_red_limit': fields.float('Old Red Limit', readonly=True),
		'new_yellow_limit': fields.float('New Yellow Limit'),
		'old_red_limit': fields.float('New Red Limit'),
		'confirm_by': fields.many2one('res.users', 'Confirm By', ondelete='restrict'),
		'confirm_date': fields.datetime('Confirm Date'),
		'reject_reason': fields.text('Reject Reason'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'request_date': lambda *a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
		'request_by': lambda self, cr, uid, ctx: uid,
		'request_longevity': 'temporary',
		'state': 'draft',
	}	
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_new_red_yellow_limit', 'CHECK(new_yellow_limit < new_red_limit)', _('New red limit must be greater than new yellow limit.')),
	]	
	

# ==========================================================================================================================

class forms_contract_quota_usage_log(osv.osv):

	_name = "forms.contract.quota.usage.log"
	_description = 'Forms Contract Quota Usage Log'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'usage_date': fields.datetime('Usage Date', required=True, readonly=True),
		'order_id': fields.many2one('forms.order', 'Order', required=True, readonly=True, ondelete='cascade'),
		'customer_contract_id': fields.many2one('forms.contract', 'Alloc Unit', required=True, readonly=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('forms.contract.alloc.unit', 'Alloc Unit', required=True, readonly=True, ondelete='cascade'),
		'period': fields.char('Period', required=True, readonly=True),
		'usage_amount': fields.float('Usage Amount', required=True, readonly=True),
	}
	