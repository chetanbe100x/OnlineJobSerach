"""
LLM Manager module for handling Large Language Model integrations.
This module provides functions to interact with various LLM models.
"""
from typing import List, Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)

# List of available free models
FREE_MODELS = {
    "huggingface/gpt2": {
        "requires_api_key": False,
        "max_tokens": 1024,
        "description": "HuggingFace's GPT-2 model"
    },
    "huggingface/distilbert": {
        "requires_api_key": False,
        "max_tokens": 512,
        "description": "HuggingFace's DistilBERT model"
    },
    "huggingface/t5-small": {
        "requires_api_key": False,
        "max_tokens": 512,
        "description": "HuggingFace's T5-small model"
    },
    "huggingface/roberta-base": {
        "requires_api_key": False,
        "max_tokens": 512,
        "description": "HuggingFace's RoBERTa model"
    },
    "openai/gpt-3.5-turbo": {
        "requires_api_key": True,
        "max_tokens": 4096,
        "description": "OpenAI's GPT-3.5 Turbo model (requires API key)"
    }
}

def get_available_models() -> List[str]:
    """
    Get a list of available LLM models.
    
    Returns:
        List of model identifiers
    """
    return list(FREE_MODELS.keys())

def is_api_key_required(model_name: str) -> bool:
    """
    Check if the selected model requires an API key.
    
    Args:
        model_name: Name of the model to check
    
    Returns:
        True if the model requires an API key, False otherwise
    """
    if model_name in FREE_MODELS:
        return FREE_MODELS[model_name]["requires_api_key"]
    return False

def query_model(
    model_name: str,
    prompt: str,
    api_key: Optional[str] = None,
    max_tokens: int = 100
) -> str:
    """
    Query the specified LLM model with the given prompt.
    
    Args:
        model_name: Name of the model to query
        prompt: The prompt to send to the model
        api_key: API key for the model (if required)
        max_tokens: Maximum number of tokens to generate
    
    Returns:
        Generated text response from the model
    
    Raises:
        ValueError: If the model requires an API key and none is provided
        RuntimeError: If there's an error querying the model
    """
    if is_api_key_required(model_name) and not api_key:
        raise ValueError(f"Model {model_name} requires an API key")
    
    logger.info(f"Querying model {model_name} with prompt: {prompt[:50]}...")
    
    # HuggingFace models
    if model_name.startswith("huggingface/"):
        return _query_huggingface(model_name.split("/")[1], prompt, max_tokens)
    
    # OpenAI models
    elif model_name.startswith("openai/"):
        return _query_openai(model_name.split("/")[1], prompt, api_key, max_tokens)
    
    else:
        raise ValueError(f"Unsupported model: {model_name}")

def _query_huggingface(model_name: str, prompt: str, max_tokens: int) -> str:
    """
    Query a HuggingFace model using their Inference API.
    
    Args:
        model_name: Name of the HuggingFace model
        prompt: The prompt to send to the model
        max_tokens: Maximum number of tokens to generate
    
    Returns:
        Generated text response from the model
    
    Raises:
        RuntimeError: If there's an error querying the model
    """
    try:
        # In a real implementation, we'd use the HuggingFace Inference API or a local model
        # For this implementation, we'll use a simple API call to the free Inference API
        
        API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {"Authorization": "Bearer hf_demo"}  # Using demo token for free models
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_tokens,
                "temperature": 0.7
            }
        }
        
        # This is mock code - in a real implementation, we'd make an actual API call
        # response = requests.post(API_URL, headers=headers, json=payload)
        # response.raise_for_status()
        # return response.json()[0]["generated_text"]
        
        # For demonstration, return a mock response
        return f"[HuggingFace {model_name} response: Processed job data based on the prompt]"
        
    except Exception as e:
        logger.error(f"Error querying HuggingFace model: {str(e)}")
        raise RuntimeError(f"Error querying HuggingFace model: {str(e)}")

def _query_openai(model_name: str, prompt: str, api_key: str, max_tokens: int) -> str:
    """
    Query an OpenAI model using their API.
    
    Args:
        model_name: Name of the OpenAI model
        prompt: The prompt to send to the model
        api_key: OpenAI API key
        max_tokens: Maximum number of tokens to generate
    
    Returns:
        Generated text response from the model
    
    Raises:
        RuntimeError: If there's an error querying the model
    """
    try:
        # In a real implementation, we'd use the OpenAI API
        API_URL = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        # This is mock code - in a real implementation, we'd make an actual API call
        # response = requests.post(API_URL, headers=headers, json=payload)
        # response.raise_for_status()
        # return response.json()["choices"][0]["message"]["content"]
        
        # For demonstration, return a mock response
        return f"[OpenAI {model_name} response: Processed job data based on the prompt]"
        
    except Exception as e:
        logger.error(f"Error querying OpenAI model: {str(e)}")
        raise RuntimeError(f"Error querying OpenAI model: {str(e)}")