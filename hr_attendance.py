from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_ATTENDANCE_SOURCE = (
	('manual',_('Manual')),
	('rfid',_('RFID')),
	('app',_('App')),
)

_OUT_OF_TOWN = (
	('no','No'),
	('roundtrip','Roundtrip'),
	('overnight','Overnight'),
)

class hr_attendance(osv.osv):
	
	_inherit = 'hr.attendance'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('hr.contract','Contract Reference'),
		'customer_approval': fields.datetime('Customer Approval'),
		'source': fields.selection(_ATTENDANCE_SOURCE,'Source'),
		'out_of_town': fields.selection(_OUT_OF_TOWN, 'Out of Town?'),
	}
	
	_defaults = {
		'out_of_town': 'no',
		'source': 'manual',
	}
	
