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

	def create(self, cr, uid, vals, context={}):
		new_id = super(resource_calendar, self).create(cr, uid, vals, context=context)
	# ambil hari libur nasional dan masukkan sebagai leave untuk working time ini
		holiday_obj = self.pool.get('resource.calendar.company.holiday')
		holiday_ids = holiday_obj.search(cr, uid, [])
		leaves_data = []
		for holiday in holiday_obj.browse(cr, uid, holiday_ids):
			leaves_data.append([0,False,{
				'name': holiday.name,
				'date_from': datetime.strptime(holiday.date_from,'%Y-%m-%d').strftime("%Y-%m-%d 00:00:00"),
				'date_to': datetime.strptime(holiday.date_to,'%Y-%m-%d').strftime("%Y-%m-%d 23:59:59"),
				'company_holiday_id': holiday.id,
			}])
		self.write(cr, uid, [new_id], {
			'leave_ids': leaves_data,
		})
		return new_id

# ==========================================================================================================================
