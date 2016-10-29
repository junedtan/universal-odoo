from openerp.osv import fields, osv
from openerp.tools.translate import _

_ORDER_STATE = [
	('new','New'),
	('rejected','Rejected'),
	('confirmed','Confirmed'),
	('ready','Ready'),
	('started','Started'),
	('start_confirmed','Start Confirmed'),
	('paused','Paused'),
	('resumed','Resumed'),
	('finished','Finished'),
	('finish_confirmed','Finish Confirmed'),
	('canceled','Canceled')
]



class forms_order(osv.osv):

	_name = 'forms.order'
	_description = 'Forms Order'

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Order #', required=True),
		'customer_contract_id': fields.many2one('forms.contract', 'Forms Contract', required=True, ondelete='restrict'),
		'service_type': fields.selection([
			('full_day','Full-day Service'),
			('by_order','By Order'),
			('shuttle','Shuttle')], 'Service Type', required=True),
		'request_date': fields.datetime('Request Date', required=True),
		'state': fields.selection(_ORDER_STATE, 'State', required=True),
		'order_by': fields.many2one('res.users', 'Order By', required=True, ondelete='restrict'),
		'confirm_date': fields.datetime('Confirm Date'),
		'confirm_by': fields.many2one('res.users', 'Confirm By', ondelete='restrict'),
		'cancel_reason': fields.many2one('forms.order.cancel.reason', 'Cancel Reason'),
		'cancel_reason_other': fields.text('Other Cancel Reason'),
		'cancel_date': fields.datetime('Cancel Date'),
		'cancel_by': fields.many2one('res.users', 'Cancel By', ondelete='restrict'),
		'cancel_previous_state': fields.selection(_ORDER_STATE, 'Previous State'),
		'alloc_unit_id': fields.many2one('forms.contract.alloc.unit', 'Alloc Unit', ondelete='restrict'),
		'alloc_unit_usage': fields.float('Allocation Unit Usage'),
		'route_id': fields.many2one('res.partner.route', 'Route', ondelete='cascade'),
		'origin_location_id': fields.many2one('res.partner.location', 'Origin Location', ondelete='set null'),
		'origin_location': fields.char('Origin Location'),
		'dest_location_id': fields.many2one('res.partner.location', 'Destination Location', ondelete='set null'),
		'dest_location': fields.char('Destination Location'),
		'order_type_by_order': fields.selection([
			('one_way_drop_off','One-way Drop Off'),
			('one_way_pickup','One-way Pick-up'),
			('two_way','Two Way')], 'Order Type by Order'),
		'passenger_count': fields.integer('Passenger Count'),
		'is_orderer_passenger': fields.boolean('Is Orderer = Passenger?'),
		'passengers': fields.one2many('forms.order.passenger', 'header_id', 'Passengers'),
		'assigned_vehicle_id': fields.many2one('fleet.vehicle', 'Assigned Vehicle', ondelete='restrict'),
		'assigned_driver_id': fields.many2one('hr.employee', 'Assigned Driver', ondelete='restrict'),
		'actual_vehicle_id': fields.many2one('fleet.vehicle', 'Actual Vehicle', ondelete='restrict'),
		'actual_driver_id': fields.many2one('hr.employee', 'Actual Driver', ondelete='restrict'),
		'pin': fields.char('PIN'),
		'start_planned_date': fields.datetime('Start Planned Date'),
		'finish_planned_date': fields.datetime('Finish Planned Date'),
		'start_date': fields.datetime('Start Date'),
		'start_confirm_date': fields.datetime('Start Confirm Date'),
		'start_confirm_by': fields.many2one('res.users', 'Start Confirm By', ondelete='set null'),
		'start_from': fields.selection([
			('mobile','Mobile App'),
			('central','Central Dispatch'),], 'Start From'),
		'finish_date': fields.datetime('Finish Date'),
		'finish_confirm_date': fields.datetime('Finish Confirm Date'),
		'finish_confirm_by': fields.many2one('res.users', 'Finish Confirm By', ondelete='set null'),
		'finish_from': fields.selection([
			('mobile','Mobile App'),
			('central','Central Dispatch'),], 'Finish From'),
		'pause_count': fields.integer('Pause Count'),
		'is_lk_pp': fields.boolean('Luar Kota PP?'),
		'is_lk_inap': fields.boolean('Luar Kota Menginap?'),
		
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'request_date': lambda *a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
		'order_by': lambda self, cr, uid, ctx: uid,
		'state': 'new',
		'pause_count': 0,
		'is_lk_pp': False,
		'is_lk_inap': False,
	}	
	

# ==========================================================================================================================

class forms_order_passenger(osv.osv):

	_name = "forms.order.passenger"
	_description = 'Forms Order Passenger'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('forms.order', 'Forms Order', required=True, ondelete='cascade'),
		'name': fields.char('Name'),
		'phone_no': fields.char('Phone No.'),
		'is_orderer': fields.boolean('Is Orderer'),
	}		
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'is_orderer': False,
	}	
	

# ==========================================================================================================================

class forms_order_cancel_reason(osv.osv):

	_name = "forms.order.cancel.reason"
	_description = 'Forms Order Cancel Reason'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Name'),
	}		
	
# ==========================================================================================================================

class forms_order_mass_input_memory(osv.osv_memory):

	_name = "forms.order.mass.input.memory"
	_description = 'Forms Order Mass Input Memory'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('forms.contract', 'Contract'),
		'customer_id': fields.many2one('res.partner', 'Customer'),
		'order_details': fields.one2many('forms.order.mass.input.memory.line', 'order_id', 'Order'),
	}		
	
# ==========================================================================================================================

class forms_order_mass_input_memory_line(osv.osv_memory):

	_name = "forms.order.mass.input.memory.line"
	_description = 'Forms Order Mass Input Memory Line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'order_id': fields.many2one('forms.order', 'Order'),
		'alloc_unit_id': fields.many2one('forms.contract.alloc.unit', 'Allocation Unit', required=True, ondelete='restrict'),
		'start_date': fields.datetime('Start Date'),
		'finish_date': fields.datetime('Finish Date'),
	}		
	
	
	
