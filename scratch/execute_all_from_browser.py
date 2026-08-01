import asyncio
import os
import sys
from playwright.async_api import async_playwright

DATASETS = [
    ("travel_v1", 25),
    ("travel_tool_calls", 20),
    ("travel_long_context", 20),
    ("travel_regression", 15),
    ("travel_missing_context", 15),
    ("travel_edge_cases", 20),
    ("travel_safety", 20),
    ("travel_adversarial", 15),
    ("travel_multilingual", 15),
    ("travel_provider_benchmark", 15)
]

SCREENSHOT_DIR = r"C:\Users\JACOB\.gemini\antigravity-ide\brain\12868e6a-f9b8-465a-8cab-07558e0263bd"

async def main():
    print("=== EvalForge Browser-Driven E2E Acceptance Test ===")
    
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)
        
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        # Navigate to Dashboard
        print("Navigating to http://localhost:3000 ...")
        await page.goto("http://localhost:3000")
        await page.wait_for_timeout(3000)
        
        # Verify connection
        status_el = page.locator("text=Connected")
        if await status_el.count() > 0:
            print("Backend connected successfully.")
        else:
            print("WARNING: Backend connection status not found.")
            
        summary_results = []
        
        for ds_id, expected_cases in DATASETS:
            print(f"\n--- Testing Dataset: {ds_id} (Expected cases: {expected_cases}) ---")
            
            # 1. Select Dataset in dropdown
            await page.click("select:has-text('Select Dataset ID'), select:near(label:text-is('Select Dataset ID'))")
            await page.select_option("select:has-text('Select Dataset ID'), select:near(label:text-is('Select Dataset ID'))", label=ds_id)
            await page.wait_for_timeout(500)
            
            # 2. Select Version
            await page.click("select:has-text('Select Version'), select:near(label:text-is('Select Version'))")
            await page.select_option("select:has-text('Select Version'), select:near(label:text-is('Select Version'))", label="1.0.0")
            await page.wait_for_timeout(500)
            
            # 3. Launch Execution
            launch_btn = page.locator("button:has-text('Launch Execution Job'), button:has-text('Execute')")
            await launch_btn.click()
            print("Clicked Launch button.")
            await page.wait_for_timeout(4000) # Wait for execution completion (very fast in mock mode)
            
            # 4. Navigate to Run History
            await page.click("button:has-text('Run History'), div:has-text('Run History')")
            await page.wait_for_timeout(1000)
            
            # Sync/Refresh if button available
            sync_btn = page.locator("button:has-text('Sync'), button:has-text('Refresh')")
            if await sync_btn.count() > 0:
                await sync_btn.click()
                await page.wait_for_timeout(1000)
                
            # 5. Verify run creation
            new_run_row = page.locator(f"tr:has-text('{ds_id}')").first
            if await new_run_row.count() > 0:
                print(f"Run created for {ds_id}.")
                
                # Check passed/failed count in row text
                row_text = await new_run_row.inner_text()
                print(f"Row stats: {row_text.strip()}")
                
                # Inspect trace
                inspect_btn = new_run_row.locator("button:has-text('Inspect')")
                if await inspect_btn.count() > 0:
                    await inspect_btn.click()
                    await page.wait_for_timeout(1500)
                    
                    # Take screenshot of Trajectory Inspector
                    ss_path = os.path.join(SCREENSHOT_DIR, f"browser_inspect_{ds_id}.png")
                    await page.screenshot(path=ss_path)
                    print(f"Saved screenshot: browser_inspect_{ds_id}.png")
                    
                    # Close drawer/inspector
                    close_btn = page.locator("button:has-text('Close'), button:has-text('X')")
                    if await close_btn.count() > 0:
                        await close_btn.first.click()
                        await page.wait_for_timeout(500)
            else:
                print(f"ERROR: No run row found for dataset {ds_id}!")
                
            # Go back to Overview for next iteration
            await page.click("button:has-text('Overview'), div:has-text('Overview')")
            await page.wait_for_timeout(1000)
            
        await browser.close()
        print("\n=== Browser certification runs complete! ===")

if __name__ == "__main__":
    asyncio.run(main())
