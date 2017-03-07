from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

from . import MAX_DRIVER_AGE, MIN_STAFF_AGE, MARITAL_STATUS, RELIGION, FAMILY_RELATIONSHIP, MIN_CHECK_DUPLI, PARAM_CHECK_DUPLI, EMP_APP_DICT, DOMAIN_DUPLI_DICT, EMPLOYEE_FIELD

_TERMINATE_TYPE = (
	('fired','Fired'),
	('resigned','Resigned'),
	('retire','Retired'),
)

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

	
# CRON --------------------------------------------------------------------------------------------------------------------------
	
	def cron_job_deadline(self, cr, uid, context=None):
	# buat dulu semuanya jadi is_late False
		recruit_job_ids = self.search(cr, uid, [('state','=','recruit')])
		if not recruit_job_ids: return
		app_obj = self.pool.get('hr.applicant')
		stage_obj = self.pool.get('hr.recruitment.stage')
		recruit_app_ids = app_obj.search(cr, uid, [('job_id','in',recruit_job_ids)])
		app_obj.write(cr, uid, recruit_app_ids, {'is_late': False})
	# ambil data job yang mau dicek
		job_ids = self.search(cr, uid, [('deadline','<',datetime.today().strftime('%Y-%m-%d'))])
		if not job_ids: return
	# ambil stage finish
		stage_ends = stage_obj.search(cr, uid, [('is_end','=',True)])
	# cek aplikan2 yang deadlinenya sudah melebihi batas waktu recruitment dan belum ada keputusan
		for row in self.browse(cr, uid, job_ids):
			app_ids = app_obj.search(cr, uid, [('job_id','=',row.id),('stage_id','not in',stage_ends)])
		# update is_late nya aplikan
			app_obj.write(cr, uid, app_ids, {'is_late': True})
	
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
		'interview_ids': fields.one2many('universal.applicant.interview','applicant_id','Interviews'),
		'survey_date': fields.date('Survey Date'),
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
		'partner_mobile': fields.char('Mobile', size=32, required=True),
		'partner_mobile2': fields.char('Mobile 2', size=32),
		'partner_mobile3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready for Overtime?'),
		'holiday_ready': fields.boolean('Work at Weekend/Holiday?'),
		'refused_date': fields.date('Refused At', readonly=True),
		'refused_by': fields.many2one('res.users', 'Refused By', readonly=True),
		'refused_reason': fields.text('Refuse Reason'),
		'is_blacklist': fields.boolean('Blacklist?'),
		'blacklist_reason': fields.text('Blacklist Reason'),
		'is_late': fields.boolean('Delayed Decision?'),
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
		duplicate_ids = {'employee':[], 'applicant':[]}
		dupli_emp_ids = []
		dupli_app_ids = []
		count_param = 0
	# cek untuk semua param yang ada
	# cari di data employee
	# active_test: False buat mengecek yang active nya false juga, ga cuma yang true
		for param_name in param_list:
			if param_name in vals:
				count_param += 1 
			# cek domain yg dipakai
				domain_check = '='
				if param_name in DOMAIN_DUPLI_DICT:
					domain_check = DOMAIN_DUPLI_DICT[param_name]
				if count_param == 1:
				# kalau parameternya date ubah dulu formatnya dari %d/%m/%Y ke %Y-%m-%d
					if param_name == 'date_of_birth':
						vals['date_of_birth'] = datetime.strptime(vals['date_of_birth'], '%d/%m/%Y').strftime('%Y-%m-%d')
					dupli_emp_ids = employee_obj.search(cr, uid, [(param_name,domain_check,vals[param_name])], context={'active_test': False})
				else:
				# kalau hasil dari pencarian pertama ada, lanjutkan pencarian
					if len(dupli_emp_ids) > 0:
						dupli_emp_ids = employee_obj.search(cr, uid, [('id','in',dupli_emp_ids),(param_name,domain_check,vals[param_name])], context={'active_test': False})
				# kalau ngga ada ya break aja	
					else:
						break
			# kalau uda lewat dari minimal pencarian & ada hasilnya, break
				if count_param >= MIN_CHECK_DUPLI:
					if len(dupli_emp_ids) > 0:
						break
		duplicate_ids['employee'] = dupli_emp_ids
	# kalau di employee uda ada yg duplicate, ya langsung return aja
		if len(dupli_emp_ids) > 0:
			return duplicate_ids
	# cari di data applicant
		count_param = 0
		for param_name in param_list:
		# cek dulu namanya beda ga sama yang di employee
			if param_name in EMP_APP_DICT:
				param_name = EMP_APP_DICT[param_name]
		# baru lanjut lagi
			if param_name in vals:
				count_param += 1 
			# cek domain yg dipakai
				domain_check = '='
				if param_name in DOMAIN_DUPLI_DICT:
					domain_check = DOMAIN_DUPLI_DICT[param_name]
				if count_param == 1:
					dupli_app_ids = applicant_obj.search(cr, uid, [(param_name,domain_check,vals[param_name])], context={'active_test': False})
				else:
				# kalau hasil dari pencarian pertama ada, lanjutkan pencarian
					if len(dupli_app_ids) > 0:
						dupli_app_ids = applicant_obj.search(cr, uid, [('id','in',dupli_app_ids),(param_name,domain_check,vals[param_name])], context={'active_test': False})
				# kalau ngga ada ya break aja
					else:
						break
			# kalau uda lewat dari minimal pencarian & ada hasilnya, break
				if count_param >= MIN_CHECK_DUPLI:
					if len(dupli_app_ids) > 0:
						break
		duplicate_ids['applicant'] = dupli_app_ids
	# kalau ada duplicate ya return datanya
		if len(dupli_app_ids) > 0:
			return duplicate_ids
		return False
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		model_obj = self.pool.get('ir.model.data')
		model, pending_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job2')
	# kalau ini driver dan di atas MAX_DRIVER_AGE tahun, maka dia harus diapprove dulu
		if vals.get('job_id'):
			job_obj = self.pool.get('hr.job')
			is_driver = job_obj.is_driver(cr, uid, vals.get('job_id'))
			birth_year = datetime.strptime(vals.get('date_of_birth'),'%Y-%m-%d').year
			if is_driver and date.today().year - birth_year > MAX_DRIVER_AGE:
				vals.update({
					'stage_id': pending_stage_id,
					'is_pending': True,
				})
		# cek minimal umurnya juga, minimal MIN_STAFF_AGE
			if date.today().year - birth_year < MIN_STAFF_AGE:
				vals.update({
					'stage_id': pending_stage_id,
					'is_pending': True,
				})
	
	# check duplicate
		check_dupli = self.check_duplicate_applicant(cr, uid, vals, ['identification_id','gender','name'])
	# kalau ada duplicate, statenya jadi pending
		if isinstance(check_dupli, dict):
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
			# kalau applicant stagenya sudah refuse, ga boleh pindah2 stage lagi
				if data.stage_id.id == refuse_stage_id:
					raise osv.except_osv(_('Recruitment Error'),_('Cannot change stage after Refused.'))
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
		
	def action_makeMeeting(self, cr, uid, ids, context=None):
		applicant_data = self.browse(cr, uid, ids[0], context)
		data_obj = self.pool.get('ir.model.data')
		action_id = data_obj.get_object(cr, uid, 'universal', 'universal_action_interview_schedule').id
		action_obj = self.pool.get('ir.actions.act_window')
		action_data = action_obj.read(cr, uid, action_id)
		action_data.update({
			'context': {
				'default_applicant_id': applicant_data.id,
				'readonly_applicant': 1,
			},
		})
		return action_data

# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	# kalau isi nama aplikan, isi langsung field bawahnya biar ga usa 2x isi
	def onchange_applicant_name(self, cr, uid, ids, name, context=None):
		if not name: return {'value': {}}
		v = {}
		v['partner_name'] = name 
		return {'value': v}
		
		
	# pengisian/pengosongan date_closed tidak berdasarkan apakah stage ybs folded atau tidak, tapi mengacu ke isi field 
	# is_end dari stage ybs
	def onchange_stage_id(self, cr, uid, ids, stage_id, context=None):
		v = {}
		if not stage_id: return {'value': {}}
		stage = self.pool['hr.recruitment.stage'].browse(cr, uid, stage_id, context=context)
	# cek stagenya
		data_obj = self.pool.get('ir.model.data')
		interview_stage = data_obj.get_object(cr, uid, 'universal', 'stage_job4').id
		if stage.id == interview_stage: 
			v['interview_date'] = fields.datetime.now()
		if stage.is_end:
			v['date_closed']= fields.datetime.now()
		else:
			v['date_closed']= False
		return {'value': v}
	
	def create_employee_from_applicant(self, cr, uid, ids, context=None):
	# ambil stage contract_signed utnuk dibandingkan di bawah
		model_obj = self.pool.get('ir.model.data')
		hr_employee_obj = self.pool.get('hr.employee')
		hr_employee_family_obj = self.pool.get('hr.employee.family')
		model, contract_signed_stage_id = model_obj.get_object_reference(cr, uid, 'universal', 'stage_job7')
		applicant_data = self.browse(cr, uid, ids[0], context=context)
	# cek untuk setiap data
		empty_field = ''
		for data in self.browse(cr, uid, ids, context):
		# applicant ini sudah harus sampai tahap accepted baru bisa jadi employee
			if data.stage_id.id != contract_signed_stage_id:
				raise osv.except_osv(_('Recruitment Error'),_('Applicant must have reach Accepted stage to be entitled for employee creation.'))
		# cek apakah data2 wajib di employee sudah diisi semua
			for emp_field, label in EMPLOYEE_FIELD.iteritems():
				if not getattr(applicant_data,emp_field):
					empty_field = empty_field + '\n' + label
		# khusus untuk status nikah, cek kalau sudah menikah harus ada data nomer KK
			if data.marital_status == 'married':
				if not data.family_card_number:
					empty_field = empty_field + '\n' + 'Family Reg. No'
		if empty_field != '':
			raise osv.except_osv(_('Recruitment Error'),_('Applicant must write down these data before becoming employee: %s.' % empty_field))
	# bikin data employee nya
		dict_act_window = super(hr_applicant, self).create_employee_from_applicant(cr, uid, ids, context=context)
	# ambil data applicant kalau ada
		emp_data = {
			'gender': applicant_data.gender,
			'place_of_birth': applicant_data.place_of_birth,
			'date_of_birth': applicant_data.date_of_birth,
			'interview_date': applicant_data.interview_date,
			'religion': applicant_data.religion,
			'driver_license_number': applicant_data.driver_license_number,
			'driver_license_date': applicant_data.driver_license_date,
			'identification_id': applicant_data.identification_id,
			'phone': applicant_data.partner_mobile,
			'mobile_phone': applicant_data.partner_mobile,
			'mobile_phone2': applicant_data.partner_mobile2,
			'mobile_phone3': applicant_data.partner_mobile3,
			'personal_email': applicant_data.email_from,
			'npwp': applicant_data.npwp,
			'overtime_ready': applicant_data.overtime_ready,
			'holiday_ready': applicant_data.holiday_ready,
			'driver_area': applicant_data.driver_area,
			'language': applicant_data.language,
			'transportation': applicant_data.transportation,
			'address': applicant_data.partner_address,
			'residence_location': applicant_data.residence_location,
			'residential_address': applicant_data.residential_address,
			'residential_phone': applicant_data.residential_phone,
			'family_card_number': applicant_data.family_card_number,
		}
		hr_employee_obj.write(cr, uid, applicant_data.emp_id.id, emp_data)
	# bikin data family kalau ada
		if applicant_data.family_contact_name:
			hr_employee_family_obj.create(cr, uid, {
				'employee_id': applicant_data.emp_id.id,
				'name': applicant_data.family_contact_name,
				'family_relationship': applicant_data.family_contactable_relationship or None,
				'address': applicant_data.family_contactable_address or "",
				'contact_number': applicant_data.family_contactable_phone or "",
				}
			)
	# kalau contactablenya bukan spouse, bikin row baru
		if applicant_data.family_contactable_relationship != "spouse" and applicant_data.marital_status == "married":
			hr_employee_family_obj.create(cr, uid, {
				'employee_id': applicant_data.emp_id.id,
				'name': applicant_data.spouse_name,
				'family_relationship': "spouse",
				}
			)
	# kalau semua data sudah dicopy, set pelamar menjadi non aktif
		self.write(cr, uid, ids, {'active': False})
		return dict_act_window

