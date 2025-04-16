"""
Direct browser test script for Naver Maps restaurant photos without using Agent.

This script demonstrates how to use the browser-use library directly to:
1. Navigate to a Naver Maps restaurant page
2. Find and click on photos
3. Click on the first photo
4. Navigate to photo categories
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext

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
    
    output_dir = Path("/tmp/naver_direct_test")
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
        
        await asyncio.sleep(5)
        
        photos_js = """
        (function() {
            // Try to find in all frames
            function findInFrames(win, depth = 0) {
                if (depth > 5) return null; // Limit recursion depth
                
                try {
                    // Try in current window/frame
                    const elements = Array.from(win.document.querySelectorAll('*'));
                    const photoButton = elements.find(el => 
                        el.textContent && 
                        el.textContent.includes('사진') && 
                        el.offsetWidth > 0 && 
                        el.offsetHeight > 0
                    );
                    
                    if (photoButton) {
                        photoButton.click();
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
        clicked = await context.execute_javascript(photos_js)
        logger.info(f"Clicked on photos button: {clicked}")
        
        await asyncio.sleep(3)
        await context.take_screenshot(path=str(output_dir / "02_after_photos_click.png"))
        
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
        logger.info(f"Clicked on first photo: {clicked}")
        
        await asyncio.sleep(5)
        await context.take_screenshot(path=str(output_dir / "03_after_photo_click.png"))
        
        category_js = """
        (function() {
            // Try to find in all frames
            function findInFrames(win, depth = 0) {
                if (depth > 5) return null; // Limit recursion depth
                
                try {
                    // Try in current window/frame
                    // First try buttons or tabs that might contain category text
                    const buttons = Array.from(win.document.querySelectorAll('button, [role="tab"], [role="button"], .tab, li'));
                    for (const btn of buttons) {
                        if (btn.textContent && 
                            (btn.textContent.includes('내부') || btn.textContent.includes('외부')) && 
                            btn.offsetWidth > 0 && 
                            btn.offsetHeight > 0) {
                            console.log("Found category button:", btn.textContent);
                            btn.click();
                            return true;
                        }
                    }
                    
                    // If no buttons found, try any element with the text
                    const elements = Array.from(win.document.querySelectorAll('*'));
                    const categoryElement = elements.find(el => 
                        el.textContent && 
                        (el.textContent.includes('내부') || el.textContent.includes('외부')) && 
                        el.textContent.length < 10 && // Likely just the category text
                        el.offsetWidth > 0 && 
                        el.offsetHeight > 0
                    );
                    
                    if (categoryElement) {
                        console.log("Found category element:", categoryElement.textContent);
                        categoryElement.click();
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
        clicked = await context.execute_javascript(category_js)
        logger.info(f"Clicked on category button: {clicked}")
        
        await asyncio.sleep(3)
        await context.take_screenshot(path=str(output_dir / "04_final_state.png"))
        
        logger.info(f"Test completed successfully. Screenshots saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        await context.take_screenshot(path=str(output_dir / "error.png"))
        raise
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
