from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from datetime import datetime, date, timedelta

from openerp.addons.website.models.website import slug

import json

import pytz
from datetime import datetime

def datetime_as_user_tz(datetime_str, tz=None, datetime_format='%Y-%m-%d %H:%M:%S'):
	if isinstance(datetime_str, (str, unicode)):
		datetime_str = datetime.strptime(datetime_str, datetime_format)
	utc_date = pytz.utc.localize(datetime_str)
	user_tz = pytz.timezone(tz or pytz.utc)
	return utc_date.astimezone(user_tz)

def datetime_as_utc(datetime_str, tz=None, datetime_format='%Y-%m-%d %H:%M:%S'):
	if isinstance(datetime_str, (str, unicode)):
		datetime_str = datetime.strptime(datetime_str, datetime_format)
	user_tz = pytz.timezone(tz or pytz.utc)
	offset = user_tz.utcoffset(datetime_str).total_seconds()/3600
	return datetime_str - timedelta(hours=offset)

class website_universal(http.Controller):

		@http.route('/hr/attendance', type='http', auth="user", website=True)
		def hr_attendance(self, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
		# tentukan apakah yang login ini employee (driver) atau customer. di luar itu ngga bisa diakses
		# driver = user yang terhubung ke employee dengan job Driver
		# customer = user yang terhubung ke res.partner dengan customer = True
			employee_obj = env['hr.employee']
			partner_obj = env['res.partner']
			user_obj = env['res.users']
			contracts = []
			attendance_confirms = []
		# cek apakah employee atau driver
			model_obj = env['ir.model.data']
			model, job_driver_id = model_obj.get_object_reference('universal', 'hr_job_driver')
			employees = employee_obj.search([('resource_id.user_id','=',uid),('job_id','=',job_driver_id)])
			user = user_obj.sudo().browse(uid)
			partner = user.partner_id
			partner_company = None
			if len(employees.ids) > 0:
				mode = 'employee'
			elif partner:
				mode = 'customer'
			# ambil perusahaan dari customer ini, karena yang dicatat di attendance adalah perusahaan customer ybs
				partner_company = partner.parent_id
				if not partner_company.id:
					mode = 'customer_error'
			else:
				mode = 'general_error'
			return request.render("universal.website_hr_attendance", {
				'view_mode': mode,
				'employee_id': employees and employees.ids[0] or 0,
				'customer_id': partner_company and partner_company.id or 0,
			})
			
		def _convert_attendance_data(self, attendance_data, confirmed_only=False):
		# asumsi: sudah di-sort by date dan customer
			attendance_list = []
			for attendance in attendance_data:
				if confirmed_only and not attendance.customer_approval: continue
				att_datetime = datetime_as_user_tz(attendance.name, tz=request.env.context.get('tz',None))
				att_date = att_datetime.strftime("%d %b")
				att_time = att_datetime.strftime("%H:%M")
				attendance_list.append({
					'id': attendance.id,
					'date': att_date,
					'time': att_time,
					'action': attendance.action.replace('_','-'),
					'customer': attendance.contract_id.customer.name,
					'out_of_town': attendance.out_of_town,
				})
			return attendance_list

		@http.route('/hr/attendance/scan/<int:employee_id>/<int:customer_id>', type='http', auth="user", website=True)
		def hr_attendance_scan(self, employee_id, customer_id, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			contracts = []
			attendances = []
			contract_id = None
			mode = employee_id and 'employee' or customer_id and 'customer' or 'error'
		# tentukan ini attendance_action: 
		# - start (belum ada klik start dari pihak employee), 
		# - start_pending (udah start, nunggu customer konfirmasi)
		# - stop (udah start, udah konfirmasi customer, tunggu finish)
		# - stop_pending (udah stop, tunggu konfirmasi customer untuk finish)
		# apakah sudah ada attendance untuk hari dan employee ini? 
			contract_obj = env['hr.contract']
			if mode == 'employee':
				contracts = contract_obj.sudo().search([('contract_type','=','contract_attc'),('state','=','ongoing'),('employee_id','=',employee_id)])
			elif mode == 'customer':
				contracts = contract_obj.sudo().search([('contract_type','=','contract_attc'),('state','=','ongoing'),('customer','=',customer_id)])
			else:
				contracts = []
			attendance_obj = env['hr.attendance']
			if mode == 'employee':
				attendances = attendance_obj.sudo().search([
					('employee_id','=',employee_id),
					('name','>=',(date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")),
				], order="name, contract_id, action") # kita manfaatkan fakta bahwa kalau di-order "sign_in" muncul sebelum "sign_out"
			elif mode == 'customer':
				attendances = attendance_obj.sudo().search([
					('contract_id.customer','=',customer_id),
					('name','>=',(date.today() - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")),
				], order="name, contract_id, action") # kita manfaatkan fakta bahwa kalau di-order "sign_in" muncul sebelum "sign_out"
		# ambil input attendance terakhir
			last_entry = None
			for attendance in attendances: last_entry = attendance
		# tentukan next action berdasarkan isi last entry ini
			attendance_action = None
			if last_entry != None:
				contract_id = last_entry.contract_id.id
				last_action = last_entry.action
				approval = last_entry.customer_approval
				if last_action == 'sign_out' and not approval: 
					attendance_action = 'stop_pending'
				elif last_action == 'sign_out' and approval:
					attendance_action = 'start'
				elif last_action == 'sign_in' and approval:
					attendance_action = 'stop'
				elif last_action == 'sign_in' and not approval:
					attendance_action = 'start_pending'
		# attendances kudu dipisahin antara tanggal dan jam
				last_entry = self._convert_attendance_data([last_entry])[0]
			else:
				attendance_action = 'start'
			attendances = self._convert_attendance_data(attendances, confirmed_only=True)
		# tentukan string out of town, untuk konfirmasi customer
			out_of_town_str = {
				'no': _('The driver said that this session is not out-of-town.'),
				'roundtrip': _('The driver said that this is a roundtrip out-of-town session.'),
				'overnight': _('The driver said that this is a overnight out-of-town session.'),
			}
			out_of_town = out_of_town_str.get(last_entry['out_of_town'])
		# udah deh
			template = mode == 'employee' and 'website_hr_attendance_employee' or mode == 'customer' and 'website_hr_attendance_customer' or ''
			return request.render("universal.%s" % template, {
				'attendance_action': attendance_action,
				'contracts': contracts,
				'attendances': attendances,
				'contract_id': contract_id,
				'last_attendance': last_entry,
				'out_of_town': out_of_town,
			})

		@http.route('/hr/attendance/employee/start/<int:employee_id>/<int:contract_id>', type='http', auth="user", website=True)
		def hr_attendance_employee_start(self, employee_id, contract_id, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			attendance_obj = env['hr.attendance']
			response = {}
			try:
				attendance_obj.create({
					'employee_id': employee_id,
					'contract_id': contract_id,
					'action': 'sign_in',
					'source': 'app',
				})
				response['info'] = _('Today has been started. Enjoy the trip!')
			except:
				response['error'] = _('Error logging in attendance. Please contact your administrator.')
			return json.dumps(response)
			
		@http.route('/hr/attendance/employee/finish/<int:employee_id>/<int:contract_id>/<string:out_of_town>', type='http', auth="user", website=True)
		def hr_attendance_employee_finish(self, employee_id, contract_id, out_of_town, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			attendance_obj = env['hr.attendance']
			response = {}
			print out_of_town
			try:
				attendance_obj.create({
					'employee_id': employee_id,
					'contract_id': contract_id,
					'action': 'sign_out',
					'source': 'app',
					'out_of_town': out_of_town or 'no',
				})
				response['info'] = _('Today has been finished. Nice job!')
			except:
				response['error'] = _('Error logging in attendance. Please contact your administrator.')
			return json.dumps(response)

		@http.route('/hr/attendance/customer/confirm/<int:attendance_id>/<string:time>', type='http', auth="user", website=True)
		def hr_attendance_customer_confirm(self, attendance_id, time, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			attendance_obj = env['hr.attendance']
			response = {}
			attendance_data = attendance_obj.sudo().browse(attendance_id)
		# ganti waktunya. time asumsinya berformat HH:MM
			temp = time.split(':')
			new_attendance_time = datetime.strptime(attendance_data.name,"%Y-%m-%d %H:%M:%S").replace(hour=int(temp[0]), minute=int(temp[1]))
			new_attendance_time = datetime_as_utc(new_attendance_time, tz=request.env.context.get('tz',None))
			try:
				attendance_data.write({
					'name': new_attendance_time,
					'customer_approval': datetime.now().replace(microsecond=0),
				})
				response['info'] = _('Confirmation accepted.')
			except:
				response['error'] = _('Error confirming start/finish. Please try again in a moment. If the trouble persists, please use paper attendance for now.')
			return json.dumps(response)
			
