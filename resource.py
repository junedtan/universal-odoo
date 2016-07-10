from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class resource_calendar(osv.osv):
	
	_inherit = 'resource.calendar'
	
	_columns = {
		'leave_ids': fields.one2many('resource.calendar.leaves', 'calendar_id', 'Leaves', help='', copy=True),
	}
	
# OVERRIDE ------------------------------------------------------------------------------------------------------------------

	def copy(self, cr, uid, id, default=None, context=None):
		if default is None:
			default = {}
		if not default.get('name', False):
			default.update(name=_('%s (copy)') % (self.browse(cr, uid, id, context=context).name))
		return super(resource_calendar, self).copy(cr, uid, id, default=default, context=context)

# ==========================================================================================================================
