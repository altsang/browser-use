"""
Utility functions for working with Naver Maps in browser-use.
Provides constants and helper functions for navigating Naver Maps restaurant listings,
especially for handling iframe traversal and Korean text elements.
"""

import re
import asyncio
import logging
from typing import Dict, Optional, List, Tuple, Any

from browser_use.browser.context import BrowserContext

logger = logging.getLogger(__name__)

NAVER_MAPS_SELECTORS = {
    'photos_button': '사진',  # "Photos" button
    'interior_category': '내부',  # "Interior" category
    'exterior_category': '외부',  # "Exterior" category
    'menu_category': '메뉴',  # "Menu" category
    'food_category': '음식',  # "Food" category
    'next_button': '다음',  # "Next" button
    'previous_button': '이전',  # "Previous" button
    
    'main_frame_pattern': r'map\.naver\.com',
    'photo_frame_pattern': r'(place|pcmap\.place)\.naver\.com',
    'content_frame_pattern': r'pcmap\.place\.naver\.com',
}

def is_naver_maps_url(url: str) -> bool:
    """
    Check if a URL is a Naver Maps URL.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is a Naver Maps URL, False otherwise
    """
    return bool(re.search(r'(map\.naver\.com|pcmap\.place\.naver\.com)', url, re.IGNORECASE))

def is_restaurant_page(url: str) -> bool:
    """
    Check if a URL is a Naver Maps restaurant page.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is a Naver Maps restaurant page, False otherwise
    """
    return bool(re.search(r'(map\.naver\.com/p/.*?/(place|restaurant|food)|pcmap\.place\.naver\.com/restaurant/\d+)', url, re.IGNORECASE))

def extract_restaurant_id(url: str) -> Optional[str]:
    """
    Extract the restaurant ID from a Naver Maps URL.
    
    Args:
        url (str): The Naver Maps URL
        
    Returns:
        Optional[str]: The restaurant ID if found, None otherwise
    """
    match = re.search(r'place/(\d+)', url)
    if match:
        return match.group(1)
    
    match = re.search(r'restaurant/(\d+)', url)
    if match:
        return match.group(1)
        
    return None

def get_photo_selector(category: Optional[str] = None) -> str:
    """
    Get the selector for a specific photo category.
    
    Args:
        category (str, optional): The category to get the selector for.
            Can be 'interior', 'exterior', 'menu', 'food', or None for the main photos button.
            
    Returns:
        str: The selector for the specified category
    """
    if category == 'interior':
        return f'text="{NAVER_MAPS_SELECTORS["interior_category"]}"'
    elif category == 'exterior':
        return f'text="{NAVER_MAPS_SELECTORS["exterior_category"]}"'
    elif category == 'menu':
        return f'text="{NAVER_MAPS_SELECTORS["menu_category"]}"'
    elif category == 'food':
        return f'text="{NAVER_MAPS_SELECTORS["food_category"]}"'
    return f'text="{NAVER_MAPS_SELECTORS["photos_button"]}"'

def get_navigation_selector(direction: str) -> str:
    """
    Get the selector for a navigation button.
    
    Args:
        direction (str): The direction to navigate. Can be 'next' or 'previous'.
        
    Returns:
        str: The selector for the specified navigation button
    """
    if direction == 'next':
        return f'text="{NAVER_MAPS_SELECTORS["next_button"]}"'
    elif direction == 'previous':
        return f'text="{NAVER_MAPS_SELECTORS["previous_button"]}"'
    return ""

def build_restaurant_url(restaurant_id: str) -> str:
    """
    Build a Naver Maps restaurant URL from a restaurant ID.
    
    Args:
        restaurant_id (str): The restaurant ID
        
    Returns:
        str: The Naver Maps restaurant URL
    """
    return f"https://map.naver.com/p/search/place/{restaurant_id}"

def get_frame_patterns() -> Dict[str, str]:
    """
    Get the frame identification patterns for Naver Maps.
    
    Returns:
        Dict[str, str]: A dictionary of frame identification patterns
    """
    return {
        'main': NAVER_MAPS_SELECTORS['main_frame_pattern'],
        'photo': NAVER_MAPS_SELECTORS['photo_frame_pattern'],
        'content': NAVER_MAPS_SELECTORS['content_frame_pattern'],
    }

def parse_photo_count(text: str) -> int:
    """
    Parse the photo count from a text string.
    Naver Maps displays photo counts like "999+", so this function
    handles that special case.
    
    Args:
        text (str): The text containing the photo count
        
    Returns:
        int: The parsed photo count
    """
    if not text:
        return 0
        
    if "+" in text:
        base = text.replace("+", "")
        try:
            return int(base)
        except ValueError:
            return 0
            
    try:
        return int(text)
    except ValueError:
        return 0

def wait_times() -> Dict[str, int]:
    """
    Get recommended wait times for various Naver Maps operations.
    
    Returns:
        Dict[str, int]: A dictionary of operation names and recommended wait times in milliseconds
    """
    return {
        'frame_load': 5000,  # Wait time for frame to load
        'category_selection': 2000,  # Wait time after selecting a category
        'photo_navigation': 1000,  # Wait time between photo navigation actions
        'initial_load': 10000,  # Wait time for initial page load
        'photos_tab_click': 3000,  # Wait time after clicking photos tab
        'photo_click': 2000,  # Wait time after clicking a photo
    }

async def find_and_click_naver_photos_button(context: BrowserContext) -> bool:
    """
    Find and click the photos button on a Naver Maps restaurant page.
    
    Args:
        context: BrowserContext instance
        
    Returns:
        bool: True if successful, False otherwise
    """
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
                    el.textContent.includes('{NAVER_MAPS_SELECTORS["photos_button"]}') && 
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
    logger.info(f"Clicked on photos button: {clicked}")
    return clicked

