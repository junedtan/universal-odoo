from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_DRIVER_TYPE = (
	('active','Active'),
	('standby','Stand By'),
	('replacement','Replacement (GS)'),
	('contract','Contracted'),
	('daily','Daily'),
	('internal','Internal/Office')
)

_RELIGION = (
	('islam','Islam'),
	('catholic','Catholic'),
	('protestant','Protestant'),
	('hindu','Hindu'),
	('buddha','Buddha'),
	('konghucu','Konghucu'),
	('other','Other'),
)

# ==========================================================================================================================

class hr_employee(osv.osv):
	
	_inherit = 'hr.employee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_type': fields.selection(_DRIVER_TYPE, 'Driver Type'),
		'is_blacklist': fields.boolean('Blacklist?'),
		'blacklist_reason': fields.text('Blacklist Reason'),
		'emp_no': fields.char('Employee No', size=256),
		'bank_name': fields.char('Bank Name'),
		'bank_acc_owner': fields.char('Bank Acc. Owner Name'),
		'start_working': fields.date('Start Working'),
		'driver_company': fields.char('Company'),
		'homebase': fields.many2one('chjs.region', 'Homebase'),
		'place_of_birth': fields.char('Place of Birth', required=True),
		'date_of_birth': fields.date('Date of Birth', required=True),
		'religion': fields.selection(_RELIGION, 'Religion'),
		'driver_lisence_number': fields.char('Driver Lisence Number'),
		'driver_lisence_date': fields.date('Driver Lisence Expiry Date'),
		'mobile_phone2': fields.char('Mobile 2', size=32),
		'mobile_phone3': fields.char('Mobile 3', size=32),
		'overtime_ready': fields.boolean('Ready to Overtime?'),
		'resign_date': fields.date('Resign date'),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------

	_defaults = {
		'is_blacklist': False,
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
		