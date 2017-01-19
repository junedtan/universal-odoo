from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date

# ==========================================================================================================================

class res_users(osv.osv):
	
	_inherit = 'res.users'
	
	_columns = {
		'pin': fields.char('PIN', size=64, copy=False),
	}
	
	def write(self , cr, uid, ids, vals, context={}):
		if isinstance(ids, int): ids = [ids]
		result = super(res_users, self).write(cr, uid, ids, vals, context=context)
	# bila ada perubahan password, untuk fullday_passenger ubah juga pin nya (idem password), dan broadcast perubahannya
		if vals.get('password'):
			user_id = ids[0]
			order_obj = self.pool.get('foms.order')
			is_fullday_passenger = self.has_group(cr, user_id, 'universal.group_universal_passenger')
		# kalau fullday passenger
			if is_fullday_passenger:
			# ubah juga pin nya. asumsikan user_id adalah usernya itu sendiri (tidak diwakilkan)
				self.write(cr, uid, [user_id], {
					'pin': vals.get('password'),
				})
			# ubah pin semua order yang sudha keburu dibuat, yang order_by nya adalah user ini
				order_ids = order_obj.search(cr, uid, [('order_by','=',user_id),\
					('state','in',['new','confirmed','ready','started','start_confirmed','paused','resumed'])])
				if len(order_ids) > 0:
					order_obj.write(cr, uid, order_ids, {
						'pin': vals.get('password'),
					}, context=context)
		return result

	def get_user_ids_by_group(self, cr, uid, module_name, usergroup_id):
		if isinstance(usergroup_id, (str)):
			model_obj = self.pool.get('ir.model.data')
			model, usergroup_id = model_obj.get_object_reference(cr, uid, module_name, usergroup_id)
		cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s" % usergroup_id)
		result = []
		for row in cr.dictfetchall():
			result.append(row['uid'])
		return result
