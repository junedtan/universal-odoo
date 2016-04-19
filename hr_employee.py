from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_DRIVER_TYPE = (
	('active','Active'),
	('standby','Stand By')
	('replacement','Replacement (GS)')
	('contract','Contracted'),
	('daily','Daily'),
	('internal','Internal (Office)')
)

class hr_employee(osv.osv):
	
	_inherit = 'hr.employee'
	
	_columns = {
		'driver_type': fields.selection(_DRIVER_TYPE, 'Driver Type'),
	}
	
	#def create(self, cr, uid, vals, context={}):
		