from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from . import RELIGION, DRIVER_TYPE

# ==========================================================================================================================

class hr_employee(osv.osv):
	
	_inherit = 'hr.employee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_type': fields.selection(DRIVER_TYPE, 'Driver Type'),
		'emp_no': fields.char('Employee No', size=32, readonly=True),
		'place_of_birth': fields.char('Place of Birth', size=100),
		'date_of_birth': fields.date('Date of Birth', required=True),
		'interview_date': fields.date('Interview Date'),
		'religion': fields.selection(RELIGION, 'Religion'),
		'driver_license_number': fields.char('License Number'),
		'driver_license_date': fields.date('License Expiry Date'),
		'driver_area': fields.char('Coverage Area', size=500),
		'npwp': fields.char('NPWP'),
		'language': fields.char('Language', size=500),
		'transportation': fields.char('Transportation', size=500),
		'residence_location': fields.char('Residence Location', size=500),
		'identification_id': fields.char('ID No', required=True),
		'mobile_phone2': fields.char('Mobile 2', size=32),
		'mobile_phone3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready for Overtime?'),
		'holiday_ready': fields.boolean('Work at Weekend/Holiday?'),
		'residential_address': fields.text('Residential Address'),
		'residential_phone': fields.char('Residential Phone', size=32),
		'address': fields.text('Current Address'),
		'phone': fields.char('Phone', size=32),
		'start_working': fields.date('Start Working', required=True),
		'work_year': fields.float('Work Year(s)'),
		'driver_company_id': fields.many2one('res.partner','Current Client', domain=[('customer','=',True)]),
		'homebase_id': fields.many2one('chjs.region', 'Homebase', domain=[('type','=','city')]),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'start_working': lambda *a: datetime.today().strftime('%Y-%m-%d'),
	}
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
	# kalau jobnya driver, maka set driver_type menjadi 'active'
		job_id = vals.get('job_id')
		if job_id:
			job_obj = self.pool.get('hr.job')
			if job_obj.is_driver(cr, uid, job_id):
				vals.update({'driver_type': 'active'})
	# siapkan data untuk employee code
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
	
# CRON --------------------------------------------------------------------------------------------------------------------------
	
	def cron_employee_work_year(self, cr, uid, context=None):
	# ambil data employee yang mau dihitung
		emp_ids = self.search(cr, uid, [('emp_state','!=','resign')])
		if not emp_ids: return
	# hitung masa kerja employee dari sejak mulai kerja hingga sekarang
		today_date = date.today()
		work_year = 0
		for row in self.browse(cr, uid, emp_ids):
			start_working = datetime.strptime(row.start_working,'%Y-%m-%d').date()
			work_year = abs((today_date - start_working).days)/365.0
			self.write(cr, uid, row.id, {'work_year': work_year}, context)
			
			