"""
Utility functions for working with Naver Maps in browser-use.
Provides constants and helper functions for navigating Naver Maps restaurant listings,
especially for handling iframe traversal and Korean text elements.
"""

import re
import logging
from typing import Dict, Optional, List, Tuple

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
