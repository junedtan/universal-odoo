from openerp.osv import osv, fields
from datetime import datetime, date
from openerp.tools.translate import _

# ==========================================================================================================================

class hr_recruitment_period(osv.osv):
	
	_inherit = 'hr.recruitment.period'

# OVERRIDES ----------------------------------------------------------------------------------------------------------------
	"""
	def create(self, cr, uid, vals, context={}):
	# hitung data acceptance rate
		if vals.get('no_of_actual'):
			acc_rate = (float(vals['no_of_accepted']) / float(vals['no_of_actual'])) * 100
			vals.update({'acceptance_rate': acc_rate})
	# yu panggil create-nya
		return super(hr_recruitment_period, self).create(cr, uid, vals, context)
		
	def write(self, cr, uid, ids, vals, context={}):
	# kalau ada perubahan data recruitment yang melamar, hitung ulang datanya
		if vals.get('no_of_actual'):
			for data in self.browse(cr, uid, ids, context):
				acc_rate = (float(data.no_of_accepted) / float(vals['no_of_actual'])) * 100
				vals.update({'acceptance_rate': acc_rate})
	# yu panggil write-nya
		return super(hr_recruitment_period, self).write(cr, uid, ids, vals, context)
	
	"""
	
	