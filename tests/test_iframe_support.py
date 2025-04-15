"""
Test the enhanced iframe support capabilities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from browser_use.browser.context import BrowserContext
from browser_use.dom.service import DomService


@pytest.mark.asyncio
async def test_get_nested_frames():
    """Test the get_nested_frames method."""
    mock_page = AsyncMock()
    mock_main_frame = AsyncMock()
    mock_child_frame = AsyncMock()
    mock_grandchild_frame = AsyncMock()
    
    mock_page.main_frame = mock_main_frame
    mock_main_frame.child_frames = [mock_child_frame]
    mock_child_frame.child_frames = [mock_grandchild_frame]
    mock_grandchild_frame.child_frames = []
    
    mock_main_frame.url = "https://example.com"
    mock_child_frame.url = "https://example.com/iframe1"
    mock_grandchild_frame.url = "https://example.com/iframe2"
    
    mock_main_frame.name = "main"
    mock_child_frame.name = "child"
    mock_grandchild_frame.name = "grandchild"
    
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    context.get_current_page = AsyncMock(return_value=mock_page)
    
    frames = await context.get_nested_frames()
    
    assert len(frames) == 1  # One top-level frame
    assert frames[0]['url'] == "https://example.com"
    assert frames[0]['name'] == "main"
    assert len(frames[0]['child_frames']) == 1
    assert frames[0]['child_frames'][0]['url'] == "https://example.com/iframe1"
    assert frames[0]['child_frames'][0]['name'] == "child"
    assert len(frames[0]['child_frames'][0]['child_frames']) == 1
    assert frames[0]['child_frames'][0]['child_frames'][0]['url'] == "https://example.com/iframe2"
    assert frames[0]['child_frames'][0]['child_frames'][0]['name'] == "grandchild"


@pytest.mark.asyncio
async def test_find_frame_by_url_pattern():
    """Test the find_frame_by_url_pattern method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_frames = [
        {
            'url': 'https://example.com',
            'name': 'main',
            'depth': 0,
            'path': [],
            'child_frames': [
                {
                    'url': 'https://maps.example.com',
                    'name': 'maps',
                    'depth': 1,
                    'path': [0],
                    'child_frames': []
                }
            ]
        }
    ]
    context.get_nested_frames = AsyncMock(return_value=mock_frames)
    
    frame = await context.find_frame_by_url_pattern(r'maps\.example\.com')
    
    assert frame is not None
    assert frame['url'] == 'https://maps.example.com'
    assert frame['name'] == 'maps'
    assert 'found_path' in frame
    assert frame['found_path'] == [0, 0]


@pytest.mark.asyncio
async def test_find_naver_maps_photos_frame():
    """Test the find_naver_maps_photos_frame method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_frames = [
        {
            'url': 'https://map.naver.com/p/search/restaurant',
            'name': 'main',
            'depth': 0,
            'path': [],
            'child_frames': [
                {
                    'url': 'https://pcmap.place.naver.com/restaurant/1234',
                    'name': 'pcmap',
                    'depth': 1,
                    'path': [0],
                    'child_frames': []
                },
                {
                    'url': 'https://place-site.naver.com/restaurant/1234',
                    'name': 'place',
                    'depth': 1,
                    'path': [1],
                    'hasKoreanText': True,
                    'child_frames': []
                }
            ]
        }
    ]
    context.get_nested_frames = AsyncMock(return_value=mock_frames)
    
    frame = await context.find_naver_maps_photos_frame()
    
    assert frame is not None
    assert frame['url'] == 'https://place-site.naver.com/restaurant/1234'
    assert frame['name'] == 'place'
    assert 'found_path' in frame
    assert frame['found_path'] == [0, 1]
    assert frame['hasKoreanText'] is True


@pytest.mark.asyncio
async def test_find_element_by_korean_text():
    """Test the find_element_by_korean_text method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    
    mock_element = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=mock_element)
    
    element = await context.find_element_by_korean_text("사진")
    
    assert element is not None
    assert element == mock_element
    mock_page.query_selector.assert_called_once_with('text="사진"')
    
    mock_page.query_selector.reset_mock()
    
    frame_path = [0, 1]
    mock_frame_locator = AsyncMock()
    mock_page.frame_locator = AsyncMock(return_value=mock_frame_locator)
    mock_frame_locator.locator = AsyncMock()
    mock_frame_locator.locator.return_value.element_handle = AsyncMock(return_value=mock_element)
    
    element = await context.find_element_by_korean_text("내부", frame_path)
    
    assert element is not None
    assert element == mock_element
    mock_page.frame_locator.assert_called()
    mock_frame_locator.locator.assert_called_with('text="내부"')


@pytest.mark.asyncio
async def test_get_element_in_nested_frame():
    """Test the get_element_in_nested_frame method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    
    mock_frame_locator = AsyncMock()
    mock_page.frame_locator = AsyncMock(return_value=mock_frame_locator)
    mock_frame_locator.frame_locator = AsyncMock(return_value=mock_frame_locator)
    
    mock_element = AsyncMock()
    mock_frame_locator.locator = AsyncMock()
    mock_frame_locator.locator.return_value.element_handle = AsyncMock(return_value=mock_element)
    
    frame_path = [0, 1]
    selector = "div.photo-container"
    
    # Call the method with the correct parameter order (selector first, then frame_path)
    element = await context.get_element_in_nested_frame(selector, frame_path)
    
    assert element is not None
    assert element == mock_element
    mock_page.frame_locator.assert_called()
    mock_frame_locator.locator.assert_called_with(selector)
