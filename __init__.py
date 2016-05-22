MAX_DRIVER_AGE = 45 # in years
MIN_CHECK_DUPLI = 3 # in params

FAMILY_RELATIONSHIP = (
	('spouse','Spouse'),
	('deceased_spouse','Deceased Spouse'),
 	('divorced_spouse','Divorced Spouse'),
	('child','Child'),
	('parent','Parent'),
	('family','Other family'),
	('no_family','No family relationship'),
)

FAMILY_GENDER = (
	('male','Male'),
	('female','Female'),
)

MARITAL_STATUS = (
	('single','Single'),
	('married','Married'),
	('widowed','Widow/Widower'),
	('divorced','Divorced'),
)

DRIVER_TYPE = (
	('active','Active'),
	('standby','Stand By'),
	('replacement','Replacement (GS)'),
	('contract','Contracted'),
	('daily','Daily'),
	('internal','Internal/Office')
)

CONTRACT_STATE = (
	('terminated','Terminated'),
	('ongoing','Ongoing'),
	('finished','Finished')
)

RELIGION = (
	('islam','Islam'),
	('catholic','Catholic'),
	('protestant','Protestant'),
	('hindu','Hindu'),
	('buddha','Buddha'),
	('konghucu','Konghucu'),
	('other','Other'),
)

PARAM_CHECK_DUPLI = (
	('name','Name'),
	('gender','Gender'),
	('date_of_birth','Date of Birth'),
	('identification_id','Identification Id'),
)

EMP_APP_DICT = {
	'mobile_phone': 'partner_mobile',
	'mobile_phone2': 'partner_mobile2',
	'mobile_phone3': 'partner_mobile3',
	'phone': 'partner_phone',
	'address': 'partner_address'
}

DOMAIN_DUPLI_DICT = {
	'name': 'ilike'
}

import hr_recruitment
import hr_employee
import hr_contract

