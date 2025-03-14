"""
Configuration and utility module for the job search framework.
This module contains various configuration settings and utility functions used across the application.
"""

# Default LLM model
DEFAULT_LLM_MODEL = "llama3"

# Dictionary of supported LLM models
SUPPORTED_MODELS = {
    "llama3": {
        "name": "LLAMA 3.3 70B (via Ollama)",
        "type": "ollama",
        "model_name": "llama3.3"
    },
    "mistral": {
        "name": "Mistral 7B (via Hugging Face)",
        "type": "huggingface",
        "model_name": "mistralai/Mistral-7B-v0.1"
    }
}

# Maximum number of jobs to display
MAX_JOBS_TO_DISPLAY = 10

# User agent for HTTP requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Common career page patterns
CAREER_PAGE_PATTERNS = [
    "{company}.com/careers",
    "{company}.com/jobs",
    "{company}.com/work-with-us",
    "{company}.com/join-us",
    "{company}.com/employment",
    "{company}.com/about/careers",
    "{company}.com/about/jobs",
    "careers.{company}.com",
    "jobs.{company}.com"
]

# LLM prompts
PROMPTS = {
    "url_finder": """
    I need to find the careers or jobs page for {company}. 
    Based on your knowledge, what would be the most likely URL for their careers page?
    Provide only the URL without any explanation or additional text.
    """,
    
    "query_refiner": """
    I want to search for jobs at {company} with these keywords: {keywords}.
    Can you help refine these keywords into a more effective search query?
    Provide only the refined query without any explanation or additional text.
    """,
    
    "job_extractor": """
    Analyze the following HTML content from {company}'s career page and extract job listings relevant to these keywords: {keywords}.
    For each relevant job, provide the following information in JSON format:
    1. title: The job title
    2. description: A brief description or snippet from the job posting
    3. url: The URL or link to the full job posting (if available)
    4. location: The job location (if available)
    5. relevance_score: A score from 1-10 indicating how relevant this job is to the keywords

    Return only the JSON array without any additional explanation or text.
    """
}

def construct_career_urls(company_name):
    """
    Construct potential career page URLs based on the company name.
    
    Args:
        company_name (str): The name of the company.
        
    Returns:
        list: A list of potential career page URLs.
    """
    company_name = company_name.lower().replace(" ", "")
    urls = []
    
    for pattern in CAREER_PAGE_PATTERNS:
        url = pattern.format(company=company_name)
        if not url.startswith("http"):
            url = "https://" + url
        urls.append(url)
    
    return urls

def clean_text(text):
    """
    Clean and normalize text by removing extra whitespace.
    
    Args:
        text (str): The text to clean.
        
    Returns:
        str: The cleaned text.
    """
    if not text:
        return ""
    return " ".join(text.split())