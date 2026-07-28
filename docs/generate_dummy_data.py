import xmlrpc.client
import random
from datetime import datetime, timedelta

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

# Create dummy partners
dummy_partners = ['Acme Corp', 'Globex Corporation', 'Initech']
partner_ids = []
for name in dummy_partners:
    pid = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['name', '=', name]]])
    if not pid:
        pid = [models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': name, 'customer_rank': 1}])]
    partner_ids.extend(pid)
print(f"Using partners: {partner_ids}")

# Get available products
products = models.execute_kw(db, uid, password, 'product.product', 'search_read',
    [[['sale_ok', '=', True]]], {'fields': ['id', 'list_price'], 'limit': 10})
if not products:
    print("No products found! Please create some products first.")
    exit(1)

print(f"Found {len(products)} products to sell.")

end_date = datetime.now()
start_date = end_date - timedelta(days=730)

orders_created = 0
invoices_created = 0

print("Generating 80 Sales Orders spread across 2 years...")

for i in range(80):
    # Random date within the last 2 years
    random_days = random.randint(0, 730)
    order_date = start_date + timedelta(days=random_days)
    
    partner_id = random.choice(partner_ids)
    
    # Create the sale order
    order_val = {
        'partner_id': partner_id,
        'date_order': order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'client_order_ref': 'DUMMY_2YEARS' # Tag to easily identify dummy data
    }
    
    try:
        order_id = models.execute_kw(db, uid, password, 'sale.order', 'create', [order_val])
        
        # Add 1 to 4 random lines
        for _ in range(random.randint(1, 4)):
            prod = random.choice(products)
            line_val = {
                'order_id': order_id,
                'product_id': prod['id'],
                'product_uom_qty': random.randint(1, 10),
                'price_unit': prod['list_price']
            }
            models.execute_kw(db, uid, password, 'sale.order.line', 'create', [line_val])
            
        # Confirm the order
        models.execute_kw(db, uid, password, 'sale.order', 'action_confirm', [[order_id]])
        orders_created += 1
        
        # Create invoice
        # In Odoo 17, _create_invoices returns an action or a list of invoice ids depending on context,
        # but using 'sale.advance.payment.inv' is safer for xmlrpc, or we can just call _create_invoices.
        invoice_ids = models.execute_kw(db, uid, password, 'sale.order', '_create_invoices', [[order_id]])
        
        # If invoice created, post it and change date
        if invoice_ids:
            if isinstance(invoice_ids, dict): # Sometimes returns an action dict
                pass # Can't easily post from xmlrpc if it returns an action
            else:
                for inv_id in invoice_ids:
                    # Set invoice date to match order date
                    models.execute_kw(db, uid, password, 'account.move', 'write', [[inv_id], {'invoice_date': order_date.strftime('%Y-%m-%d')}])
                    models.execute_kw(db, uid, password, 'account.move', 'action_post', [[inv_id]])
                    invoices_created += 1
                    
        if i % 10 == 0:
            print(f"Generated {i} orders...")
            
    except Exception as e:
        print(f"Error creating order: {e}")

print(f"Success! Generated {orders_created} Sales Orders and {invoices_created} Invoices over 2 years.")
