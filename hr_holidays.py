from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp import tools
import math
import time
from . import SPECIAL_PERMIT

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
			date_to_with_delta = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=holiday_status_data.leave_duration)
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

	def cron_reset_allocation(self, cr, uid, context=None):
	# ambil data taun di database
		model_obj = self.pool.get('ir.model.data')
		param_obj = self.pool.get('ir.config_parameter')
		model, db_year = model_obj.get_object_reference(cr, uid, 'universal', 'database_year_ongoing')
		param_year = param_obj.browse(cr, uid, db_year)
		this_year = datetime.today().strftime('%Y')
	# cek apakah taunnya sama dengan taun ini 
		if int(param_year.value) < int(this_year):
			emp_obj = self.pool.get('hr.employee')
			holiday_obj = self.pool.get('hr.holidays')
			leave_rule_obj = self.pool.get('universal.leave.rule')
			leave_rule_ids = leave_rule_obj.search(cr, uid, [])
			# non aktifkan semua cuti & alokasi cuti
			holiday_ids = holiday_obj.search(cr, uid, [])
			holiday_obj.write(cr, uid, holiday_ids, {'active': False})
			reset_ids = []
		# untuk semua leave rule, ambil datanya lalu tambahkan alokasi cuti
			for rule_data in leave_rule_obj.browse(cr, uid, leave_rule_ids):
				emp_ids = []
			# cari employee berdasarkan tag kalau ada
				emp_ids = emp_obj.search(cr, uid, [('category_ids', 'child_of', [rule_data.category_id.id])])
				if len(emp_ids) > 0:
				# untuk setiap employee di bawah tag tadi, alokasikan holiday baru dengan leave_type yang sama
					for employee_id in emp_ids:
						new_id = holiday_obj.create(cr, uid, {
							'type': 'add',
							'name': _('Allocation reset as of %s') % this_year,
							'holiday_status_id': rule_data.holiday_status_id.id,
							'number_of_days_temp': rule_data.duration,
							'employee_id': employee_id,
						})
						reset_ids.append(new_id)
			# otomatis approve
			holiday_obj.holidays_validate(cr, uid, reset_ids)
			param_obj.write(cr, uid, db_year, {'value': int(this_year)+1})

# ==========================================================================================================================

class resource_calendar_company_holiday(osv.osv):

	_name = 'resource.calendar.company.holiday'
	_description = 'General purpose company/national holiday'

	_columns = {
		'name': fields.char('Description', required=True),
		'date_from': fields.date('Date From', required=True),
		'date_to': fields.date('Date To', required=True),
		'holiday_type': fields.selection((
			('company','Company'),
			('national','National'),
		), 'Type'),
	}

	_defaults = {
		'holiday_type': 'national',
	}

	def create(self, cr, uid, vals, context={}):
		new_id = super(resource_calendar_company_holiday, self).create(cr, uid, vals, context=context)
	# untuk setiap working time yang ada, set hari libur nya (asumsi per holiday diset di masing2 working 
	# time belum ada holiday). kasih m2o dari holiday di working time ke model ini
		calendar_obj = self.pool.get('resource.calendar')
		calendar_ids = calendar_obj.search(cr, uid, [])
		for calendar in calendar_obj.browse(cr, uid, calendar_ids):
			new_vals = {
				'leave_ids': [(0, False, {
					'name': vals['name'],
					'date_from': datetime.strptime(vals['date_from'],'%Y-%m-%d').strftime("%Y-%m-%d 00:00:00"),
					'date_to': datetime.strptime(vals['date_to'],'%Y-%m-%d').strftime("%Y-%m-%d 23:59:59"),
					'company_holiday_id': new_id,
				})]
			}
			calendar_obj.write(cr, uid, [calendar.id], new_vals, context)
		return new_id

	def write(self, cr, uid, ids, vals, context={}):
		result = super(resource_calendar_company_holiday, self).write(cr, uid, ids, vals, context=context)
		calendar_leave_obj = self.pool.get('resource.calendar.leaves')
		for holiday in self.browse(cr, uid, ids, context=context):
			calendar_leave_ids = calendar_leave_obj.search(cr, uid, [('company_holiday_id','=',holiday.id)])
			if len(calendar_leave_ids) == 0: continue
			calendar_leave_obj.write(cr, uid, calendar_leave_ids, {
				'name': holiday.name,
				'date_from': datetime.strptime(holiday.date_from,'%Y-%m-%d').strftime("%Y-%m-%d 00:00:00"),
				'date_to': datetime.strptime(holiday.date_to,'%Y-%m-%d').strftime("%Y-%m-%d 23:59:59"),
			})
		return result


