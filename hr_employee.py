from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
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
		'religion': fields.selection(RELIGION, 'Religion'),
		'driver_license_number': fields.char('License Number'),
		'driver_license_date': fields.date('License Expiry Date'),
		'driver_area': fields.char('Coverage Area', size=500),
		'npwp': fields.char('NPWP'),
		'language': fields.char('Language', size=500),
		'transportation': fields.char('Transportation', size=500),
		'residence_location': fields.char('Residence Location', size=500),
		'identification_id': fields.char('ID No', required=True),
		'mobile_phone_2': fields.char('Mobile 2', size=32),
		'mobile_phone_3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready for Overtime?'),
		'holiday_ready': fields.boolean('Work at Weekend/Holiday?'),
		'residential_address': fields.text('Residential Address'),
		'residential_phone': fields.char('Residential Phone', size=32),
		'address': fields.text('Current Address'),
		'phone': fields.char('Phone', size=32),
		'start_working': fields.date('Start Working'),
		'driver_company_id': fields.many2one('res.partner','Current Client', domain=[('customer','=',True)]),
		'homebase_id': fields.many2one('chjs.region', 'Homebase', domain=[('type','=','city')]),
	}
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
	# kalau jobnya driver, maka set driver_type menjadi 'active'
		job_id = vals.get('job_id')
		if job_id:
			job_obj = self.pool.get('hr.job')
			if job_obj.is_driver(cr, uid, job_id):
				vals.update({'driver_type': 'active'})
	# panggil create biasa
		return super(hr_employee, self).create(cr, uid, vals, context)
		