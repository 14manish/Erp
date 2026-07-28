import xmlrpc.client
import pprint

url = 'http://localhost:8069'
db = 'Wingspann_DB'
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

lines = models.execute_kw(db, uid, password, 'account.move.line', 'search_read',
    [[['move_id.name', '=', 'INV/2026/00001']]],
    {'fields': ['id', 'name', 'display_type']}
)
pprint.pprint(lines)
