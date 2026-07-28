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

# Find mrp.workcenter
workcenters = models.execute_kw(db, uid, password, 'mrp.workcenter', 'search',
    [[['name', 'in', ['Drone Assembly Line', 'Percy Jackson']]]])
if workcenters:
    print(f"Found work centers: {workcenters}. Deleting...")
    models.execute_kw(db, uid, password, 'mrp.workcenter', 'unlink', [workcenters])
    print("Deleted work centers.")
else:
    print("Work centers already deleted or not found.")

# Find resource.resource
resources = models.execute_kw(db, uid, password, 'resource.resource', 'search',
    [[['name', 'in', ['Drone Assembly Line', 'Percy Jackson']]]])
if resources:
    print(f"Found resources: {resources}. Deleting...")
    models.execute_kw(db, uid, password, 'resource.resource', 'unlink', [resources])
    print("Deleted resources.")
else:
    print("Resources already deleted or not found.")

print("Successfully removed demo data!")
