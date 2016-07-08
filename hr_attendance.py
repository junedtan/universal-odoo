from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta

_ATTENDANCE_SOURCE = (
	('manual',_('Manual')),
	('rfid',_('RFID')),
	('app',_('App')),
)

_OUT_OF_TOWN = (
	('no','No'),
	('roundtrip','Roundtrip'),
	('overnight','Overnight'),
)

# ==========================================================================================================================

class hr_attendance(osv.osv):
	
	_inherit = 'hr.attendance'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('hr.contract','Contract Reference'),
		'customer_approval': fields.datetime('Customer Approval'),
		'source': fields.selection(_ATTENDANCE_SOURCE,'Source'),
		'out_of_town': fields.selection(_OUT_OF_TOWN, 'Out of Town?'),
		'routes': fields.text('Routes'),
	}
	
# ==========================================================================================================================

class hr_absence_reason(osv.osv):
	
	_inherit = 'hr.absence.reason'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.many2one('Absence Reason'),
	}
	
# ==========================================================================================================================

class hr_attendance_mass_memory(osv.osv_memory):
	
	_name = 'hr.attendance.mass.memory'
	_description = 'HR-Attendance Mass'
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------
	
	def get_driver_replacement(self, cr, uid, emp_id, contract_id, att_date, context={}):
		if not emp_id or not contract_id or not att_date: return False
		driver_rep_obj = self.pool.get('hr.driver.replacement')
		driver_rep_ids = driver_rep_obj.search(cr, uid, [('driver_original','=',emp_id),('replace_date','=',att_date),('contract','=',contract_id)])
		if len(driver_rep_ids) > 0:
			driver_rep = driver_rep_obj.browse(cr, uid, driver_rep_ids[0])
			return driver_rep.driver_replace.id
		return False
	
	
	_columns = {
		'attendance_type': fields.selection([('employee','Employee'),('driver','Driver')], 'Type', required=True),
		'employee': fields.many2one('hr.employee', "Employee", required=True),
		'contract': fields.many2one('hr.contract','Contract'),
		'attendance_mass_lines': fields.one2many('hr.attendance.mass.memory.lines', 'attendance_mass_id', "Attendance Lines",),
	}
	
	_defaults = {
		'out_of_town': 'no',
		'source': 'manual',
	}
	
# ======= ACTION MEMORY ==================================================================
	
	def create(self, cr, uid, vals, context=None):	
		if 'attendance_mass_lines' not in vals: return False
		attendance_obj = self.pool.get('hr.attendance')
		emp_id = vals['employee']
		con_id = vals['contract']
	# cek kalau attendance_type nya = driver, employeenya harus driver juga
		if vals['attendance_type'] == "driver":
			employee_obj = self.pool.get('hr.employee')
			is_driver = employee_obj.emp_is_driver(cr, uid, emp_id)
			if not is_driver:
				raise osv.except_osv(_('Attendance Error'),_('This employee is not a driver. Please check again.'))
		for row in vals['attendance_mass_lines']:
		# cek tipe employeenya, kalau tipenya driver cek apakah ada driver pengganti untuk tanggal, kontrak, dan employee tersebut.
			if vals['attendance_type'] == "driver":
				driver_rep_ids = self.get_driver_replacement(cr, uid, emp_id, con_id, row[2]['attendance_date'])
				print "driver rep %s" % driver_rep_ids
				if driver_rep_ids:
					emp_id = driver_rep_ids
			signin_date = datetime.strptime(row[2]['attendance_date'],'%Y-%m-%d') + timedelta(seconds=(row[2]['start_time'] - 7) *  3600)
			signout_date = datetime.strptime(row[2]['attendance_date'],'%Y-%m-%d') + timedelta(seconds=(row[2]['finish_time'] - 7) *  3600)
		# bikin list attendance, untuk setiap row bikin 2 baris attendance
		# sign in
			attendance_obj.create(cr, uid, {
				'name': signin_date,
				'action': 'sign_in',
				'employee_id': emp_id,
				'source': 'manual'
			})
		# sign out
			attendance_obj.create(cr, uid,{
				'name': signout_date,
				'action': 'sign_out',
				'employee_id': emp_id,
				'out_of_town': row[2]['out_of_town'],
				'source': 'manual',
				'routes': row[2]['routes'],
			})
		return True
	
# ==========================================================================================================================
	
class hr_attendance_mass_memory_lines(osv.osv_memory):
	
	_name = 'hr.attendance.mass.memory.lines'
	_description = 'HR-Attendance Mass Memory Lines'
	
	_columns = {
		'attendance_mass_id': fields.many2one('hr.attendance.mass.memory','Attendance Mass Reference', required=True, ondelete='cascade', select=True),
		'attendance_date': fields.date('Date', required=True, select=1),
		'start_time': fields.float('Start Time', required=True),
		'finish_time': fields.float('Finish Time', required=True),
		'out_of_town': fields.selection(_OUT_OF_TOWN, 'Out of Town?'),
		'routes': fields.text('Routes'),
	}
	
	_defaults = {
		'out_of_town': 'no',
	}
	