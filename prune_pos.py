pos = env['purchase.order'].search([])
print(f"Found {len(pos)} Purchase Orders.")
for po in pos:
    try:
        # Cancel related receipts
        for picking in po.picking_ids:
            if picking.state != 'cancel':
                picking.action_cancel()
        
        # Cancel related bills
        for inv in po.invoice_ids:
            if inv.state != 'cancel':
                inv.button_cancel()
        
        # Cancel and delete PO
        if po.state != 'cancel':
            po.button_cancel()
        po.unlink()
        print(f"Deleted PO: {po.name}")
    except Exception as e:
        print(f"Failed to delete {po.name}: {e}")

env.cr.commit()
print("Done.")
