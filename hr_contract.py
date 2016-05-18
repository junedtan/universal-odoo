from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
from . import CONTRACT_STATE


class hr_customer_contract(osv.osv):
	
	 _name = "hr.customer.contract"
	 _description = "Customer Contract"
	 
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Customer Contract', size=64, required=True),
	}
	
# ==========================================================================================================================

class hr_contract(osv.osv):
	
	_inherit = 'hr.contract'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'cust_contract': fields.many2one('hr.customer.contract','Customer Contract'),
		'customer': fields.many2one('res.partner','Customer'),
		'parent_contract': fields.many2one('hr.contract','Parent Contract'),
		'homebase': fields.many2one('chjs.region','Homebase'),
		'responsible': fields.many2one('hr.employee','First Party'),
		'job_id': fields.related('responsible','job_id',type="char",string="Job Title"),
		'state': fields.selection(CONTRACT_STATE, 'State')
	}
	