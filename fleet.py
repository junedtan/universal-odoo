from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date


# ==========================================================================================================================

class fleet_vehicle(osv.osv):
	
	_inherit = 'fleet.vehicle'
	
	# PRIVATE METHOD ------------------------------------------------------------------------------------------------------------------

	def _get_current_contract(self, cr, uid, ids, field_name, arg, context):
		res = {}
		for id in ids:
			cr.execute("""
				SELECT contract.id as 'contract_id' 
				FROM forms_contract_fleet fleet, forms_contract contract
				WHERE 
					fleet.header_id = contract.id and 
					fleet.fleet_vehicle_id = %s and 
					contract.state = 'active'
			""" % id)
			rows = cr.dictfetchall()
			if not rows: return None
		# update deh
			res[id] = rows[0]['contract_id']	
		return res
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'bpkb': fields.char('BPKB', required=True),
		'current_contract_id': fields.function(_get_current_contract, method=True, type='many2one', obj='forms.contract', string="Current Contract"),
		'contract_ids': fields.one2many('forms.contract.fleet', 'fleet_vehicle_id', 'Contract Fleet'),
		'state_change_ids': fields.one2many('fleet.vehicle.state.change.log', 'header_id', 'State Change Log'),
	}
	
	
# ==========================================================================================================================

class fleet_vehicle_state_change_log(osv.osv):
	
	_name = 'fleet.vehicle.state.change.log'
	_description = 'Vehicle State Change Log'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('fleet.vehicle', 'Vehicle Id', ondelete='cascade'),
		'state_from': fields.many2one('fleet.vehicle.state', 'State From', required=True, ondelete='restrict'),
		'state_to': fields.many2one('fleet.vehicle.state', 'State To', required=True, ondelete='restrict'),
		'change_date': fields.datetime('Change Date', required=True),
		'change_by': fields.many2one('res.users', 'Change By', required=True),
	}
	
	
