"""
Simple test script to verify the enhanced JavaScript execution capabilities.
This script demonstrates the core JavaScript capabilities added to browser-use.
"""
import asyncio
import logging
import os
from pathlib import Path

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_javascript_execution():
    """Test the enhanced JavaScript execution capabilities."""
    tmp_dir = Path("/tmp/js_test")
    tmp_dir.mkdir(exist_ok=True)
    
    config = BrowserConfig(
        headless=False,
    )
    
    context_config = BrowserContextConfig(
        ignore_https_errors=True,
        trace_path=None
    )
    
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
            url = "https://example.com"
            await context.navigate_to(url)
            logger.info(f"Navigated to {url}")
            
            result = await context.execute_javascript("(a, b) => a + b", 5, 7)
            
            logger.info(f"JavaScript execution result (5 + 7): {result}")
            assert result == 12, "JavaScript execution failed"
            
            await context.wait_for_function("""
                () => document.readyState === 'complete'
            """, 5000)
            logger.info("wait_for_function successful")
            
            load_result = await context.wait_for_javascript_load(5000)
            logger.info(f"wait_for_javascript_load result: {load_result}")
            
            await context.execute_javascript("""
                () => {
                    const div = document.createElement('div');
                    div.id = 'test-div';
                    div.textContent = 'Created by JavaScript';
                    div.style.padding = '20px';
                    div.style.backgroundColor = 'lightblue';
                    div.style.margin = '20px';
                    div.style.borderRadius = '5px';
                    document.body.appendChild(div);
                }
            """)
            
            element_exists = await context.execute_javascript("""
                () => document.getElementById('test-div') !== null
            """)
            
            logger.info(f"Element created successfully: {element_exists}")
            assert element_exists, "Failed to create element with JavaScript"
            
            screenshot_path = tmp_dir / "js_execution_test.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            import base64
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            await context.execute_javascript("""
                () => {
                    const div = document.getElementById('test-div');
                    if (div) {
                        // Add a button
                        const button = document.createElement('button');
                        button.textContent = 'Click Me';
                        button.id = 'test-button';
                        button.style.padding = '10px';
                        button.style.margin = '10px';
                        button.style.backgroundColor = '#4CAF50';
                        button.style.color = 'white';
                        button.style.border = 'none';
                        button.style.borderRadius = '4px';
                        button.style.cursor = 'pointer';
                        
                        // Add click event listener
                        button.addEventListener('click', function() {
                            const result = document.createElement('p');
                            result.textContent = 'Button clicked at ' + new Date().toLocaleTimeString();
                            result.id = 'click-result';
                            div.appendChild(result);
                        });
                        
                        div.appendChild(button);
                    }
                }
            """)
            
            button_exists = await context.execute_javascript("""
                () => document.getElementById('test-button') !== null
            """)
            
            logger.info(f"Button created successfully: {button_exists}")
            assert button_exists, "Failed to create button with JavaScript"
            
            await context.execute_javascript("""
                () => {
                    const button = document.getElementById('test-button');
                    if (button) {
                        button.click();
                    }
                }
            """)
            
            click_result = await context.execute_javascript("""
                () => {
                    const result = document.getElementById('click-result');
                    return result ? result.textContent : null;
                }
            """)
            
            logger.info(f"Button click result: {click_result}")
            assert click_result and "Button clicked at" in click_result, "Button click failed"
            
            screenshot_path = tmp_dir / "js_execution_test_after_click.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            logger.info("All JavaScript execution tests passed successfully!")
            
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_javascript_execution())
