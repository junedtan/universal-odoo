MAX_DRIVER_AGE = 45 # in years

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

RELIGION = (
	('islam','Islam'),
	('catholic','Catholic'),
	('protestant','Protestant'),
	('hindu','Hindu'),
	('buddha','Buddha'),
	('konghucu','Konghucu'),
	('other','Other'),
)

import hr_recruitment
import hr_employee

