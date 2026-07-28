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

# Check Partners
partners = models.execute_kw(db, uid, password, 'res.partner', 'search_read',
    [[['customer_rank', '>', 0]]], {'fields': ['id', 'name'], 'limit': 5})
if not partners:
    partners = models.execute_kw(db, uid, password, 'res.partner', 'search_read',
        [[]], {'fields': ['id', 'name'], 'limit': 5})
print("Partners:", partners)

# Check Products
products = models.execute_kw(db, uid, password, 'product.product', 'search_read',
    [[['sale_ok', '=', True]]], {'fields': ['id', 'name', 'list_price'], 'limit': 5})
if not products:
    products = models.execute_kw(db, uid, password, 'product.product', 'search_read',
        [[]], {'fields': ['id', 'name', 'list_price'], 'limit': 5})
print("Products:", products)

# Check Sales Orders to see if sale module exists
try:
    sales = models.execute_kw(db, uid, password, 'sale.order', 'search_read',
        [[]], {'fields': ['id', 'name'], 'limit': 1})
    print("Sale order module exists. Count:", len(sales))
except Exception as e:
    print("Error querying sale.order:", e)
