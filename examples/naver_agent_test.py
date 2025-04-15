"""
Agent-based test script for Naver Maps restaurant photos.

This script follows the simple.py pattern to use the browser-use Agent model to:
1. Navigate to a Naver Maps restaurant page
2. Find and click on photos
3. Click on the first photo
4. Verify the category frame is visible
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class MockLLM(BaseChatModel):
    """Mock LLM for testing purposes."""
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response."""
        response = """
        I'll help you navigate to the Naver Maps restaurant page and interact with photos.
        
        ```json
        {
          "current_state": "I need to navigate to the Naver Maps restaurant page",
          "actions": [
            {
              "action": "navigate_to",
              "params": {
                "url": "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"
              }
            }
          ]
        }
        ```
        """
        return AIMessage(content=response)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)

llm = MockLLM()

task = '''
Navigate to this Naver Maps restaurant page: https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true

Then:
1. Find and click on the "사진" (photos) section
2. Wait for the photos to load
3. Click on the first photo in the grid
4. Verify that the photo viewer opens
5. Look for category options like "내부" (interior) or "외부" (exterior)
6. Take screenshots at each step
'''

async def main():
    output_dir = Path("/tmp/naver_agent_test")
    output_dir.mkdir(exist_ok=True)
    
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
    
    agent = Agent(
        task=task, 
        llm=llm,
        browser=browser
    )
    
    try:
        await agent.run()
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
