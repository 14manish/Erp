import xmlrpc.client

url = 'http://localhost:8069'
db = 'Wingspann_DB'  # the stock db verified earlier
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

print(f"Authenticated as UID: {uid}")

# Check our custom view
views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read',
    [[['key', '=', 'drone_traceability.report_invoice_document_wingspann']]],
    {'fields': ['id', 'name', 'active', 'arch']}
)

if views:
    print(f"Found our view: {views[0]['id']} - Active: {views[0]['active']}")
else:
    print("Our custom view is NOT in the database! The module was not upgraded successfully.")

# Check l10n_in views that might conflict
l10n_views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read',
    [[['key', '=', 'l10n_in.l10n_in_report_invoice_document_inherit']]],
    {'fields': ['id', 'key', 'name', 'active', 'arch']}
)
print("l10n_in invoice views:")
for v in l10n_views:
    print(f"  {v['key']}")
    print(v['arch'])
