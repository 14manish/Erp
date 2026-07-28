import xmlrpc.client
import pprint

url = 'http://localhost:8069'
db = 'Wingspann_DB'
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Search for the report action for invoices
reports = models.execute_kw(db, uid, password, 'ir.actions.report', 'search_read',
    [[['model', '=', 'account.move']]],
    {'fields': ['id', 'name', 'report_name', 'report_type', 'xml_id']}
)

print("Invoice Report Actions:")
pprint.pprint(reports)
