"""
Utility functions to handle JSON serialization issues with NumPy types
"""

import json
import numpy as np
from typing import Any, Dict, List, Union, Callable


class NumPyJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles NumPy types like int64, float32, etc.
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return super().default(obj)


def convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert NumPy types in a nested structure to Python standard types
    
    Args:
        obj: Object to convert (can be dict, list, or NumPy type)
        
    Returns:
        Object with all NumPy types converted to Python standard types
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj


def safe_json_dump(obj: Any, fp, indent: int = 2) -> None:
    """
    Safely dump an object to JSON, handling NumPy types
    
    Args:
        obj: Object to serialize
        fp: File-like object to write to
        indent: Indentation level
    """
    json.dump(convert_numpy_types(obj), fp, indent=indent)


def safe_json_dumps(obj: Any, indent: int = 2) -> str:
    """
    Safely convert an object to a JSON string, handling NumPy types
    
    Args:
        obj: Object to serialize
        indent: Indentation level
        
    Returns:
        JSON string representation
    """
    return json.dumps(convert_numpy_types(obj), indent=indent)