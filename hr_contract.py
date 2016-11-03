from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
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
	
	_name = "hr.contract"
	_inherit = ['hr.contract','mail.thread']
	
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Contract Reference', readonly=True),
		'contract_type': fields.selection(_CONTRACT_TYPE, 'Contract Type', required=True),
		'cust_contract': fields.many2one('hr.customer.contract','Customer Contract'),
		'customer': fields.many2one('res.partner','Customer'),
		'parent_contract': fields.many2one('hr.contract','Parent Contract', ondelete="cascade"),
		'homebase': fields.many2one('chjs.region','Homebase', domain=[('active','=',True)]),
		'contract_ids': fields.one2many('hr.contract','parent_contract','Past Contract Attachment'),
		'car_lisence_no': fields.char('Car Lisence No', track_visibility='onchange'),
		'oot_roundtrip_fee': fields.float('Roundtrip Fee/day'),
		'oot_overnight_fee': fields.float('Overnight Fee/day'),
		'first_party_name': fields.char('First Party Name', size=100),
		'first_party_position': fields.char("First Party's Job Title", size=100),
		'state': fields.selection(CONTRACT_STATE, 'State'),
		'allow_driver_replace': fields.boolean('Allow Driver Replacement?'),
		'meal_voc': fields.float('Meal Allowance/day', digits=(16,2)),
		'transport_voc': fields.float('Transport Allowance/day', digits=(16,2)),
		'absence_voc': fields.float('Absence Allowance/month', digits=(16,2)),
		'allowance': fields.float('Allowance/day', digits=(16,2)),
		'finished_by': fields.many2one('res.users', 'Finished By', readonly=True, copy=False),
		'finished_date': fields.date('Finish Date', copy=False),
		'terminate_by': fields.many2one('res.users', 'Terminated By', readonly=True, copy=False),
		'terminate_reason': fields.text('Termination Reason', copy=False),
		'terminate_date': fields.date('Termination Date', copy=False),
		'contract_sign_date': fields.date('Contract Sign Date', copy=False),
		'trial_date_start': fields.date('Trial Start Date', copy=False),
		'trial_date_end': fields.date('Trial End Date', copy=False),
		'extension_of': fields.many2one('hr.contract', 'Extended Contract'),
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
	# kalau tipe kontraknya lampiran kontrak, ambil latest contract nya
		if vals['contract_type'] == "contract_attc":
			emp_obj = self.pool.get('hr.employee').browse(cr, uid, vals['employee_id'], context=context)
			lastest_contract = self.get_latest_contract(cr, uid, vals['employee_id'])
			if not lastest_contract:
				raise osv.except_osv(_('Contract Error'),_('This employee do not have parent contract. Please create parent contract first before create contract attachment.'))
			vals['parent_contract'] = lastest_contract
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
	
	def action_extend(self, cr, uid, ids, context=None):
		return {
			'name': _('Extend Contract'),
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'hr.contract.extend.memory',
			'type': 'ir.actions.act_window',
			'context': {
				'default_contract_id': ids[0],
			},
			'target': 'new',
		}
		
	def action_terminate(self, cr, uid, ids, context=None):
		contract_data = self.browse(cr, uid, ids[0], context)
		model_obj = self.pool.get('ir.model.data')
		model, view_id = model_obj.get_object_reference(cr, uid, 'universal', 'hr_contract_terminate_form')
		return {
			'name': _('Terminate Contract'),
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

	def onchange_employee_id(self, cr, uid, ids, emp_id, contract_type, wage=None, context=None):
	# set dulu wage nya dengan default 1 kalau contract type nya rent driver
		if not contract_type:
		  return {'value': {'wage': False}}
		if contract_type == 'rent_driver':
			wage = 1
	# ambil parent contract
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
		return {'value': {'parent_contract': parent_contract, 'job_id': job_id, 'homebase': False, 'wage': wage}}
	
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
	
# CRON --------------------------------------------------------------------------------------------------------------------------
	
	def cron_contract_finish_status(self, cr, uid, context=None):
	# cek untuk masing2 contract apakah sudah ada yang durasinya habis?
		contract_ids = self.search(cr, uid, [('date_end','<',datetime.today().strftime('%Y-%m-%d'))])
		if len(contract_ids) > 0:
			self.write(cr, uid, contract_ids, {'state': 'finished'})
			

# ==========================================================================================================================

class hr_contract_extend_memory(osv.osv):
	_name = "hr.contract.extend.memory"
	
	_columns = {
		'contract_id': fields.many2one('hr.contract', 'Contract to be Extended'),
		'start_date': fields.date('Date Start', required=True),
		'end_date': fields.date('Date End', required=True),
	}
	
	def action_save(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids, context)[0]
		old_contract_id = form_data.contract_id.id
		contract_obj = self.pool.get('hr.contract')
		new_contract_id = contract_obj.copy(cr, uid, old_contract_id, context=context)
		contract_obj.write(cr, uid, [new_contract_id], {
			'extension_of': old_contract_id,
			'date_start': form_data.start_date,
			'date_end': form_data.end_date,
		}, context=context)
		start_date = datetime.strptime(form_data.start_date, '%Y-%m-%d')
		finish_date = start_date + timedelta(hours=-24)
		contract_obj.write(cr, uid, [old_contract_id], {
			'finished_by': uid,
			'finished_date': finish_date.strftime('%Y-%m-%d'),
		})
		return True
	
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
	
	


	
	
	
	
	