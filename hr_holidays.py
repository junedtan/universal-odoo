from openerp.osv import osv, fields
from openerp.tools.translate import _
import datetime
from openerp import tools
import math
import time

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

# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	def onchange_status_id(self, cr, uid, ids, holiday_status_id, date_from):
		result = {'value': {}}
		if not holiday_status_id: return False
		holiday_status_data = self.pool.get('hr.holidays.status').browse(cr, uid, holiday_status_id)
		if date_from and holiday_status_data.leave_duration > 0:
			date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(days=holiday_status_data.leave_duration)
			result['value']['date_to'] = str(date_to_with_delta)
		result['value']['number_of_days_temp'] = holiday_status_data.leave_duration 
		return result
	
# ACTION BUTTON HANDLER ----------------------------------------------------------------------------------------------------
	
	def action_change_duration(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids[0], context=context)
		return {
			'type': 'ir.actions.act_window',
			'name': 'Change Leave Duration',
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'hr.holidays.change.duration.memory',
			'context': {
				'default_employee_id': form_data.employee_id.id,
				'default_holiday_status_id': form_data.holiday_status_id.id,
				'default_leave_id': form_data.id,
				'default_date_from_old': form_data.date_from,
				'default_date_to_old': form_data.date_to,
				'default_duration_old': form_data.number_of_days_temp,
				'default_date_from_new': form_data.date_from,
				'default_date_to_new': form_data.date_to,
				'default_duration_new': form_data.number_of_days_temp,
			},
			'target': 'new',
		}
		
# CRON --------------------------------------------------------------------------------------------------------------------------
	
	
		
# ==========================================================================================================================

class hr_holidays_status(osv.osv):
	
	_inherit = 'hr.holidays.status'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'leave_duration': fields.integer('Leave Duration'),
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
	
	
# ==========================================================================================================================

class hr_holidays_change_duration_memory(osv.osv_memory):
	
	_name = 'hr.holidays.change.duration.memory'
	_description = 'HR Holidays - Change Duration Memory'
	
	_columns = {
		'employee_id': fields.many2one('hr.employee', "Employee", readonly=True),
		'holiday_status_id': fields.many2one('hr.holidays.status', 'Leave Type', readonly=True),
		'leave_id': fields.many2one('hr.holidays', 'Leave Description', readonly=True),
		'date_from_old': fields.datetime('Old Start Date',readonly=True),
		'date_to_old': fields.datetime('Old End Date',readonly=True),
		'duration_old': fields.integer('Old Duration (days)', readonly=True),
		'date_from_new': fields.datetime('New Start Date',required=True),
		'date_to_new': fields.datetime('New End Date',required=True),
		'duration_new': fields.integer('New Duration (days)'),
	}
	
	def _get_number_of_days(self, date_from, date_to):
		"""Returns a float equals to the timedelta between two dates given as string."""

		DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
		from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
		to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
		timedelta = to_dt - from_dt
		diff_day = timedelta.days + float(timedelta.seconds) / 86400
		return diff_day
	
# ONCHANGE ----------------------------------------------------------------------------------------------------------------
	
	def onchange_date_from(self, cr, uid, ids, date_to, date_from):
		"""
		If there are no date set for date_to, automatically set one 8 hours later than
		the date_from.
		Also update the number_of_days.
		"""
		# date_to has to be greater than date_from
		if (date_from and date_to) and (date_from > date_to):
				raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

		result = {'value': {}}

		# No date_to set so far: automatically compute one 8 hours later
		if date_from and not date_to:
				date_to_with_delta = datetime.datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + datetime.timedelta(hours=8)
				result['value']['date_to_new'] = str(date_to_with_delta)

		# Compute and update the number of days
		if (date_to and date_from) and (date_from <= date_to):
				diff_day = self._get_number_of_days(date_from, date_to)
				result['value']['duration_new'] = round(math.floor(diff_day))+1
		else:
				result['value']['duration_new'] = 0

		return result

	def onchange_date_to(self, cr, uid, ids, date_to, date_from):
		"""
		Update the number_of_days.
		"""

		# date_to has to be greater than date_from
		if (date_from and date_to) and (date_from > date_to):
				raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

		result = {'value': {}}

		# Compute and update the number of days
		if (date_to and date_from) and (date_from <= date_to):
				diff_day = self._get_number_of_days(date_from, date_to)
				result['value']['duration_new'] = round(math.floor(diff_day))+1
		else:
				result['value']['duration_new'] = 0

		return result

# ACTION BUTTON HANDLER ----------------------------------------------------------------------------------------------------
	
	def action_change_duration(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids[0], context=context)
		holidays_obj = self.pool.get('hr.holidays')
		result = holidays_obj.write(cr, uid, [form_data.leave_id.id], {
			'date_from': form_data.date_from_new,
			'date_to': form_data.date_to_new,
			'number_of_days_temp': form_data.duration_new,
		})
		return result
		
# ==========================================================================================================================

class hr_holidays_leave_rule(osv.osv):
	
	_name = 'hr.holidays.leave.rule'
	_description = 'HR-Holidays Leave Rule'
	
	_columns = {
		'category_id': fields.many2one('hr.employee.category', "Employee Tag", required=True),
		'leave_type': fields.many2one('hr.holidays.status', 'Leave Type', required=True),
		'duration': fields.integer('Duration (days)', required=True),
	}
