from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
from . import CONTRACT_STATE

_CONTRACT_TYPE = [
	('employee',_('Employee')),
	('rent_driver',_('Rent Driver')),
	('non_rent_driver',_('Non-Rent Driver')),
	('contract_attc',_('Contract Attachment for Rent Driver')),
]

_WORKING_TIME_TYPE = [
	('duration',_('Duration')),
	('max_hour',_('Max Hour')),
]

# ==========================================================================================================================

class hr_customer_contract(osv.osv):
	
	_name = "hr.customer.contract"
	_description = "Customer Contract"
	 
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Contract No', size=64, required=True),
		'customer': fields.many2one('res.partner','Customer', required=True, domain=[('customer','=',True),('is_company','=',True)]),
	}
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def name_get(self, cr, uid, ids, context={}):
		if isinstance(ids, (list, tuple)) and not len(ids): return []
		if isinstance(ids, (long, int)): ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids):
			name = record.name
			if record.customer:
				name = '%s (%s)' % (record.customer.name, record.name)
			res.append((record.id, name))
		return res
	
# ==========================================================================================================================

class hr_contract(osv.osv):
	
	_inherit = 'hr.contract'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Contract Reference', readonly=True),
		'contract_type': fields.selection(_CONTRACT_TYPE, 'Contract Type', required=True),
		'cust_contract': fields.many2one('hr.customer.contract','Customer Contract'),
		'customer': fields.many2one('res.partner','Customer'),
		'parent_contract': fields.many2one('hr.contract','Parent Contract', ondelete="cascade"),
		'homebase': fields.many2one('chjs.region','Homebase', domain=[('type', '=', 'city'),('active','=',True)]),
		'oot_roundtrip_fee': fields.float('Roundtrip Fee/day'),
		'oot_overnight_fee': fields.float('Overnight Fee/day'),
		'responsible': fields.many2one('hr.employee','First Party', required=True),
		'responsible_job_id': fields.related('responsible','job_id',type="many2one",relation="hr.job",string="First Party's Job Title",readonly=True),
		'state': fields.selection(CONTRACT_STATE, 'State'),
		'allow_driver_replace': fields.boolean('Allow Driver Replacement?'),
		'meal_voc': fields.float('Meal Allowance', digits=(16,2)),
		'transport_voc': fields.float('Transport Allowance', digits=(16,2)),
		'absence_voc': fields.float('Absence Allowance', digits=(16,2)),
		'allowance': fields.float('Allowance', digits=(16,2)),
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
	
	def name_get(self, cr, uid, ids, context={}):
		if isinstance(ids, (list, tuple)) and not len(ids): return []
		if isinstance(ids, (long, int)): ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids):
			name = record.name
			if record.customer:
				name = '%s (%s)' % (record.customer.name, record.name)
			res.append((record.id, name))
		return res
	
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
		if not emp_id or not contract_type:
		  return {'value': {'parent_contract': False, 'job_id': False}}
		emp_obj = self.pool.get('hr.employee').browse(cr, uid, emp_id, context=context)
		job_id = False
		parent_contract = False
	# ambil job id employee
		if emp_obj.job_id: job_id = emp_obj.job_id.id
	# kalau contract typenya berhubungan sama driver, isi job id sama driver
		if contract_type in ['rent_driver','non_rent_driver','contract_attc']:
			job_driver = self.pool.get('hr.job').search(cr, uid, [('name','ilike','driver')])
			if len(job_driver) > 0:
				job_id = job_driver[0]
	# ambil contract employee terbaru kalau tipenya driver sewa
		if emp_obj.driver_type == "contract" and contract_type == "contract_attc":
			parent_contract = self.get_latest_contract(cr, uid, emp_id)
	
		return {'value': {'parent_contract': parent_contract, 'job_id': job_id, 'homebase': False}}
	
	def onchange_homebase(self, cr, uid, ids, contract_type, homebase, context=None):
		if not contract_type or not homebase: return {'value': {'homebase': False}}
		homebase_obj = self.pool.get('chjs.region')
		wage = 0
		if contract_type == "contract_attc":
			homebase_data = homebase_obj.browse(cr, uid, homebase)
			wage = homebase_data.default_wage
		return {'value': {'wage': wage}}

	def onchange_cust_contract(self, cr, uid, ids, cust_contract, context=None):
		if not cust_contract:
		  return {'value': {'customer': False, 'cust_contract': False}}
		cust_contract_obj = self.pool.get('hr.customer.contract').browse(cr, uid, cust_contract, context=context)
		return {'value': {'customer': cust_contract_obj.customer.id}}
	

# ==========================================================================================================================

class resource_calendar_attendance(osv.osv):
	_inherit = "resource.calendar.attendance"
	
	_columns = {
		'working_time_type': fields.selection(_WORKING_TIME_TYPE, 'Type', required=True),
		'max_hour': fields.float('Max Work Hour'),
		'hour_from' : fields.float('Work from', help="Start and End time of working.", select=True),
    'hour_to' : fields.float("Work to"),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'working_time_type': 'duration',
	}
	
	
			
