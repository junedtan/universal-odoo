from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta

# ==========================================================================================================================

class foms_contract(osv.osv):

	_name = "foms.contract"
	_inherit = ['mail.thread','chjs.base.webservice']
	_description = 'Forms Contract'
	
# FUNCTION FIELD METHODS ---------------------------------------------------------------------------------------------------

	def _get_fee_gapok(self, cr, uid, ids, field_name, arg, context):
		res = {}
		gapok_fee_obj = self.pool.get('res.partner.gapok.fee')
		for row in self.browse(cr, uid, ids, context):
			gapok_fee_ids = gapok_fee_obj.search(cr, uid, [('header_id','=',row.customer_id.id),('homebase_id','=',row.homebase_id.id)])
			if len(gapok_fee_ids) > 0:
				gapok_fee_data = gapok_fee_obj.browse(cr, uid, gapok_fee_ids[0])
				res[row.id] = gapok_fee_data.gapok_fee
			else:
				res[row.id] = None
		return res

	_columns = {
	# BASIC INFORMATION
		'name': fields.char('Contract No.', required=True, copy=False),
		'contract_date': fields.date('Contract Date'),
		'homebase_id' : fields.many2one('chjs.region', 'Homebase'),
		'customer_id' : fields.many2one('res.partner', 'Customer', required=True, domain=[('customer','=',True),('is_company','=',True)], ondelete='restrict'),
		'customer_contact_id' : fields.many2one('res.partner', 'Customer PIC', required=True, domain=[('customer','=',True),('is_company','=',False)], ondelete='restrict'),
		'is_order_replacement_vehicle': fields.boolean('Can Have Replacement?'),
		'start_date': fields.date('Start Date', required=True, copy=False),
		'end_date': fields.date('End Date', required=True, copy=False),
		'service_type': fields.selection([
			('full_day','Full-day Service'),
			('by_order','By Order'),
			('shuttle','Shuttle')], 'Service Type', required=True),
		'state': fields.selection([
			('proposed','Proposed'),
			('confirmed','Confirmed'),
			('planned','Planned'),
			('active','Active'),
			('prolonged','Prolonged'),
			('terminated','Terminated'),
			('finished','Finished')], 'State', required=True, track_visibility="onchange", copy=False),
		'termination_reason': fields.text('Termination Reason', copy=False),
		'overtime_id' : fields.many2one('hr.overtime', 'Overtime Setting', ondelete='restrict'),
		'working_time_id' : fields.many2one('resource.calendar', 'Working Time', ondelete='restrict'),
		'fleet_types': fields.one2many('foms.contract.fleet.type', 'header_id', 'Fleet Types'),
		'car_drivers': fields.one2many('foms.contract.fleet', 'header_id', 'Car and Drivers'),
		'shuttle_schedules': fields.one2many('foms.contract.shuttle.schedule', 'header_id', 'Shuttle Schedules'),
		'allocation_units': fields.one2many('foms.contract.alloc.unit', 'header_id', 'Allocation Units'),
		'extended_contract_id' : fields.many2one('foms.contract', 'Extended Contract', readonly=True, copy=False,
			help="If not empty, this contract is an extension of the contract."),
		'last_fullday_autogenerate_date': fields.date('Last Fullday Autogenerate Date', copy=False),
		'last_shuttle_autogenerate_date': fields.date('Last Shuttle Autogenerate Date', copy=False),
	# FEES
		'fee_calculation_type': fields.selection([
			('monthly','Period-based'),
			('order_based','Order-based')], 'Fee Calculation Type'),
		'fee_fleet': fields.one2many('foms.contract.fleet.fee', 'header_id', 'Fleet Monthly Fee'),
		'fee_premature_termination': fields.float('Premature Termination Fee'),
		'fee_structure_id' : fields.many2one('hr.payroll.structure', 'Fee Structure', domain=[('is_customer_contract','=',True)], ondelete='restrict'),
		'fee_gapok': fields.function(_get_fee_gapok, method=True, type='float', string="Gapok"),
		'fee_varpok': fields.float('Varpok'),
		'fee_makan': fields.float('Makan/hari'),
		'fee_pulsa': fields.float('Pulsa'),
		'fee_hadir': fields.float('Uang Hadir'),
		'fee_seragam': fields.float('Seragam'),
		'fee_bpjs_tk': fields.float('BPJS TK (%)'),
		'fee_bpjs_ks': fields.float('BPJS Kesehatan (%)'),
		'fee_insurance': fields.float('Insurance'),
		'fee_cuti': fields.float('Cuti/hari'),
		'fee_mcu': fields.float('Medical Checkup'),
		'fee_training': fields.float('Training'),
		'fee_lk_pp': fields.float('LK PP/trip'),
		'fee_lk_inap': fields.float('LK Inap/trip'),
		'fee_holiday_allowance': fields.float('Holiday Allowance'),
		'fee_management': fields.float('Management Fee (%)'),
		'fee_order_based': fields.one2many('foms.contract.order.based.fee', 'header_id', 'Order-Based Fees'),
	# USAGE CONTROL
		'allocation_unit_limits': fields.one2many('foms.contract.alloc.unit.limit', 'header_id', 'Allocation Unit Usage Limits'),
		'usage_control_level': fields.selection([
			('no_control','No Control'),
			('warning','Limit with Warning'),
			('approval','Limit with Approval')], 'Usage Control Level'),
		'usage_control_setting': fields.selection([
			('global', 'Single setting applies to all allocation units'),
			('per_alloc_unit', 'Each allocation unit may have different setting'),
		], 'Usage Control Setting'),
		'usage_allocation_maintained_by': fields.selection([
			('customer','Customer'),
			('universal','Universal')], 'Usage Allocation Maintained By'),
		'global_yellow_limit': fields.float('Yellow Limit (Rp)'),	
		'global_red_limit': fields.float('Red Limit (Rp)'),	
		'global_balance_credit_per_usage': fields.float('Balance Credit per Usage'),	
		'is_expense_record': fields.boolean('Include Expense Report'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'state': 'proposed',
		'usage_control_level': 'no_control',
		'usage_allocation_maintained_by': 'customer',
		'fee_varpok': 0,
		'fee_makan': 0,
		'fee_pulsa': 0,
		'fee_hadir': 0,
		'fee_seragam': 0,
		'fee_bpjs_tk': 0,
		'fee_bpjs_ks': 0,
		'fee_insurance': 0,
		'fee_cuti': 0,
		'fee_mcu': 0,
		'fee_training': 0,
		'fee_lk_pp': 0,
		'fee_lk_inap': 0,
		'fee_holiday_allowance': 0,
		'fee_management': 0,
		'is_expense_record': False,
	}	
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_constraints = [
		#(_const_start_end_date, _('Start date must'), ['shipper_id']),
	]
	
	_sql_constraints = [
		('const_start_end_date','CHECK(end_date > start_date)','End date must be after start date.'),
		('const_premature1', 'CHECK(fee_premature_termination >= 0)', _('Premature termination must be greater than or equal to zero.')),
		('const_premature2', 'CHECK(fee_premature_termination <= 100)', _('Premature termination must be less than or equal to 100.')),
		('const_bpjs_tk1', 'CHECK(fee_bpjs_tk >= 0)', _('BPJS TK must be greater than or equal to zero.')),
		('const_bpjs_tk2', 'CHECK(fee_bpjs_tk <= 100)', _('BPJS TK must be less than or equal to 100.')),
		('const_bpjs_ks1', 'CHECK(fee_bpjs_ks >= 0)', _('BPJS Kesehatan must be greater than or equal to zero.')),
		('const_bpjs_ks2', 'CHECK(fee_bpjs_ks <= 100)', _('BPJS Kesehatan must be less than or equal to 100.')),
		('const_management1', 'CHECK(fee_management >= 0)', _('Management fee must be greater than or equal to zero.')),
		('const_management2', 'CHECK(fee_management <= 100)', _('Management fee must be less than or equal to 100.')),
		('const_varpok', 'CHECK(fee_varpok >= 0)', _('Fee varpok must be greater than or equal to zero.')),
		('const_makan', 'CHECK(fee_makan >= 0)', _('Fee makan must be greater than or equal to zero.')),
		('const_pulsa', 'CHECK(fee_pulsa >= 0)', _('Fee pulsa must be greater than or equal to zero.')),
		('const_hadir', 'CHECK(fee_hadir >= 0)', _('Fee hadir must be greater than or equal to zero.')),
		('const_seragam', 'CHECK(fee_seragam >= 0)', _('Fee seragam must be greater than or equal to zero.')),
		('const_insurance', 'CHECK(fee_insurance >= 0)', _('Fee insurance must be greater than or equal to zero.')),
		('const_cuti', 'CHECK(fee_cuti >= 0)', _('Fee cuti must be greater than or equal to zero.')),
		('const_mcu', 'CHECK(fee_mcu >= 0)', _('Fee MCU must be greater than or equal to zero.')),
		('const_training', 'CHECK(fee_training >= 0)', _('Fee training must be greater than or equal to zero.')),
		('const_lk_pp', 'CHECK(fee_lk_pp >= 0)', _('Fee Luar Kota PP must be greater than or equal to zero.')),
		('const_lk_inap', 'CHECK(fee_lk_inap >= 0)', _('Fee Luar Kota Menginap must be greater than or equal to zero.')),
		('const_holiday_allowance', 'CHECK(fee_holiday_allowance >= 0)', _('Fee holiday allowance must be greater than or equal to zero.')),
	]		

# OVERRIDES ----------------------------------------------------------------------------------------------------------------

	def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
		context = context and context or {}
		user_obj = self.pool.get('res.users')
	# kalau diminta untuk mengambil semua kontrak by user_id tertentu
		if context.get('by_user_id',False):
			domain = []
			user_id = context.get('user_id', uid)
			is_pic = user_obj.has_group(cr, user_id, 'universal.group_universal_customer_pic')
			is_approver = user_obj.has_group(cr, user_id, 'universal.group_universal_approver')
			is_driver = user_obj.has_group(cr, user_id, 'universal.group_universal_driver')
			is_booker = user_obj.has_group(cr, user_id, 'universal.group_universal_booker')
			is_fullday_passenger = user_obj.has_group(cr, user_id, 'universal.group_universal_passenger')
		# kalau pic, domainnya menjadi semua contract yang pic nya adalah partner terkait
			if is_pic:
				user_data = user_obj.browse(cr, uid, user_id)
				if user_data.partner_id:
					domain.append(('customer_contact_id','=',user_data.partner_id.id))
		# kalau driver, domainnya menjadi semua contract yang car_drivers assignment nya adalah dia
			if is_driver:
				employee_obj = self.pool.get('hr.employee')
				employee_ids = employee_obj.search(cr, uid, [('user_id','=',user_id)])
				if len(employee_ids) > 0:
					contract_fleet_obj = self.pool.get('foms.contract.fleet')
					contract_fleet_ids = contract_fleet_obj.search(cr, uid, [('driver_id','=',employee_ids[0])])
					if len(contract_fleet_ids) > 0:
						contract_ids = []
						for contract_fleet in contract_fleet_obj.browse(cr, uid, contract_fleet_ids):
							contract_ids.append(contract_fleet.header_id.id)
						contract_ids = list(set(contract_ids))
						domain.append(('id','in',contract_ids))
		# kalau full-day passenger
			if is_fullday_passenger:
				contract_fleet_obj = self.pool.get('foms.contract.fleet')
				contract_fleet_ids = contract_fleet_obj.search(cr, uid, [('fullday_user_id','=',user_id)])
				if len(contract_fleet_ids) > 0:
					contract_ids = []
					for contract_fleet in contract_fleet_obj.browse(cr, uid, contract_fleet_ids):
						contract_ids.append(contract_fleet.header_id.id)
					contract_ids = list(set(contract_ids))
					domain.append(('id','in',contract_ids))
				else:
					args = [('id','=',-1)] # supaya ga keambil apapun despite isi args nya
			if len(domain) > 0:
				args = domain + args
			else:
				return []
		return super(foms_contract, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)
	
	def webservice_handle(self, cr, uid, user_id, command, data_id, model_data, context={}):
		user_obj = self.pool.get('res.users')
		result = super(foms_contract, self).webservice_handle(cr, uid, user_id, command, data_id, model_data, context=context)
	# untuk command change_password
		if command == 'change_password':
			user_obj = self.pool.get('res.users')
			old_password = model_data.get('old_password')
			new_password = model_data.get('new_password')
		# change password usernya
			user_obj.change_password(cr, user_id, old_password, new_password)
			result = 'ok'
		return result

# ACTION -------------------------------------------------------------------------------------------------------------------

	def action_load_customer_defaults(self, cr, uid, ids, context=None):
		for contract in self.browse(cr, uid, ids):
			if not contract.homebase_id:
				raise osv.except_osv(_('Contract Error'),_('Please set homebase first before loading customer defaults.'))
			customer = contract.customer_id
			if contract.fee_calculation_type == 'monthly':
				new_data = {
					'fee_makan': customer.default_fee_makan,
					'fee_pulsa': customer.default_fee_pulsa,
					'fee_hadir': customer.default_fee_hadir,
					'fee_seragam': customer.default_fee_seragam,
					'fee_bpjs_tk': customer.default_fee_bpjs_tk,
					'fee_bpjs_ks': customer.default_fee_bpjs_ks,
					'fee_insurance': customer.default_fee_insurance,
					'fee_cuti': customer.default_fee_cuti,
					'fee_mcu': customer.default_fee_mcu,
					'fee_training': customer.default_fee_training,
					'fee_lk_pp': customer.default_fee_lk_pp,
					'fee_lk_inap': customer.default_fee_lk_inap,
				}
			elif contract.fee_calculation_type == 'order_based':
				order_based_fee = []
			# order-based fee: hapus dari kontrak sekarang
				if len(contract.fee_order_based) > 0:
					for fee in contract.fee_order_based:
						order_based_fee.append([2,fee.id,{}])
			# order-based fee: tambahin yang default dari customer setting
				if len(customer.order_based_fee) > 0: 
					for fee in customer.order_based_fee:
						order_based_fee.append([0,False,{
							'fleet_vehicle_model_id': fee.fleet_vehicle_model_id.id,
							'fee_by_order': fee.fee_by_order,
							'fee_by_hour': fee.fee_by_hour,
							'fee_by_day': fee.fee_by_day,
						}])
					new_data = {
						'fee_order_based': order_based_fee,
					}
			else:
				raise osv.except_osv(_('Contract Error'),_('Please select Fee Calculation Type first.'))
		# load rent fees (sewa mobil)
			rent_fees = []
			if len(contract.fee_fleet) > 0:
				for fee in contract.fee_fleet:
					rent_fees.append([2,fee.id,{}])
			for fee in customer.rent_fees:
				rent_fees.append([0,False,{
					'fleet_type_id': fee.fleet_vehicle_model_id.id,
					'monthly_fee': fee.monthly_fee,
				}])
			new_data.update({
				'fee_fleet': rent_fees,
			})
		# update kontrak dengan mengisi default values dari customer
			self.write(cr, uid, [contract.id], new_data)
		return True

	def action_confirm(self, cr, uid, ids, context=None):
		user_obj = self.pool.get('res.users')
		for contract in self.browse(cr, uid, ids, context=context):
		# cek setting2an yang seharusnya sudah ada by the time kontrak di-confirm
			if len(contract.fleet_types) == 0:
				raise osv.except_osv(_('Contract Error'),_('Please input Fleet Types first.'))
			if not contract.homebase_id or not contract.working_time_id or not contract.fee_calculation_type:
				raise osv.except_osv(_('Contract Error'),_('Please complete Fee Basic Setting first.'))
			if len(contract.fee_fleet) == 0:
				raise osv.except_osv(_('Contract Error'),_('Please input Vehicle Fees first.'))
			if contract.fee_calculation_type == 'monthly':
				if not contract.fee_structure_id:
					raise osv.except_osv(_('Contract Error'),_('Please input Fee Structure first.'))
				if not contract.fee_management:
					raise osv.except_osv(_('Contract Error'),_('Please input Management Fee first.'))
		# pic customer sudah harus dikasih user dengan group PIC Customer tentunya
			user_ids = user_obj.search(cr, uid, [('partner_id','=',contract.customer_contact_id.id)])
			has_user = False
			if len(user_ids) > 0:
				if user_obj.has_group(cr, user_ids[0], 'universal.group_universal_customer_pic'):
					has_user = True
			if not has_user:
				raise osv.except_osv(_('Contract Error'),_('Customer PIC has not been given user login, or the user login does not belong to Customer PIC group.'))
		# ganti status menjadi Confirmed
			self.write(cr, uid, [contract.id], {'state': 'confirmed'})
	
	def action_plan_fleet(self, cr, uid, ids, context=None):
		contract = self.browse(cr, uid, ids[0], context=context)
	# untuk setiap kebutuhan jenis mobil, buat dulu list of dict sejumlah kebutuhan
		vehicle_needs = []
		for fleet_type in contract.fleet_types:
			for i in range(0,fleet_type.number):
				vehicle_needs.append({
					'fleet_type_id': fleet_type.fleet_type_id.id,
					'fleet_vehicle_id': None,
					'driver_id': None,
				})
	# isikan dengan alokasi yang sudah ada, bila ada tentunya
		if len(contract.car_drivers) > 0:
			for allocation in contract.car_drivers:
				if not allocation.fleet_vehicle_id and not allocation.driver_id: continue
				for idx, need in enumerate(vehicle_needs):
					if need['fleet_vehicle_id']: continue
					if need['fleet_type_id'] != allocation.fleet_type_id.id: continue
					vehicle_needs[idx].update({
						'fleet_vehicle_id': allocation.fleet_vehicle_id and allocation.fleet_vehicle_id.id or None,
						'driver_id': allocation.driver_id and allocation.driver_id.id or None,
					})
					break
	# panggil si memory yang buat allocate driver
		return {
			'name': _('Fleet Planning'),
			'view_mode': 'form',
			'view_type': 'form',
			'res_model': 'foms.contract.fleet.planning.memory',
			'type': 'ir.actions.act_window',
			'context': {
				'default_contract_id': contract.id,
				'default_contract_no': contract.name,
				'default_customer_id': contract.customer_id.id,
				'default_start_date': contract.start_date,
				'default_end_date': contract.end_date,
				'default_planning_line': vehicle_needs,
			},
			'target': 'new',
		}
		
# ONCHANGE -----------------------------------------------------------------------------------------------------------------
	
	def onchange_customer(self, cr, uid, ids, customer_id):
		if not customer_id: return {}
		result = {'value': {}, 'domain': {}}
		customer_obj = self.pool.get('res.partner')
		customer_data = customer_obj.browse(cr, uid, customer_id)
	# isikan fleet_types dan fee_fleet sesuai default di customer ybs
		if len(customer_data.rent_fees) > 0:
			fleet_types = []
			fleet_fees = []
			for row in customer_data.rent_fees:
				fleet_types.append({
					'fleet_type_id': row.fleet_vehicle_model_id.id,
				})
				fleet_fees.append({
					'fleet_type_id': row.fleet_vehicle_model_id.id,
					'monthly_fee': row.monthly_fee,
				})
			result['value'].update({
				'fleet_types': fleet_types,
				'fee_fleet': fleet_fees,
			})
	# kasih domain ke field customer_contact_id, supaya memilih hanya yang di bawah perusahaan customer
		pic_ids = []
		for contact in customer_data.child_ids:
			pic_ids.append(contact.id)
		if len(pic_ids) > 0:
			result['domain'].update({
				'customer_contact_id': [('id','in',pic_ids)]
			})
	# isikan default working time dan overtime, sekalian premature termination fee
		result['value'].update({
			'working_time_id': customer_data.default_working_time.id,
			'overtime_id': customer_data.default_overtime.id,
			'fee_premature_termination': customer_data.default_fee_premature_termination,
		})
	# sudah selesai
		return result

# CRON ---------------------------------------------------------------------------------------------------------------------

	def cron_set_contract_start_end(self, cr, uid, context=None):
	# otomatis ubah status menjadi started atau finished sesuai tanggal kontrak
		today = (datetime.now() - timedelta(hours=7) + timedelta(hours=24)).strftime('%Y-%m-%d')
	# ubah status menjadi mulai
		contract_ids = self.search(cr, uid, [('state','in',['planned']),('start_date','<=',today)])
		if len(contract_ids) > 0:
			self.write(cr, uid, contract_ids, {'state': 'active'})
	# ubah status menjadi selesai
		today = (datetime.now() - timedelta(hours=7)).strftime('%Y-%m-%d')
		contract_ids = self.search(cr, uid, [('state','in',['active']),('end_date','<=',today)])
		if len(contract_ids) > 0:
			self.write(cr, uid, contract_ids, {'state': 'finished'})

# ==========================================================================================================================

class foms_contract_fleet_type(osv.osv):

	_name = "foms.contract.fleet.type"
	_description = 'Contract Fleet Types'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type', ondelete='restrict'),
		'number': fields.integer('Number of Vehicles'),
	}
	
