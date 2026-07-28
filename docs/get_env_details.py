import xmlrpc.client

url = 'http://localhost:8069'
db = 'Wingspann_DB'
username = 'test@example.com'
password = 'Admin@123'

common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
try:
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("Authentication failed.")
        exit()
except Exception as e:
    print(f"Could not connect: {e}")
    exit()

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

print("=== Users ===")
users = models.execute_kw(db, uid, password, 'res.users', 'search_count', [[]])
print(f"Total Users: {users}")

print("=== Companies ===")
companies = models.execute_kw(db, uid, password, 'res.company', 'search_read', [[]], {'fields': ['name']})
for c in companies:
    print(f"- {c['name']}")

print("=== Installed Apps ===")
apps = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', [[['state', '=', 'installed'], ['application', '=', True]]], {'fields': ['name', 'shortdesc']})
print(f"Total Installed Apps: {len(apps)}")
for a in apps:
    print(f"- {a['name']}: {a['shortdesc']}")

print("=== Data Volumes ===")
products = models.execute_kw(db, uid, password, 'product.product', 'search_count', [[]])
partners = models.execute_kw(db, uid, password, 'res.partner', 'search_count', [[]])
sales = models.execute_kw(db, uid, password, 'sale.order', 'search_count', [[]])
purchases = models.execute_kw(db, uid, password, 'purchase.order', 'search_count', [[]]) if 'purchase' in [a['name'] for a in apps] else 0
mrp = models.execute_kw(db, uid, password, 'mrp.production', 'search_count', [[]]) if 'mrp' in [a['name'] for a in apps] else 0

print(f"Products: {products}")
print(f"Partners/Contacts: {partners}")
print(f"Sales Orders: {sales}")
print(f"Purchase Orders: {purchases}")
print(f"Manufacturing Orders: {mrp}")
