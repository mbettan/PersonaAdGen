# bettan_agent/debug_image_handler.py
"""
Debug script to test and understand the ADK image handling mechanism
"""

from typing import Dict
from google.adk.tools import ToolContext

def debug_save_image(tool_context: ToolContext) -> Dict[str, str]:
    """
    Debug version of save_image_as_artifact to understand the structure
    """
    result = {
        "status": "debug",
        "tool_context_attributes": [],
        "prompt_info": None,
        "image_found": False
    }
    
    # List all attributes of tool_context
    result["tool_context_attributes"] = dir(tool_context)
    
    # Check prompt structure
    if hasattr(tool_context, 'prompt'):
        prompt = tool_context.prompt
        result["prompt_info"] = {
            "type": str(type(prompt)),
            "has_parts": hasattr(prompt, 'parts'),
            "is_list": isinstance(prompt, list),
            "attributes": dir(prompt) if prompt else []
        }
        
        # If prompt has parts, examine them
        if hasattr(prompt, 'parts'):
            parts_info = []
            for i, part in enumerate(prompt.parts):
                part_info = {
                    "index": i,
                    "type": str(type(part)),
                    "has_mime_type": hasattr(part, 'mime_type'),
                    "mime_type": getattr(part, 'mime_type', None),
                    "attributes": dir(part)[:10]  # First 10 attributes
                }
                parts_info.append(part_info)
                
                # Check if this is an image
                if hasattr(part, 'mime_type') and part.mime_type and 'image' in str(part.mime_type):
                    result["image_found"] = True
                    result["image_part_index"] = i
                    
            result["parts_info"] = parts_info
    
    # Check for other potential image locations
    if hasattr(tool_context, 'messages'):
        result["has_messages"] = True
        result["messages_count"] = len(tool_context.messages) if hasattr(tool_context.messages, '__len__') else "unknown"
    
    if hasattr(tool_context, 'history'):
        result["has_history"] = True
        result["history_count"] = len(tool_context.history) if hasattr(tool_context.history, '__len__') else "unknown"
    
    if hasattr(tool_context, 'current_message'):
        result["has_current_message"] = True
        
    # Check state functionality
    if hasattr(tool_context, 'state'):
        result["has_state"] = True
        result["state_type"] = str(type(tool_context.state))
        try:
            if hasattr(tool_context.state, 'keys') and callable(getattr(tool_context.state, 'keys', None)):
                result["state_keys"] = list(tool_context.state.keys())
            else:
                result["state_keys"] = []
        except Exception:
            result["state_keys"] = []
    
    # Check save_artifact functionality
    if hasattr(tool_context, 'save_artifact'):
        result["has_save_artifact"] = True
        
    return result


def inspect_image_part(part) -> Dict:
    """
    Detailed inspection of a part that might be an image
    """
    info = {
        "type": str(type(part)),
        "attributes": dir(part),
        "mime_type": None,
        "has_data": False,
        "data_attributes": []
    }
    
    if hasattr(part, 'mime_type'):
        info["mime_type"] = str(part.mime_type)
    
    # Check for various data attributes
    data_attrs = ['data', 'blob', 'inline_data', 'file_data', 'content', 'bytes']
    for attr in data_attrs:
        if hasattr(part, attr):
            info["has_data"] = True
            info["data_attributes"].append(attr)
            
    return info
