from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class hr_recruitment_requirement(osv.osv):
	
	_inherit = 'hr.recruitment.requirement'
	
	_columns = {
		'requirement_test_lines': fields.one2many('hr.recruitment.requirement.test', 'header_id', 'Tests', copy=True),
		'requirement_document_lines': fields.one2many('hr.recruitment.requirement.document', 'header_id', 'Documents', copy=True),
	}

# OVERRIDE ------------------------------------------------------------------------------------------------------------------

	def copy(self, cr, uid, id, default=None, context=None):
		if default is None:
			default = {}
		if not default.get('name', False):
			default.update(name=_('%s (copy)') % (self.browse(cr, uid, id, context=context).name))
		return super(hr_recruitment_requirement, self).copy(cr, uid, id, default=default, context=context)

