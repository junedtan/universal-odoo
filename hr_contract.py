from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
from . import CONTRACT_STATE

_CONTRACT_TYPE = [
	('employee',_('Employee')),
	('rent_driver',_('Rent Driver')),
	('contract_attc',_('Contract Attachment')),
	('non_rent_driver',_('Non-Rent Driver')),
]

class hr_customer_contract(osv.osv):
	
	 _name = "hr.customer.contract"
	 _description = "Customer Contract"
	 
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	 _columns = {
			'name': fields.char('Contract No.', size=64, required=True),
		}
	
# ==========================================================================================================================

class hr_contract(osv.osv):
	
	_inherit = 'hr.contract'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Contract Reference', readonly=True),
		'contract_type': fields.selection(_CONTRACT_TYPE, 'Contract Type', required=True),
		'cust_contract': fields.many2one('hr.customer.contract','Customer Contract'),
		'customer': fields.many2one('res.partner','Customer'),
		'parent_contract': fields.many2one('hr.contract','Parent Contract'),
		'homebase': fields.many2one('chjs.region','Homebase'),
		'responsible': fields.many2one('hr.employee','First Party'),
		'responsible_job_id': fields.related('responsible','job_id',type="many2one",relation="hr.job",string="First Party's Job Title",readonly=True),
		'state': fields.selection(CONTRACT_STATE, 'State'),
		'finished_by': fields.many2one('res.users', 'Finished By', readonly=True),
		'finished_date': fields.date('Finish Date'),
		'terminate_by': fields.many2one('res.users', 'Terminated By', readonly=True),
		'terminate_reason': fields.text('Termination Reason'),
		'terminate_date': fields.date('Termination Date'),
	}

# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'state': 'ongoing',
	}
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------
	
	def get_latest_contract(self, cr, uid, emp_id):
		contract_obj = self.pool.get('hr.contract')
		contract_ids = contract_obj.search(cr, uid, [('employee_id','=',emp_id),('contract_type','!=','contract_attc'),('state','not in',['terminated'])], order='date_start')
		if contract_ids: return contract_ids[-1:][0]
		return False
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
	# siapkan data untuk contract code
		contract_seq = self.pool.get('ir.sequence').next_by_code(cr, uid, 'hr.contract.seq')
		contract_no = 'CONTRACT.%s' % (contract_seq)
		vals.update({'name': contract_no})
	# panggil create biasa
		return super(hr_contract, self).create(cr, uid, vals, context)
	
# ACTIONS -----------------------------------------------------------------------------------------------------------------
	
	def action_finish(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {
			'finished_by': uid,
			'finished_date': date.today(),
			'state': 'finished',
		}, context=context)
		
	def action_terminate(self, cr, uid, ids, context=None):
		contract_data = self.browse(cr, uid, ids[0], context)
		model_obj = self.pool.get('ir.model.data')
		model, view_id = model_obj.get_object_reference(cr, uid, 'universal', 'hr_contract_terminate_form')
		return {
			'name': _('Terminate contract'),
			'view_mode': 'form',
			'view_id': view_id,
			'view_type': 'form',
			'res_model': 'hr.contract',
			'res_id': ids and ids[0] or None,
			'type': 'ir.actions.act_window',
			'target': 'new',
		}
		
	def action_terminate_save(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {
			'terminate_date': date.today(),
			'terminate_by': uid,
			'state': 'terminated',
		})

# ONCHANGE ----------------------------------------------------------------------------------------------------------------

	def onchange_employee_id(self, cr, uid, ids, emp_id, contract_type, context=None):
		if not emp_id:
		  return {'value': {'parent_contract': False, 'job_id': False}}
		emp_obj = self.pool.get('hr.employee').browse(cr, uid, emp_id, context=context)
		job_id = False
		parent_contract = False
	# ambil job id employee
		if emp_obj.job_id: job_id = emp_obj.job_id.id
	# ambil contract employee terbaru kalau tipenya driver sewa
		print "emp %s" % emp_id
		print emp_obj.driver_type
		print contract_type
		if emp_obj.driver_type == "contract" and contract_type == "contract_attc":
			print "aaa"
			parent_contract = self.get_latest_contract(cr, uid, emp_id)
		print parent_contract
		return {'value': {'parent_contract': parent_contract, 'job_id': job_id}}

