"""
Agent-based test script for Naver Maps restaurant photos using the simple.py pattern.

This script follows the exact structure of simple.py to ensure compatibility.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

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
    cdp_url=f"http://localhost:{cdp_port}" if cdp_port else None
)
browser = Browser(config=browser_config)

task = '''
Navigate to this Naver Maps restaurant page: https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true

Then complete these steps:
1. Find and click on the "사진" (photos) section
2. Wait for the photos to load
3. Click on the first photo in the grid
4. Verify that the photo viewer opens
5. Look for category options like "내부" (interior) or "외부" (exterior)
6. Take screenshots at each step to document the process
'''

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage

class MockLLM(BaseChatModel):
    """Mock LLM for testing purposes."""
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response."""
        if not hasattr(self, "_step"):
            self._step = 0
        
        self._step += 1
        step = self._step
        
        if step == 1:
            content = """I'll help you navigate to the Naver Maps restaurant page and interact with photos.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Starting task",
    "memory": "",
    "next_goal": "Navigate to the restaurant page"
  },
  "action": [
    {
      "navigate_to": {
        "url": "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"
      }
    }
  ]
}
```"""
        elif step == 2:
            content = """Now I'll find and click on the "사진" (photos) section.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Successfully navigated to the restaurant page",
    "memory": "The page has loaded and shows restaurant information",
    "next_goal": "Find and click on the photos section"
  },
  "action": [
    {
      "execute_javascript": {
        "code": "(function() { const elements = Array.from(document.querySelectorAll('*')); const photoButton = elements.find(el => el.textContent && el.textContent.includes('사진') && el.offsetWidth > 0 && el.offsetHeight > 0); if (photoButton) { photoButton.click(); return true; } return false; })();"
      }
    }
  ]
}
```"""
        elif step == 3:
            content = """Now I'll click on the first photo in the grid.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Successfully clicked on the photos section",
    "memory": "The photos grid is now visible",
    "next_goal": "Click on the first photo in the grid"
  },
  "action": [
    {
      "execute_javascript": {
        "code": "(function() { const images = Array.from(document.querySelectorAll('img')); const photoImg = images.find(img => img.offsetWidth > 50 && img.offsetHeight > 50 && (img.src.includes('pstatic.net') || img.src.includes('static.naver.net'))); if (photoImg) { photoImg.click(); return true; } return false; })();"
      }
    }
  ]
}
```"""
        elif step == 4:
            content = """Now I'll look for category options like "내부" (interior) or "외부" (exterior).

```json
{
  "current_state": {
    "evaluation_previous_goal": "Successfully clicked on the first photo",
    "memory": "The photo viewer is now open",
    "next_goal": "Look for category options"
  },
  "action": [
    {
      "execute_javascript": {
        "code": "(function() { const buttons = Array.from(document.querySelectorAll('button, [role=\"tab\"], [role=\"button\"], .tab, li')); for (const btn of buttons) { if (btn.textContent && (btn.textContent.includes('내부') || btn.textContent.includes('외부')) && btn.offsetWidth > 0 && btn.offsetHeight > 0) { console.log('Found category button:', btn.textContent); btn.click(); return true; } } return false; })();"
      }
    }
  ]
}
```"""
        elif step == 5:
            content = """Now I'll take a screenshot to document the final state.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Successfully found category options",
    "memory": "The photo viewer shows category options",
    "next_goal": "Take a screenshot to document the process"
  },
  "action": [
    {
      "take_screenshot": {
        "path": "/tmp/naver_agent_test_simple/final_state.png"
      }
    }
  ]
}
```"""
        else:
            content = """I've completed all the requested steps.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Successfully took screenshots",
    "memory": "Completed all steps: navigated to restaurant page, found photos section, clicked first photo, found category options, and took screenshots",
    "next_goal": "Task complete"
  },
  "action": [
    {
      "done": {}
    }
  ]
}
```"""
        
        return AIMessage(content=content)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)

llm = MockLLM()


output_dir = Path("/tmp/naver_agent_test_simple")
output_dir.mkdir(exist_ok=True)

agent = Agent(
    task=task, 
    llm=llm,
    browser=browser,
    save_conversation_path=str(output_dir / "conversation.json")
)

async def main():
    try:
        await agent.run()
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        
        if hasattr(browser, 'context') and browser.context:
            await browser.context.take_screenshot(path=str(output_dir / "error.png"))
    finally:
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
