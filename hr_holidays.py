from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

class hr_holidays(osv.osv):
	
	_inherit = 'hr.holidays'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'active': fields.boolean('Active'),
	}
	
# DEFAULTS -----------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'active': True,
	}
	
# ==========================================================================================================================

class hr_holidays_reset_memory(osv.osv_memory):
	
	_name = 'hr.holidays.reset.memory'
	_description = 'HR-Holidays Reset'
	
	_columns = {
		'reset_before': fields.date('Reset Before:', required=True),
		'category_id': fields.many2one('hr.employee.category', "Employee Tag", help='If empty, this action will reset all employee holidays'),
		'reset_type': fields.selection([('remove','Leave Request'),('add','Allocation Request')], 'Request Type'),  
	}
	
# ======= ACTION MEMORY ==================================================================
	
	def create(self, cr, uid, vals, context=None):
		if 'reset_before' not in vals: return False
		emp_obj = self.pool.get('hr.employee')
		holiday_obj = self.pool.get('hr.holidays')
		emp_ids = []
		domain = [('date_to','<=',vals['reset_before'])]
	# cari employee berdasarkan tag kalau ada
		if vals['category_id']:
			emp_ids = emp_obj.search(cr, uid, [('category_ids', 'child_of', [vals['category_id']])])
			domain.append(('employee_id','in',emp_ids))
	# kalau ada type nya, isi ke domain
		if vals['reset_type']:
			domain.append(('type','=',vals['reset_type']))
		holiday_ids = holiday_obj.search(cr, uid, domain)
	# non aktifkan liburan sebelum tanggal ini
		if len(holiday_ids) > 0:
			holiday_obj.write(cr, uid, holiday_ids, {'active': False})
		return True
	


