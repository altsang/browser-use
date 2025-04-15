"""
Test script to verify the enhanced React event simulation capabilities.
This script demonstrates the new JavaScript capabilities added to browser-use.
"""
import asyncio
import logging
import os
from pathlib import Path

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from browser_use.utils.react import detect_react_app, get_react_component_props, find_react_components

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_react_event_simulation():
    """Test the enhanced React event simulation capabilities."""
    tmp_dir = Path("/tmp/react_test")
    tmp_dir.mkdir(exist_ok=True)
    
    config = BrowserConfig(
        headless=False,
        slow_mo=50,
    )
    
    context_config = BrowserContextConfig(
        ignore_https_errors=True,
        trace_path=None
    )
    config.new_context_config = context_config
    
    cdp_port = None
    try:
        import subprocess
        result = subprocess.run(
            "ps aux | grep -o '\\-\\-remote-debugging-port=[0-9]\\+' | awk -F= '{print $2}'",
            shell=True, capture_output=True, text=True
        )
        ports = result.stdout.strip().split('\n')
        if ports and ports[0]:
            from collections import Counter
            port_counter = Counter(ports)
            cdp_port = port_counter.most_common(1)[0][0]
            logger.info(f"Detected CDP port: {cdp_port}")
    except Exception as e:
        logger.warning(f"Could not detect CDP port: {e}")
    
    if cdp_port:
        config.cdp_url = f"http://localhost:{cdp_port}"
        
    browser = Browser(config)
    
    try:
        async with await browser.new_context(config=context_config) as context:
            url = "https://codepen.io/gaearon/pen/gWWZgR?editors=0010"
            await context.navigate_to(url)
            logger.info(f"Navigated to {url}")
            
            await context.wait_for_javascript_load()
            
            page = await context.get_current_page()
            
            logger.info("Using main page for React testing")
                
            react_info = await detect_react_app(page)
            
            if react_info.get("isReactApp"):
                logger.info("React application detected!")
                logger.info(f"React info: {react_info}")
            else:
                logger.warning("Not a React application or React not detected")
            
            components = await find_react_components(page)
            logger.info(f"Found {len(components)} React components")
            
            state = await context.get_state(cache_clickable_elements_hashes=True)
            
            button_element = None
            
            elements = await context.execute_javascript(
                "(selector) => Array.from(document.querySelectorAll(selector)).map(el => ({" +
                "    tagName: el.tagName," +
                "    text: el.textContent," +
                "    id: el.id," +
                "    className: el.className" +
                "}))",
                "button"
            )
            
            logger.info(f"Found {len(elements)} button elements")
            
            if elements:
                logger.info(f"First button: {elements[0]}")
                
                button_selector = ".square"
                logger.info(f"Using selector: {button_selector}")
            else:
                logger.error("Could not find any button elements")
                return
                
            button_element_handle = await page.query_selector(button_selector)
            
            if not button_element_handle:
                logger.error(f"Could not find button element with selector {button_selector}")
                return
                
            button_attributes = await context.execute_javascript(
                "(selector) => {" +
                "    const el = document.querySelector(selector);" +
                "    if (!el) return null;" +
                "    const attrs = {};" +
                "    for (const attr of el.attributes) {" +
                "        attrs[attr.name] = attr.value;" +
                "    }" +
                "    return {" +
                "        tagName: el.tagName," +
                "        attributes: attrs," +
                "        textContent: el.textContent" +
                "    };" +
                "}",
                button_selector
            )
            
            logger.info(f"Button attributes: {button_attributes}")
            
            event_data = {"bubbles": True}
            
            await button_element_handle.click()
            logger.info("Clicked button directly")
            
            await asyncio.sleep(2)
            
            screenshot_path = tmp_dir / "react_event_test.png"
            screenshot_b64 = await context.take_screenshot(full_page=True)
            
            import base64
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            button_element = None
            for element in state.element_tree:
                if element.tag_name == 'button':
                    button_element = element
                    logger.info(f"Found button element: {element.tag_name}")
                    break
                    
            if button_element:
                result = await context.simulate_react_event(button_element, "click")
                logger.info(f"Button click result: {result}")
                await asyncio.sleep(2)
                
                screenshot_path = tmp_dir / "react_event_test_after_click.png"
                screenshot_b64 = await context.take_screenshot(full_page=True)
                
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(screenshot_b64))
                logger.info(f"Saved screenshot to {screenshot_path}")
            
            await asyncio.sleep(3)
            
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_react_event_simulation())
