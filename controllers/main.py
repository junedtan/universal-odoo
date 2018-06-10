from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request
from openerp.addons.website.controllers.main import Website
from datetime import datetime, date, timedelta

from openerp.addons.website.models.website import slug

import json

import pytz
from datetime import datetime, date

def datetime_as_user_tz(datetime_str, tz=None, datetime_format='%Y-%m-%d %H:%M:%S'):
	if isinstance(datetime_str, (str, unicode)):
		datetime_str = datetime.strptime(datetime_str, datetime_format)
	utc_date = pytz.utc.localize(datetime_str)
	user_tz = pytz.timezone(tz or 'Asia/Jakarta')
	return utc_date.astimezone(user_tz)

def datetime_as_utc(datetime_str, tz=None, datetime_format='%Y-%m-%d %H:%M:%S'):
	if isinstance(datetime_str, (str, unicode)):
		datetime_str = datetime.strptime(datetime_str, datetime_format)
	user_tz = pytz.timezone(tz or 'Asia/Jakarta')
	offset = user_tz.utcoffset(datetime_str).total_seconds()/3600
	return datetime_str - timedelta(hours=offset)
	
def unserialize_expense(expense_str):
	if not expense_str: return []
	temp = expense_str.split('@')
	if not temp[0] or not temp[1] or not temp[2]: return []
	product_id = temp[0].split('|')
	qty = temp[1].split('|')
	unit_price = temp[2].split('|')
	if len(qty) != len(unit_price) or len(qty) != len(product_id): return[]
	result = []
	for idx in range(0,len(qty)):
		result.append({
			'product_id': product_id[idx],
			'unit_amount': unit_price[idx],
			'unit_quantity': qty[idx],
		})
	return result

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
			employees = employee_obj.sudo().search([('resource_id.user_id','=',uid),('job_id','=',job_driver_id)])
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
			absence_obj = env['hr.employee.absence']
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
			out_of_town = None
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
			# tentukan string out of town, untuk konfirmasi customer
				out_of_town_str = {
					'no': _('The driver said that this session is not out-of-town.'),
					'roundtrip': _('The driver said that this is a ROUNDTRIP out-of-town session.'),
					'overnight': _('The driver said that this is a OVERNIGHT out-of-town session.'),
				}
				out_of_town = out_of_town_str.get(last_entry['out_of_town'])
			else:
				attendance_action = 'start'
			attendances = self._convert_attendance_data(attendances, confirmed_only=True)
		
		# untuk biaya perjalanan: ambil semua product expense untuk bahan isian driver, dan 
		# hasil isian driver untuk divalidasi customer
			expenses = []
			expense_id = 0
			if mode == 'employee':
				product_obj = env['product.product']
				expenses_raw = product_obj.sudo().search([('hr_expense_ok','=',True),('is_trip_related','=',True)], order="id")
				for row in expenses_raw:
					expenses.append({
						'name': row.name,
						'product_id': row.id,
						'qty': None,
						'unit_price': row.standard_price,
					})
			elif mode == 'customer':
				expense_obj = env['hr.expense.expense']
				expenses_raw = expense_obj.sudo().search([('state','=','draft'),('contract_id','=',contract_id)],order="id")
				if expenses_raw:
					expense_id = expenses_raw[0].id
					for line in expenses_raw[0].line_ids:
						expenses.append({
							'name': line.product_id.name,
							'product_id': line.product_id.id,
							'qty': line.unit_quantity,
							'unit_price': line.unit_amount,
						})
		# udah deh
			template = mode == 'employee' and 'website_hr_attendance_employee' or mode == 'customer' and 'website_hr_attendance_customer' or ''
			return request.render("universal.%s" % template, {
				'mode': mode,
				'attendance_action': attendance_action,
				'contracts': contracts,
				'attendances': attendances,
				'contract_id': contract_id,
				'last_attendance': last_entry,
				'out_of_town': out_of_town,
				'expense_id': expense_id,
				'expenses': expenses,
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
				response['error'] = _('error di start Error logging in attendance. Please contact your administrator.')
			return json.dumps(response)
			
		@http.route('/hr/attendance/employee/finish/<int:employee_id>/<int:contract_id>/<string:out_of_town>/<string:expense>/<string:routes>', type='http', auth="user", website=True)
		def hr_attendance_employee_finish(self, employee_id, contract_id, out_of_town, expense, routes, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			attendance_obj = env['hr.attendance']
			response = {}
			try:
			# create attendance entry baru dengan action Sign Out
				attendance_obj.create({
					'employee_id': employee_id,
					'contract_id': contract_id,
					'action': 'sign_out',
					'source': 'app',
					'out_of_town': out_of_town or 'no',
					'routes': routes,
				})
			# urus expense
				if expense != '-':
					expense_obj = env['hr.expense.expense']
					product_obj = env['product.product']
					expense_line = unserialize_expense(expense)
					if expense_line:
						new_expense_line = []
						for line in expense_line:
							product = product_obj.sudo().browse(int(line['product_id']))
							line.update({
								'product_id': int(line['product_id']),
								'unit_amount': float(line['unit_amount']),
								'unit_quantity': float(line['unit_quantity']),
								'name': product.name,
								'date_value': date.today(),
							})
							new_expense_line.append([0,False,line])
					expense_obj.sudo().create({
						'employee_id': employee_id,
						'name': _('Trip expense for %s' % date.today().strftime("%d %b %Y")),
						'contract_id': contract_id,
						'source': 'app',
						'date': date.today(),
						'line_ids': new_expense_line,
					})
				response['info'] = _('Thank you for today. Please wait for your client to approve this session finish.')
			except ValueError:
				response['error'] = _('It seems that some expenses are incorrectly inputted. Please make sure all inputs are numeric.')
			except:
				response['error'] = _('error di finish Error logging in attendance. Please contact your administrator.')
			return json.dumps(response)

		@http.route('/hr/attendance/customer/confirm/<int:attendance_id>/<string:time>/<int:expense_id>', type='http', auth="user", website=True)
		def hr_attendance_customer_confirm(self, attendance_id, time, expense_id, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			response = {}
			try:
				attendance_obj = env['hr.attendance']
				attendance_data = attendance_obj.sudo().browse(attendance_id)
			# ganti waktunya. time asumsinya berformat HH:MM
				#temp = time.split(':')
				#new_attendance_time = datetime.strptime(attendance_data.name,"%Y-%m-%d %H:%M:%S").replace(hour=int(temp[0]), minute=int(temp[1]))
				#new_attendance_time = datetime_as_utc(new_attendance_time, tz=request.env.context.get('tz',None))
				attendance_data.write({
					#'name': new_attendance_time,
					'customer_approval': datetime.now().replace(microsecond=0),
				})
			# konfirmasi expense
				expense_obj = env['hr.expense.expense']
				expense = expense_obj.sudo().browse(expense_id)
				expense.sudo().write({
					'state': 'accepted', 
					'date_confirm': date.today(),
					'user_valid': uid,
					'date_valid': date.today(),
				})
				response['info'] = _('Confirmation accepted.')
			except:
				response['error'] = _('Error confirming start/finish. Please try again in a moment. If the trouble persists, please use paper attendance for now.')
			return json.dumps(response)
			
		@http.route('/hr/attendance/customer/reject/<int:attendance_id>/<int:expense_id>', type='http', auth="user", website=True)
		def hr_attendance_customer_reject(self, attendance_id, expense_id, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
			response = {}
			try:
				attendance_obj = env['hr.attendance']
				attendance_data = attendance_obj.sudo().search([('id','=',attendance_id)]).unlink()
				if expense_id:
					expense_obj = env['hr.expense.expense']
					expense = expense_obj.sudo().search([('id','=',expense_id)]).unlink()
				response['info'] = _('Confirmation accepted.')
			except:
				response['error'] = _('Error confirming start/finish. Please try again in a moment. If the trouble persists, please use paper attendance for now.')
			return json.dumps(response)


class Website(Website):
	@http.route('/', type='http', auth="public", website=True)
	def index(self, **kwargs):
		# If user use mobile app as default, reroute to /mobile_app, otherwise use default behaviour
		user_obj = request.registry['res.users']
		if user_obj._is_mobile_user(request.cr, SUPERUSER_ID, request.uid):
			return request.registry['ir.http'].reroute('/mobile_app')
		return super(Website, self).index(**kwargs)
	
	@http.route()
	def web_login(self, redirect=None, *args, **kw):
		# Remove site redirection function on login page
		if 'redirect' in kw:
			del kw['redirect']
		# Limits login form input by 64 char
		values = request.params.copy()
		if not redirect:
			redirect = '/web?' + request.httprequest.query_string
		values['redirect'] = redirect
		if request.httprequest.method == 'POST':
			id = request.params['login']
			passwd = request.params['password']
			if len(id) > 64 or len(passwd) > 64:
				values['error'] = _("Maximal length of character for email and password is 64.")
				if request.env.ref('web.login', False):
					return request.render('web.login', values)
		return super(Website, self).web_login(*args, **kw)

# ==========================================================================================================================
