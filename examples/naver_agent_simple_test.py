"""
Simplified Agent-based test script for Naver Maps restaurant photos.

This script follows the simple.py pattern exactly to use the browser-use Agent model.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

load_dotenv()

class MockLLM(BaseChatModel):
    """Minimal mock LLM for testing."""
    
    @property
    def _llm_type(self) -> str:
        return "mock_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="I'll help navigate to the restaurant page.")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return self._generate(messages, stop, run_manager, **kwargs)

llm = MockLLM()

task = 'Navigate to this Naver Maps restaurant page: https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true and find the photos section'

agent = Agent(task=task, llm=llm)

async def main():
    await agent.run()

if __name__ == '__main__':
    asyncio.run(main())
