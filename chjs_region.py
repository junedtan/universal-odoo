from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta

class chjs_region(osv.osv):

	_inherit = 'chjs.region'

	_columns = {
		'emergency_number': fields.char('Emergency Number'),
	}