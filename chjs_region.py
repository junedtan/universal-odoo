from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class chjs_region(osv.osv):
	
	_inherit = 'chjs.region'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'default_wage': fields.float('Default Wage'),
	}