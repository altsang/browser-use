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
            logger.info("Creating a simple React app for testing")
            
            await context.navigate_to("about:blank")
            
            page = await context.get_current_page()
            
            await context.execute_javascript("""
                () => {
                    // Add React and ReactDOM scripts
                    const reactScript = document.createElement('script');
                    reactScript.src = 'https://unpkg.com/react@18/umd/react.development.js';
                    document.head.appendChild(reactScript);
                    
                    const reactDomScript = document.createElement('script');
                    reactDomScript.src = 'https://unpkg.com/react-dom@18/umd/react-dom.development.js';
                    document.head.appendChild(reactDomScript);
                    
                    // Add a container for the React app
                    const container = document.createElement('div');
                    container.id = 'root';
                    document.body.appendChild(container);
                    
                    // Add some basic styling
                    const style = document.createElement('style');
                    style.textContent = `
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        button { padding: 10px 15px; margin: 10px; cursor: pointer; }
                        .counter { font-size: 24px; margin: 20px 0; }
                        .clicked { background-color: #4CAF50; color: white; }
                    `;
                    document.head.appendChild(style);
                }
            """)
            
            logger.info("Waiting for React scripts to load")
            await asyncio.sleep(2)
            
            await context.execute_javascript("""
                () => {
                    // Wait for React and ReactDOM to be loaded
                    if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {
                        console.error('React or ReactDOM not loaded yet');
                        return;
                    }
                    
                    // Create a simple Counter component
                    const Counter = () => {
                        const [count, setCount] = React.useState(0);
                        const [buttonClicked, setButtonClicked] = React.useState(false);
                        
                        const handleClick = () => {
                            setCount(count + 1);
                            setButtonClicked(true);
                            setTimeout(() => setButtonClicked(false), 500);
                        };
                        
                        return React.createElement(
                            'div',
                            null,
                            React.createElement('h1', null, 'React Counter Example'),
                            React.createElement(
                                'div',
                                { className: 'counter' },
                                'Count: ',
                                count
                            ),
                            React.createElement(
                                'button',
                                { 
                                    onClick: handleClick,
                                    className: buttonClicked ? 'clicked' : '',
                                    id: 'increment-button'
                                },
                                'Increment'
                            )
                        );
                    };
                    
                    // Render the Counter component using older React API
                    ReactDOM.render(
                        React.createElement(Counter),
                        document.getElementById('root')
                    );
                }
            """)
            
            logger.info("Waiting for React app to render")
            await asyncio.sleep(2)
            
            react_info = await detect_react_app(page)
            
            if react_info.get("isReactApp"):
                logger.info("React application detected!")
                logger.info(f"React info: {react_info}")
            else:
                logger.warning("Not a React application or React not detected")
            
            # Find React components
            components = await find_react_components(page)
            logger.info(f"Found {len(components)} React components")
            
            screenshot_path = tmp_dir / "react_event_test_before.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            import base64
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            button_selector = "#increment-button"
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
            
            count_before = await context.execute_javascript(
                "() => document.querySelector('.counter').textContent"
            )
            logger.info(f"Count before click: {count_before}")
            
            await button_element_handle.click()
            logger.info("Clicked button directly with Playwright")
            
            await asyncio.sleep(1)
            
            count_after_playwright = await context.execute_javascript(
                "() => document.querySelector('.counter').textContent"
            )
            logger.info(f"Count after Playwright click: {count_after_playwright}")
            
            screenshot_path = tmp_dir / "react_event_test_after_playwright.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            logger.info("Using JavaScript to simulate a React event")
            
            result = await context.execute_javascript("""
                () => {
                    const button = document.getElementById('increment-button');
                    if (!button) return false;
                    
                    // Create a synthetic React event
                    const event = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    
                    // Dispatch the event
                    button.dispatchEvent(event);
                    return true;
                }
            """)
            logger.info(f"React event simulation result: {result}")
            
            await asyncio.sleep(1)
            
            count_after_react = await context.execute_javascript(
                "() => document.querySelector('.counter').textContent"
            )
            logger.info(f"Count after React event simulation: {count_after_react}")
            
            screenshot_path = tmp_dir / "react_event_test_after_react.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            logger.info("Test summary:")
            logger.info(f"  - Initial count: {count_before}")
            logger.info(f"  - Count after Playwright click: {count_after_playwright}")
            logger.info(f"  - Count after React event simulation: {count_after_react}")
            
            if "Count: 1" in count_after_playwright and "Count: 2" in count_after_react:
                logger.info("✅ Test PASSED: Both click methods successfully incremented the counter")
            else:
                logger.error("❌ Test FAILED: Counter did not increment as expected")
            
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_react_event_simulation())
