import asyncio
from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright


async def get_scrapybara_browser():
    client = Scrapybara(api_key="enter your API key here")
    instance = client.start_browser()
    return instance

async def retrieve_menu_items(instance, start_url: str) -> list[dict]:
    """
    :args:
    instance: the scrapybara instance to use
    url: the initial url to navigate to

    :desc:
    this function navigates to the url and collects detailed data for all menu items found.

    :returns:
    a list of all menu items on the page, represented as dictionaries
    """
    menu_items = []
    processed_texts = set()  
    cdp_url = instance.get_cdp_url().cdp_url
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()
        
        print("Navigating to URL...")
        response = await page.goto(start_url, wait_until='domcontentloaded')
        print(f"Page response status: {response.status}")

        print("Waiting for page to fully load...")
        await asyncio.sleep(5)

        print("Setting delivery address...")
        try:
            address_input = await page.wait_for_selector('input[data-testid="AddressAutocompleteField"]', timeout=5000)
            if address_input:
                await address_input.fill('100 1st St, San Francisco, CA 94105, United States')
                await asyncio.sleep(1) 
                await page.keyboard.press('Enter')
                await asyncio.sleep(2) 
                print("Successfully set delivery address")
        except Exception as e:
            print(f"Warning: Could not set address: {e}")

        print("Scanning and processing menu items...")
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while scroll_attempts < max_scroll_attempts:
            curr_position = await page.evaluate('window.pageYOffset')
            total_height = await page.evaluate('document.documentElement.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            print(f"\nScan attempt {scroll_attempts + 1}: Position {curr_position}/{total_height}")
            
            items = await page.query_selector_all('div[data-anchor-id="MenuItem"]')
            found_new = False
            
            for item in items:
                try:
                    text = await item.text_content()
                    if text not in processed_texts:
                        print(f"\nFound new item: {text[:50]}...")
                        processed_texts.add(text)
                        found_new = True
                        
                        try:
                            async with page.expect_response(
                                lambda response: "graphql/itemPage?operation=itemPage" in response.url,
                                timeout=3000
                            ) as response_info:
                                await item.click()
                                data = await (await response_info.value).json()
                            
                            menu_items.append({
                                "menu_item_index": len(menu_items),
                                "text": text,
                                "data": data
                            })
                            print(f"Successfully processed item {len(menu_items)}")
                            await page.keyboard.press("Escape")
                            
                        except Exception as e:
                            print(f"Error processing item: {e}")
                            continue
                except Exception as e:
                    print(f"Error checking item: {e}")
                    continue
            
            if not found_new:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                
            if curr_position + viewport_height >= total_height and scroll_attempts >= 3:
                break
                
            new_position = min(curr_position + viewport_height, total_height)
            await page.evaluate(f'window.scrollTo(0, {new_position})')
            await asyncio.sleep(0.2)
        
        print(f"\nProcessed {len(menu_items)} menu items")
        await browser.close()
        return menu_items

async def main():
    instance = await get_scrapybara_browser()
    try:
        items = await retrieve_menu_items(
            instance,
            "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false",
        )
        print("Saving menu items to menu_items.json")
        import json
        with open('menu_items.json', 'w') as f:
            json.dump(items, f, indent=2)
        print("Successfully saved menu items to menu_items.json")
    finally:
        instance.stop()

if __name__ == "__main__":
    asyncio.run(main())
