from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_EXPENSE_INPUT_SOURCE = (
	('manual',_('Manual Input')),
	('app',_('App')),
)

# ==========================================================================================================================

class hr_hr_expense_expense(osv.osv):
	
	_inherit = 'hr.expense.expense'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('hr.contract','Contract Reference', domain=[('contract_type','in',['contract_attc'])]),
		'source': fields.selection(_EXPENSE_INPUT_SOURCE,'Source', readonly=True),
	}
	

# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'source': 'manual',
	}

# ==========================================================================================================================

class hr_expense_line(osv.osv):
	
	_inherit = 'hr.expense.line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'product_id': fields.many2one('product.product', 'Category', domain=[('hr_expense_ok','=',True)]),
	}