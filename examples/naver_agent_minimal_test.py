"""
Minimal Agent-based test script for Naver Maps restaurant photos.

This script follows the exact structure of simple.py to ensure compatibility.
"""
import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

from browser_use import Agent

load_dotenv()

class MockLLM(BaseChatModel):
    """Mock LLM for testing purposes."""
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response."""
        return AIMessage(content="""I'll help you navigate to the Naver Maps restaurant page.

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
```""")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)

llm = MockLLM()

task = 'Go to https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true and find photos'

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
        print(f"Detected CDP port: {cdp_port}")
except Exception as e:
    print(f"Could not detect CDP port: {e}")

from browser_use.browser.browser import Browser, BrowserConfig
browser_config = BrowserConfig(
    headless=True,
    cdp_url=f"http://localhost:{cdp_port}" if cdp_port else None
)
browser = Browser(config=browser_config)

agent = Agent(task=task, llm=llm, browser=browser)

async def main():
    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())
