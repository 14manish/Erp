"""
generate_more_demo_jobs.py
Fills the Wingspann_DB with an additional 40 dense Manufacturing Orders
to demonstrate the zoom feature over multiple weeks.
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

# ── Resolve Products & BOMs ────────────────────────────────────
boms = search('mrp.bom', [], ['id', 'product_id'])
bom_map = {b['id']: b['product_id'][0] for b in boms if b.get('product_id')}

if not bom_map:
    print("No BOMs found. Please run generate_demo_gantt_data.py first.")
    exit(1)

# ── Get Users ──────────────────────────────────────────────────
users = search('res.users', [['active','=',True],['share','=',False]], ['id','name'])
user_ids = [u['id'] for u in users]

# ── Create 45 more orders for density ───────────────────────────
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
mo_ids = []
sessions = [(7, 30), (9, 0), (10, 30), (12, 0), (13, 30), (15, 0), (16, 30), (18, 0)]
bom_list = list(bom_map.keys())

print("Generating 45 more dense Manufacturing Orders...")
for i in range(45):
    # Denser grouping (mostly around current week and next two weeks)
    day_offset = random.choice([0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 16, 17, 21, 22])
    target = today + timedelta(days=day_offset)
    
    h, mn = random.choice(sessions)
    planned = target.replace(hour=h, minute=mn, second=0)

    bom_id   = random.choice(bom_list)
    prod_id  = bom_map[bom_id]
    user_id  = random.choice(user_ids)

    mo_id = create('mrp.production', {
        'product_id':  prod_id,
        'product_qty': random.choice([1, 2]),
        'bom_id':      bom_id,
        'date_start':  planned.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id':     user_id,
    })
    mo_ids.append(mo_id)

print("Confirming new orders...")
models.execute_kw(DB, uid, PASSWORD, 'mrp.production', 'action_confirm', [mo_ids])
print("Planning new orders...")
models.execute_kw(DB, uid, PASSWORD, 'mrp.production', 'button_plan', [mo_ids])

print(f"Successfully generated and planned {len(mo_ids)} additional jobs.")