# ==========================================================================================================================

class foms_contract_fleet(osv.osv):

	_name = "foms.contract.fleet"
	_description = 'Contract Fleets'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type', ondelete='restrict'),
		'fleet_vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle', ondelete='restrict'),
		'driver_id': fields.many2one('hr.employee', 'Driver', ondelete='restrict'),
		'fullday_user_id': fields.many2one('res.users', 'Fullday User', ondelete='restrict'),
	}

# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	def _constraint_employee_is_driver(self, cr, uid, ids, context=None):
		employee_obj = self.pool.get('hr.employee')
		for data in self.browse(cr, uid, ids, context):
			if not data.driver_id: continue
			if not employee_obj.emp_is_driver(cr, uid, data.driver_id.id, context):
				raise osv.except_osv(_('Contract Error'),_('Employee %s is not a driver. Please check his/her job position.' % data.driver_id.name))
				return False
		return True
	
	_constraints = [
		(_constraint_employee_is_driver, _('Driver Check Error'), ['driver_id'])
	]
	
	_sql_constraints = [
		('unique_fleet_type', 'UNIQUE(header_id,fleet_vehicle_id)', _('You cannot assign the same vehicle more than once under one contract.')),
		('unique_driver_id', 'UNIQUE(header_id,driver_id)', _('You cannot assign the same driver more than once under one contract.')),
	]	
	
