"""
Minimal Agent-based test script for Naver Maps restaurant photos.

This script follows the simple.py pattern exactly to use the browser-use Agent model.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockLLM(BaseChatModel):
    """Minimal mock LLM for testing."""
    
    @property
    def _llm_type(self) -> str:
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="""
        I'll help navigate to the Naver Maps restaurant page and interact with photos.
        
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
        """)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return self._generate(messages, stop, run_manager, **kwargs)

task = 'Navigate to this Naver Maps restaurant page: https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true and find the photos section'

llm = MockLLM()

async def main():
    agent = Agent(task=task, llm=llm)
    
    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())
