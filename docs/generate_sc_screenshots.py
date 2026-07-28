import os
import time
import requests
from playwright.sync_api import sync_playwright
import urllib.parse
try:
    import fitz
except ImportError:
    fitz = None

def convert_pdf_to_img(pdf_path, img_path):
    if not fitz:
        print("PyMuPDF not installed, skipping PDF conversion.")
        return
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        pix.save(img_path)
        doc.close()
        print(f"Converted {pdf_path} to {img_path}")
    except Exception as e:
        print(f"Error converting PDF: {e}")

def run():
    img_dir = "/home/krishnashis/Office/ERP/docs/manual/images/supplychain"
    os.makedirs(img_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("Logging in...")
        page.goto("http://localhost:8069/web/login")
        page.fill("input[name='login']", "p.chandekar@wingspannglobal.com")
        page.fill("input[name='password']", "user123")
        page.locator("button[type='submit']").click()
        page.wait_for_load_state('domcontentloaded')
        time.sleep(3)

        print("Checking Inventory...")
        page.goto("http://localhost:8069/web#action=stock.stock_picking_type_action")
        time.sleep(4)
        page.screenshot(path=os.path.join(img_dir, "01_inventory_dashboard.png"))

        print("Navigating to Purchase...")
        page.goto("http://localhost:8069/web#action=purchase.purchase_rfq")
        time.sleep(4)
        
        print("Creating PO...")
        page.locator("button.o_list_button_add").filter(has_text="New").locator("visible=true").first.click()
        time.sleep(3)
        
        page.fill("div[name='partner_id'] input", "Dazzle Robotics")
        time.sleep(1)
        page.press("div[name='partner_id'] input", "Enter")
        time.sleep(1)

        page.locator("a:has-text('Add a product')").locator("visible=true").first.click()
        time.sleep(1)
        page.fill("div[name='product_id'] input", "Battery")
        time.sleep(1)
        page.press("div[name='product_id'] input", "Enter")
        time.sleep(2)
        
        save_btn = page.locator("button.o_form_button_save, button:has-text('Save')").locator("visible=true").first
        if save_btn.is_visible():
            save_btn.click()
            time.sleep(3)
        page.screenshot(path=os.path.join(img_dir, "02_po_draft.png"))

        url = page.url
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).fragment)
        po_id = qs.get('id', [None])[0]
        
        if po_id:
            print(f"PO created with ID: {po_id}")
            pdf_path = os.path.join(img_dir, "po.pdf")
            try:
                cookies = {c['name']: c['value'] for c in context.cookies()}
                res = requests.get(f"http://localhost:8069/report/pdf/purchase.report_purchaseorder/{po_id}", cookies=cookies)
                with open(pdf_path, 'wb') as f:
                    f.write(res.content)
                convert_pdf_to_img(pdf_path, os.path.join(img_dir, "03_po_document.png"))
                time.sleep(1)
            except Exception as e:
                print("Could not download PO PDF:", e)

            print("Confirming PO...")
            confirm_btn = page.locator("button[name='button_confirm']").locator("visible=true").first
            if confirm_btn.is_visible():
                confirm_btn.click()
                time.sleep(4)
                page.screenshot(path=os.path.join(img_dir, "04_po_confirmed.png"))

            print("Receiving Products...")
            receive_btn = page.locator("button[name='action_view_picking']").locator("visible=true").first
            if receive_btn.is_visible():
                receive_btn.click()
                time.sleep(4)
                
                val_btn = page.locator("button[name='button_validate']").locator("visible=true").first
                if val_btn.is_visible():
                    val_btn.click()
                    time.sleep(2)
                    apply_btn = page.locator("button:has-text('Apply')").locator("visible=true").first
                    if apply_btn.is_visible():
                        apply_btn.click()
                        time.sleep(3)
                page.screenshot(path=os.path.join(img_dir, "05_receipt_validated.png"))

            print("Creating Vendor Bill...")
            page.goto(url)
            time.sleep(3)
            create_bill_btn = page.locator("button[name='action_create_invoice']").locator("visible=true").first
            if create_bill_btn.is_visible():
                create_bill_btn.click()
                time.sleep(4)
                
                try:
                    page.wait_for_url(lambda url: "model=account.move" in url, timeout=10000)
                except Exception:
                    pass # fallback if it doesn't change
                    
                bill_url = page.url
                print(f"Vendor bill url is {bill_url}")
                bill_id = urllib.parse.parse_qs(urllib.parse.urlparse(bill_url).fragment).get('id', [None])[0]
                
                page.fill("div[name='invoice_date'] input", "07/22/2026")
                time.sleep(1)
                page.press("div[name='invoice_date'] input", "Enter")
                time.sleep(1)

                save_btn_bill = page.locator("button.o_form_button_save, button:has-text('Save')").locator("visible=true").first
                if save_btn_bill.is_visible():
                    save_btn_bill.click()
                    time.sleep(3)
                page.screenshot(path=os.path.join(img_dir, "06_vendor_bill_draft.png"))

                bill_confirm = page.locator("button[name='action_post']").locator("visible=true").first
                if bill_confirm.is_visible():
                    bill_confirm.click()
                    time.sleep(4)
                    page.screenshot(path=os.path.join(img_dir, "07_vendor_bill_confirmed.png"))
                
                if bill_id:
                    print(f"Bill created with ID: {bill_id}")
                    pdf_path_bill = os.path.join(img_dir, "bill.pdf")
                    try:
                        cookies = {c['name']: c['value'] for c in context.cookies()}
                        res = requests.get(f"http://localhost:8069/report/pdf/account.report_invoice_with_payments/{bill_id}", cookies=cookies)
                        with open(pdf_path_bill, 'wb') as f:
                            f.write(res.content)
                        convert_pdf_to_img(pdf_path_bill, os.path.join(img_dir, "08_bill_document.png"))
                    except Exception as e:
                        print("Could not download Bill PDF:", e)

        print("Done capturing screenshots.")
        browser.close()

if __name__ == "__main__":
    run()
