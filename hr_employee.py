from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from . import RELIGION, DRIVER_TYPE

# ==========================================================================================================================

class hr_employee(osv.osv):
	
	_inherit = 'hr.employee'
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------
	
# cek apakah employee ini driver atau bukan
	def emp_is_driver(self, cr, uid, ids, context={}):
		if not ids: return False
		if isinstance(ids, int) == False: ids = ids[0]
		job_obj = self.pool.get('hr.job')
		employee_data = self.browse(cr, uid, ids)
		is_driver = job_obj.is_driver(cr, uid, employee_data.job_id.id)
		return is_driver
	
	def _broadcast_changed_driver_phone(self, cr, uid, ids, vals, context={}):
		"""
		Broadcast ke dirty jika HR mengganti nomor handphone supir untuk mengganti semua field nomor hape supir di setiap
		order yang sudah ada di app dalam state [new, confirmed, ready, started]
		"""
		order_obj = self.pool.get('foms.order')
	# kalau nomor2 hapenya berubah
		phone1 = vals.get('phone', False)
		phone2 = vals.get('mobile_phone2', False)
		phone3 = vals.get('mobile_phone3', False)
		if phone1 or phone2 or phone3:
		# kalau jobnya driver, update ke semua order2 di app yang beliau pernah tangani pake dirty
			order_ids = order_obj.search(cr, uid, [('state', 'in', ['new', 'confirmed', 'ready', 'started'])])
			orders = order_obj.browse(cr, uid, order_ids)
			for id in ids:
				for order in orders:
				# Kalau actual_driver_id adalah supir ini, tambahin di yang nanti update
				# Kalau bukan, cek kalau assigned_driver_id adalah supir ini, kalau ya tambahin di yang nanti update
				# Ini mencegah kalau2 dia cuman assigned driver tapi bukan actual
					if order.actual_driver_id.id == id \
						or (order.actual_driver_id is False and order.assigned_driver_id.id == id):
						data_columns = {
							'driver_mobile': order.driver_mobile
						}
						order_obj.webservice_post(cr, uid, ['pic','booker','approver','driver','fullday_passenger'],
							'update', order, data_columns=data_columns, webservice_context={}, context=context)
		
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_type': fields.selection(DRIVER_TYPE, 'Driver Type'),
		'emp_no': fields.char('Employee No', size=32),
		'place_of_birth': fields.char('Place of Birth', size=100),
		'date_of_birth': fields.date('Date of Birth'),
		'interview_date': fields.date('Interview Date'),
		'last_survey_date': fields.date('Last Survey Date'),
		'religion': fields.selection(RELIGION, 'Religion'),
		'driver_license_number': fields.char('License Number'),
		'driver_license_date': fields.date('License Expiry Date'),
		'driver_area': fields.char('Coverage Area', size=500),
		'npwp': fields.char('NPWP'),
		'personal_email': fields.char('Personal Email', size=200),
		'language': fields.char('Language', size=500),
		'transportation': fields.char('Transportation', size=500),
		'residence_location': fields.char('Residence Location', size=500),
		'identification_id': fields.char('ID No'),
		'mobile_phone2': fields.char('Mobile 2', size=32),
		'mobile_phone3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready for Overtime?'),
		'holiday_ready': fields.boolean('Work at Weekend/Holiday?'),
		'residential_address': fields.text('Residential Address'),
		'residential_phone': fields.char('Residential Phone', size=32),
		'address': fields.text('Current Address'),
		'phone': fields.char('Phone', size=32, required=True),
		'start_working': fields.date('Start Working', required=True),
		'work_year': fields.float('Work Year(s)'),
		'driver_company_id': fields.many2one('res.partner','Current Client', domain=[('customer','=',True)]),
		'homebase_id': fields.many2one('chjs.region', 'Homebase'),
		'verbal_ids': fields.one2many('universal.verbal.warning', 'employee_id', 'Verbal Warnings'),
		'cron_leaves': fields.boolean('Cron Leaves'),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'start_working': lambda *a: datetime.today().strftime('%Y-%m-%d'),
		'driver_type': 'active'
	}
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
	# kalau jobnya driver, maka set driver_type menjadi 'active'
		job_id = vals.get('job_id')
		if job_id:
			job_obj = self.pool.get('hr.job')
			if not vals.get('driver_type') and job_obj.is_driver(cr, uid, job_id):
				vals.update({'driver_type': 'active'})
	# siapkan data untuk employee code
		if not vals.get('emp_no',False):
			start_working = ''
			if 'start_working' in vals:
				start_working = datetime.strptime(vals['start_working'],'%Y-%m-%d').strftime('%d%m%y')
			else:
				start_working = datetime.today().strftime('%d%m%y')
			emp_seq = self.pool.get('ir.sequence').next_by_code(cr, uid, 'hr.employee.seq')
			emp_no = '%s.%s' % (emp_seq, start_working)
			vals.update({'emp_no': emp_no})
	# panggil create biasa
		return super(hr_employee, self).create(cr, uid, vals, context)
	
	def write(self, cr, uid, ids, vals, context={}):
		result = super(hr_employee, self).write(cr, uid, ids, vals, context)
		self._broadcast_changed_driver_phone(cr, uid, ids, vals, context)
		return result

	def name_get(self, cr, uid, ids, context={}):
		if isinstance(ids, (list, tuple)) and not len(ids): return []
		if isinstance(ids, (long, int)): ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids):
			name = record.name
			if record.emp_no:
				name = '%s (%s)' % (record.name, record.emp_no)
			res.append((record.id, name))
		return res

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
		if not args: args = []
		if not context: context = {}
		if name:
			ids = self.search(cr, uid, ['|',('name', operator, name),('emp_no', operator, name)] + args, limit=limit, context=context)
		else:
			ids = self.search(cr, uid, args, limit=limit, context=context)
		return self.name_get(cr, uid, ids, context)

# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	# kalau isi nama aplikan, isi langsung field bawahnya biar ga usa 2x isi
	def onchange_applicant_name(self, cr, uid, ids, name, context=None):
		if not name: return {'value': {}}
		v = {}
		v['partner_name'] = name 
		return {'value': v}
		
	# kalau isi job, isi departmentnya juga
	def onchange_job_id(self, cr, uid, ids, job_id, context=None):
		if not job_id: return {'value': {}}
		v = {}
		job_data = self.pool.get('hr.job').browse(cr,uid,job_id)
		v['department_id'] = job_data.department_id 
		return {'value': v}
		
# CRON --------------------------------------------------------------------------------------------------------------------------
	
	def cron_employee_work_year(self, cr, uid, context=None):
	# ambil data employee yang mau dihitung
		emp_ids = self.search(cr, uid, [])
		if not emp_ids: return
	# hitung masa kerja employee dari sejak mulai kerja hingga sekarang
		today_date = date.today()
		work_year = 0
		for row in self.browse(cr, uid, emp_ids):
			start_working = datetime.strptime(row.start_working,'%Y-%m-%d').date()
			work_year = abs((today_date - start_working).days)/365.0
			self.write(cr, uid, row.id, {'work_year': work_year}, context)
	
	def cron_calculate_leaves(self, cr, uid, context=None):
	# ambil id cuti legal
		model_obj = self.pool.get('ir.model.data')
		model, legal_id = model_obj.get_object_reference(cr, uid, 'hr_holidays', 'holiday_status_cl')
	# ambil semua employee yg belum dihitung cuti legalnya
		emp_obj = self.pool.get('hr.employee')
		holiday_obj = self.pool.get('hr.holidays')
		emp_ids = emp_obj.search(cr, uid, [('cron_leaves','=',False)])
		if len(emp_ids) > 0:
		# bikin cuti legalnya
			today_date = date.today()
			this_year = today_date.strftime('%Y')
			this_month = today_date.strftime('%m')
			for emp_data in emp_obj.browse(cr, uid, emp_ids):
				start_working = datetime.strptime(emp_data.start_working,'%Y-%m-%d')
			# kalau tahunnya sama baru dikurangin
				if start_working.strftime('%Y') == this_year:
					month_left = 12 - int(start_working.strftime('%m'))
				else:
					month_left = 12 - int(this_month)
			# buat alokasi cutinya
				holiday_id = holiday_obj.create(cr, uid, {
					'name': "Alokasi tahunan %s" % this_year,
					'holiday_status_id': legal_id,
					'number_of_days_temp': month_left,
					'mode': 'employee',
					'employee_id': emp_data.id,
					'type': 'add',
					'state': 'validate'
				})
			# confirm langsung
				holiday_obj.holidays_validate(cr, uid, [holiday_id])
			# update status employeenya supaya tidak dihitung ulang
			emp_obj.write(cr, uid, emp_ids, {'cron_leaves': True})
			
