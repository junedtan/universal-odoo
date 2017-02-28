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
				SELECT contract.id as contract_id 
				FROM foms_contract_fleet fleet, foms_contract contract
				WHERE 
					fleet.header_id = contract.id and 
					fleet.fleet_vehicle_id = %s and 
					contract.state in ('active','planned')
			""" % id)
			rows = cr.dictfetchall()
			if not rows: 
				res[id] = None
			else:
		# update deh
				res[id] = rows[0]['contract_id']	
		return res
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'bpkb': fields.char('BPKB'),
		'current_contract_id': fields.function(_get_current_contract, method=True, type='many2one', obj='foms.contract', string="Current Contract"),
		'contract_ids': fields.one2many('foms.contract.fleet', 'fleet_vehicle_id', 'Contract Fleet'),
		'state_change_ids': fields.one2many('fleet.vehicle.state.change.log', 'header_id', 'State Change Log'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	def _default_state_id(self, cr, uid, context=None):
		model_obj = self.pool.get('ir.model.data')
		model, state_id = model_obj.get_object_reference(cr, uid, 'universal', 'vehicle_state_active')
		return state_id
		
	_defaults = {
		'state_id': _default_state_id,
	}	
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def write(self, cr, uid, ids, vals, context=None):
		if vals.get('state_id', False):
			change_log_obj = self.pool.get('fleet.vehicle.state.change.log')
			for original_data in self.browse(cr, uid, ids):
				change_log_obj.create(cr, uid, {
					'header_id': original_data.id,
					'state_from': original_data.state_id.id,
					'state_to': vals['state_id'],
					'change_date': datetime.now(),
					'change_by': uid,
				}, context=context)
		return super(fleet_vehicle, self).write(cr, uid, ids, vals, context=context)
	
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
	
	
