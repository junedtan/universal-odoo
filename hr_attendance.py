from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

_ATTENDANCE_SOURCE = [
	('manual',_('Manual')),
	('rfid',_('RFID')),
	('website',_('Website')),
]

class hr_attendance(osv.osv):
	
	_inherit = 'hr.attendance'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('hr.contract','Contract Reference'),
		'customer_approval': fields.datetime('Customer Approval'),
		'source': fields.selection(_ATTENDANCE_SOURCE,'Source'),
	}
	
# ==========================================================================================================================

class hr_attendance_mass_memory(osv.osv_memory):
	
	_name = 'hr.attendance.mass.memory'
	_description = 'HR-Attendance Mass'
	
	_columns = {
		'attendance_type': fields.selection([('employee','Employee'),('driver','Driver')], 'Type'),
		'employee': fields.many2one('hr.employee', "Employee", required=True),
		'contract': fields.many2one('hr.contract','Contract'),
		'attendance': fields.one2many('hr.attendance.mass.lines', "Attendance Lines",),
	}
	
# ======= ACTION MEMORY ==================================================================
	
	def create(self, cr, uid, vals, context=None):
		
		return True
	
# ==========================================================================================================================
	
class hr_attendance_mass_memory_lines(osv.osv_memory):
	
	_name = 'hr.attendance.mass.memory.lines'
	_description = 'HR-Attendance Mass Memory Lines'
	
	_columns = {
		'attendance_mass_id': fields.many2one('hr.attendance.mass.memory','Attendance Mass Reference', required=True, ondelete='cascade', select=True),
		'attendance_date': fields.date('Date', required=True, select=1),
		'start_time': fields.float('Start Time'),
		'finish_time': fields.float('Finish Time'),
	}
	
	
	