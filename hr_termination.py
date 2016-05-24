from openerp.osv import osv, fields
from datetime import datetime, date
from openerp.tools.translate import _

# ==========================================================================================================================

class hr_employee_termination_memory(osv.osv_memory):
	
	_inherit = 'hr.employee.termination.memory'

# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def action_terminate_employee(self, cr, uid, ids, context={}):
		result = super(hr_employee_termination_memory, self).action_terminate_employee(cr, uid, ids, context=context)
		form_data = self.browse(cr, uid, ids[0])
	# terminate seluruh contract yang sedang aktif untuk employee ybs
		employee_obj = self.pool.get('hr.employee')
		contract_obj = self.pool.get('hr.contract')
		employee_data = employee_obj.browse(cr, uid, form_data.employee_id.id)
		for contract in employee_data.contract_ids:
			if contract.state != 'ongoing': continue
			contract_obj.write(cr, uid, [contract.id], {
				'state': 'terminated',
				'terminate_by': uid,
				'terminate_reason': _('Employee termination'),
				'terminate_date': date.today(),
			})
		return result