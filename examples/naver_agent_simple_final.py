"""
Simplified Agent-based test script for Naver Maps restaurant photos.

This script follows the simple.py structure to use the Agent model pattern
for navigating Naver Maps restaurant pages, finding photos, and interacting
with photo categories.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

NAVER_RESTAURANT_URL = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"

class NaverMapsMockLLM(BaseChatModel):
    """Mock LLM for testing Naver Maps restaurant photos navigation."""
    
    def __init__(self):
        """Initialize the LLM."""
        super().__init__()
        self._step_counter = 0
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "naver_maps_mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response."""
        self._step_counter += 1
        
        if NaverMapsMockLLM._step_counter == 1:
            return AIMessage(content=f"""I'll help you navigate to the Naver Maps restaurant page, find photos, click on the first photo, and select the interior photo category.

```json
{{
  "current_state": {{
    "evaluation_previous_goal": "Starting task",
    "memory": "",
    "next_goal": "Navigate to the restaurant page"
  }},
  "action": [
    {{
      "navigate_to": {{
        "url": "{NAVER_RESTAURANT_URL}"
      }}
    }}
  ]
}}
```""")
        elif self._step_counter == 2:
            return AIMessage(content="""I've navigated to the restaurant page. Now I'll look for the photo section.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Navigate to the restaurant page",
    "memory": "Successfully navigated to the Naver Maps restaurant page",
    "next_goal": "Find and click on the photo section"
  },
  "action": [
    {
      "find_element_by_text": {
        "text": "사진",
        "exact_match": false
      }
    }
  ]
}
```""")
        elif self._step_counter == 3:
            return AIMessage(content="""I've found the photo section. Now I'll click on it.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Find and click on the photo section",
    "memory": "Found the photo section with text '사진'",
    "next_goal": "Click on the photo section"
  },
  "action": [
    {
      "click_element": {
        "element_index": 0
      }
    }
  ]
}
```""")
        elif self._step_counter == 4:
            return AIMessage(content="""I've clicked on the photo section. Now I'll look for the first photo.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Click on the photo section",
    "memory": "Clicked on the photo section",
    "next_goal": "Find and click on the first photo"
  },
  "action": [
    {
      "find_element_by_selector": {
        "selector": "img[alt*='사진']",
        "multiple": true
      }
    }
  ]
}
```""")
        elif self._step_counter == 5:
            return AIMessage(content="""I've found the photos. Now I'll click on the first one.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Find and click on the first photo",
    "memory": "Found photos in the photo section",
    "next_goal": "Click on the first photo"
  },
  "action": [
    {
      "click_element": {
        "element_index": 0
      }
    }
  ]
}
```""")
        elif self._step_counter == 6:
            return AIMessage(content="""I've clicked on the first photo. Now I'll look for the photo category section.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Click on the first photo",
    "memory": "Clicked on the first photo",
    "next_goal": "Find the photo category section"
  },
  "action": [
    {
      "find_element_by_text": {
        "text": "내부",
        "exact_match": false
      }
    }
  ]
}
```""")
        elif self._step_counter == 7:
            return AIMessage(content="""I've found the interior photo category. Now I'll click on it.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Find the photo category section",
    "memory": "Found the interior photo category with text '내부'",
    "next_goal": "Click on the interior photo category"
  },
  "action": [
    {
      "click_element": {
        "element_index": 0
      }
    }
  ]
}
```""")
        else:
            return AIMessage(content="""I've completed the task successfully.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Click on the interior photo category",
    "memory": "Successfully navigated through the Naver Maps restaurant photos",
    "next_goal": "Task completed"
  },
  "action": [
    {
      "navigate_to": {
        "url": "about:blank"
      }
    }
  ]
}
```""")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)

async def setup_browser():
    """Set up the browser with proper CDP connection."""
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
        headless=False,
        disable_security=True,
        browser_class='chromium',
        cdp_url=f"http://localhost:{cdp_port}" if cdp_port else None
    )
    
    return Browser(config=browser_config)

async def main():
    """Main function to run the Naver Maps Agent test."""
    logger.info("Starting Naver Maps Agent test...")
    
    try:
        browser = await setup_browser()
        
        llm = NaverMapsMockLLM()
        task = 'Navigate to the Naver Maps restaurant page, find photos, click on the first photo, and select the interior photo category'
        
        output_dir = Path("/tmp/naver_agent_test")
        output_dir.mkdir(exist_ok=True)
        
        logger.info("Initializing Agent...")
        agent = Agent(
            task=task, 
            llm=llm,
            browser=browser,
            save_conversation_path=str(output_dir / "conversation.json")
        )
        
        logger.info("Running Agent...")
        await agent.run()
        
        logger.info("Agent test successful!")
        return True
    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'browser' in locals():
            await browser.close()

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
