from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_EXPENSE_INPUT_SOURCE = (
	('manual',_('Manual Input')),
	('app',_('App')),
)

# ==========================================================================================================================

class product_template(osv.osv):
	
	_inherit = "product.template"
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'is_trip_related': fields.boolean('Trip Related?', 
			help="Specify if the expense is trip-related. Only these will show up in driver's menu."),
	}
	
	_defaults = {
		'is_trip_related': False,
	}
		
# ==========================================================================================================================

class hr_expense_expense(osv.osv):
	
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