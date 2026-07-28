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

print("1. Enabling Work Orders (group_mrp_routings)...")
config_id = models.execute_kw(db, uid, password, 'res.config.settings', 'create', [{'group_mrp_routings': True}])
models.execute_kw(db, uid, password, 'res.config.settings', 'execute', [[config_id]])

print("2. Creating Work Centers...")
wc_fx10_id = models.execute_kw(db, uid, password, 'mrp.workcenter', 'create', [{
    'name': 'Markforged FX10',
    'time_efficiency': 100,
    'default_capacity': 1.0,
}])
wc_marktwo_id = models.execute_kw(db, uid, password, 'mrp.workcenter', 'create', [{
    'name': 'Markforged Mark Two',
    'time_efficiency': 100,
    'default_capacity': 1.0,
}])

print("3. Creating Test Product...")
product_id = models.execute_kw(db, uid, password, 'product.product', 'create', [{
    'name': 'Test Drone Frame Print',
    'type': 'product',
    'route_ids': [(6, 0, [models.execute_kw(db, uid, password, 'stock.route', 'search', [[['name', '=', 'Manufacture']]])[0]])]
}])

# Need product template id for BOM
product = models.execute_kw(db, uid, password, 'product.product', 'read', [[product_id]], {'fields': ['product_tmpl_id']})
tmpl_id = product[0]['product_tmpl_id'][0]

print("4. Creating BOM and Routing...")
bom_id = models.execute_kw(db, uid, password, 'mrp.bom', 'create', [{
    'product_tmpl_id': tmpl_id,
    'product_id': product_id,
    'product_qty': 1.0,
    'type': 'normal',
}])

# Add operations
op1_id = models.execute_kw(db, uid, password, 'mrp.routing.workcenter', 'create', [{
    'name': 'Print on FX10',
    'workcenter_id': wc_fx10_id,
    'bom_id': bom_id,
    'time_mode': 'manual',
    'time_cycle_manual': 120, # 2 hours
}])

op2_id = models.execute_kw(db, uid, password, 'mrp.routing.workcenter', 'create', [{
    'name': 'Print on Mark Two',
    'workcenter_id': wc_marktwo_id,
    'bom_id': bom_id,
    'time_mode': 'manual',
    'time_cycle_manual': 90, # 1.5 hours
}])

print("5. Generating Manufacturing Orders scheduled over next 14 days...")
base_date = datetime.now()
created_mos = []

# Generate 6 scattered MOs
for i in range(6):
    # Pick a random day in next 14 days, avoiding weekends for better scheduling mapping
    days_ahead = random.choice([1, 2, 3, 4, 7, 8, 9, 10, 11, 14])
    # Pick random hour between 9 AM and 2 PM (so 2-hour jobs fit in same day)
    hour = random.randint(9, 14)
    
    planned_date = base_date.replace(hour=hour, minute=0, second=0) + timedelta(days=days_ahead)
    
    mo_id = models.execute_kw(db, uid, password, 'mrp.production', 'create', [{
        'product_id': product_id,
        'product_qty': 1.0,
        'bom_id': bom_id,
        'date_start': planned_date.strftime('%Y-%m-%d %H:%M:%S'),
    }])
    created_mos.append(mo_id)
    print(f"   Created MO ID {mo_id} for {planned_date.strftime('%Y-%m-%d %H:%M')}")

print("6. Confirming and Planning MOs...")
models.execute_kw(db, uid, password, 'mrp.production', 'action_confirm', [created_mos])
models.execute_kw(db, uid, password, 'mrp.production', 'button_plan', [created_mos])

print("Setup Complete! All components ready.")
