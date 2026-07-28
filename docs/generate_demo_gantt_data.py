"""
generate_demo_gantt_data.py
Creates 4 products with BOMs and 30 Manufacturing Orders across 4 weeks.
"""
import xmlrpc.client, random
from datetime import datetime, timedelta

URL      = 'http://localhost:8069'
DB       = 'Wingspann_DB'
USERNAME = 'test@example.com'
PASSWORD = 'Admin@123'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid    = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

def search(model, domain, fields=None, limit=100, order=None):
    kw = {'limit': limit}
    if fields: kw['fields'] = fields
    if order:  kw['order']  = order
    return models.execute_kw(DB, uid, PASSWORD, model, 'search_read', [domain], kw)

def create(model, vals):
    return models.execute_kw(DB, uid, PASSWORD, model, 'create', [vals])

def write(model, ids, vals):
    return models.execute_kw(DB, uid, PASSWORD, model, 'write', [ids, vals])

def call(model, method, ids, *args):
    return models.execute_kw(DB, uid, PASSWORD, model, method, [ids] + list(args))

print("=" * 60)
print("  Wingspann ERP — Demo Data Generator")
print("=" * 60)

# ── Work Centers ───────────────────────────────────────────────
wcs = search('mrp.workcenter', [['active','=',True]], ['id','name'])
fx10_id  = next((w['id'] for w in wcs if 'FX10'     in w['name']), None)
mark2_id = next((w['id'] for w in wcs if 'Mark Two' in w['name']), None)
print(f"Work Centers → FX10: {fx10_id}, Mark Two: {mark2_id}")

# ── Users ──────────────────────────────────────────────────────
users    = search('res.users', [['active','=',True],['share','=',False]], ['id','name'], limit=10)
user_ids = [u['id'] for u in users]
print(f"Users: {[u['name'] for u in users]}")

# ── Find Manufacture route ─────────────────────────────────────
routes = search('stock.route', [['name','ilike','Manufacture']], ['id','name'], limit=1)
mfg_route_id = routes[0]['id'] if routes else None
print(f"Manufacture route: {mfg_route_id}")

# ── Create Products + BOMs ─────────────────────────────────────
PRODUCTS = [
    ("Wingspann Drone Frame MK-1",  "FX10: Print Frame",    120, "Mark Two: Finish Frame",  90),
    ("Wingspann Propeller Hub",     "FX10: Print Hub",       90, "Mark Two: Hub Quality",   60),
    ("Wingspann Landing Strut",     "FX10: Print Strut",    150, "Mark Two: Strut Finish",  75),
    ("Wingspann Battery Mount",     "FX10: Print Mount",    100, "Mark Two: Mount QC",      45),
]

bom_map = {}  # bom_id → product_id

for pname, op1_name, op1_dur, op2_name, op2_dur in PRODUCTS:
    existing = search('product.product', [['name','=',pname]], ['id'])
    if existing:
        prod_id = existing[0]['id']
        print(f"  ✓ '{pname}' exists (id={prod_id})")
    else:
        vals = {'name': pname, 'type': 'product'}
        if mfg_route_id:
            vals['route_ids'] = [(4, mfg_route_id)]
        prod_id = create('product.product', vals)
        print(f"  + Created '{pname}' (id={prod_id})")

    tmpl_data = models.execute_kw(DB, uid, PASSWORD, 'product.product', 'read', [[prod_id]], {'fields':['product_tmpl_id']})
    tmpl_id   = tmpl_data[0]['product_tmpl_id'][0]

    existing_bom = search('mrp.bom', [['product_tmpl_id','=',tmpl_id]], ['id'])
    if existing_bom:
        bom_id = existing_bom[0]['id']
        print(f"    ✓ BOM exists (id={bom_id})")
    else:
        bom_id = create('mrp.bom', {
            'product_tmpl_id': tmpl_id, 'product_id': prod_id,
            'product_qty': 1.0, 'type': 'normal',
        })
        create('mrp.routing.workcenter', {
            'name': op1_name, 'workcenter_id': fx10_id,
            'bom_id': bom_id, 'time_mode': 'manual', 'time_cycle_manual': op1_dur,
        })
        create('mrp.routing.workcenter', {
            'name': op2_name, 'workcenter_id': mark2_id,
            'bom_id': bom_id, 'time_mode': 'manual', 'time_cycle_manual': op2_dur,
        })
        print(f"    + Created BOM+Routing (id={bom_id})")

    bom_map[bom_id] = prod_id

# ── Generate 30 MOs ───────────────────────────────────────────
print(f"\nGenerating 30 Manufacturing Orders over ±4 weeks …")

today    = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
mo_ids   = []
sessions = [(8,0),(9,30),(11,0),(13,0),(14,30),(15,30),(16,0)]
bom_list = list(bom_map.keys())

for i in range(30):
    day_offset = random.randint(-3, 25)
    target = today + timedelta(days=day_offset)
    # Push weekends to next Monday
    if target.weekday() == 5: target += timedelta(days=2)
    if target.weekday() == 6: target += timedelta(days=1)

    h, mn = random.choice(sessions)
    mn += random.choice([0, 15, 30])
    planned = target.replace(hour=h, minute=mn % 60, second=0)

    bom_id   = random.choice(bom_list)
    prod_id  = bom_map[bom_id]
    user_id  = random.choice(user_ids)

    mo_id = create('mrp.production', {
        'product_id':  prod_id,
        'product_qty': random.choice([1, 1, 1, 2, 3]),
        'bom_id':      bom_id,
        'date_start':  planned.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id':     user_id,
    })
    mo_ids.append(mo_id)
    print(f"  MO {mo_id:3d} | {planned.strftime('%a %d-%b %H:%M')} | user {user_id}")

# ── Confirm all ────────────────────────────────────────────────
print("\nConfirming all MOs …")
models.execute_kw(DB, uid, PASSWORD, 'mrp.production', 'action_confirm', [mo_ids])

# ── Plan all (puts WOs on Gantt) ───────────────────────────────
print("Planning all MOs …")
models.execute_kw(DB, uid, PASSWORD, 'mrp.production', 'button_plan', [mo_ids])

print("\n" + "=" * 60)
print("  ✅  Demo data COMPLETE!")
print(f"  • 4 products with BOMs and routings")
print(f"  • {len(mo_ids)} MOs confirmed and planned")
print(f"  • Go to: Manufacturing > Operations > Work Center Schedule")
print("=" * 60)