# ==========================================================================================================================

class resource_calendar_leaves(osv.osv):

	_inherit = 'resource.calendar.leaves'

	_columns = {
		'company_holiday_id': fields.many2one('resource.calendar.company.holiday', 'National/Company Holiday', ondelete="cascade"),
	}

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
		from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
		to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
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
				date_to_with_delta = datetime.strptime(date_from, tools.DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(hours=8)
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

class universal_leave_rule(osv.osv):
	
	_name = 'universal.leave.rule'
	_description = 'Universal - Leave Rule'
	
	_columns = {
		'category_id': fields.many2one('hr.employee.category', "Employee Tag", required=True),
		'holiday_status_id': fields.many2one('hr.holidays.status', 'Leave Type', required=True),
		'duration': fields.integer('Duration (days)', required=True),
	}
	
# ==========================================================================================================================

class universal_special_permit(osv.osv):
	
	_name = 'universal.special.permit'
	_description = 'Universal - Special Permit'
	
	_inherit = ['document.approval']
	
	_columns = {
		'name': fields.char('Description', required=True),
		'employee_id': fields.many2one('hr.employee', "Employee", required=True),
		'req_date_start': fields.datetime('Request Date Start', required=True),
		'req_date_end': fields.datetime('Request Date End', required=True),
		'act_date_start': fields.datetime('Actual Date Start'),
		'act_date_end': fields.datetime('Actual Date End'),
		'state': fields.selection((
			('new','Proposed'),
			('approved','Approved'),
			('rejected','Rejected'),
			('done','Done'),
		)),
		'decision': fields.selection(SPECIAL_PERMIT, 'Decision'),
	}
	
	_defaults = {
		'state': 'new',
	}
	
# ACTION BUTTON HANDLER ----------------------------------------------------------------------------------------------------
	
	def action_set_decision(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids[0], context=context)
		return {
			'type': 'ir.actions.act_window',
			'name': 'Set Decision',
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'universal.special.permit.decision.memory',
			'context': {
				'default_permit_id': form_data.id,
				'default_employee_id': form_data.employee_id.id,
				'default_req_date_start': form_data.req_date_start,
				'default_req_date_end': form_data.req_date_end,
				'default_act_date_start': form_data.act_date_start,
				'default_act_date_end': form_data.act_date_end,
				'default_name': form_data.name,
			},
			'target': 'new',
		}
		
# ==========================================================================================================================

class universal_special_permit_decision_memory(osv.osv_memory):
	
	_name = 'universal.special.permit.decision.memory'
	_description = 'Universal - Special Permit Decision Memory'
	
	_columns = {
		'permit_id': fields.many2one('universal.special.permit', 'Special Permit'),
		'employee_id': fields.many2one('hr.employee', "Employee", readonly=True),
		'req_date_start': fields.datetime('Request Date Start', readonly=True),
		'req_date_end': fields.datetime('Request Date End', readonly=True),
		'act_date_start': fields.datetime('Actual Date Start', readonly=True),
		'act_date_end': fields.datetime('Actual Date End', readonly=True),
		'decision': fields.selection(SPECIAL_PERMIT, 'Decision', required=True),
		'absence_reason': fields.many2one('hr.absence.reason', 'Absence Reason'),
		'holiday_status_id': fields.many2one('hr.holidays.status', 'Leave Type'),
		'name': fields.char('Description', readonly=True),
	}
	
# ACTION BUTTON HANDLER ----------------------------------------------------------------------------------------------------
	
	def action_set_decision(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids[0], context=context)
		special_permit_obj = self.pool.get('universal.special.permit')
		result = special_permit_obj.write(cr, uid, [form_data.permit_id.id], {
			'decision': form_data.decision,
			'state': 'done',
		})
		if form_data.decision == "absence":
			absence_obj = self.pool.get('hr.employee.absence')
			absence_obj.create(cr, uid, {
				'employee_id': form_data.employee_id.id,
				'absence_date': form_data.req_date_start,
				'absence_reason_id': form_data.absence_reason.id,
			})
		elif form_data.decision == "leave":
			leave_obj = self.pool.get('hr.holidays')
			leave_obj.create(cr, uid, {
				'name': _('Decision of special permit'),
				'holiday_status_id': form_data.holiday_status_id.id,
				'date_from': form_data.req_date_start,
				'date_to': form_data.req_date_end,
				'number_of_days_temp': 1.0,
				'employee_id': form_data.employee_id.id,
				'department_id': form_data.employee_id.department_id.id,
			})
		return result