"""
Test script to verify the enhanced iframe support and JavaScript execution capabilities
with Naver Maps restaurant listing.

This script:
1. Navigates to a Naver Maps restaurant page
2. Finds the photos iframe
3. Clicks on the first photo
4. Verifies the category frame is visible
"""
import asyncio
import logging
import os
import time
from pathlib import Path

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from browser_use.utils.naver_maps import (
    NAVER_MAPS_SELECTORS,
    is_naver_maps_url,
    get_photo_selector,
)

WAIT_TIMES = {
    'page_load': 5,  # seconds
    'tab_change': 2,  # seconds
    'photo_load': 3,  # seconds
    'frame_load': 2,  # seconds
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NAVER_USERNAME = os.environ.get("NAVER_USERNAME")
NAVER_PASSWORD = os.environ.get("NAVER_PASSWORD")

async def test_naver_restaurant_photos():
    """Test navigating to Naver Maps restaurant, clicking photos, and verifying category frame."""
    tmp_dir = Path("/tmp/naver_test")
    tmp_dir.mkdir(exist_ok=True)
    
    config = BrowserConfig(
        headless=False,
        slow_mo=100,  # Slow down operations for better visibility
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
            url = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"
            
            logger.info(f"Navigating to Naver Maps restaurant: {url}")
            await context.navigate_to(url)
            
            await asyncio.sleep(WAIT_TIMES["page_load"])
            
            screenshot_path = tmp_dir / "01_initial_page.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            import base64
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved initial screenshot to {screenshot_path}")
            
            logger.info("Finding all frames in the page...")
            frames = await context.get_nested_frames()
            logger.info(f"Found {len(frames)} frames")
            
            logger.info("Finding the main content frame...")
            main_frame = await context.find_frame_by_url_pattern(r"pcmap\.place\.naver\.com")
            
            if not main_frame:
                logger.error("Could not find main content frame")
                return
                
            logger.info(f"Found main content frame: {main_frame['url']}")
            
            logger.info("Looking for photos section...")
            
            try:
                photos_element = await context.find_element_by_korean_text("사진")
                
                if photos_element:
                    logger.info("Found photos tab, clicking it...")
                    element_handle = await context.get_locate_element(photos_element)
                    if element_handle:
                        await element_handle.click()
                        logger.info("Clicked on photos tab")
                        await asyncio.sleep(WAIT_TIMES["tab_change"])
                    else:
                        logger.warning("Could not locate photos tab element")
                else:
                    logger.info("Photos tab not found or already on photos section")
            except Exception as e:
                logger.warning(f"Error finding/clicking photos tab: {e}")
            
            screenshot_path = tmp_dir / "02_after_photos_tab.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot after photos tab to {screenshot_path}")
            
            logger.info("Trying to click on photos tab using JavaScript...")
            
            click_photos_result = await context.execute_javascript("""
                () => {
                    try {
                        // Look for the photos tab by Korean text "사진"
                        const elements = Array.from(document.querySelectorAll('*'));
                        const photoElements = elements.filter(el => 
                            el.textContent && 
                            el.textContent.includes('사진') && 
                            el.tagName !== 'SCRIPT' &&
                            el.tagName !== 'STYLE' &&
                            el.offsetWidth > 0 &&
                            el.offsetHeight > 0
                        );
                        
                        if (photoElements.length === 0) {
                            return { success: false, error: 'No photos tab found' };
                        }
                        
                        // Click the first visible element containing "사진"
                        photoElements[0].click();
                        return { 
                            success: true, 
                            message: 'Clicked photos tab',
                            elementInfo: {
                                tagName: photoElements[0].tagName,
                                className: photoElements[0].className,
                                id: photoElements[0].id,
                                text: photoElements[0].textContent
                            }
                        };
                    } catch (error) {
                        return { success: false, error: error.toString() };
                    }
                }
            """)
            
            logger.info(f"Click photos tab result: {click_photos_result}")
            
            await asyncio.sleep(WAIT_TIMES["tab_change"] * 2)
            
            screenshot_path = tmp_dir / "02b_after_js_photos_click.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot after JavaScript photos click to {screenshot_path}")
            
            logger.info("Finding the photos frame after clicking photos tab...")
            photos_frame = await context.find_naver_maps_photos_frame()
            
            if not photos_frame:
                logger.info("Still couldn't find photos frame, trying alternative approach...")
                
                logger.info("Looking for photo thumbnails using JavaScript...")
                
                photo_elements = await context.execute_javascript("""
                    () => {
                        try {
                            // Common selectors for photo thumbnails in Naver Maps
                            const selectors = [
                                '.place_thumb', '.thumb_area', '.thumb_item', 
                                'img[alt*="사진"]', 'img[class*="thumb"]',
                                '.photo_area img', '.list_item img'
                            ];
                            
                            let photos = [];
                            
                            // Try each selector
                            for (const selector of selectors) {
                                const elements = document.querySelectorAll(selector);
                                if (elements.length > 0) {
                                    photos = Array.from(elements);
                                    break;
                                }
                            }
                            
                            // If no photos found with selectors, try to find img elements with certain characteristics
                            if (photos.length === 0) {
                                const allImages = document.querySelectorAll('img');
                                photos = Array.from(allImages).filter(img => 
                                    img.offsetWidth > 50 && 
                                    img.offsetHeight > 50 &&
                                    !img.src.includes('icon') &&
                                    !img.src.includes('logo')
                                );
                            }
                            
                            return {
                                success: photos.length > 0,
                                count: photos.length,
                                selectors: photos.map(el => ({
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    src: el.src,
                                    width: el.offsetWidth,
                                    height: el.offsetHeight
                                }))
                            };
                        } catch (error) {
                            return { success: false, error: error.toString() };
                        }
                    }
                """)
                
                logger.info(f"Photo elements result: {photo_elements}")
                
                if photo_elements.get('success', False) and photo_elements.get('count', 0) > 0:
                    logger.info(f"Found {photo_elements.get('count')} photo elements, clicking the first one...")
                    
                    click_result = await context.execute_javascript("""
                        (photoInfo) => {
                            try {
                                // Try to find the element again
                                let element = null;
                                
                                if (photoInfo.id) {
                                    element = document.getElementById(photoInfo.id);
                                }
                                
                                if (!element && photoInfo.className) {
                                    const elements = document.getElementsByClassName(photoInfo.className);
                                    if (elements.length > 0) {
                                        element = elements[0];
                                    }
                                }
                                
                                if (!element && photoInfo.tagName) {
                                    const elements = document.getElementsByTagName(photoInfo.tagName);
                                    for (const el of elements) {
                                        if (el.src === photoInfo.src) {
                                            element = el;
                                            break;
                                        }
                                    }
                                }
                                
                                if (!element) {
                                    return { success: false, error: 'Could not find the photo element again' };
                                }
                                
                                // Click the element
                                element.click();
                                return { success: true, message: 'Clicked first photo' };
                            } catch (error) {
                                return { success: false, error: error.toString() };
                            }
                        }
                    """, photo_elements.get('selectors', [])[0])
                    
                    logger.info(f"Click result: {click_result}")
                else:
                    logger.error("No photo elements found to click")
                    click_result = { 'success': False, 'error': 'No photo elements found' }
                
            if photos_frame:
                logger.info(f"Found photos frame: {photos_frame['url']}")
            else:
                logger.info("Using alternative approach without photos frame")
            
            page = await context.get_current_page()
            
            logger.info("Using JavaScript to find and click the first photo...")
            
            frames_info = await context.execute_javascript("""
                () => {
                    const frames = Array.from(document.querySelectorAll('iframe'));
                    return frames.map(frame => ({
                        name: frame.name,
                        id: frame.id,
                        src: frame.src
                    }));
                }
            """)
            
            logger.info(f"Found {len(frames_info)} frames via JavaScript")
            
            photos_frame_path = [] if photos_frame is None else photos_frame.get('found_path', [])
            logger.info(f"Photos frame path: {photos_frame_path}")
            
            click_result = await context.execute_javascript("""
                () => {
                    try {
                        // Target specific photo elements based on what we see in the browser
                        const photoSelectors = [
                            // Target the photo grid items
                            'a > img[src*="search.pstatic.net"]',
                            'a[href*="photo"] > img',
                            '.place_thumb img',
                            '.photo_area img',
                            '.list_item img',
                            // Target by Korean text
                            'a:has(span:contains("사진"))',
                            'a:has(span:contains("내부"))',
                            'a:has(span:contains("외부"))',
                            // Target by position in grid
                            'div[role="main"] a > img',
                            // Fallback to any visible image
                            'img[width][height]:not([width="0"])'
                        ];
                        
                        // Try each selector
                        let photoElement = null;
                        let photoElements = [];
                        
                        for (const selector of photoSelectors) {
                            try {
                                const elements = document.querySelectorAll(selector);
                                if (elements && elements.length > 0) {
                                    photoElements = Array.from(elements).filter(el => 
                                        el.offsetWidth > 50 && 
                                        el.offsetHeight > 50 && 
                                        !el.src.includes('map.pstatic.net')
                                    );
                                    
                                    if (photoElements.length > 0) {
                                        photoElement = photoElements[0];
                                        // If we found an image, get its parent <a> tag if it exists
                                        if (photoElement.tagName === 'IMG' && photoElement.parentElement && photoElement.parentElement.tagName === 'A') {
                                            photoElement = photoElement.parentElement;
                                        }
                                        break;
                                    }
                                }
                            } catch (selectorError) {
                                console.log('Selector error:', selectorError);
                            }
                        }
                        
                        // If we still don't have a photo element, try a more aggressive approach
                        if (!photoElement) {
                            // Look for any clickable elements that might be photos
                            const allLinks = document.querySelectorAll('a');
                            const potentialPhotoLinks = Array.from(allLinks).filter(link => {
                                // Check if link contains an image
                                const img = link.querySelector('img');
                                return img && img.offsetWidth > 50 && img.offsetHeight > 50 && !img.src.includes('map.pstatic.net');
                            });
                            
                            if (potentialPhotoLinks.length > 0) {
                                photoElement = potentialPhotoLinks[0];
                            }
                        }
                        
                        if (!photoElement) {
                            return { 
                                success: false, 
                                error: 'No photos found in any frame',
                                selectors: photoSelectors
                            };
                        }
                        
                        // Get info before clicking
                        const elementInfo = {
                            tagName: photoElement.tagName,
                            className: photoElement.className,
                            id: photoElement.id,
                            href: photoElement.href || '',
                            innerText: photoElement.innerText || '',
                            childCount: photoElement.children.length
                        };
                        
                        if (photoElement.querySelector('img')) {
                            const img = photoElement.querySelector('img');
                            elementInfo.imgSrc = img.src || '';
                            elementInfo.imgWidth = img.offsetWidth;
                            elementInfo.imgHeight = img.offsetHeight;
                        }
                        
                        // Click the photo
                        photoElement.click();
                        
                        return { 
                            success: true, 
                            message: 'Clicked first photo',
                            elementInfo: elementInfo,
                            totalPhotos: photoElements.length
                        };
                    } catch (error) {
                        return { 
                            success: false, 
                            error: error.toString()
                        };
                    }
                }
            """)
            
            logger.info(f"Click result: {click_result}")
            
            await asyncio.sleep(WAIT_TIMES["photo_load"])
            
            screenshot_path = tmp_dir / "03_after_photo_click.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot after photo click to {screenshot_path}")
            
            logger.info("Trying new find_and_click_naver_photo method...")
            
            await context.refresh_page()
            await asyncio.sleep(WAIT_TIMES["page_load"])
            
            screenshot_path = tmp_dir / "03a_before_new_method.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot before using new method to {screenshot_path}")
            
            click_success = await context.find_and_click_naver_photo()
            
            logger.info(f"Photo click result using new method: {click_success}")
            
            await asyncio.sleep(WAIT_TIMES["photo_load"])
            
            screenshot_path = tmp_dir / "03b_after_new_method_click.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot after new method click to {screenshot_path}")
            
            await context.refresh_page()
            await asyncio.sleep(WAIT_TIMES["page_load"])
            
            logger.info("Trying new method with '내부' (interior) category...")
            category_click_success = await context.find_and_click_naver_photo("내부")
            
            logger.info(f"Category click result: {category_click_success}")
            
            await asyncio.sleep(WAIT_TIMES["photo_load"])
            
            screenshot_path = tmp_dir / "03c_after_category_click.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved screenshot after category click to {screenshot_path}")
            
            logger.info("Verifying category frame is visible...")
            
            category_result = await context.execute_javascript("""
                () => {
                    try {
                        console.log("Checking for category frame visibility...");
                        
                        // More robust approach - look for Korean category text
                        const koreanCategories = ['내부', '외부', '메뉴', '음식'];
                        
                        // Function to check if an element contains Korean category text
                        function containsKoreanCategory(element) {
                            if (!element || !element.textContent) return false;
                            return koreanCategories.some(category => 
                                element.textContent.includes(category)
                            );
                        }
                        
                        // Function to find elements with Korean category text
                        function findCategoryElements(doc) {
                            if (!doc || !doc.body) return [];
                            
                            // Check all elements with text
                            const allElements = Array.from(doc.querySelectorAll('*'));
                            const categoryElements = allElements.filter(el => 
                                containsKoreanCategory(el) && 
                                el.offsetWidth > 0 && 
                                el.offsetHeight > 0
                            );
                            
                            console.log(`Found ${categoryElements.length} elements with Korean category text`);
                            return categoryElements;
                        }
                        
                        // Check main document
                        const mainCategoryElements = findCategoryElements(document);
                        if (mainCategoryElements.length > 0) {
                            console.log("Found category elements in main document");
                            return {
                                success: true,
                                message: 'Category frame is visible in main document',
                                categories: mainCategoryElements.map(el => el.textContent.trim())
                            };
                        }
                        
                        // Check all accessible frames
                        const frames = Array.from(document.querySelectorAll('iframe'));
                        console.log(`Checking ${frames.length} frames for category elements`);
                        
                        for (let i = 0; i < frames.length; i++) {
                            try {
                                console.log(`Checking frame ${i}: ${frames[i].src}`);
                                const frameDoc = frames[i].contentDocument || frames[i].contentWindow.document;
                                const frameCategoryElements = findCategoryElements(frameDoc);
                                
                                if (frameCategoryElements.length > 0) {
                                    console.log(`Found category elements in frame ${i}`);
                                    return {
                                        success: true,
                                        message: `Category frame is visible in iframe ${i}`,
                                        categories: frameCategoryElements.map(el => el.textContent.trim())
                                    };
                                }
                            } catch (frameError) {
                                console.log(`Cannot access frame ${i} due to cross-origin restrictions`);
                                // Cross-origin frame access error, ignore
                            }
                        }
                        
                        // Check if we're in a photo viewer mode by looking for navigation elements
                        const navElements = document.querySelectorAll('button, a');
                        const photoViewerNav = Array.from(navElements).filter(el => 
                            (el.textContent.includes('다음') || el.textContent.includes('이전')) &&
                            el.offsetWidth > 0 && 
                            el.offsetHeight > 0
                        );
                        
                        if (photoViewerNav.length > 0) {
                            console.log("Found photo viewer navigation elements");
                            return {
                                success: true,
                                message: 'Photo viewer navigation is visible',
                                navElements: photoViewerNav.map(el => el.textContent.trim())
                            };
                        }
                        
                        // Last resort - check for any large images that might indicate we're in photo view
                        const largeImages = Array.from(document.querySelectorAll('img')).filter(img => 
                            img.offsetWidth > 300 && img.offsetHeight > 300
                        );
                        
                        if (largeImages.length > 0) {
                            console.log("Found large images indicating photo view");
                            return {
                                success: true,
                                message: 'Large photo is visible',
                                imageCount: largeImages.length
                            };
                        }
                        
                        return {
                            success: false,
                            error: 'Category frame not found'
                        };
                    } catch (error) {
                        console.error("Error in category verification:", error);
                        return {
                            success: false,
                            error: error.toString()
                        };
                    }
                }
            """)
            
            logger.info(f"Category verification result: {category_result}")
            
            screenshot_path = tmp_dir / "04_final_state.png"
            screenshot_b64 = await context.take_screenshot(full_page=False)
            
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(screenshot_b64))
            logger.info(f"Saved final screenshot to {screenshot_path}")
            
            logger.info("Test summary:")
            logger.info(f"  - Navigation to Naver Maps restaurant: {'Success' if main_frame else 'Failed'}")
            logger.info(f"  - Finding photos frame: {'Success' if photos_frame else 'Failed'}")
            logger.info(f"  - Clicking first photo (original method): {'Success' if click_result.get('success', False) else 'Failed'}")
            logger.info(f"  - Clicking first photo (new method): {'Success' if click_success else 'Failed'}")
            logger.info(f"  - Clicking photo with category (new method): {'Success' if category_click_success else 'Failed'}")
            logger.info(f"  - Verifying category frame: {'Success' if category_result.get('success', False) else 'Failed'}")
            
            new_method_success = click_success or category_click_success
            original_method_success = click_result.get('success', False)
            
            if main_frame and photos_frame and (new_method_success or original_method_success) and category_result.get('success', False):
                logger.info("✅ TEST PASSED: Successfully navigated to restaurant, clicked photo, and verified category frame")
            else:
                logger.error("❌ TEST FAILED: Could not complete all steps successfully")
                
            if new_method_success and not original_method_success:
                logger.info("📊 COMPARISON: New method succeeded where original method failed")
            elif not new_method_success and original_method_success:
                logger.info("📊 COMPARISON: Original method succeeded where new method failed")
            elif new_method_success and original_method_success:
                logger.info("📊 COMPARISON: Both methods succeeded")
            else:
                logger.info("📊 COMPARISON: Both methods failed")
            
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_naver_restaurant_photos())
