from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date


class hr_driver_replacement(osv.osv):
	
	_name = 'hr.driver.replacement'
	_description = 'HR-Driver Replacement'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'driver_original': fields.many2one('hr.employee','Driver Original'),
		'driver_replace': fields.many2one('hr.employee','Driver Replace'),
		'replace_date': fields.date('Replace Date'),
	}