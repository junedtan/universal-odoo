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
		'reset_before': fields.date('As of Date', required=True),
		'category_id': fields.many2one('hr.employee.category', "Employee Tag", help='If empty, this action will reset all employee holidays', required=True),
		'leave_type': fields.many2one('hr.holidays.status', 'Leave Type', required=True),
		'duration': fields.integer('Duration (days)', required=True),
	}
	
# ======= ACTION MEMORY ==================================================================
	
	def create(self, cr, uid, vals, context=None):
		emp_obj = self.pool.get('hr.employee')
		holiday_obj = self.pool.get('hr.holidays')
		emp_ids = []
		domain = [('date_to','<=',vals['reset_before'])]
	# cari employee berdasarkan tag kalau ada
		emp_ids = emp_obj.search(cr, uid, [('category_ids', 'child_of', [vals['category_id']])])
		domain.append(('employee_id','in',emp_ids))
	# kalau ada type nya, isi ke domain
		domain.append(('holiday_status_id','=',vals['leave_type']))
		holiday_ids = holiday_obj.search(cr, uid, domain)
	# non aktifkan liburan sebelum tanggal ini
		if len(holiday_ids) > 0:
			holiday_obj.write(cr, uid, holiday_ids, {'active': False})
	# karena di atas ada domain date_to maka yang allocation ngga ikut di-nonaktifkan
	# maka dari itu nonaktifkanlah yang allocation
		domain = [('employee_id','in',emp_ids),('type','=','add'),('holiday_status_id','=',vals['leave_type'])]
		holiday_ids = holiday_obj.search(cr, uid, domain)
		if len(holiday_ids) > 0:
			holiday_obj.write(cr, uid, holiday_ids, {'active': False})
	# untuk setiap employee di bawah tag tadi, alokasikan holiday baru dengan leave_type yang sama
		reset_ids = []
		for employee_id in emp_ids:
			new_id = holiday_obj.create(cr, uid, {
				'type': 'add',
				'name': _('Allocation reset as of %s') % vals.get('reset_before'),
				'holiday_status_id': vals.get('leave_type'),
				'number_of_days_temp': vals.get('duration'),
				'employee_id': employee_id,
			})
			reset_ids.append(new_id)
	# otomatis approve
		holiday_obj.signal_workflow(cr, uid, reset_ids, "validate")
		return True
	


