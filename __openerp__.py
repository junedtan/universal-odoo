{
	'name': 'Universal Car Rental HR',
	'version': '0.1',
	'category': 'Human Resources',
	'description': """
		Custom implementation for PT. Universal Car Rental Jakarta
	""",
	'author': 'Christyan Juniady and Associates',
	'maintainer': 'Christyan Juniady and Associates',
	'website': 'http://www.chjs.biz',
	'depends': [
		"base","board","web",
		"chjs_custom_view","chjs_region",
		"hr","hr_recruitment",
		"hr_recruitment_period","hr_recruitment_requirement","hr_employee_family","hr_employee_health",
	],
	'sequence': 150,
	'data': [
		'data/hr.department.csv',
		'data/hr.job.csv',
		'data/hr_recruitment.xml',
		'data/hr_employee.xml',
		'views/hr_recruitment.xml',
		'views/hr_employee.xml',
		'menu/universal_menu.xml',
		'cron/hr_employee.xml'
	],
	'demo': [
	],
	'test': [
	],
	'installable': True,
	'auto_install': False,
	'qweb': [
	]
}
