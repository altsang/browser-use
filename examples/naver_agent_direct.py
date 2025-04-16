"""
Agent-based test script for Naver Maps restaurant photos using direct browser control.

This script follows the simple.py structure but uses direct browser control instead of Agent.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

RESTAURANT_URL = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"

OUTPUT_DIR = Path("/tmp/naver_agent_direct")
OUTPUT_DIR.mkdir(exist_ok=True)

async def main():
    """Main function to run the browser automation."""
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
    
    browser_config = BrowserConfig(
        headless=True,
        cdp_url=f"http://localhost:{cdp_port}" if cdp_port else None
    )
    browser = Browser(config=browser_config)
    
    try:
        context_config = BrowserContextConfig(
            allowed_domains=None  # Allow all domains
        )
        context = await browser.new_context(config=context_config)
        
        logger.info(f"Step 1: Navigating to {RESTAURANT_URL}")
        await context.navigate_to(RESTAURANT_URL)
        await context.take_screenshot(path=str(OUTPUT_DIR / "01_restaurant_page.png"))
        await asyncio.sleep(3)
        
        logger.info("Step 2: Finding and clicking on photos section")
        photos_clicked = await context.execute_javascript("""
            (function() {
                const elements = Array.from(document.querySelectorAll('*'));
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
                return false;
            })()
        """)
        logger.info(f"Clicked on photos button: {photos_clicked}")
        await context.take_screenshot(path=str(OUTPUT_DIR / "02_photos_section.png"))
        await asyncio.sleep(3)
        
        logger.info("Step 3: Clicking on the first photo in the grid")
        first_photo_clicked = await context.execute_javascript("""
            (function() {
                const images = Array.from(document.querySelectorAll('img'));
                const photoImg = images.find(img => 
                    img.offsetWidth > 50 && 
                    img.offsetHeight > 50 && 
                    (img.src.includes('pstatic.net') || img.src.includes('static.naver.net'))
                );
                
                if (photoImg) {
                    photoImg.click();
                    return true;
                }
                return false;
            })()
        """)
        logger.info(f"Clicked on first photo: {first_photo_clicked}")
        await context.take_screenshot(path=str(OUTPUT_DIR / "03_first_photo.png"))
        await asyncio.sleep(3)
        
        logger.info("Step 4: Looking for category options")
        category_clicked = await context.execute_javascript("""
            (function() {
                const buttons = Array.from(document.querySelectorAll('button, [role="tab"], [role="button"], .tab, li'));
                for (const btn of buttons) {
                    if (btn.textContent && 
                        (btn.textContent.includes('내부') || btn.textContent.includes('외부')) && 
                        btn.offsetWidth > 0 && 
                        btn.offsetHeight > 0
                    ) {
                        console.log('Found category button:', btn.textContent);
                        btn.click();
                        return true;
                    }
                }
                return false;
            })()
        """)
        logger.info(f"Clicked on category button: {category_clicked}")
        await context.take_screenshot(path=str(OUTPUT_DIR / "04_category_view.png"))
        
        await context.take_screenshot(path=str(OUTPUT_DIR / "05_final_state.png"))
        
        logger.info(f"Test completed successfully. Screenshots saved to {OUTPUT_DIR}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        if 'context' in locals():
            await context.take_screenshot(path=str(OUTPUT_DIR / "error.png"))
    finally:
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
