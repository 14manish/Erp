import xmlrpc.client

url = 'http://localhost:8069'
db = 'Wingspann_DB'
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

if not uid:
    print("Authentication failed.")
    exit(1)

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

print(f"Authenticated as UID: {uid}")
print("Searching for dummy data tagged with 'DUMMY_2YEARS'...")

# 1. Cancel and Delete Invoices
invoices = models.execute_kw(db, uid, password, 'account.move', 'search',
    [[['ref', 'like', 'DUMMY_2YEARS']]]) # Invoices generated from SOs often inherit the client_order_ref into the ref field
if not invoices:
    # Let's search by origin/source document if ref didn't work
    orders = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
        [[['client_order_ref', '=', 'DUMMY_2YEARS']]], {'fields': ['name']})
    order_names = [o['name'] for o in orders]
    if order_names:
        invoices = models.execute_kw(db, uid, password, 'account.move', 'search',
            [[['invoice_origin', 'in', order_names]]])

if invoices:
    print(f"Found {len(invoices)} dummy invoices. Canceling and deleting...")
    models.execute_kw(db, uid, password, 'account.move', 'button_cancel', [invoices])
    models.execute_kw(db, uid, password, 'account.move', 'unlink', [invoices])

# 2. Cancel and Delete Sales Orders
orders = models.execute_kw(db, uid, password, 'sale.order', 'search',
    [[['client_order_ref', '=', 'DUMMY_2YEARS']]])
if orders:
    print(f"Found {len(orders)} dummy sales orders. Canceling and deleting...")
    models.execute_kw(db, uid, password, 'sale.order', 'action_cancel', [orders])
    models.execute_kw(db, uid, password, 'sale.order', 'unlink', [orders])

print("Cleanup complete!")
