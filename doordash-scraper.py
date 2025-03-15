import asyncio
from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright


async def get_scrapybara_browser():
    client = Scrapybara(api_key="scrapy-5fd9ce61-42ab-4076-a2a4-3236df1173f4")
    instance = client.start_browser()
    return instance

async def retrieve_menu_items(instance, start_url: str) -> list[dict]:
    """
    :args:
    instance: the scrapybara instance to use
    url: the initial url to navigate to

    :desc:
    this function navigates to {url}. then, it will collect the detailed
    data for each menu item in the store and return it.

    (hint: click a menu item, open dev tools -> network tab -> filter for
            "https://www.doordash.com/graphql/itemPage?operation=itemPage")

    one way to do this is to scroll through the page and click on each menu
    item.

    determine the most efficient way to collect this data.

    :returns:
    a list of menu items on the page, represented as dictionaries
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
        
        while True:
            curr_position = await page.evaluate('window.pageYOffset')
            total_height = await page.evaluate('document.documentElement.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            print(f"\nScanning at position {curr_position}/{total_height}")
            
            items = await page.query_selector_all('div[data-anchor-id="MenuItem"]')
            
            for item in items:
                try:
                    text = await item.text_content()
                    if text not in processed_texts:
                        print(f"\nFound new item: {text[:50]}...")
                        processed_texts.add(text)
                        
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
                            await asyncio.sleep(0.3)
                            
                        except Exception as e:
                            print(f"Error processing item: {e}")
                            continue
                except Exception as e:
                    print(f"Error checking item: {e}")
                    continue
            
            # If we've reached the bottom, stop scrolling
            if curr_position + viewport_height >= total_height:
                break
                
            await page.evaluate(f'window.scrollTo(0, {min(curr_position + viewport_height, total_height)})')
            await asyncio.sleep(0.3)
        
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