async def find_and_click_first_photo(context: BrowserContext) -> bool:
    """
    Find and click the first photo in a Naver Maps photo grid.
    
    Args:
        context: BrowserContext instance
        
    Returns:
        bool: True if successful, False otherwise
    """
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
    return clicked

async def find_and_click_photo_category(context: BrowserContext, category: str = "interior") -> bool:
    """
    Find and click a photo category button in Naver Maps photo viewer.
    
    Args:
        context: BrowserContext instance
        category: Category to click ("interior" or "exterior")
        
    Returns:
        bool: True if successful, False otherwise
    """
    category_text = NAVER_MAPS_SELECTORS["interior_category"] if category == "interior" else NAVER_MAPS_SELECTORS["exterior_category"]
    
    for attempt in range(3):
        logger.info(f"Attempt {attempt+1} to find category '{category_text}'")
        
        if attempt == 0:
            category_js = f"""
            (function() {{
                // Try to find in all frames
                function findInFrames(win, depth = 0) {{
                    if (depth > 5) return null; // Limit recursion depth
                    
                    try {{
                        // Try buttons or tabs first
                        const buttons = Array.from(win.document.querySelectorAll('button, [role="tab"], [role="button"], .tab, li'));
                        for (const btn of buttons) {{
                            if (btn.textContent && 
                                btn.textContent.includes('{category_text}') && 
                                btn.offsetWidth > 0 && 
                                btn.offsetHeight > 0) {{
                                console.log("Found category button:", btn.textContent);
                                btn.click();
                                return true;
                            }}
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
        elif attempt == 1:
            category_js = f"""
            (function() {{
                // Try to find in all frames
                function findInFrames(win, depth = 0) {{
                    if (depth > 5) return null; // Limit recursion depth
                    
                    try {{
                        // Try elements with exact text match
                        const elements = Array.from(win.document.querySelectorAll('*'));
                        for (const el of elements) {{
                            if (el.childNodes.length === 1 && 
                                el.childNodes[0].nodeType === 3 && 
                                el.textContent.trim() === '{category_text}' && 
                                el.offsetWidth > 0 && 
                                el.offsetHeight > 0) {{
                                console.log("Found exact category text:", el.textContent);
                                el.click();
                                return true;
                            }}
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
        else:
            category_js = f"""
            (function() {{
                // Try to find in all frames
                function findInFrames(win, depth = 0) {{
                    if (depth > 5) return null; // Limit recursion depth
                    
                    try {{
                        // Try any element with the text
                        const elements = Array.from(win.document.querySelectorAll('*'));
                        const categoryElement = elements.find(el => 
                            el.textContent && 
                            el.textContent.includes('{category_text}') && 
                            el.textContent.length < 10 && // Likely just the category text
                            el.offsetWidth > 0 && 
                            el.offsetHeight > 0
                        );
                        
                        if (categoryElement) {{
                            console.log("Found category element:", categoryElement.textContent);
                            categoryElement.click();
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
        
        clicked = await context.execute_javascript(category_js)
        if clicked:
            logger.info(f"Clicked on category button '{category_text}': {clicked}")
            return True
        
        await asyncio.sleep(1)
    
    logger.warning(f"Failed to find and click category '{category_text}' after multiple attempts")
    return False

async def navigate_naver_restaurant_photos(
    context: BrowserContext,
    restaurant_url: Optional[str] = None,
    category: str = "interior",
    wait_for_screenshots: bool = True,
    screenshot_dir: Optional[str] = None
) -> bool:
    """
    Navigate to a Naver Maps restaurant page, find photos, and interact with them.
    
    Args:
        context: BrowserContext instance
        restaurant_url: URL of the restaurant page (optional if already navigated)
        category: Photo category to select ("interior" or "exterior")
        wait_for_screenshots: Whether to wait between steps for screenshots
        screenshot_dir: Directory to save screenshots (None for no screenshots)
        
    Returns:
        bool: True if all steps completed successfully, False otherwise
    """
    try:
        if restaurant_url:
            await context.navigate_to(restaurant_url)
            logger.info(f"Navigated to {restaurant_url}")
            
            if wait_for_screenshots:
                await asyncio.sleep(wait_times()["initial_load"] / 1000)
                
            if screenshot_dir:
                await context.take_screenshot(path=f"{screenshot_dir}/01_initial_page.png")
        
        photos_clicked = await find_and_click_naver_photos_button(context)
        if not photos_clicked:
            logger.error("Failed to find and click photos button")
            return False
            
        if wait_for_screenshots:
            await asyncio.sleep(wait_times()["photos_tab_click"] / 1000)
            
        if screenshot_dir:
            await context.take_screenshot(path=f"{screenshot_dir}/02_after_photos_click.png")
        
        photo_clicked = await find_and_click_first_photo(context)
        if not photo_clicked:
            logger.error("Failed to find and click first photo")
            return False
            
        if wait_for_screenshots:
            await asyncio.sleep(wait_times()["photo_click"] / 1000)
            
        if screenshot_dir:
            await context.take_screenshot(path=f"{screenshot_dir}/03_after_photo_click.png")
        
        category_clicked = await find_and_click_photo_category(context, category)
        if not category_clicked:
            logger.warning(f"Failed to find and click {category} category")
            
        if wait_for_screenshots:
            await asyncio.sleep(wait_times()["category_selection"] / 1000)
            
        if screenshot_dir:
            await context.take_screenshot(path=f"{screenshot_dir}/04_final_state.png")
        
        return True
        
    except Exception as e:
        logger.error(f"Error navigating Naver restaurant photos: {e}")
        if screenshot_dir:
            await context.take_screenshot(path=f"{screenshot_dir}/error.png")
        return False
