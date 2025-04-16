"""
Agent-based test script for Naver Maps restaurant photos.

This script follows the simple.py structure to use the Agent model pattern
for navigating Naver Maps restaurant pages, finding photos, and interacting
with photo categories.
"""
import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult
from langchain_core.language_models.llms import Generation

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

NAVER_RESTAURANT_URL = "https://map.naver.com/p/search/%EB%B0%98%ED%8F%AC%EC%8B%9D%EC%8A%A4%20%EB%8D%95%EC%88%98%EA%B6%81%EC%A0%90/place/1188320878?c=15.00,0,0,0,dh&isCorrectAnswer=true"

class NaverMapsAgentLLM(BaseChatModel):
    """Mock LLM for testing Naver Maps restaurant photos navigation."""
    
    def __init__(self, max_steps=5):
        """Initialize the LLM with a step counter."""
        super().__init__()
        self._step_counter = 0
        self._max_steps = max_steps
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "naver_maps_agent_llm"
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response based on step counter."""
        self._step_counter += 1
        
        if self._step_counter == 1:
            content = f"""I'll help you navigate to the Naver Maps restaurant page.

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
```"""
        elif self._step_counter == 2:
            content = """I've navigated to the restaurant page. Now I'll look for the photo section.

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
```"""
        elif self._step_counter == 3:
            content = """I've found the photo section. Now I'll click on it.

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
```"""
        elif self._step_counter == 4:
            content = """I've clicked on the photo section. Now I'll look for the first photo.

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
```"""
        elif self._step_counter == 5:
            content = """I've found the photos. Now I'll click on the first one.

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
```"""
        elif self._step_counter == 6:
            content = """I've clicked on the first photo. Now I'll look for the photo category section.

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
```"""
        elif self._step_counter == 7:
            content = """I've found the interior photo category. Now I'll click on it.

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
```"""
        else:
            content = """I've completed the task successfully.

```json
{
  "current_state": {
    "evaluation_previous_goal": "Click on the interior photo category",
    "memory": "Successfully navigated through the Naver Maps restaurant photos",
    "next_goal": "Task completed"
  },
  "action": [
    {
      "finish": {
        "success": true,
        "message": "Successfully navigated to the restaurant page, found photos, clicked on the first photo, and selected the interior photo category"
      }
    }
  ]
}
```"""
        
        message = AIMessage(content=content)
        
        generations = [[Generation(text=message.content)]]
        return LLMResult(generations=generations)
    
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        """Generate a mock response asynchronously."""
        return self._generate(messages, stop, run_manager, **kwargs)
        
    def bind_tools(self, tools=None, tool_choice=None, **kwargs):
        """Mock implementation of bind_tools to avoid NotImplementedError."""
        return self
        
    def with_structured_output(self, schema, **kwargs):
        """Mock implementation of with_structured_output."""
        class StructuredLLM:
            def __init__(self, llm, schema):
                self.llm = llm
                self.schema = schema
                
            async def ainvoke(self, messages, **kwargs):
                logger.info(f"StructuredLLM.ainvoke called with parent step_counter={self.llm._step_counter}")
                self.llm._step_counter += 1
                
                if self.llm._step_counter > 10:
                    logger.info("Maximum steps reached, finishing task")
                    json_content = {
                        "current_state": {
                            "evaluation_previous_goal": "Maximum steps reached",
                            "memory": "Reached maximum number of steps",
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
                    parsed = self.schema(**json_content)
                    raw = AIMessage(content=str(json_content))
                    return {"parsed": parsed, "raw": raw}
                
                if self.llm._step_counter == 1:
                    json_content = {
                        "current_state": {
                            "evaluation_previous_goal": "Starting task",
                            "memory": "",
                            "next_goal": "Navigate to the restaurant page"
                        },
                        "action": [
                            {
                                "navigate_to": {
                                    "url": NAVER_RESTAURANT_URL
                                }
                            }
                        ]
                    }
                elif self.llm._step_counter == 2:
                    json_content = {
                        "current_state": {
                            "evaluation_previous_goal": "Navigate to the restaurant page",
                            "memory": "Successfully navigated to the Naver Maps restaurant page",
                            "next_goal": "Find and click on the photo section"
                        },
                        "action": [
                            {
                                "find_element_by_text": {
                                    "text": "사진",
                                    "exact_match": False
                                }
                            }
                        ]
                    }
                elif self.llm._step_counter == 3:
                    json_content = {
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
                elif self.llm._step_counter == 4:
                    json_content = {
                        "current_state": {
                            "evaluation_previous_goal": "Click on the photo section",
                            "memory": "Clicked on the photo section",
                            "next_goal": "Find and click on the first photo"
                        },
                        "action": [
                            {
                                "find_element_by_selector": {
                                    "selector": "img[alt*='사진']",
                                    "multiple": True
                                }
                            }
                        ]
                    }
                elif self.llm._step_counter == 5:
                    json_content = {
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
                elif self.llm._step_counter == 6:
                    json_content = {
                        "current_state": {
                            "evaluation_previous_goal": "Click on the first photo",
                            "memory": "Clicked on the first photo",
                            "next_goal": "Find the photo category section"
                        },
                        "action": [
                            {
                                "find_element_by_text": {
                                    "text": "내부",
                                    "exact_match": False
                                }
                            }
                        ]
                    }
                elif self.llm._step_counter == 7:
                    json_content = {
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
                else:
                    json_content = {
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
                
                parsed = self.schema(**json_content)
                
                raw = AIMessage(content=str(json_content))
                
                return {"parsed": parsed, "raw": raw}
                
        return StructuredLLM(self, schema)

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

async def test_naver_maps_agent():
    """Test the Agent with Naver Maps restaurant photos navigation."""
    logger.info("Testing Agent with Naver Maps restaurant photos navigation...")
    
    try:
        browser = await setup_browser()
        
        llm = NaverMapsAgentLLM(max_steps=8)
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
        try:
            await agent.run()
            
            logger.info("Agent test successful!")
            return True
        except Exception as e:
            logger.error(f"Agent test failed with exception: {e}")
            traceback.print_exc()
            return False
        finally:
            await browser.close()
    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Main function to run the Naver Maps Agent test."""
    logger.info("Starting Naver Maps Agent test...")
    
    agent_success = await test_naver_maps_agent()
    
    if agent_success:
        logger.info("Naver Maps Agent test passed!")
    else:
        logger.error("Naver Maps Agent test failed!")

if __name__ == '__main__':
    asyncio.run(main())
