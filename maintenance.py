from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from datetime import datetime, date, timedelta
from openerp import SUPERUSER_ID
from . import SERVER_TIMEZONE
from . import datetime_to_server, now_to_server
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class universal_maintenance(osv.osv):
	_name = 'universal.maintenance'
	_description = 'Utility class for one-time maintenance scripts'
	_auto = False

	# kasus september 2018: 
	"""
	ada kebutuhan supaya expense begitu create langsung waiting approval. sebelumnya 
	diimplementastikan dengan memanggil langsung method button Confirm. sementara ini 
	works fine, ketika user mengklik button Approve untuk ke langkah berikutnya, record 
	tidak ada perubahan apa2 TANPA pesan error apapun.

	karena expense menggunakan workflow, seharusnya yang dipanggil adalah signal_workflow 
	"confirm" untuk mengubah record dari draft menjadi waiting approval. sehingga ketika
	user mengklik button Approve, yang mana men-signal wofkflow process accepted, karena 
	record sudah ada di workflow confirm maka dia bisa maju.

	untuk record2 lama yang udah keburu "nyangkut", kita signal supaya maju.
	PS: kode asli hr_expense method expense_confirm dikondisikan me-return True saja supaya 
	proses confirm ngga kepanggil dua kali.
	JANGAN LUPA ngembaliin lagi kode asli itu ke kondisi semula!!!!
	"""
	def fix_workflow_signal_on_expense(self, cr, uid, context={}):
		expense_obj = self.pool.get('hr.expense.expense')
		expense_ids = expense_obj.search(cr, uid, [
			('state','=','confirm'),
			])
		for expense in expense_obj.browse(cr, uid, expense_ids):
			expense.signal_workflow('confirm')

	"""
	sampai 7 sept 2018 pengisian expense line tidak otomatis mengisi kolom Expense Note
	kondisikan supaya kolom yang kosong diisi dengan nama produknya
	"""
	def fix_empty_expense_note(self, cr, uid, context={}):
		expense_line_obj = self.pool.get('hr.expense.line')
		expense_ids = expense_line_obj.search(cr, uid, [])
		for expense_line in expense_line_obj.browse(cr, uid, expense_ids):
			if not expense_line.name:
				expense_line_obj.write(cr, uid, [expense_line.id], {'name': expense_line.product_id.name})

