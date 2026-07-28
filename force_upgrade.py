import xmlrpc.client
import sys

url = 'http://localhost:8069'
db = 'Wingspann'
username = 'test@example.com'
password = 'Admin@123'

try:
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # Get module ID
    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read',
        [[['name', '=', 'drone_traceability']]],
        {'fields': ['id']}
    )
    mod_id = modules[0]['id']
    
    # Set to upgrade
    models.execute_kw(db, uid, password, 'ir.module.module', 'button_upgrade', [[mod_id]])
    
    # Create wizard
    wizard_id = models.execute_kw(db, uid, password, 'base.module.upgrade', 'create', [{}])
    
    # Call upgrade
    print("Executing upgrade wizard...")
    models.execute_kw(db, uid, password, 'base.module.upgrade', 'upgrade_module', [[wizard_id]])
    print("Upgrade wizard executed successfully!")
    
except Exception as e:
    print("Error:", e)
