from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta

class chjs_region(osv.osv):

	_inherit = 'chjs.region'

	_columns = {
		'sequence': fields.integer('Sequence'),
		'emergency_number': fields.char('Emergency Number'),
		'active': fields.boolean('Active'),
	}

	_defaults = {
		'active': True,
	}

	_order = 'sequence'