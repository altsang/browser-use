"""
Test the enhanced JavaScript execution capabilities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from browser_use.browser.context import BrowserContext
from browser_use.dom.views import DOMElementNode


@pytest.mark.asyncio
async def test_execute_javascript_with_args():
    """Test the execute_javascript method with arguments."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.evaluate = AsyncMock(return_value=42)
    
    script = "(a, b) => a + b"
    result = await context.execute_javascript(script, 20, 22)
    
    assert result == 42
    mock_page.evaluate.assert_called_once_with(script, 20, 22)


@pytest.mark.asyncio
async def test_evaluate_element_javascript():
    """Test the evaluate_element_javascript method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_element_node = MagicMock(spec=DOMElementNode)
    mock_element_handle = AsyncMock()
    
    context.get_locate_element = AsyncMock(return_value=mock_element_handle)
    mock_element_handle.evaluate = AsyncMock(return_value="test result")
    
    script = "(element) => element.textContent"
    result = await context.evaluate_element_javascript(mock_element_node, script)
    
    assert result == "test result"
    context.get_locate_element.assert_called_once_with(mock_element_node)
    mock_element_handle.evaluate.assert_called_once_with(script)


@pytest.mark.asyncio
async def test_evaluate_element_javascript_with_args():
    """Test the evaluate_element_javascript method with arguments."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_element_node = MagicMock(spec=DOMElementNode)
    mock_element_handle = AsyncMock()
    
    context.get_locate_element = AsyncMock(return_value=mock_element_handle)
    mock_element_handle.evaluate = AsyncMock(return_value="test result with args")
    
    script = "(element, arg1, arg2) => element.textContent + arg1 + arg2"
    result = await context.evaluate_element_javascript(mock_element_node, script, " with", " args")
    
    assert result == "test result with args"
    context.get_locate_element.assert_called_once_with(mock_element_node)
    mock_element_handle.evaluate.assert_called_once_with(script, " with", " args")


@pytest.mark.asyncio
async def test_evaluate_element_javascript_element_not_found():
    """Test the evaluate_element_javascript method when element is not found."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_element_node = MagicMock(spec=DOMElementNode)
    
    context.get_locate_element = AsyncMock(return_value=None)
    
    script = "(element) => element.textContent"
    
    with pytest.raises(Exception) as excinfo:
        await context.evaluate_element_javascript(mock_element_node, script)
    
    assert "Element not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_wait_for_function():
    """Test the wait_for_function method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.wait_for_function = AsyncMock()
    
    expression = "() => document.readyState === 'complete'"
    await context.wait_for_function(expression, 5000)
    
    mock_page.wait_for_function.assert_called_once_with(expression, timeout=5000, polling='raf')


@pytest.mark.asyncio
async def test_wait_for_function_with_args():
    """Test the wait_for_function method with arguments."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.wait_for_function = AsyncMock()
    
    expression = "(selector) => document.querySelector(selector) !== null"
    await context.wait_for_function(expression, 5000, polling='interval', args=["#my-element"])
    
    mock_page.wait_for_function.assert_called_once_with(expression, timeout=5000, polling='interval', args=["#my-element"])


@pytest.mark.asyncio
async def test_wait_for_javascript_load_success():
    """Test the wait_for_javascript_load method with successful load."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.wait_for_function = AsyncMock()
    
    result = await context.wait_for_javascript_load(10000)
    
    assert result is True
    mock_page.wait_for_load_state.assert_called_once_with('load')
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_javascript_load_failure():
    """Test the wait_for_javascript_load method with load failure."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.wait_for_load_state = AsyncMock(side_effect=Exception("Load state timeout"))
    
    result = await context.wait_for_javascript_load(10000)
    
    assert result is False
    mock_page.wait_for_load_state.assert_called_once_with('load')
    mock_page.wait_for_function.assert_not_called()


@pytest.mark.asyncio
async def test_wait_for_javascript_load_function_failure():
    """Test the wait_for_javascript_load method with function wait failure."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.wait_for_function = AsyncMock(side_effect=Exception("Function wait timeout"))
    
    result = await context.wait_for_javascript_load(10000)
    
    assert result is False
    mock_page.wait_for_load_state.assert_called_once_with('load')
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_simulate_react_event():
    """Test the simulate_react_event method."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_element_node = MagicMock(spec=DOMElementNode)
    mock_element_handle = AsyncMock()
    
    context.get_locate_element = AsyncMock(return_value=mock_element_handle)
    
    mock_page = AsyncMock()
    context.get_current_page = AsyncMock(return_value=mock_page)
    mock_page.evaluate = AsyncMock(return_value=True)
    
    result = await context.simulate_react_event(mock_element_node, "click", {"bubbles": True})
    
    assert result is True
    context.get_locate_element.assert_called_once_with(mock_element_node)
    mock_page.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_simulate_react_event_element_not_found():
    """Test the simulate_react_event method when element is not found."""
    mock_browser = MagicMock()
    context = BrowserContext(mock_browser)
    
    mock_element_node = MagicMock(spec=DOMElementNode)
    
    context.get_locate_element = AsyncMock(return_value=None)
    
    with pytest.raises(Exception) as excinfo:
        await context.simulate_react_event(mock_element_node, "click")
    
    assert "not found" in str(excinfo.value)
