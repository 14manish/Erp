import xmlrpc.client
import sys

url = 'http://localhost:8069'
db = 'Wingspann_DB'
username = 'test@example.com'
password = 'Admin@123'

try:
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("Authentication failed.")
        sys.exit(1)
        
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # Find the module
    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',
        [[['name', '=', 'drone_traceability']]],
        {'fields': ['id', 'state']}
    )
    
    if modules:
        mod_id = modules[0]['id']
        print(f"Found drone_traceability module. ID: {mod_id}, State: {modules[0]['state']}")
        
        print("Triggering upgrade...")
        # trigger upgrade
        res = models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [[mod_id]])
        print("Upgrade result:", res)
    else:
        print("Module drone_traceability not found!")
except Exception as e:
    print(f"Error during upgrade: {e}")
