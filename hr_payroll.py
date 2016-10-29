from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class hr_payroll_structure(osv.osv):
	
	_inherit = 'hr.payroll.structure'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'is_customer_contract': fields.boolean('Customer Contract?'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'is_customer_contract': True,
	}	