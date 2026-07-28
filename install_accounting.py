import xmlrpc.client
import sys

url = 'http://localhost:8069'
db = 'Wingspann_ERP-v0.1.3'
username = 'test@example.com'
password = 'Admin@123'
module_name = 'wingspann_accounting'

try:
    print(f"Connecting to {url}...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("Authentication failed.")
        sys.exit(1)
        
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    print("Updating module list...")
    models.execute_kw(db, uid, password, 'ir.module.module', 'update_list', [])
    
    print(f"Searching for module {module_name}...")
    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',
        [[['name', '=', module_name]]],
        {'fields': ['id', 'state']}
    )
    
    if modules:
        mod = modules[0]
        print(f"Found {module_name}. ID: {mod['id']}, State: {mod['state']}")
        
        if mod['state'] == 'installed':
            print("Module is already installed. Upgrading...")
            res = models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [[mod['id']]])
            print("Upgrade result:", res)
        else:
            print("Installing module...")
            res = models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [[mod['id']]])
            print("Install result:", res)
    else:
        print(f"Module {module_name} not found! Check if it is in the addons path.")
except Exception as e:
    print(f"Error during install/upgrade: {e}")
