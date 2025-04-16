"""
Minimal Agent test script to isolate Pydantic schema validation issues.
"""
import os
import sys
import asyncio
import logging
import inspect
from typing import Any, Dict, Type

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_use import Agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_model_json_schema(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Safely generate a JSON schema for a Pydantic model, handling inspect._empty annotations.
    
    Args:
        model_class: The Pydantic model class
        
    Returns:
        A JSON schema dictionary or a simplified schema if errors occur
    """
    try:
        instance = model_class()
        return instance.model_json_schema()
    except Exception as e:
        logger.warning(f"Schema generation error: {e}")
        return {
            "title": model_class.__name__,
            "type": "object",
            "properties": {
                field_name: {"type": "string", "description": "Parameter description unavailable"}
                for field_name in getattr(model_class, "__annotations__", {}).keys()
                if field_name != "__root__"
            }
        }

def patch_registry_service():
    """Apply the schema fix to the registry service."""
    try:
        from browser_use.controller.registry import service
        
        original_create_action_model = service.Registry.create_action_model
        
        def patched_create_action_model(self, *args, **kwargs):
            try:
                return original_create_action_model(self, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Error in create_action_model: {e}")
                from pydantic import create_model
                from browser_use.controller.registry.views import ActionModel
                return create_model('ActionModel', __base__=ActionModel)
        
        service.Registry.create_action_model = patched_create_action_model
        logger.info("Successfully patched Registry.create_action_model")
        
    except Exception as e:
        logger.error(f"Failed to patch registry service: {e}")

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
        patch_registry_service()
        
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