# ==========================================================================================================================

class foms_contract_fleet_planning_memory(osv.osv):

	_name = "foms.contract.fleet.planning.memory"
	_description = 'Contract Fleet Planning'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'contract_id': fields.many2one('foms.contract', 'Contract'),
		'contract_no': fields.char('Contract No.', readonly=True),
		'customer_id' : fields.many2one('res.partner', 'Customer', readonly=True),
		'start_date': fields.date('Start Date', readonly=True),
		'end_date': fields.date('End Date', readonly=True),
		'planning_line': fields.one2many('foms.contract.fleet.planning.line.memory', 'header_id', 'Planning Lines'),
	}
	
	def action_save_planning(self, cr, uid, ids, context=None):
		form_data = self.browse(cr, uid, ids[0])
		contract_id = form_data.contract_id.id
		contract_obj = self.pool.get('foms.contract')
		contract_data = contract_obj.browse(cr, uid, contract_id)
		new_fleet_data = []
	# hapus yang sudah ada
		if contract_data.car_drivers:
			for fleet in contract_data.car_drivers:
				new_fleet_data.append([2,fleet.id])
	# masukkan yang baru
		vehicle_ids = []
		for fleet in form_data.planning_line:
			vehicle_id = fleet.fleet_vehicle_id and fleet.fleet_vehicle_id.id or None
			if vehicle_id: vehicle_ids.append(vehicle_id)
			new_fleet_data.append([0,False,{
				'fleet_type_id': fleet.fleet_type_id.id,
				'fleet_vehicle_id': vehicle_id,
				'driver_id': fleet.driver_id and fleet.driver_id.id or None,
				'fullday_user_id': fleet.fullday_user_id and fleet.fullday_user_id.id or None,
			}])
		contract_obj.write(cr, uid, [contract_id], {
			'car_drivers': new_fleet_data,
		})
	# ini di-load ulang supaya mendapatkan data fleet planning yang terbaru
		contract_data = contract_obj.browse(cr, uid, contract_id)
	# semua driver harus sudah punya user_id
		user_obj = self.pool.get('res.users')
		if contract_data.car_drivers:
			for fleet in contract_data.car_drivers:
				if not fleet.driver_id: continue
				if not fleet.driver_id.user_id.id or not user_obj.has_group(cr, fleet.driver_id.user_id.id, 'universal.group_universal_driver'):
					raise osv.except_osv(_('Contract Error'),_('Driver %s has not been given user login, or the user login does not belong to Driver group.') % fleet.driver_id.name)
	# fullday user harus termasuk group fullday-service passenger sudah diset passwordnya
		if contract_data.service_type in ['full_day']:
			for fleet in contract_data.car_drivers:
				if not fleet.fullday_user_id: continue
				if not user_obj.has_group(cr, fleet.fullday_user_id.id, 'universal.group_universal_passenger'):
					raise osv.except_osv(_('Contract Error'),_('User %s does not belong to Fullday-service Passenger group.') % fleet.fullday_user_id.name)
				user_data = user_obj.browse(cr, uid, fleet.fullday_user_id.id)
				if user_data.password_crypt == '':
					raise osv.except_osv(_('Contract Error'),_('A password has not been set to user %s. Password (PIN) is needed to confirm start/finish order.') % fleet.fullday_user_id.name)
	# kalau status sekarang adalah confirmed, ubah menjadi planned
		if contract_data.state in ['confirmed']:
		# ...hanya jika semua vehicle dan driver sudah diset
			all_set = True
			if contract_data.car_drivers:
				for fleet in contract_data.car_drivers:
					if not fleet.fleet_vehicle_id or not fleet.driver_id:
						all_set = False
						break
					if contract_data.service_type in ['full_day']:
						if not fleet.fullday_user_id:
							all_set = False
							break
			else:
				all_set = False
			if all_set:
				contract_obj.write(cr, uid, [contract_id], {
					'state': 'planned',
				})
			# sync post outgoing ke user-user yang terkait (PIC, driver, PJ Alloc unit) , memberitahukan ada contract baru
				self.webservice_post(cr, uid, ['pic','driver','fullday_passenger'], 'create', contract_data, webservice_context={
					'notification': 'contract_new',
				}, context=context)
		return True
		
