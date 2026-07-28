# Fix Purchase Order Customizations

This plan outlines the fixes to address the printing issues and manual entry constraints on Purchase Orders/RFQs.

## Proposed Changes

### custom-addons/drone_traceability/views/purchase_order_views.xml
We will update the form view to ensure the fields you need are visible and editable:
1. **Order Number**: Make the `name` field editable (`readonly="0"`) so you can manually type or override the order number.
2. **Month**: Unhide the `date_order` field (which determines the month for the PO sequence) so you can manually set the date/month of the order.

### custom-addons/drone_traceability/views/purchase_order_templates.xml
1. **Address & GST Not Printing**: We will replace the manually-coded address fields with Odoo's standard `widget="contact"` layout. This guarantees that if a vendor inherits its address and GST from a parent company (a very common reason for it not printing), it will correctly display on the PDF. We will do this for both PO and RFQ templates.
2. **HSN, Order Number, and Quotation Data Not Printing**: 
    - The RFQ (Request for Quotation) template is currently missing these fields entirely, which is likely why they appear to be "not printing" if you click "Print RFQ" before confirming. 
    - We will add the **HSN Code** column, **Order Number**, and **Quotation Ref** to the RFQ template to match the PO template exactly. 
    - We will also ensure the PO template relies on the correct contact widget.

## Open Questions

> [!WARNING]
> Regarding "Month and order number not accepting manual entry": I plan to make the `name` (Order Number) editable and unhide `date_order` (so you can select the month). Is this what you meant, or did you want me to create entirely new custom fields named "Month" and "Order Number" separate from Odoo's native ones?

## Verification Plan

### Automated Tests
- N/A

### Manual Verification
- Upgrade the `drone_traceability` module.
- Open a Purchase Order. Verify that you can edit the PO Number (`name`) and the Order Date (`date_order`).
- Print the PO and RFQ PDFs and verify that Address, GST, HSN, and Quotation Data appear correctly in both.
