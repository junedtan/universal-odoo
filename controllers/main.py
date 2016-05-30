from openerp import SUPERUSER_ID
from openerp import http
from openerp.tools.translate import _
from openerp.http import request

from openerp.addons.website.models.website import slug

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
			contracts = []
			attendance_confirms = []
		# cek apakah employee atau driver
			model_obj = env['ir.model.data']
			model, job_driver_id = model_obj.get_object_reference('universal', 'hr_job_driver')
			employee_id = employee_obj.search([('resource_id.user_id','=',uid),('job_id','=',job_driver_id)]).ids
			partner_id = partner_obj.search([('is_company','=',False),('customer','=',True),('user_id','=',uid)]).ids
			if len(employee_id) > 0:
				mode = 'employee'
			elif len(partner_id) > 0:
				mode = 'customer'
			else:
				mode = 'error'
			return request.render("universal.website_hr_attendance", {
				'view_mode': mode,
				'employee_id': employee_id and employee_id[0] or None,
				'customer_id': partner_id and partner_id[0] or None,
			})

		@http.route('/hr/attendance/employee/<int:employee_id>', type='http', auth="user", website=True)
		def hr_attendance_employee(self, employee_id, **kwargs):
			env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
			uid = env.uid
		# tentukan ini attendance_action: 
		# - start (belum ada klik start dari pihak employee), 
		# - start_pending (udah start, nunggu customer konfirmasi)
		# - stop (udah start, udah konfirmasi customer, tunggu finish)
			
			attendance_action = 'start_pending'
			contract_obj = env['hr.contract']
			contracts = contract_obj.sudo().search([('contract_type','=','contract_attc'),('state','=','ongoing'),('employee_id','=',employee_id)])
			attendance = [{
				'date': '24/05',
				'start': '08:14',
				'customer': 'PT. Harapan Jaya',
			}]
			return request.render("universal.website_hr_attendance_employee", {
				'attendance_action': attendance_action,
				'contracts': contracts,
				'attendance': attendance,
			})