# SYNCRONIZER MOBILE APP ---------------------------------------------------------------------------------------------------

	def webservice_post(self, cr, uid, targets, command, contract_data, webservice_context={}, data_columns=[], context=None):
		sync_obj = self.pool.get('chjs.webservice.sync.bridge')
		user_obj = self.pool.get('res.users')
		if command == 'create':
			if 'pic' in targets:
				pic_user_ids = user_obj.search(cr, uid, [('partner_id','=',contract_data.customer_contact_id.id)])
				if len(pic_user_ids) > 0:
					sync_obj.post_outgoing(cr, pic_user_ids[0], 'foms.contract', 'create', contract_data.id, data_context=webservice_context)
			if 'driver' in targets:
				for car_driver in contract_data.car_drivers:
					if not car_driver.driver_id: continue
					sync_obj.post_outgoing(cr, car_driver.driver_id.user_id.id, 'foms.contract', 'create', contract_data.id, data_context=webservice_context)
			if 'fullday_passenger' in targets:
				for car_driver in contract_data.car_drivers:
					if not car_driver.fullday_user_id: continue
					sync_obj.post_outgoing(cr, car_driver.fullday_user_id.id, 'foms.contract', 'create', contract_data.id, data_context=webservice_context)

# ==========================================================================================================================

