"""
Minimal test script to verify headless browser configuration works.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent, BrowserConfig
from browser_use.browser.browser import Browser
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLM(BaseChatModel):
    """Mock LLM for testing purposes."""
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response."""
        return AIMessage(content="""I'll help you navigate to Google.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Starting task",
    "memory": "",
    "next_goal": "Navigate to Google"
  },
  "action": [
    {
      "navigate_to": {
        "url": "https://www.google.com"
      }
    }
  ]
}
```""")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)

async def test_browser_directly():
    """Test the browser directly with headless=True."""
    browser_config = BrowserConfig(
        headless=True,
        browser_class='chromium'
    )
    
    browser = Browser(config=browser_config)
    
    try:
        async with await browser.new_context() as context:
            await context.navigate_to("https://www.google.com")
            logger.info("Successfully navigated to Google with headless browser")
            
            screenshot_path = "/tmp/google_screenshot.png"
            await context.take_screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
    finally:
        await browser.close()

async def test_agent_with_browser_config():
    """Test the Agent with explicit browser configuration."""
    try:
        llm = MockLLM()
        
        task = 'Go to Google'
        
        browser_config = BrowserConfig(
            headless=True,
            browser_class='chromium'
        )
        
        agent = Agent(
            task=task, 
            llm=llm,
            browser_config=browser_config
        )
        
        await agent.run()
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run both tests."""
    logger.info("Testing direct browser with headless=True")
    try:
        await test_browser_directly()
        logger.info("Direct browser test succeeded")
    except Exception as e:
        logger.error(f"Direct browser test failed: {e}")
    
    logger.info("\nTesting Agent with browser_config")
    await test_agent_with_browser_config()

if __name__ == '__main__':
    asyncio.run(main())
