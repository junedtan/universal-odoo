from openerp.osv import fields, osv
from openerp.tools.translate import _

class universal_config_settings(osv.osv_memory):
	_name = 'universal.config.settings'
	_inherit = 'res.config.settings'

	_columns = {
		'default_first_party_name': fields.char("Contract's First Party Name", size=100, default_model="hr.contract", 
			help="When printing out contract there is a section for signing up containing first party (representing company) and second party (the employee). This setting is for name of the first party."),
		'default_first_party_position': fields.char("Contract's First Party Position", size=100, default_model="hr.contract", 
			help="When printing out contract there is a section for signing up containing first party (representing company) and second party (the employee). This setting is for position of the first party."),
	}
	
