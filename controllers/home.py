from openerp.addons.web.controllers import main

import openerp
from openerp import http
from openerp.tools.translate import _

from openerp.http import request, serialize_exception as _serialize_exception

class Home(main.Home):
	
	@http.route('/web/login', type='http', auth="none")
	def web_login(self, redirect=None, **kw):
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
				
		return super(Home, self).web_login(redirect)