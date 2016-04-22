from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

from . import MAX_DRIVER_AGE, MARITAL_STATUS, RELIGION, FAMILY_RELATIONSHIP, MIN_CHECK_DUPLI


# ==========================================================================================================================

class hr_job(osv.osv):
	
	_inherit = 'hr.job'
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------

	# apakah job ini adalah driver atau bukan, dilihat dari xml id
	def is_driver(self, cr, uid, ids, context={}):
		if isinstance(ids, int): ids = [ids]
		model_obj = self.pool.get('ir.model.data')
		model, job_id = model_obj.get_object_reference(cr, uid, 'universal', 'hr_job_driver')
		return ids[0] == job_id
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------

#	def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
#		result = super(res_partner,self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
		
	
# ==========================================================================================================================

class hr_recruitment_degree(osv.osv):
	
	_inherit = 'hr.recruitment.degree'
	_order = 'sequence'

# ==========================================================================================================================

class hr_recruitment_stage(osv.osv):
	
	_inherit = 'hr.recruitment.stage'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'is_end': fields.boolean('End of Process?',
			help='If checked, moving an applicant to this stage means ending recruitment process for him/her.'),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_default = {
		'is_end': False,
	}
	
# ==========================================================================================================================

class hr_applicant(osv.osv):
	
	_inherit = 'hr.applicant'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'gender': fields.selection([('male', 'Male'), ('female', 'Female')], 'Gender'),
		'is_pending': fields.boolean('Pending Approval?',
			help='If checked, this applicant is waiting for SPV/manager\'s approval.'),
		'place_of_birth': fields.char('Place of Birth', required=True),
		'date_of_birth': fields.date('Date of Birth', required=True),
		'religion': fields.selection(RELIGION, 'Religion'),
		'driver_license_number': fields.char('License Number'),
		'driver_license_date': fields.date('License Expiry Date'),
		'driver_area': fields.char('Coverage Area', size=500),
		'npwp': fields.char('NPWP'),
		'family_card_number': fields.char('Family Reg. No.', size=64),
		'marital_status': fields.selection(MARITAL_STATUS, 'Marital Status'),
		'no_of_children': fields.integer('Children'),
		'spouse_name': fields.char('Spouse Name', size=500),
		'family_contact_name': fields.char('Contactable Name', size=500),
		'family_contactable_address': fields.text('Address'),
		'family_contactable_phone': fields.char('Phone'),
		'family_contactable_relationship': fields.selection(FAMILY_RELATIONSHIP, 'Relationship'),
		'language': fields.char('Language', size=500),
		'transportation': fields.char('Transportation', size=500),
		'residence_location': fields.char('Residence Location', size=500),
		'identification_id': fields.char('ID No', required=True),
		'residential_address': fields.text('Residential Address'),
		'residential_phone': fields.char('Residential Phone', size=32),
		'partner_address': fields.text('Current Address'),
		'partner_mobile2': fields.char('Mobile 2', size=32),
		'partner_mobile3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready for Overtime?'),
		'holiday_ready': fields.boolean('Work at Weekend/Holiday?'),
		'refused_date': fields.date('Refused At', readonly=True),
		'refused_by': fields.many2one('res.users', 'Refused By', readonly=True),
		'refused_reason': fields.text('Refuse Reason'),
		'is_blacklist': fields.boolean('Blacklist?'),
		'blacklist_reason': fields.text('Blacklist Reason'),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_default = {
		'is_pending': False,
		'is_blacklist': False,
	}
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------

	def action_approve_applicant(self, cr, uid, ids, context={}):
	# pindahin ke stage setelah si pending
		stage_obj = self.pool.get('hr.recruitment.stage')
		for data in self.browse(cr, uid, ids):
			stage_ids = stage_obj.search(cr, uid, [('sequence','>',data.stage_id.sequence)], order='sequence')
			self.write(cr, uid, [data.id], {'stage_id': stage_ids[0]}, context={'skip_pending_check': True})
	# jadi ngga pending lagi
		self.write(cr, uid, ids, {'is_pending': False}, context)
		return True

	def action_refuse_applicant(self, cr, uid, ids, context={}):
		model_obj = self.pool.get('ir.model.data')
		model, view_id = model_obj.get_object_reference(cr, uid, 'universal', 'hr_applicant_refusal_form')
		applicant_data = self.browse(cr, uid, ids[0])
		return {
			'type': 'ir.actions.act_window',
			'name': 'Refuse Applicant',
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': view_id,
			'res_id': ids and ids[0] or None,
			'res_model': 'hr.applicant',
			'context': {
				'refusal_mode': True,
				'bypass_requirement_check': True,
			},
			'target': 'new',
		}

	def action_refuse_applicant_save(self, cr, uid, ids, context={}):
		return True
	
