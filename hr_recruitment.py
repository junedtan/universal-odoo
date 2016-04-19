from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

MAX_DRIVER_AGE = 45 # in years

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
		'is_pending': fields.boolean('Pending Approval?',
			help='If checked, this applicant is waiting for SPV/manager\'s approval.'),
		'date_of_birth': fields.date('Date of Birth', required=True),
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
			self.write(cr, uid, data.id, {'stage_id': stage_ids[0]}, context={'skip_pending_check': True})
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
			},
			'target': 'new',
		}
		self.write(cr, uid, ids, {'is_pending': False}, context)
		return True

	def action_refuse_applicant_save(self, cr, uid, ids, context={}):
		return True
		
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	# kalau ini driver dan di atas MAX_DRIVER_AGE tahun, maka dia harus diapprove dulu
	def create(self, cr, uid, vals, context={}):
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
		model, contract_signed_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job7')
	# cek untuk setiap data
		for data in self.browse(cr, uid, ids, context):
		# applicant ini sudah harus sampai tahap contract signed baru bisa jadi employee
			if data.stage_id.id != contract_signed_stage_id:
				raise osv.except_osv(_('Recruitment Error'),_('Applicant must have reach Contract Signed stage to be entitled for employee creation.'))
	# normal deh
		return super(hr_applicant, self).create_employee_from_applicant(cr, uid, ids, context=context)
			

