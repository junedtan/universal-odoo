from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
import urllib
import re
import csv
import os 
from . import SERVER_TIMEZONE, GPS_URL

class foms_gps_sync(osv.osv):

	_name = 'foms.gps.sync'
	_description = 'Logging and syncing with GPS system'

	_columns = {
		'location_id': fields.many2one('res.partner.location', 'Location'),
		'action_time': fields.datetime('Time'),
		'action': fields.selection((
			('in','Go in'),
			('out','Go out')
		), 'Action'),
		'vehicle_id': fields.many2one('fleet.vehicle', 'Vehicle'),
		'km': fields.integer('KM'),
	}

	_order = "vehicle_id, action_time"

	def cron_sync_gps_data(self, cr, uid, context={}):
		dir_path = os.path.dirname(os.path.realpath(__file__))
		processed_logs_url = "%s%sstatic%sprocessed_gps_files.log" % (dir_path,os.sep,os.sep)
	# ambil list url ke file2 CSV
	# file2 yang diambil hanyalah yang sekian hari ke belakang, sesuai isi variabel days
		f = urllib.urlopen(GPS_URL+'group/')
		content = f.read()
		result = re.findall("href=\"geoIO-[0-9]{14}-[0-9]{14}.csv\"", content)
		paths = []
		days = [
			datetime.now().strftime("%Y%m%d"),
			(datetime.now() - timedelta(hours=24)).strftime("%Y%m%d"),
			(datetime.now() - timedelta(hours=48)).strftime("%Y%m%d"),
		]
		today = datetime.now().strftime("")
		for line in result:
			path = line.replace("\"","").replace("href=","")
			included = False
			for day in days:
				if path.startswith("geoIO-"+day): 
					included = True
					break
			if included:
				paths.append("%sgroup/%s" % (GPS_URL,path))
	# supaya ngga dobel proses file, ambil dulu list file yang sudah pernah diproses
		processed_files = []
		try:
			with open(processed_logs_url) as f:
				content = f.readlines()
				processed_files = [x.strip() for x in content] 
		except IOError:
			pass
	# mulai buka satu persatu url csv nya, mengambil isi csv dan menarunya ke geo_lines
		geo_lines = []
		has_been_added = []
		for path in paths:
			if path in processed_files: continue
			f = urllib.urlopen(path)
			csvlines = csv.reader(f)
			for row in csvlines:
				if row[0] == 'geofence_id': continue
				key = "%s_%s_%s_%s" % (row[0],row[2],row[3],row[5])
				if key not in has_been_added:
					has_been_added.append(key)
					geo_lines.append(row)
		# sekalian tambahkan file baru ke list file yang sudah pernah diproses
			processed_files.append(path)
	# tulis kembali list file yang sudah pernah diproses
		with open(processed_logs_url, "wt") as f:
			for file in processed_files:
				f.write("%s\n" % file)
	# mulai masukin satu2 log GPS nya ke model ini
		locations = {}
		vehicles = {}
		location_obj = self.pool.get('res.partner.location')
		vehicle_obj = self.pool.get('fleet.vehicle')
		for line in geo_lines:
		# line[0] = geofence_id, line[1] = nama geofence (not used), line[2] = time, 
		# line[3] = action (Go In atau Go Out), line [4] = gps_id (not used), line[5] = nopol,
		# line[6] = km
			geofence_id = int(line[0])
			action_time = datetime.strptime(line[2],"%Y-%m-%d %H:%M:%S") - timedelta(hours=SERVER_TIMEZONE)
			action = line[3] == 'Go Out' and 'out' or 'in'
			vehicle_nopol = line[5]
			km = int(line[6])
		# ambil location_id berdasarkan geofence_id
		# locations adalah cache supaya ngga bolak balik ambil database
			if geofence_id not in locations:
				location_ids = location_obj.search(cr, uid, [('gps_system_id','=',geofence_id)])
				if len(location_ids) > 0:
					locations.update({geofence_id: location_ids[0]})
		# kalo udah dicoba dicari ngga ada juga, ya sudah ignore entri ini
			if geofence_id not in locations: continue
			location_id = locations[geofence_id]
		# cari mobil
		# vehicles adalah cache supaya ngga bolak balik ambil database
			if vehicle_nopol not in vehicles:
				vehicle_ids = vehicle_obj.search(cr, uid, ['|',('license_plate_nospace','=',vehicle_nopol),('license_plate','=',vehicle_nopol)])
				if len(vehicle_ids) > 0:
					vehicles.update({vehicle_nopol: vehicle_ids[0]})
		# kalo udah dicoba dicari ngga ada juga, ya sudah ignore entri ini
			if vehicle_nopol not in vehicles: continue
			vehicle_id = vehicles[vehicle_nopol]
		# masukin ke log GPS
			new_id = self.create(cr, uid, {
				'location_id': location_id,
				'action_time': action_time,
				'action': action,
				'vehicle_id': vehicle_id,
				'km': km,
				})
