from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_ATTENDANCE_SOURCE = [
	('manual',_('Manual')),
	('rfid',_('RFID')),
	('website',_('Website')),
]

class hr_attendance(osv.osv):
	
	_inherit = 'hr.attendance'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('hr.contract','Contract Reference'),
		'customer_approval': fields.datetime('Customer Approval'),
		'source': fields.selection(_ATTENDANCE_SOURCE,'Source'),
	}