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

# FIELD FUNCTION -----------------------------------------------------------------------------------------------------------

	def _has_proof_of_payment(self, cr, uid, ids, field_name, arg, context):
		res = {}
		for row in self.browse(cr, uid, ids, context):
			res[row.id] = not (row.proof_of_payment == False or row.proof_of_payment == None)
		return res

# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('foms.contract','Contract Reference'),
		'order_id': fields.many2one('foms.order', 'Order'),
		'source': fields.selection(_EXPENSE_INPUT_SOURCE,'Source', readonly=True),
		'proof_of_payment': fields.binary('Proof of Payment'),
		'has_proof_of_payment': fields.function(_has_proof_of_payment, type="boolean", method=True, string="Has Proof of Payment"),
	}
	

# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'source': 'manual',
	}

# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		# print vals.get('proof_of_payment', False)
		context = context and context or {}
	# bila ini dari mobile apps, asumsikan employee_id adalah user_id driver, sehingga harus dicari employee_idnya
		if context.get('from_webservice') == True:
			user_id = vals.get('employee_id')
			employee_obj = self.pool.get('hr.employee')
			employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
			if len(employee_ids) == 0:
				raise osv.except_osv(_('Expense Error'),_('There is no driver with requested user id.'))
			vals.update({'employee_id': employee_ids[0]})
		expense_id = super(hr_expense_expense, self).create(cr, uid, vals, context=context)
		# otomatis submit to manager
		self.write(cr, uid, [expense_id], {'state': 'confirm'})
		return expense_id
	
	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		context = context and context or {}
		user_obj = self.pool.get('res.users')
		contract_obj = self.pool.get('foms.contract')
		order_obj = self.pool.get('foms.order')
	# kalau diminta untuk mengambil semua order by user_id tertentu
		if context.get('by_user_id',False):
			domain = []
			user_id = context.get('user_id', uid)
			is_pic = user_obj.has_group(cr, user_id, 'universal.group_universal_customer_pic')
			is_approver = user_obj.has_group(cr, user_id, 'universal.group_universal_approver')
			is_driver = user_obj.has_group(cr, user_id, 'universal.group_universal_driver')
			is_booker = user_obj.has_group(cr, user_id, 'universal.group_universal_booker')
			is_fullday_passenger = user_obj.has_group(cr, user_id, 'universal.group_universal_passenger')
		# kalau pic, domainnya menjadi semua expense dengan contract yang pic nya adalah partner terkait
			if is_pic:
				user_data = user_obj.browse(cr, uid, user_id)
				if user_data.partner_id:
					contract_ids = contract_obj.search(cr, uid, [('customer_contact_id','=',user_data.partner_id.id)])
					domain.append(('contract_id','in',contract_ids))
		# kalau driver, domainnya menjadi expense semua order yang di-assign ke dia, atau actual nya dia
			if is_driver:
				employee_obj = self.pool.get('hr.employee')
				employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
				if len(employee_ids) > 0:
					order_ids = order_obj.search(cr, uid, [
						'|',
						('assigned_driver_id','=',employee_ids[0]),
						('actual_driver_id','=',employee_ids[0]),
					])
					if len(order_ids) > 0:
						domain.append(('order_id','in',order_ids))
					else:
						args = [('id','=',-1)] # supaya ga keambil apa2
				else:
					args = [('id','=',-1)] # supaya ga keambil apa2
		# kalau passenger, ambil expense yang order.order_by nya adalah dia
			if is_fullday_passenger:
				order_ids = order_obj.search(cr, uid, [
					('order_by','=',user_id)
				])
				if len(order_ids) > 0:
					domain.append(('order_id','in',order_ids))
				else:
					args = [('id','=',-1)] # supaya ga keambil apa2
			if len(domain) > 0:
				args = domain + args
			else:
				return []
		return super(hr_expense_expense, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
		
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
		elif command == 'get_proof_of_payment':
			expense_data = self.browse(cr, uid, data_id)
			if expense_data.proof_of_payment:
				result = str(expense_data.proof_of_payment).replace('+','-')
				result = result.replace('/','_')
			else:
				result = None
		return result

# ==========================================================================================================================

class hr_expense_line(osv.osv):
	
	_inherit = 'hr.expense.line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'product_id': fields.many2one('product.product', 'Category', domain=[('hr_expense_ok','=',True)]),
	}
