import xmlrpc.client

url = 'http://localhost:8069'
db = 'Wingspann_ERP-v0.1.3'
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Find the Purchase Order sequence
seq_ids = models.execute_kw(db, uid, password, 'ir.sequence', 'search', [[['code', '=', 'purchase.order']]])

if seq_ids:
    # Update the sequence format
    models.execute_kw(db, uid, password, 'ir.sequence', 'write', [seq_ids, {
        'prefix': 'WSGPL/[FY]/',
        'padding': 3,
        'number_next': 100
    }])
    print("Successfully updated PO sequence to %(fy)s/ format.")
else:
    print("Could not find purchase.order sequence.")
