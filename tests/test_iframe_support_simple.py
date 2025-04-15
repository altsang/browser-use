"""
Simplified test for the enhanced iframe support capabilities.
This test file only tests the iframe support functionality without importing the entire library.
"""
import pytest
import asyncio
import re
from unittest.mock import AsyncMock, MagicMock, patch

from browser_use.browser.context import BrowserContext


@pytest.mark.asyncio
async def test_get_element_in_nested_frame():
    """Test the get_element_in_nested_frame method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    
    mock_frame = AsyncMock()
    mock_page.main_frame = mock_frame
    mock_frame.child_frames = [AsyncMock(), AsyncMock()]
    mock_frame.child_frames[1].query_selector = AsyncMock(return_value=AsyncMock())
    
    selector = "div.photo-container"
    frame_path = [0, 1]
    
    with patch.object(context, 'get_current_page', return_value=mock_page):
        element = await context.get_element_in_nested_frame(selector, frame_path)
    
    assert element is not None


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
    
    with patch.object(context, 'get_nested_frames', AsyncMock(return_value=mock_frames)):
        frame = await context.find_frame_by_url_pattern(r'maps\.example\.com')
    
    assert frame is not None
    assert frame['url'] == 'https://maps.example.com'
    assert frame['name'] == 'maps'
    assert 'found_path' in frame
    assert frame['found_path'] == [0, 0]


if __name__ == "__main__":
    asyncio.run(test_get_element_in_nested_frame())
    asyncio.run(test_find_frame_by_url_pattern())
    print("All tests passed!")