# method untuk mengecek applicant yang duplicate
	def check_duplicate_applicant(self, cr, uid, vals, param_list=[]):
		if not vals: return False
		applicant_obj = self.pool.get('hr.applicant')
		employee_obj = self.pool.get('hr.employee')
		duplicate_ids = {}
		dupli_emp_ids = []
		dupli_app_ids = []
		count_param = 0
	# cek untuk semua param yang ada
	# cari di data employee
		for param_name in param_list:
			if param_name in vals:
				count_param += 1 
				if len(dupli_emp_ids) == 0:
					dupli_emp_ids = employee_obj.search(cr, uid, [(param_name,'=',vals[param_name])])
				else:
					dupli_emp_ids = employee_obj.search(cr, uid, [('id','in',dupli_emp_ids),(param_name,'=',vals[param_name])])
				if count_param >= MIN_CHECK_DUPLI:
					if len(dupli_emp_ids) > 0:
						break
		duplicate_ids['employee'] = dupli_emp_ids
		if len(dupli_emp_ids) > 0:
			return duplicate_ids
		return False
		
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
	# kalau ini driver dan di atas MAX_DRIVER_AGE tahun, maka dia harus diapprove dulu
		if vals.get('job_id'):
			job_obj = self.pool.get('hr.job')
			is_driver = job_obj.is_driver(cr, uid, vals.get('job_id'))
			birth_year = datetime.strptime(vals.get('date_of_birth'),'%Y-%m-%d').year
			if is_driver and date.today().year - birth_year > MAX_DRIVER_AGE:
				model_obj = self.pool.get('ir.model.data')
				model, pending_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job2')
				vals.update({
					'stage_id': pending_stage_id,
					'is_pending': True,
				})
	# check duplicate
		check_dupli = self.check_duplicate_applicant(cr, uid, vals, ['identification_id','gender','name','date_of_birth'])
		if not check_dupli: 
			return False
		else:
			raise osv.except_osv(_('Recruitment Error'),_('Duplicate detected.'))
		return False
		return super(hr_applicant, self).create(cr, uid, vals, context)
		
	def write(self, cr, uid, ids, vals, context={}):
	# buat dipake di bawah
		model_obj = self.pool.get('ir.model.data')
		model, refuse_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job8')
		if not refuse_stage_id:
			raise osv.except_osv(_('Recruitment Error'),_('Cannot find stage Refused. Please contact Developer.'))
		model, pending_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job2')
		if not pending_stage_id:
			raise osv.except_osv(_('Recruitment Error'),_('Cannot find stage Pending Approval. Please contact Developer.'))
	# bila ada perubahan stage
		if vals.get('stage_id'):
		# telusurin satu persatu datanya
			for data in self.browse(cr, uid, ids, context):
			# kalau applicant ini pindah DARI stage Pending Approval, cegah kalau is_pending nya True
			# asumsi kalo masuk ke pending approval maka is_pending nya True
				if data.is_pending == True and not context.get('skip_pending_check') and vals['stage_id'] != refuse_stage_id:
					raise osv.except_osv(_('Recruitment Error'),_('This applicant needs approval from your superior. Please wait for his/her approval before continuing.'))
		# kalau applicant pindah ke Refused, cegah sehingga user harus pakai button Refuse Applicant
			if vals.get('stage_id') == refuse_stage_id:
				raise osv.except_osv(_('Recruitment Error'),_('Cannot directly change stage to Refused. Please use Refuse Applicant button instead.'))
		# kalau applicant ini pindah KE stage Pending Approval maka aktifkan is_pending
			if vals.get('stage_id') == pending_stage_id:
				vals.update({'is_pending': True})
	# kalau ditulis dalam rangka refusal, isi refused_by dan refused_at
		if context.get('refusal_mode'):
			vals.update({
				'refused_date': date.today(),
				'refused_by': uid,
				'stage_id': refuse_stage_id,
				'is_pending': False,
			})
	# yu panggil write-nya
		return super(hr_applicant, self).write(cr, uid, ids, vals, context)
		
	# pengisian/pengosongan date_closed tidak berdasarkan apakah stage ybs folded atau tidak, tapi mengacu ke isi field 
	# is_end dari stage ybs
	def onchange_stage_id(self, cr, uid, ids, stage_id, context=None):
		if not stage_id: return {'value': {}}
		stage = self.pool['hr.recruitment.stage'].browse(cr, uid, stage_id, context=context)
		if stage.is_end:
			return {'value': {'date_closed': fields.datetime.now()}}
		else:
			return {'value': {'date_closed': False}}
	
	def create_employee_from_applicant(self, cr, uid, ids, context=None):
	# ambil stage contract_signed utnuk dibandingkan di bawah
		model_obj = self.pool.get('ir.model.data')
		hr_employee_obj = self.pool.get('hr.employee')
		model, contract_signed_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job7')
	# cek untuk setiap data
		for data in self.browse(cr, uid, ids, context):
		# applicant ini sudah harus sampai tahap contract signed baru bisa jadi employee
			if data.stage_id.id != contract_signed_stage_id:
				raise osv.except_osv(_('Recruitment Error'),_('Applicant must have reach Contract Signed stage to be entitled for employee creation.'))
	# bikin data employee nya
		dict_act_window = super(hr_applicant, self).create_employee_from_applicant(cr, uid, ids, context=context)
	# ambil data applicant kalau ada
		applicant_data = self.browse(cr, uid, ids[0], context=context)
		emp_data = {
			'gender': applicant_data.gender,
			'place_of_birth': applicant_data.place_of_birth,
			'date_of_birth': applicant_data.date_of_birth,
			'religion': applicant_data.religion,
			'driver_license_number': applicant_data.driver_license_number,
			'driver_license_date': applicant_data.driver_license_date,
			'identification_id': applicant_data.identification_id,
			'mobile_phone': applicant_data.partner_mobile,
			'mobile_phone2': applicant_data.partner_mobile2,
			'mobile_phone3': applicant_data.partner_mobile3,
			'overtime_ready': applicant_data.overtime_ready
		}
		hr_employee_obj.write(cr, uid, applicant_data.emp_id.id, emp_data)
		return dict_act_window
			