class foms_contract_fleet_planning_line_memory(osv.osv):

	_name = "foms.contract.fleet.planning.line.memory"
	_description = 'Contract Fleet Planning Line'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract.fleet.planning.memory', 'Fleet Planning'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type'),
		'fleet_vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle'),
		'driver_id': fields.many2one('hr.employee', 'Driver'),
		'fullday_user_id': fields.many2one('res.users', 'Fullday User', ondelete='restrict'),
	}
	
# ==========================================================================================================================

class foms_contract_fleet_fee(osv.osv):

	_name = "foms.contract.fleet.fee"
	_description = 'Contract Fleet Type Monthly Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'fleet_type_id': fields.many2one('fleet.vehicle.model', 'Fleet Type', ondelete='restrict'),
		'monthly_fee': fields.float('Monthly Fee/Vehicle'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('check_monthly_fee', 'CHECK(monthly_fee >= 0)', _('Monthly Fee must be greater than or equal to 0.')),
		('unique_fleet_type', 'UNIQUE(header_id,fleet_type_id)', _('There can only be one fleet type for each vehicle fee setting.')),
	]	
	
# ==========================================================================================================================

class foms_contract_order_based_fee(osv.osv):

	_name = "foms.contract.order.based.fee"
	_description = 'Contract Order-Based Fee'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'fleet_vehicle_model_id': fields.many2one('fleet.vehicle.model', 'Vehicle Model', ondelete='restrict'),
		'fee_by_order': fields.float('per Order'),
		'fee_by_hour': fields.float('per Hour'),
		'fee_by_day': fields.float('per Day'),
	}
	
