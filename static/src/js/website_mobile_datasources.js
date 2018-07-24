var mobile_app_data_sources = {
	'shuttle_contracts' : {
		id : 'shuttle_contracts',
		type: 'ajax',
		url: '/mobile_app/fetch_contract_shuttles',
		views: {}, 
	},
	'shuttle_by_day': {
		id: 'shuttle_by_day',
		type: 'static',
		views: {},
	},
	'contracts': {
		id: 'contracts',
		type: 'ajax',
		url: '/mobile_app/fetch_contracts',
		views: {},
	},
	'contract_detail': {
		id: 'contract_detail',
		type: 'static',
		views: {},
	},
	'contract_detail_usage_control': {
		id: 'contract_detail_usage_control',
		type: 'ajax',
		url: '/mobile_app/get_usage_control_list',
		views: {},
	},
	'contract_detail_quota_changes': {
		id: 'contract_detail_quota_changes',
		type: 'ajax',
		url: '/mobile_app/fetch_contract_quota_changes',
		views: {},
	},
	'contract_detail_request_quota_change': {
		id: 'contract_detail_request_quota_change',
		type: 'static',
		views: {},
	},
	'contract_detail_request_quota_reject': {
		id: 'contract_detail_request_quota_reject',
		type: 'static',
		views: {},
	},
	'order_pending': {
		id: 'order_pending',
		type: 'ajax',
		url: '/mobile_app/fetch_orders/{"classification":"pending"}',
		views: {},
	},
	'order_ready': {
		id: 'order_ready',
		type: 'ajax',
		url: '/mobile_app/fetch_orders/{"classification":"ready"}',
		views: {},
	},
	'order_running': {
		id: 'order_running',
		type: 'ajax',
		url: '/mobile_app/fetch_orders/{"classification":"running"}',
		views: {},
	},
	'order_history': {
		id: 'order_history',
		type: 'ajax',
		url: '/mobile_app/fetch_orders/{"classification":"history"}',
		views: {},
	},
	'orders': {
		id: 'orders',
		type: 'ajax',
		url: '/mobile_app/fetch_orders/{}',
		views: {},
	},
	'order_detail': {
		id: 'order_detail',
		type: 'ajax',
		url: '/mobile_app/fetch_orders',
		views: {},
	},
	'order_edit': {
		id: 'order_edit',
		type: 'ajax',
		url: '/mobile_app/get_required_edit_order',
		views: {},
	},
	'book_vehicle': {
		id: 'book_vehicle',
		type: 'ajax',
		url: '/mobile_app/get_required_book_vehicle',
		views: {},
    },
}