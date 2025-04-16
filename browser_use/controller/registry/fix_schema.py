"""
Fix for Pydantic schema validation issues with inspect._empty class.
"""
import inspect
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

def safe_model_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Safely generate a JSON schema for a Pydantic model, handling inspect._empty annotations.
    
    Args:
        model: The Pydantic model class
        
    Returns:
        A JSON schema dictionary or a simplified schema if errors occur
    """
    try:
        return model.model_json_schema()
    except Exception as e:
        return {
            "title": model.__name__,
            "type": "object",
            "properties": {
                field_name: {"type": "string", "description": "Parameter description unavailable"}
                for field_name in model.__annotations__.keys()
                if field_name != "__root__"
            }
        }