# CONSTRAINTS -------------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('check_fee_by_order', 'CHECK(fee_by_order >= 0)', _('per Order Fee must be greater than or equal to 0.')),
		('check_fee_by_hour', 'CHECK(fee_by_hour >= 0)', _('per Hour Fee must be greater than or equal to 0.')),
		('check_fee_by_day', 'CHECK(fee_by_day >= 0)', _('per Day Fee must be greater than or equal to 0.')),
		('unique_fleet_type', 'UNIQUE(header_id,fleet_vehicle_model_id)', _('There can only be one fleet type for each fee setting.')),
	]	
	
# ==========================================================================================================================

class foms_contract_shuttle_schedule(osv.osv):

	_name = "foms.contract.shuttle.schedule"
	_description = 'Forms Contract Shuttle Schedule'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'dayofweek': fields.selection([
			('0','Monday'),
			('1','Tuesday'),
			('2','Wednesday'),
			('3','Thursday'),
			('4','Friday'),
			('5','Saturday'),
			('6','Sunday'),], 'Day of Week'),
		'sequence': fields.integer('Sequence'),
		'route_id': fields.many2one('res.partner.route', 'Route', ondelete='restrict'),
		'fleet_vehicle_id': fields.many2one('fleet.vehicle', 'Fleet Vehicle', ondelete='restrict'),
		'departure_time': fields.float('Departure Time'),	
		'arrival_time': fields.float('Arrival Time'),	
	}		
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_departure_arrival', 'CHECK(arrival_time > departure_time)', _('Arrival time must be greater than departure time.')),
	]
	
