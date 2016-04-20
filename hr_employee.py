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

# ==========================================================================================================================

class hr_employee(osv.osv):
	
	_inherit = 'hr.employee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_type': fields.selection(_DRIVER_TYPE, 'Driver Type'),
		'is_blacklist': fields.boolean('Blacklist?'),
		'blacklist_reason': fields.text('Blacklist Reason'),
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
		