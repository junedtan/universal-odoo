from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

	
# ==========================================================================================================================

class res_partner(osv.osv):
	
	_inherit = 'res.partner'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'partner_code': fields.char('Partner Code'),
		'default_working_time': fields.many2one('resource.calendar', 'Default Working Time', ondelete='set null'),
		'favorite_locations': fields.one2many('res.partner.location','header_id','Favorite Locations'),
		'default_routes': fields.one2many('res.partner.route','header_id','Default Routes'),
		'default_alloc_units': fields.one2many('res.partner.alloc.unit','header_id','Default Allocation Units'),
		'rent_fees': fields.one2many('res.partner.rent.fee','header_id','Rent Fees'),
		'gapok_fee': fields.one2many('res.partner.gapok.fee','header_id','Gapok Fee'),
		'order_based_fee': fields.one2many('res.partner.order.based.fee','header_id','Order Based Fee'),
		'default_fee_premature_termination': fields.float('Fee Premature Termination (%)'),
		'default_fee_makan': fields.float('Fee Makan'),
		'default_fee_pulsa': fields.float('Fee Pulsa'),
		'default_fee_hadir': fields.float('Fee Hadir'),
		'default_fee_seragam': fields.float('Fee Seragam'),
		'default_fee_bpjs_tk': fields.float('Fee BPJS Ketenagakerjaan'),
		'default_fee_bpjs_ks': fields.float('Fee BPJS Kesehatan'),
		'default_fee_insurance': fields.float('Fee Insurance'),
		'default_fee_cuti': fields.float('Fee Cuti'),
		'default_fee_mcu': fields.float('Fee MCU'),
		'default_fee_training': fields.float('Fee Training'),
		'default_fee_lk_pp': fields.float('Fee Luar Kota PP'),
		'default_fee_lk_inap': fields.float('Fee Luar Kota Menginap'),
		'default_fee_ot1': fields.float('Fee Overtime 1'),
		'default_fee_ot2': fields.float('Fee Overtime 2'),
		'default_fee_ot3': fields.float('Fee Overtime 3'),
		'default_fee_ot4': fields.float('Fee Overtime 4'),
		'default_fee_ot_flat': fields.float('Fee Overtime Flat'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_premature1', 'CHECK(default_fee_premature_termination >= 0)', _('Premature termination must be greater than or equal to zero.')),
		('const_premature2', 'CHECK(default_fee_premature_termination <= 100)', _('Premature termination must be less than or equal to 100.')),
	]	
	
	
# ==========================================================================================================================

class res_partner_location(osv.osv):

	_name = 'res.partner.location'
	_description = 'Partner Location'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
		'name': fields.char('Name', required=True),
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
	_description = 'Partner Route'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
		'name': fields.char('Name', required=True),
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
	_description = 'Partner Allocation Unit'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
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
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
		'fleet_vehicle_model_id': fields.many2one('fleet.vehicle.model', 'Fleet Vehicle Model', required=True, ondelete='restrict'),
		'monthly_fee': fields.float('Monthly Fee', required=True),
	}
	

# ==========================================================================================================================

class res_partner_gapok_fee(osv.osv):

	_name = 'res.partner.gapok.fee'
	_description = 'Partner Gapok Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
		'homebase_id': fields.many2one('chjs.region', 'Homebase'),
		'gapok_fee': fields.float('Gapok Fee', required=True),
	}

	
# ==========================================================================================================================

class res_partner_order_based_fee(osv.osv):

	_name = 'res.partner.order.based.fee'
	_description = 'Partner Order Based Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('res.partner', 'Partner Id', ondelete='cascade'),
		'fleet_vehicle_model_id': fields.many2one('fleet.vehicle.model', 'Fleet Vehicle Model', required=True, ondelete='restrict'),
		'fee_by_order': fields.float('Fee by Order'),
		'fee_by_hour': fields.float('Fee by Hour'),
		'fee_by_daily': fields.float('Fee by Daily'),
	}
	
	