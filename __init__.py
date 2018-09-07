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
	'partner_mobile': 'Work Mobile',
	'gender': 'Gender',
	'partner_mobile': 'Phone',
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

GPS_URL = "http://geo.u.utrack.co.id/geof/"

SERVER_TIMEZONE = 7 # WIB

"""
mengkonversi sebuah datetime (string) atau date (string) menjadi datetime yang sesuai timezone
server. Di Odoo, timezone pasti GMT, yang artinya bila kita ingin men-store misal tanggal 
2017-04-13 00:00:00 dalam WIB maka seharusnya yang disimpan bila timezone adalah GMT+7 adalah 
2017-04-12 17:00:00. method ini melakukan hal itu

date_time: date atau datetime string yang mau dikonversi
is_date: apakah string mengandung date (True) atau datetime (False)
reverse: kalau True, maka jam dikurangi, bila False maka ditambah
to_string: kalau True, hasil konversi dibalikin menjadi string instead of direturn mentah2
	sebagai datetime
"""
def datetime_to_server(date_time, is_date=False, reverse=False, to_string=True, 
datetime_format='%Y-%m-%d %H:%M:%S', datetime_display_format='%d-%m-%Y %H:%M:%S',
empty_value=None):
	if not date_time: 
		if to_string:
			return empty_value is None and '' or str(empty_value)
		else:
			return empty_value
	from datetime import datetime, timedelta
	if isinstance(date_time, datetime):
		date_time_convert = date_time
	else:
		if is_date:
			date_time += ' 00:00:00'
		date_time_convert = datetime.strptime(date_time,datetime_format)
	if reverse:
		date_time_convert = date_time_convert - timedelta(hours=SERVER_TIMEZONE)
	else:
		date_time_convert = date_time_convert + timedelta(hours=SERVER_TIMEZONE)
	if to_string:
		return date_time_convert.strftime(datetime_display_format)
	else:
		return date_time_convert

def now_to_server(reverse=False, to_string=True, datetime_display_format='%d-%m-%Y %H:%M:%S'):
	from datetime import datetime, timedelta
	date_time = datetime.now()
	return datetime_to_server(date_time, reverse=reverse, to_string=to_string, datetime_display_format=datetime_display_format)


import chjs_region
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
import res_users
import controllers
import res_partner
import fleet
import hr_payroll
import hr_contract
import foms_contract
import foms_order
import gps
import timeline
import maintenance