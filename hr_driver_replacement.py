from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date


class hr_driver_replacement(osv.osv):
	
	_name = 'hr.driver.replacement'
	_description = 'HR-Driver Replacement'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_original': fields.many2one('hr.employee','Original Driver', required=True),
		'driver_replace': fields.many2one('hr.employee','Replacement', required=True),
		'replace_date': fields.date('Date of Replace', required=True),
		'contract': fields.many2one('hr.contract','Contract', required=True),
		'customer': fields.many2one('res.partner','Customer'),
	}
	
# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	def onchange_contract(self, cr, uid, ids, contract_id):
		result = {}
		if not contract_id: return False
		contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)
		result['value'] = { 'customer' : contract_obj.customer.id }
		return result