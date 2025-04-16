"""
Test script to verify the enhanced iframe support for Naver Maps.
This script demonstrates the new iframe traversal capabilities added to browser-use.
"""
import asyncio
import logging
import os
from pathlib import Path

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from browser_use.utils.naver_maps import (
    NAVER_MAPS_SELECTORS,
    is_naver_maps_url,
    get_photo_selector,
    get_navigation_selector,
    wait_times,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_naver_maps_iframe_support():
    """Test the enhanced iframe support with Naver Maps."""
    tmp_dir = Path("/tmp/naver_maps_test")
    tmp_dir.mkdir(exist_ok=True)
    
    config = BrowserConfig(
        headless=False,
        slow_mo=50,
        context_config=BrowserContextConfig(
            ignore_https_errors=True,
            locale="ko-KR",  # Use Korean locale for Naver
        )
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
    
    browser_kwargs = {}
    if cdp_port:
        browser_kwargs["cdp_port"] = int(cdp_port)
        
    browser = Browser(config, **browser_kwargs)
    
    try:
        async with await browser.new_context() as context:
            url = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"
            await context.navigate_to(url)
            logger.info(f"Navigated to {url}")
            
            await asyncio.sleep(wait_times()['initial_load'] / 1000)
            
            frames = await context.get_nested_frames()
            logger.info(f"Found {len(frames)} top-level frames")
            for frame in frames:
                logger.info(f"Frame: {frame['url']} with {len(frame.get('child_frames', []))} child frames")
            
            photos_frame = await context.find_naver_maps_photos_frame()
            if photos_frame:
                logger.info(f"Found photos frame: {photos_frame['url']}")
                logger.info(f"Frame path: {photos_frame.get('found_path')}")
                
                photos_button = await context.find_element_by_korean_text(
                    NAVER_MAPS_SELECTORS['photos_button'], 
                    photos_frame.get('found_path')
                )
                
                if photos_button:
                    logger.info("Found 'Photos' button!")
                    action_result = await context.perform_action("click_element", {
                        "element": photos_button,
                        "frame_path": photos_frame.get('found_path')
                    })
                    logger.info(f"Clicked on 'Photos' button: {action_result.success}")
                    
                    await asyncio.sleep(wait_times()['frame_load'] / 1000)
                    
                    interior_button = await context.find_element_by_korean_text(
                        NAVER_MAPS_SELECTORS['interior_category'],
                        photos_frame.get('found_path')
                    )
                    
                    if interior_button:
                        logger.info("Found 'Interior' category button!")
                        action_result = await context.perform_action("click_element", {
                            "element": interior_button,
                            "frame_path": photos_frame.get('found_path')
                        })
                        logger.info(f"Clicked on 'Interior' category button: {action_result.success}")
                        
                        await asyncio.sleep(wait_times()['category_selection'] / 1000)
                        
                        screenshot_path = tmp_dir / "naver_maps_interior_photos.png"
                        await context.take_screenshot(path=str(screenshot_path))
                        logger.info(f"Saved screenshot to {screenshot_path}")
                    else:
                        logger.warning("Could not find 'Interior' category button")
                else:
                    logger.warning("Could not find 'Photos' button")
            else:
                logger.warning("Could not find photos frame")
                
            await asyncio.sleep(10)
            
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_naver_maps_iframe_support())
