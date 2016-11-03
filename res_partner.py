from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
	
# ==========================================================================================================================

class res_partner(osv.osv):
	
	_inherit = 'res.partner'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'partner_code': fields.char('Partner Code'), # disiapkan buat nomor kontrak kalo sampe ada customer code
		'default_working_time': fields.many2one('resource.calendar', 'Default Working Time', ondelete='set null'),
		'default_overtime': fields.many2one('hr.overtime', 'Default Overtime', ondelete="set null"),
		'favorite_locations': fields.one2many('res.partner.location','header_id','Favorite Locations'),
		'default_routes': fields.one2many('res.partner.route','header_id','Default Routes'),
		'default_alloc_units': fields.one2many('res.partner.alloc.unit','header_id','Default Allocation Units'),
		'rent_fees': fields.one2many('res.partner.rent.fee','header_id','Rent Fees'),
		'gapok_fee': fields.one2many('res.partner.gapok.fee','header_id','Gapok Fee'),
		'order_based_fee': fields.one2many('res.partner.order.based.fee','header_id','Order Based Fee'),
		'default_fee_premature_termination': fields.float('Premature Termination Fee (%)'),
		'default_fee_makan': fields.float('Makan/hari'),
		'default_fee_pulsa': fields.float('Pulsa'),
		'default_fee_hadir': fields.float('Uang Hadir'),
		'default_fee_seragam': fields.float('Seragam'),
		'default_fee_bpjs_tk': fields.float('BPJS TK (%)'),
		'default_fee_bpjs_ks': fields.float('BPJS Kesehatan (%)'),
		'default_fee_insurance': fields.float('Insurance'),
		'default_fee_cuti': fields.float('Cuti/hari'),
		'default_fee_mcu': fields.float('Medical Checkup'),
		'default_fee_training': fields.float('Training'),
		'default_fee_lk_pp': fields.float('LK PP/trip'),
		'default_fee_lk_inap': fields.float('LK Inap/trip'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_premature1', 'CHECK(default_fee_premature_termination >= 0)', _('Premature termination must be greater than or equal to zero.')),
		('const_premature2', 'CHECK(default_fee_premature_termination <= 100)', _('Premature termination must be less than or equal to 100.')),
		('const_bpjs_tk1', 'CHECK(default_fee_bpjs_tk >= 0)', _('BPJS Ketenagakerjaan must be greater than or equal to zero.')),
		('const_bpjs_tk2', 'CHECK(default_fee_bpjs_tk <= 100)', _('BPJS Ketenagakerjaan must be less than or equal to 100.')),
		('const_bpjs_ks1', 'CHECK(default_fee_bpjs_ks >= 0)', _('BPJS Kesehatan must be greater than or equal to zero.')),
		('const_bpjs_ks1', 'CHECK(default_fee_bpjs_ks <= 100)', _('BPJS Kesehatan must be less than or equal to 100.')),
	]	
	
	
# ==========================================================================================================================

class res_partner_location(osv.osv):

	_name = 'res.partner.location'
	_description = 'Customer Favorite Locations'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Customer', ondelete='cascade'),
		'name': fields.char('Location', required=True),
		'google_map_coordinates': fields.text('Google Map Coordinates', required=True, help="Google Map coordinates based on Google Map API or other GPS system."),
		'radius': fields.float('Radius', required=True)
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_partner_location', 'UNIQUE(header_id,google_map_coordinates)', _('Please input unique coordinates for each location.')),
	]	
	

# ==========================================================================================================================

class res_partner_route(osv.osv):

	_name = 'res.partner.route'
	_description = 'Customer Default Route'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
		'name': fields.char('Route Name', required=True),
		'start_location': fields.many2one('res.partner.location', 'Start Location', required=True, ondelete='restrict'),
		'end_location': fields.many2one('res.partner.location', 'End Location', required=True, ondelete='restrict'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_partner_route', 'UNIQUE(header_id,name)', _('Please input unique route name.')),
		('const_route', 'CHECK(start_location <> end_location)', _('Start location and end location must be different.')),
	]	
	
	
# ==========================================================================================================================

class res_partner_alloc_unit(osv.osv):

	_name = 'res.partner.alloc.unit'
	_description = 'Customer Allocation Unit'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
		'name': fields.char('Name', required=True),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_partner_alloc', 'UNIQUE(header_id,name)', _('Please input unique allocation unit name.')),
	]	
		
# ==========================================================================================================================

class res_partner_rent_fee(osv.osv):

	_name = 'res.partner.rent.fee'
	_description = 'Partner Rent Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
		'fleet_vehicle_model_id': fields.many2one('fleet.vehicle.model', 'Vehicle Model', required=True, ondelete='restrict'),
		'monthly_fee': fields.float('Monthly Fee', required=True),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('check_monthly_fee', 'CHECK(monthly_fee >= 0)', _('Monthly Fee must be greater than or equal to 0.')),
	]	
	
# ==========================================================================================================================

class res_partner_gapok_fee(osv.osv):

	_name = 'res.partner.gapok.fee'
	_description = 'Customer Gapok Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
		'homebase_id': fields.many2one('chjs.region', 'Homebase'),
		'gapok_fee': fields.float('Gapok', required=True),
	}

# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('check_gapok_fee', 'CHECK(gapok_fee >= 0)', _('Gapok Fee must be greater than or equal to 0.')),
	]	
	
# ==========================================================================================================================

class res_partner_order_based_fee(osv.osv):

	_name = 'res.partner.order.based.fee'
	_description = 'Customer Order Based Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
		'fleet_vehicle_model_id': fields.many2one('fleet.vehicle.model', 'Vehicle Model', required=True, ondelete='restrict'),
		'fee_by_order': fields.float('per Order'),
		'fee_by_hour': fields.float('per Hour'),
		'fee_by_day': fields.float('per Day'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('check_by_order_fee', 'CHECK(fee_by_order >= 0)', _('Fee per Order must be greater than or equal to 0.')),
		('check_by_hour_fee', 'CHECK(fee_by_hour >= 0)', _('Fee per Hour must be greater than or equal to 0.')),
		('check_by_day_fee', 'CHECK(fee_by_day >= 0)', _('Fee per Day must be greater than or equal to 0.')),
	]	
	
	