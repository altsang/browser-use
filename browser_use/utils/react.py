"""
Utility functions for React component interaction in browser-use.
Provides helper functions for simulating React synthetic events,
interacting with React components, and detecting React applications.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

REACT_EVENT_MAPPING = {
    'onClick': 'click',
    'onChange': 'change',
    'onFocus': 'focus',
    'onBlur': 'blur',
    'onSubmit': 'submit',
    'onKeyDown': 'keydown',
    'onKeyUp': 'keyup',
    'onKeyPress': 'keypress',
    'onMouseDown': 'mousedown',
    'onMouseUp': 'mouseup',
    'onMouseMove': 'mousemove',
    'onMouseEnter': 'mouseenter',
    'onMouseLeave': 'mouseleave',
    'onTouchStart': 'touchstart',
    'onTouchEnd': 'touchend',
    'onTouchMove': 'touchmove',
}

REACT_DETECTION_SCRIPT = """
() => {
    // Check for React DevTools
    const hasReactDevTools = !!window.__REACT_DEVTOOLS_GLOBAL_HOOK__;
    
    // Check for common React properties on DOM
    const reactRoot = document.querySelector('[data-reactroot]');
    
    // Check for React in global namespace
    const hasReactGlobal = !!window.React;
    
    // Check for common React libraries
    const hasReactDOM = !!window.ReactDOM;
    
    // Check for React Fiber
    const hasReactFiber = Array.from(document.querySelectorAll('*')).some(el => {
        const keys = Object.keys(el);
        return keys.some(key => key.startsWith('__reactFiber$') || 
                         key.startsWith('__reactInternalInstance$') ||
                         key.startsWith('_reactFiber'));
    });
    
    return {
        isReactApp: hasReactDevTools || !!reactRoot || hasReactGlobal || hasReactDOM || hasReactFiber,
        hasReactDevTools,
        hasReactRoot: !!reactRoot,
        hasReactGlobal,
        hasReactDOM,
        hasReactFiber
    };
}
"""

REACT_SYNTHETIC_EVENT_SCRIPT = """
(element, eventType, eventData) => {
    // Find React instance on the element or its parent
    function findReactInstance(element) {
        let key;
        const keys = Object.keys(element);
        
        // Find the React Fiber key
        for (key of keys) {
            if (key.startsWith('__reactFiber$') || 
                key.startsWith('__reactInternalInstance$') ||
                key.startsWith('_reactFiber')) {
                return element[key];
            }
        }
        
        // If not found on element, try parent
        if (element.parentNode) {
            return findReactInstance(element.parentNode);
        }
        
        return null;
    }
    
    // Create and dispatch a React synthetic event
    function simulateEvent(element, eventType, eventData) {
        // For React 16+, we need to access the event system differently
        const event = new Event(eventType, { bubbles: true, cancelable: true });
        
        // Add custom event data
        Object.assign(event, eventData);
        
        // Dispatch the event
        element.dispatchEvent(event);
        
        return true;
    }
    
    return simulateEvent(element, eventType, eventData);
}
"""

async def detect_react_app(page):
    """
    Detect if the current page is a React application.
    
    Args:
        page: The Playwright page object
        
    Returns:
        dict: Dictionary with React detection information
    """
    try:
        return await page.evaluate(REACT_DETECTION_SCRIPT)
    except Exception as e:
        logger.error(f"Error detecting React app: {str(e)}")
        return {"isReactApp": False, "error": str(e)}

async def get_react_component_props(page, selector):
    """
    Get the props of a React component.
    
    Args:
        page: The Playwright page object
        selector: CSS selector to target the component
        
    Returns:
        dict: Component props or None if not found
    """
    script = """
    (selector) => {
        const element = document.querySelector(selector);
        if (!element) return null;
        
        // Find React Fiber instance
        const keys = Object.keys(element);
        let fiber = null;
        
        for (const key of keys) {
            if (key.startsWith('__reactFiber$') || 
                key.startsWith('__reactInternalInstance$') || 
                key.startsWith('_reactFiber')) {
                fiber = element[key];
                break;
            }
        }
        
        if (!fiber) return null;
        
        // Navigate to the component instance to get props
        if (fiber.memoizedProps) {
            return fiber.memoizedProps;
        }
        
        return null;
    }
    """
    
    try:
        return await page.evaluate(script, selector)
    except Exception as e:
        logger.error(f"Error getting React component props: {str(e)}")
        return None

def get_react_event_name(browser_event_name):
    """
    Convert a browser event name to a React event name.
    
    Args:
        browser_event_name (str): Browser event name (e.g., 'click')
        
    Returns:
        str: React event name (e.g., 'onClick')
    """
    for react_event, browser_event in REACT_EVENT_MAPPING.items():
        if browser_event == browser_event_name.lower():
            return react_event
    
    if browser_event_name:
        event_name = browser_event_name.lower()
        return f"on{event_name[0].upper()}{event_name[1:]}"
    
    return None

async def find_react_components(page, component_name=None):
    """
    Find React components in the page.
    
    Args:
        page: The Playwright page object
        component_name (str, optional): Filter by component name
        
    Returns:
        list: List of found components with their properties
    """
    script = """
    (componentName) => {
        // Helper to get component name from fiber
        function getComponentName(fiber) {
            if (!fiber) return null;
            
            // React 16+ component name detection
            if (fiber.type) {
                if (typeof fiber.type === 'string') {
                    return fiber.type; // HTML element
                }
                if (fiber.type.displayName) {
                    return fiber.type.displayName;
                }
                if (fiber.type.name) {
                    return fiber.type.name;
                }
            }
            
            // Fallback for function components
            if (fiber.elementType) {
                if (fiber.elementType.displayName) {
                    return fiber.elementType.displayName;
                }
                if (fiber.elementType.name) {
                    return fiber.elementType.name;
                }
            }
            
            return 'Unknown';
        }
        
        // Find all React components
        const components = [];
        const elements = document.querySelectorAll('*');
        
        for (const el of elements) {
            const keys = Object.keys(el);
            let fiber = null;
            
            // Find React Fiber
            for (const key of keys) {
                if (key.startsWith('__reactFiber$') || 
                    key.startsWith('__reactInternalInstance$') || 
                    key.startsWith('_reactFiber')) {
                    fiber = el[key];
                    break;
                }
            }
            
            if (fiber) {
                const name = getComponentName(fiber);
                
                // Filter by component name if provided
                if (componentName && name !== componentName) {
                    continue;
                }
                
                components.push({
                    name,
                    element: el,
                    props: fiber.memoizedProps || {},
                    state: fiber.memoizedState || {},
                    domNode: el,
                });
            }
        }
        
        // Convert to serializable format
        return components.map(comp => ({
            name: comp.name,
            props: comp.props,
            hasState: !!comp.state,
            tagName: comp.domNode.tagName,
            id: comp.domNode.id,
            className: comp.domNode.className,
            rect: comp.domNode.getBoundingClientRect().toJSON(),
        }));
    }
    """
    
    try:
        return await page.evaluate(script, component_name)
    except Exception as e:
        logger.error(f"Error finding React components: {str(e)}")
        return []
