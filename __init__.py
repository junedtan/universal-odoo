MAX_DRIVER_AGE = 45 # in years
MIN_STAFF_AGE = 18 # in years
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
	('contract','Contractable'),
)

CONTRACT_STATE = (
	('ongoing','Ongoing'),
	('finished','Finished'),
	('terminated','Terminated'),
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

SPECIAL_PERMIT = (
	('no_action','No Action'),
	('leave','Leave'),
	('absence','Absence'),
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

EMPLOYEE_FIELD = {
	'partner_name': "Applicant's Name",
	'job_id': 'Applied Job',
	'department_id': 'Department',
	'partner_mobile': 'Work Mobile',
	'gender': 'Gender',
	'place_of_birth': 'Place of Birth',
	'date_of_birth': 'Date of Birth',
	'residential_address': 'Residential Address',
	'partner_address': 'Current Address',
	'religion': 'Religion',
	'identification_id': 'ID No',
	'partner_mobile': 'Mobile 1',
	'family_contact_name': 'Contactable Name',
	'family_contactable_address': 'Contactable Address',
	'family_contactable_phone': 'Contactable Phone',
	'family_contactable_relationship': 'Contactable Relationship',
	'marital_status': 'Marital Status'
}

DOMAIN_DUPLI_DICT = {
	'name': 'ilike'
}

import hr_recruitment
import hr_employee
import hr_contract
import hr_termination
import hr_attendance
import hr_holidays
import hr_expense
import hr_recruitment_requirement
import hr_recruitment_period
import resource
import res_config
import controllers
import res_partner
import fleet
import hr_payroll
import hr_contract
import foms_contract
import foms_order
