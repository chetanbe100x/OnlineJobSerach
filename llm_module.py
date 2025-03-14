"""
LLM Interaction Module for the job search framework.
This module is responsible for interacting with various LLM models, 
including initializing models, formatting prompts, and processing responses.
"""

import os
import json
import requests
from transformers import pipeline
import config

class LLMHandler:
    """Handler for LLM interactions."""
    
    def __init__(self, model_type="llama3", api_key=None):
        """
        Initialize the LLM handler.
        
        Args:
            model_type (str): The type of LLM model to use.
            api_key (str, optional): API key for the LLM service, if needed.
        """
        self.model_type = model_type
        self.api_key = api_key
        self.model = None
        self.initialize_model()
        
    def initialize_model(self):
        """
        Initialize the selected LLM model based on the model type.
        """
        model_config = config.SUPPORTED_MODELS.get(self.model_type)
        
        if not model_config:
            raise ValueError(f"Unsupported model type: {self.model_type}")
            
        if model_config["type"] == "ollama":
            # Check if Ollama is installed and running
            try:
                # Try to ping Ollama server
                response = requests.get("http://localhost:11434/api/version")
                if response.status_code != 200:
                    raise ConnectionError("Ollama server is not running")
                print(f"Successfully connected to Ollama server")
            except Exception as e:
                print(f"Error connecting to Ollama server: {str(e)}")
                print("Please make sure Ollama is installed and running")
            
            # For Ollama models, we don't need to initialize anything else here
            # We'll use the Ollama API directly when we need to generate text
            self.model = model_config["model_name"]
            
        elif model_config["type"] == "huggingface":
            # Initialize Hugging Face model
            try:
                self.model = pipeline(
                    "text-generation",
                    model=model_config["model_name"],
                    max_length=2048
                )
                print(f"Successfully loaded {model_config['name']} from Hugging Face")
            except Exception as e:
                print(f"Error loading Hugging Face model: {str(e)}")
                print("Falling back to default model")
                # Fall back to default
                self.model_type = "llama3"
                self.initialize_model()
        
        else:
            raise ValueError(f"Unsupported model type: {model_config['type']}")
    
    def generate_text(self, prompt, max_tokens=500):
        """
        Generate text using the LLM based on the given prompt.
        
        Args:
            prompt (str): The prompt to send to the LLM.
            max_tokens (int, optional): Maximum number of tokens to generate.
            
        Returns:
            str: The generated text.
        """
        model_config = config.SUPPORTED_MODELS.get(self.model_type)
        
        if model_config["type"] == "ollama":
            # Use Ollama API for text generation
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens
                        }
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("response", "")
                else:
                    print(f"Error from Ollama API: {response.text}")
                    return "Error generating response from LLM."
                    
            except Exception as e:
                print(f"Error with Ollama API: {str(e)}")
                return "Error connecting to Ollama API."
                
        elif model_config["type"] == "huggingface":
            # Use Hugging Face pipeline for text generation
            try:
                result = self.model(
                    prompt,
                    max_length=len(prompt.split()) + max_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
                
                generated_text = result[0]["generated_text"]
                # Extract only the newly generated part
                new_text = generated_text[len(prompt):]
                return new_text
                
            except Exception as e:
                print(f"Error generating text with Hugging Face: {str(e)}")
                return "Error generating response from LLM."
        
        return "Unsupported model type."
    
    def find_career_url(self, company_name):
        """
        Use the LLM to suggest the most likely career page URL for a company.
        
        Args:
            company_name (str): The name of the company.
            
        Returns:
            str: The suggested career page URL.
        """
        prompt = config.PROMPTS["url_finder"].format(company=company_name)
        response = self.generate_text(prompt, max_tokens=100).strip()
        
        # Clean up the response to ensure it's a valid URL
        if not response.startswith("http"):
            response = "https://" + response
        
        return response
    
    def refine_search_query(self, company_name, keywords):
        """
        Use the LLM to refine the search query based on the company and keywords.
        
        Args:
            company_name (str): The name of the company.
            keywords (str): The original search keywords.
            
        Returns:
            str: The refined search query.
        """
        prompt = config.PROMPTS["query_refiner"].format(
            company=company_name, 
            keywords=keywords
        )
        response = self.generate_text(prompt, max_tokens=200).strip()
        
        # If the response is empty or an error occurred, return the original keywords
        if not response or "error" in response.lower():
            return keywords
            
        return response
    
    def extract_jobs_from_html(self, company_name, keywords, html_content):
        """
        Use the LLM to extract relevant job listings from HTML content.
        
        Args:
            company_name (str): The name of the company.
            keywords (str): The search keywords.
            html_content (str): The HTML content to analyze.
            
        Returns:
            list: A list of job listings (dictionaries).
        """
        # Limit the HTML content to avoid exceeding token limits
        html_content = html_content[:50000]  # Use a reasonable limit
        
        prompt = config.PROMPTS["job_extractor"].format(
            company=company_name,
            keywords=keywords
        ) + "\n\nHTML content:\n" + html_content
        
        response = self.generate_text(prompt, max_tokens=1000).strip()
        
        try:
            # Try to parse the response as JSON
            # Find the first [ and last ] to extract just the JSON array
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            
            if start_idx == -1 or end_idx == 0:
                # If no JSON array is found, check if it's a valid JSON object
                jobs_data = json.loads(response)
            else:
                # Extract and parse the JSON array
                json_str = response[start_idx:end_idx]
                jobs_data = json.loads(json_str)
            
            # Ensure jobs_data is a list
            if isinstance(jobs_data, dict):
                jobs_data = [jobs_data]
                
            return jobs_data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing job data from LLM response: {str(e)}")
            print(f"Raw response: {response}")
            return []