# ORDER -------------------------------------------------------------------------------------------------------------------------

	_order = 'header_id, dayofweek, sequence'
	
# ==========================================================================================================================

class foms_contract_alloc_unit(osv.osv):

	_name = "foms.contract.alloc.unit"
	_description = 'Contract Allocation Unit'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'name': fields.char('Name', required=True),
		'approver_ids': fields.many2many('res.users', 'foms_alloc_unit_approvers', 'alloc_unit_id', 
			'user_id', string='Responsibles'),
		'booker_ids': fields.many2many('res.users', 'foms_alloc_unit_bookers', 'alloc_unit_id', 
			'booker_id', string='Bookers'),
	}		
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_contract_alloc_unit', 'UNIQUE(header_id,name)', _('Please input unique contract allocation unit.')),
	]	
	
# ==========================================================================================================================

class foms_contract_alloc_unit_limit(osv.osv):

	_name = "foms.contract.alloc.unit.limit"
	_description = 'Contract Allocation Unit Usage Limit'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'header_id': fields.many2one('foms.contract', 'Contract', ondelete='cascade'),
		'name': fields.char('Name', required=True),
		'yellow_limit': fields.float('Yellow Limit'),
		'red_limit': fields.float('Red Limit'),
		'balance_credit_per_usage': fields.float('Balance Credit Per Usage'),
	}		
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'yellow_limit': 0,
		'red_limit': 0,
	}	
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_contract_alloc_unit', 'UNIQUE(header_id,name)', _('Please input unique contract allocation unit.')),
	]	
	
