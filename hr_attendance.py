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
	
	_inherit = ['hr.attendance','chjs.base.webservice']
	_name = 'hr.attendance'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('foms.contract','Contract Reference'),
		'order_id': fields.many2one('foms.order','Order Reference'),
		'customer_approval': fields.datetime('Customer Approval'),
		'source': fields.selection(_ATTENDANCE_SOURCE,'Source'),
		'out_of_town': fields.selection(_OUT_OF_TOWN, 'Out of Town?'),
		'routes': fields.text('Routes'),
	}
	
# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context={}):
		context = context and context or {}
	# bila ini dari mobile apps, asumsikan employee_id adalah user_id driver, sehingga harus dicari employee_idnya
		if context.get('from_webservice') == True:
			user_id = vals.get('employee_id')
			employee_obj = self.pool.get('hr.employee')
			employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
			if len(employee_ids) == 0:
				raise osv.except_osv(_('Expense Error'),_('There is no driver with requested user id.'))
			vals.update({'employee_id': employee_ids[0]})
		return super(hr_attendance, self).create(cr, uid, vals, context=context)
	
	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		context = context and context or {}
	# kalau diminta untuk mengambil semua order by user_id tertentu
		if context.get('by_user_id',False):
			domain = []
			user_obj = self.pool.get('res.users')
			user_id = context.get('user_id', uid)
			is_driver = user_obj.has_group(cr, user_id, 'universal.group_universal_driver')
		# kalau driver, domainnya menjadi semua attendance dia, dan 100 data terakhir
			if is_driver:
				employee_obj = self.pool.get('hr.employee')
				employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
				if len(employee_ids) > 0:
					domain = [('employee_id','=',employee_ids[0])]
					limit = 100
					order = 'name desc'
			if len(domain) > 0:
				args = domain + args
			else:
				return []
		return super(hr_attendance, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

# ==========================================================================================================================

class hr_absence_reason(osv.osv):
	
	_name = 'hr.absence.reason'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'name': fields.char('Absence Reason', required=True),
	}
	
# ==========================================================================================================================

class hr_employee_absence(osv.osv):
	
	_name = 'hr.employee.absence'
	_description = 'HR-Employee Absence and Driver replacement'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'employee_id': fields.many2one('hr.employee','Employee', required=True),
		'absence_date': fields.date('Date', required=True),
		'absence_reason_id': fields.many2one('hr.absence.reason', 'Absence Reason'),
		'is_driver': fields.boolean('Is driver?', readonly=True),
		'driver_replace': fields.many2one('hr.employee','Replacement Driver'),
		'contract': fields.many2one('hr.contract','Contract'),
		'customer': fields.many2one('res.partner','Customer'),
	}
	
	def _check_contract(self, cr, uid, ids, context=None):
		for absence in self.browse(cr, uid, ids, context=context):
			if not (absence.is_driver and absence.contract): continue
			if absence.contract.allow_driver_replace != True: return False
		return True
	
	_constraints = [
		(_check_contract, "Error: The contract does not allow for driver replacement.", ['contract']),
	]
	
# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	def onchange_contract(self, cr, uid, ids, contract_id):
		result = {}
		if not contract_id: return False
		contract_obj = self.pool.get('hr.contract').browse(cr, uid, contract_id)
		result['value'] = { 'customer' : contract_obj.customer.id }
		return result

# OVERRIDES ----------------------------------------------------------------------------------------------------------------

	def name_get(self, cr, uid, ids, context={}):
		if isinstance(ids, (list, tuple)) and not len(ids): return []
		if isinstance(ids, (long, int)): ids = [ids]
		res = []
		for record in self.browse(cr, uid, ids):
			name = '%s (%s)' % (record.employee_id.name, record.absence_reason_id.name)
			res.append((record.id, name))
		return res
	
# ==========================================================================================================================

class hr_attendance_mass_memory(osv.osv_memory):
	
	_name = 'hr.attendance.mass.memory'
	_description = 'HR-Attendance Mass'
	
# CUSTOM METHODS -----------------------------------------------------------------------------------------------------------
	
	def get_driver_replacement(self, cr, uid, emp_id, contract_id, att_date, context={}):
		if not emp_id or not contract_id or not att_date: return False
		absence_obj = self.pool.get('hr.employee.absence')
		absence_ids = absence_obj.search(cr, uid, [('employee_id','=',emp_id),('absence_date','=',att_date),('contract','=',contract_id)])
		if len(absence_ids) > 0:
			driver_rep = driver_rep_obj.browse(cr, uid, absence_ids[0])
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
	