# ==========================================================================================================================
			
class universal_applicant_interview(osv.osv_memory):
	
	_name = 'universal.applicant.interview'
	_description = 'Universal - Applicant Interview Sessions'
	
	_columns = {
		'applicant_id': fields.many2one('hr.applicant', 'Applicant', required=True),
		'date_start': fields.datetime('Start Time', required=True),
		'date_end':fields.datetime('End Time', required=True),
		'interviewer_id': fields.many2one('hr.employee', 'Main Interviwer'),
		'notes': fields.text('Notes/Remarks'),
	}
	
# ==========================================================================================================================
			
class universal_check_duplicate_memory(osv.osv_memory):
	
	_name = 'universal.check.duplicate.memory'
	_description = 'Universal - Check Duplicate'
	
	_columns = {
		'check_duplicate_lines': fields.one2many('universal.check.duplicate.lines','check_duplicate_id','Parameter Fields'),
	}
	
	def name_get(self, cr, uid, ids, context={}):
		result = []
		for id in ids:
			result.append((id,_('Check for Duplicate Applicant')))
		return result
	
# CUSTOM METHOD -----------------------------------------------------------------------------------------------------------

	# cek apakah param sudah terurut
	def check_sorted_list(self, cr, uid, param_list):
		if not param_list or len(param_list) == 0: return True
	# isi list planned_seq yang sudah ada di agent listnya
	# kalau belum ada, tambahkan. kalau sudah ada, berarti ada yang double, return False
	# dan juga harus ada yang seq nya 0
		seq_list = []
		max_seq = len(param_list)
		check_dupli_line_obj = self.pool.get('universal.check.duplicate.lines')
		for param in param_list:
			param_seq = 0
			if 'param_seq' in param:
				param_seq = param['param_seq']
		# kalau record baru, langsung ambil planned seq nya
			elif param[0] == 0:
				if 'param_seq' in param[2]:
					param_seq = param[2]['param_seq']
		# kalau datanya ada yang diubah, ambil lagi
			elif param[0] == 1 or param[0] == 4:
				param_seq = check_dupli_line_obj.read(cr, uid, param[1], ['param_seq'])['param_seq']
		# baru cek sorted nya
			if param_seq and param_seq not in seq_list and param_seq <= max_seq:
				seq_list.append(param_seq)
			else:
				return False
		return True
	