# ==========================================================================================================================

class foms_contract_quota(osv.osv):

	_name = "foms.contract.quota"
	_description = 'Contract Quota'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'customer_contract_id': fields.many2one('foms.contract', 'Contract', required=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('foms.contract.alloc.unit', 'Alloc. Unit', required=True, ondelete='cascade'),
		'period': fields.char('Period', required=True),
		'yellow_limit': fields.float('Yellow Limit'),
		'red_limit': fields.float('Red Limit'),
	}		
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('unique_contract_alloc_period', 'UNIQUE(customer_contract_id,allocation_unit_id,period)', _('Please input unique contract, allocation unit, and period.')),
	]	
	

# ==========================================================================================================================

class foms_contract_quota_change_log(osv.osv):

	_name = "foms.contract.quota.change.log"
	_description = 'Contract Quota Change Log'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'customer_contract_id': fields.many2one('foms.contract', 'Contract', required=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('foms.contract.alloc.unit', 'Alloc. Unit', required=True, ondelete='cascade'),
		'state': fields.selection([
			('draft','Draft'),
			('approved','Approved'),
			('rejected','Rejected'),], 'State'),
		'request_by': fields.many2one('res.users', 'Request By', ondelete='restrict'),
		'request_date': fields.datetime('Request Date', required=True),
		'period': fields.char('Period', required=True),
		'request_longevity': fields.selection([
			('temporary','Temporary'),
			('permanent','Permanent'),], 'Request Longevity'),
		'old_yellow_limit': fields.float('Old Yellow Limit', readonly=True),
		'old_red_limit': fields.float('Old Red Limit', readonly=True),
		'new_yellow_limit': fields.float('New Yellow Limit'),
		'new_red_limit': fields.float('New Red Limit'),
		'confirm_by': fields.many2one('res.users', 'Confirm By', ondelete='restrict'),
		'confirm_date': fields.datetime('Confirm Date'),
		'reject_reason': fields.text('Reject Reason'),
	}
	
# DEFAULTS ----------------------------------------------------------------------------------------------------------------------
	
	_defaults = {
		'request_date': lambda *a: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
		'request_by': lambda self, cr, uid, ctx: uid,
		'request_longevity': 'temporary',
		'state': 'draft',
	}	
	
# CONSTRAINTS --------------------------------------------------------------------------------------------------------------
	
	_sql_constraints = [
		('const_new_red_yellow_limit', 'CHECK(new_yellow_limit < new_red_limit)', _('New red limit must be greater than new yellow limit.')),
	]	
	

# ==========================================================================================================================

class foms_contract_quota_usage_log(osv.osv):

	_name = "foms.contract.quota.usage.log"
	_description = 'Contract Quota Usage Log'
	
# COLUMNS ------------------------------------------------------------------------------------------------------------------

	_columns = {
		'usage_date': fields.datetime('Usage Date', required=True, readonly=True),
		'order_id': fields.many2one('foms.order', 'Order', required=True, readonly=True, ondelete='cascade'),
		'customer_contract_id': fields.many2one('foms.contract', 'Contract', required=True, readonly=True, ondelete='cascade'),
		'allocation_unit_id': fields.many2one('foms.contract.alloc.unit', 'Alloc. Unit', required=True, readonly=True, ondelete='cascade'),
		'period': fields.char('Period', required=True, readonly=True),
		'usage_amount': fields.float('Usage Amount', required=True, readonly=True),
	}
	
