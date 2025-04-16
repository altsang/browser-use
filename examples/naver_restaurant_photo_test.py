"""
Direct interface manipulation test script for Naver Maps restaurant photos.

This script demonstrates how to:
1. Navigate to a Naver Maps restaurant page
2. Find and click on photos
3. Verify the category frame is visible
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext
from browser_use.utils.naver_maps import NAVER_MAPS_SELECTORS, wait_times

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
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
    
    output_dir = Path("/tmp/naver_test")
    output_dir.mkdir(exist_ok=True)
    
    browser_config = BrowserConfig(
        headless=False,
        cdp_url=f"http://localhost:{cdp_port}" if cdp_port else None
    )
    browser = Browser(config=browser_config)
    
    try:
        context = BrowserContext(browser=browser)
        
        restaurant_url = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"
        await context.navigate_to(restaurant_url)
        logger.info(f"Navigated to {restaurant_url}")
        
        await context.take_screenshot(path=str(output_dir / "01_initial_page.png"))
        
        await asyncio.sleep(wait_times()['initial_load'] / 1000)
        
        photos_text = NAVER_MAPS_SELECTORS['photos_button']
        logger.info(f"Looking for photos button with text: {photos_text}")
        
        await context.take_screenshot(path=str(output_dir / "02_before_photos_click.png"))
        
        photos_js = f"""
        (function() {{
            // Try to find in all frames
            function findInFrames(win, depth = 0) {{
                if (depth > 5) return null; // Limit recursion depth
                
                try {{
                    // Try in current window/frame
                    const elements = Array.from(win.document.querySelectorAll('*'));
                    const photoButton = elements.find(el => 
                        el.textContent && 
                        el.textContent.includes('{photos_text}') && 
                        el.offsetWidth > 0 && 
                        el.offsetHeight > 0
                    );
                    
                    if (photoButton) {{
                        photoButton.click();
                        return true;
                    }}
                    
                    // Try in child frames
                    for (let i = 0; i < win.frames.length; i++) {{
                        try {{
                            const result = findInFrames(win.frames[i], depth + 1);
                            if (result) return result;
                        }} catch (e) {{
                            // Cross-origin frame, skip
                            console.log("Cross-origin frame, skipping");
                        }}
                    }}
                }} catch (e) {{
                    console.log("Error in frame: " + e.message);
                }}
                
                return false;
            }}
            
            return findInFrames(window);
        }})();
        """
        clicked = await context.execute_javascript(photos_js)
        logger.info(f"Clicked on photos button using JavaScript with iframe traversal: {clicked}")
        
        await asyncio.sleep(wait_times()['photos_tab_click'] / 1000)
        
        await context.take_screenshot(path=str(output_dir / "03_after_photos_click.png"))
        
        logger.info("Skipping interior category selection - proceeding directly to photo selection")
        
        await asyncio.sleep(wait_times()['category_selection'] / 1000)
        
        await context.take_screenshot(path=str(output_dir / "04_after_category_click.png"))
        
        logger.info("Looking for first photo in grid")
        
        photo_js = """
        (function() {
            // Try to find in all frames
            function findInFrames(win, depth = 0) {
                if (depth > 5) return null; // Limit recursion depth
                
                try {
                    // Try in current window/frame
                    const images = Array.from(win.document.querySelectorAll('img'));
                    const photoImg = images.find(img => 
                        img.offsetWidth > 50 && 
                        img.offsetHeight > 50 && 
                        (img.src.includes('pstatic.net') || img.src.includes('static.naver.net'))
                    );
                    
                    if (photoImg) {
                        photoImg.click();
                        return true;
                    }
                    
                    // Try in child frames
                    for (let i = 0; i < win.frames.length; i++) {
                        try {
                            const result = findInFrames(win.frames[i], depth + 1);
                            if (result) return result;
                        } catch (e) {
                            // Cross-origin frame, skip
                            console.log("Cross-origin frame, skipping");
                        }
                    }
                } catch (e) {
                    console.log("Error in frame: " + e.message);
                }
                
                return false;
            }
            
            return findInFrames(window);
        })();
        """
        clicked = await context.execute_javascript(photo_js)
        logger.info(f"Clicked on first photo using JavaScript with iframe traversal: {clicked}")
        
        await asyncio.sleep(wait_times()['photo_click'] / 1000)
        
        await context.take_screenshot(path=str(output_dir / "05_after_photo_click.png"))
        
        logger.info("Verifying category frame is visible")
        
        await context.take_screenshot(path=str(output_dir / "06_final_state.png"))
        
        logger.info("Test completed successfully")
        logger.info(f"Screenshots saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        await context.take_screenshot(path=str(output_dir / "error.png"))
        raise
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
