var mobile_app_intent_definition = {
	'univmobile_intent_main': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_main',
		'target': 'main',
	},
	'univmobile_intent_chpwd': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_chpwd',
		'target': 'main',
	},
	'univmobile_intent_logout': {
		'intent_type': 'url_internal',
		'url': '/web/session/logout?redirect=/',
	},
	'univmobile_intent_shuttle': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_shuttle',
		'target': 'main',
	},
	'univmobile_intent_contract': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_contract',
		'target': 'main',
	},
	'univmobile_intent_contract_detail': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_contract_detail',
		'target': 'main',
	},
	'univmobile_intent_request_quota_change': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_request_quota_change',
		'target': 'modal',
	},
	'univmobile_intent_request_quota_reject': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_request_quota_reject',
		'target': 'modal',
	},
	'univmobile_intent_request_quota_approve': {
		'intent_type': 'confirm_and_action',
		'target_activity_id': 'univmobile_actv_request_quota_approve',
		'target': 'confirm',
	},
	'univmobile_intent_order': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_order',
		'target': 'main',
	},
	'univmobile_intent_order_detail': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_order_detail',
		'target': 'main',
	},
	'univmobile_intent_change_start_planned_time': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_change_start_planned_time',
		'target': 'modal',
	},
	'univmobile_intent_book_vehicle': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_book_vehicle',
		'target': 'main',
    },
	'univmobile_intent_edit_order': {
		'intent_type': 'page',
		'target_activity_id': 'univmobile_actv_edit_order',
		'target': 'modal',
	},
	'univmobile_intent_cancel_order': {
		'intent_type': 'confirm_and_action',
		'target_activity_id': 'univmobile_actv_cancel_order',
		'target': 'confirm',
	},
}