# ACTION BUTTON HANDLER ----------------------------------------------------------------------------------------------------
	
	def action_check_duplicate(self, cr, uid, ids, context=None):
		app_obj = self.pool.get('hr.applicant')
		emp_obj = self.pool.get('hr.employee')
		termi_log_obj = self.pool.get('hr.employee.termination.log')
		check_dupli_line = []
		check_vals = {}
		check_param = []
		dupli_emp_ids = []
		dupli_app_ids = []
		has_duplicates = False
		for data in self.browse(cr, uid, ids, context=context):
			if len(data.check_duplicate_lines) > 0:
				for dupli_line in data.check_duplicate_lines:
					check_dupli_line.append({
						'param_seq': dupli_line.param_seq,
						'param_name': dupli_line.param_name,
						'param_value': dupli_line.param_value
					})
					check_vals[dupli_line.param_name] = dupli_line.param_value
		order_param_data = sorted(check_dupli_line, key=lambda k: k['param_seq'])
		for order_data in order_param_data:
			check_param.append(order_data['param_name'])
	# cek hasil duplicatenya
		result_dupli = app_obj.check_duplicate_applicant(cr, uid, check_vals, check_param)
		if isinstance(result_dupli, dict):
			has_duplicates = True
			dupli_emp_ids = result_dupli['employee'] # ini ceritanya hasil pencarian duplicate di employee
			dupli_app_ids = result_dupli['applicant']
	# di check.duplicate.result ada o2m ke check.duplicate.result.employee dan check.duplicate.result.applicant
	# di bawah ini siapkan variabel untuk dijadikan nilai default kedua field itu
		employee_default = []
		for employee_id in dupli_emp_ids:
		# ambil data termination log kalau ada
			emp_data = emp_obj.browse(cr, uid, employee_id)
			termi_log_ids = termi_log_obj.search(cr, uid, [('employee_id','=',employee_id)], order='id desc', context={'active_test': False})
			if len(termi_log_ids) > 0:
				termi_data = termi_log_obj.browse(cr, uid, termi_log_ids[0])
				employee_default.append({
					'employee_id': employee_id,
					'terminate_date': termi_data.terminate_date,
					'terminate_by': termi_data.terminate_by,
					'terminate_type': termi_data.terminate_type,
					'is_blacklist': termi_data.is_blacklist,
					'blacklist_reason': termi_data.blacklist_reason,
				})
			else:
				employee_default.append({
					'employee_id': employee_id,
					'terminate_date': emp_data.terminate_date,
					'terminate_by': emp_data.terminate_by.id,
					'terminate_type': emp_data.terminate_type,
					'is_blacklist': emp_data.is_blacklist,
					'blacklist_reason': emp_data.blacklist_reason,
				})
		applicant_default = []
		for applicant_id in dupli_app_ids:
			applicant_default.append({
				'applicant_id': applicant_id
			})
		return {
			'type': 'ir.actions.act_window',
			'name': 'Duplicate Search Result',
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'universal.check.duplicate.result',
			'context': {
				'default_has_duplicates': has_duplicates,
				'default_duplicate_employee_line': employee_default,
				'default_duplicate_applicant_line': applicant_default,
			},
			'target': 'new',
		}
	
