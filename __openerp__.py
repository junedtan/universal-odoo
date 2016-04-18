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
	'depends': ["base","board","web","hr","hr_recruitment","hr_employee_family"],
	'sequence': 150,
	'data': [
		'data/hr.department.csv',
		'data/hr.job.csv',
		'data/hr_recruitment.xml',
		'views/hr_recruitment.xml',
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
