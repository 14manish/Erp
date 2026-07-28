import os
import time
from playwright.sync_api import sync_playwright

def generate_screenshots():
    img_dir = "/home/krishnashis/Office/ERP/docs/manual/images"
    os.makedirs(img_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("Navigating to Odoo login...")
        page.goto("http://localhost:8069/web/login")
        
        print("Logging in...")
        page.fill("input[name='login']", "test@example.com")
        page.fill("input[name='password']", "Admin@123")
        page.click("button[type='submit']")
        
        time.sleep(8)
        print("Capturing Dashboard...")
        page.screenshot(path=os.path.join(img_dir, "dashboard.png"))
        
        print("Navigating to Inventory App...")
        page.goto("http://localhost:8069/web#action=stock.action_inventory_form")
        time.sleep(6)
        print("Capturing Inventory Overview...")
        page.screenshot(path=os.path.join(img_dir, "inventory_overview.png"))
        
        print("Navigating to Internal Transfers...")
        page.goto("http://localhost:8069/web#action=stock.action_picking_tree_all")
        time.sleep(6)
        print("Capturing Transfers List...")
        page.screenshot(path=os.path.join(img_dir, "internal_transfers_list.png"))
        
        # Open first transfer
        first_transfer = page.locator(".o_data_row").first
        if first_transfer.count() > 0:
            first_transfer.click()
            time.sleep(5)
            print("Capturing Issue Note Form...")
            page.screenshot(path=os.path.join(img_dir, "issue_note.png"))
        else:
            print("No internal transfers found.")
            # Fallback screenshot
            page.screenshot(path=os.path.join(img_dir, "issue_note.png"))

        browser.close()
        print("Screenshots captured successfully.")

if __name__ == "__main__":
    generate_screenshots()
