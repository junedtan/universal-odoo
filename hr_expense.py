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
	
	_inherit = ['chjs.base.webservice','hr.expense.expense']
	_name = 'hr.expense.expense'
	
	_valid_commands = ['search_read', 'search_by_user_id', 'create', 'update', 'delete', 'expense_types']
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('foms.contract','Contract Reference'),
		'source': fields.selection(_EXPENSE_INPUT_SOURCE,'Source', readonly=True),
	}
	

# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'source': 'manual',
	}

# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		context = context and context or {}
	# bila ini dari mobile apps, asumsikan employee_id adalah user_id driver, sehingga harus dicari employee_idnya
		if context.get('from_webservice') == True:
			user_id = vals.get('employee_id')
			employee_obj = self.pool.get('hr.employee')
			employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
			if len(employee_ids) == 0:
				raise osv.except_osv(_('Expense Error'),_('There is no driver with requested user id.'))
			vals.update({'employee_id': employee_ids[0]})
		return super(hr_expense_expense, self).create(cr, uid, vals, context=context)
	
	def webservice_handle(self, cr, uid, user_id, command, data_id, model_data, context={}):
		result = super(hr_expense_expense, self).webservice_handle(cr, uid, user_id, command, data_id, model_data, context=context)
		if command == 'expense_types':
			expense_type_obj = self.pool.get('product.template')
			expense_type_ids = expense_type_obj.search(cr, uid, [('hr_expense_ok','=',True),('is_trip_related','=',True)])
			result = []
			for expense_type in expense_type_obj.browse(cr, uid, expense_type_ids):
				result.append({
					'id': expense_type.id,
					'name': expense_type.name,
				})
		return result

# ==========================================================================================================================

class hr_expense_line(osv.osv):
	
	_inherit = 'hr.expense.line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'product_id': fields.many2one('product.product', 'Category', domain=[('hr_expense_ok','=',True)]),
	}