# ==========================================================================================================================

class universal_check_duplicate_lines(osv.osv_memory):
	
	_name = 'universal.check.duplicate.lines'
	_description = 'Universal - Check Duplicate Lines'
	
	_columns = {
		'check_duplicate_id': fields.many2one('universal.check.duplicate.memory','Check Duplicate Reference', required=True, ondelete='cascade', select=True),
		'param_name': fields.selection(PARAM_CHECK_DUPLI, 'Parameter'),
		'param_value': fields.char('Value'),
		'param_seq': fields.integer('Sequence'),
	}

# ==========================================================================================================================

class universal_check_duplicate_result(osv.osv_memory):
	
	_name = 'universal.check.duplicate.result'
	_description = 'Universal - Check Duplicate Result'
	
	_columns = {
		'has_duplicates': fields.boolean('Has Duplicates?', readonly=True),
		'duplicate_employee_line': fields.one2many('universal.check.duplicate.result.employee', 'header_id', 'Employees', readonly=True),
		'duplicate_applicant_line': fields.one2many('universal.check.duplicate.result.applicant', 'header_id', 'Applicants', readonly=True),
	}

# ==========================================================================================================================

class universal_check_duplicate_result_employee(osv.osv_memory):
	
	_name = 'universal.check.duplicate.result.employee'
	_description = 'Universal - Check Duplicate Result Employee'
	
	_columns = {
		'header_id': fields.many2one('universal.check.duplicate.result', 'Header'),
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'date_of_birth': fields.related('employee_id','date_of_birth',type="date",string="Date of Birth"),
		'gender': fields.related('employee_id','gender',type="selection",selection=[('male', 'Male'), ('female', 'Female')],string="Gender"),
		'identification_id': fields.related('employee_id','identification_id',type="char",string="ID No"),
		'terminate_date': fields.date('Termination Date'),
		'terminate_by': fields.many2one('res.users', 'Terminated By'),
		'terminate_type': fields.selection(_TERMINATE_TYPE, 'Reason'),
		'is_blacklist': fields.boolean('Blacklist?'),
		'blacklist_reason': fields.text('Blacklist Reason'),
	}

# ==========================================================================================================================

class universal_check_duplicate_result_applicant(osv.osv_memory):
	
	_name = 'universal.check.duplicate.result.applicant'
	_description = 'Universal - Check Duplicate Result Applicant'
	
	_columns = {
		'header_id': fields.many2one('universal.check.duplicate.result', 'Header'),
		'applicant_id': fields.many2one('hr.applicant', 'Applicant'),
	}

# ==========================================================================================================================

class universal_launch_recruitment_memory(osv.osv_memory):
	
	_name = 'universal.launch.recruitment.memory'
	_description = 'Universal - Launch Recruitment'
	
	_columns = {
		'job_id': fields.many2one('hr.job','Job', required=True),
		'document_ref': fields.char('Document Ref', size=64, required=True),
		'deadline': fields.date('Deadline',required=True),
		'start_date': fields.date('Start Date',required=True),
		'no_of_recruitment': fields.integer('Expected New Employees', help='Number of new employees you expect to recruit.', required=True),
	}
	
	def _check_recruitment(self, cr, uid, ids, context=None):
		for job in self.browse(cr, uid, ids, context=context):
			if job.no_of_recruitment <= 0:
				return False
		return True
	
	_constraints = [
		(_check_recruitment, "Error: Expected New Employees must be given.", ['no_of_recruitment']),
	]
	
	def action_launch_recruitment(self, cr, uid, ids, context=None):
		job_obj = self.pool.get('hr.job')
		form_data = self.browse(cr, uid, ids[0], context=context)
		job_id = form_data.job_id.id
	# write dulu data2 yg dibutuhkan ke model job
		job_obj.write(cr, uid, [job_id], {
			'document_ref': form_data.document_ref,
			'deadline': form_data.deadline,
			'no_of_recruitment': form_data.no_of_recruitment,
			'start_date': form_data.start_date,
			'deadline': form_data.deadline,
		})
	# baru panggil methodnya
		return job_obj.set_recruit(cr, uid, [job_id], context=context)
	
	