"""
Minimal Agent test script to isolate Pydantic schema validation issues.
"""
import os
import sys
import asyncio
import logging

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
        return AIMessage(content="Test response")
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        return self._generate(messages, stop, run_manager, **kwargs)

async def main():
    try:
        from browser_use.controller.registry.fix_schema import safe_model_json_schema
        
        from pydantic import BaseModel
        original_model_json_schema = BaseModel.model_json_schema
        
        def patched_model_json_schema(self, *args, **kwargs):
            try:
                return original_model_json_schema(self, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Schema generation error: {e}")
                return safe_model_json_schema(self.__class__)
        
        BaseModel.model_json_schema = patched_model_json_schema
        
        agent = Agent(
            task="Test task", 
            llm=MockLLM()
        )
        
        await agent.run()
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
