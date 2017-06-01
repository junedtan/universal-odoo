from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date
from openerp import SUPERUSER_ID

# ==========================================================================================================================

class res_users(osv.osv):
	
	_inherit = 'res.users'
	
	def _is_hr(self, cr, uid, ids, field_name, arg, context={}):
		result = {}
		try:
			model_obj = self.pool.get('ir.model.data')
			groups = [
				['universal','group_universal_staff_adm_drv_1'],
				['universal','group_universal_spv_hrd_staff'],
				['universal','group_universal_spv_hrd_driver'],
			]
			group_ids = []
			for group_xml_id in groups:
				model, group_id = model_obj.get_object_reference(cr, SUPERUSER_ID, group_xml_id[0], group_xml_id[1])
				if not group_id: continue
				group_ids.append(str(group_id))
			user_ids = []
			if len(group_ids) > 0:
				cr.execute("SELECT uid FROM res_groups_users_rel WHERE gid IN (%s)" % ",".join(group_ids))
				for row in cr.dictfetchall():
					user_ids.append(row['uid'])
			if len(user_ids) == 0: user_ids = [-1]
			for row in self.browse(cr, uid, ids, context=context):
				result[row.id] = row.id in user_ids
		except:
			pass
		return result
	
	_columns = {
		'pin': fields.char('PIN', size=64, copy=False),
		'is_hr': fields.function(_is_hr, type="boolean", method=True, store=True, string='Is HR?'),
	}
	
# OVERRIDES -------------------------------------------------------------------------------------------------------------
	
	def create(self, cr, uid, vals, context=None):
		new_hr_id = super(res_users, self).create(cr, uid, vals, context=context)
		
	# if is_pic or is_approver or is_booker or is_fullday_passenger or is_webservice_sync
	# then delete user group employee, because it shouldn't be that way
		if self._should_hr_off(cr, uid, new_hr_id):
			cr.execute("DELETE FROM res_groups_users_rel WHERE uid=%s AND gid in (" % new_hr_id +
						"SELECT id FROM res_groups WHERE category_id in (" +
						"SELECT id FROM ir_module_category WHERE name='Human Resources' ))")
		return new_hr_id
	
	def write(self, cr, uid, ids, vals, context={}):
		if isinstance(ids, int): ids = [ids]
		result = super(res_users, self).write(cr, uid, ids, vals, context=context)
	# if is_pic or is_approver or is_booker or is_fullday_passenger or is_webservice_sync
	# then delete user group employee, because it shouldn't be that way
	# 	for id in ids:
	# 		if self._should_hr_off(cr, uid, id):
	# 			cr.execute("DELETE FROM res_groups_users_rel WHERE uid=%s AND gid in (" % id +
	# 					   "SELECT id FROM res_groups WHERE category_id in (" +
	# 					   "SELECT id FROM ir_module_category WHERE name='Human Resources' ))")
		
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
	
# METHODS -----------------------------------------------------------------------------------------------------------------
	
	def get_user_ids_by_group(self, cr, uid, module_name, usergroup_id):
		if isinstance(usergroup_id, (str)):
			model_obj = self.pool.get('ir.model.data')
			model, usergroup_id = model_obj.get_object_reference(cr, uid, module_name, usergroup_id)
		cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s" % usergroup_id)
		result = []
		for row in cr.dictfetchall():
			result.append(row['uid'])
		return result

	def get_partner_ids_by_group(self, cr, uid, module_name, usergroup_id):
		if isinstance(usergroup_id, (str)):
			model_obj = self.pool.get('ir.model.data')
			model, usergroup_id = model_obj.get_object_reference(cr, uid, module_name, usergroup_id)
		cr.execute("SELECT * FROM res_groups_users_rel WHERE gid=%s" % usergroup_id)
		user_ids = []
		for row in cr.dictfetchall():
			user_ids.append(row['uid'])
		partner_ids = []
		for user in self.browse(cr, uid, user_ids):
			partner_ids.append(user.partner_id.id)
		return partner_ids
	
	def _should_hr_off(self, cr, uid, id):
		"""
		Check whether user can't have both his universal group and HR group.
		:param cr:
		:param uid:
		:param id: user_id
		:return: true if the user_id
		"""
		groups = ['universal.group_universal_customer_pic',
			'universal.group_universal_approver',
			'universal.group_universal_booker',
			'universal.group_universal_passenger',
			'universal.group_universal_webservice_sync', ]
		isHROff = False
		for group in groups:
			if self.has_group(cr, id, group):
				isHROff = True
				break
		return isHROff