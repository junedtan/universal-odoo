from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class res_users(osv.osv):
	
	_inherit = 'res.users'
	
	_columns = {
		'pin': fields.char('PIN', size=64, copy=False),
	}
	
