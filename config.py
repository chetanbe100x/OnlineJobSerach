"""
Configuration settings for the Job Search Agent.
"""

# Application settings
APP_TITLE = "AI Job Search Agent"
APP_DESCRIPTION = """
This application uses AI to search for job listings on company career pages.
Enter a company name and job keywords to find relevant positions.
"""

# Default settings
DEFAULT_MODEL = "huggingface/gpt2"
MAX_RESULTS = 20

# Request settings
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Job Search Agent/1.0"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Search settings
SEARCH_ENGINE_DELAY = 2  # seconds between searches to avoid rate limiting
SEARCH_TIMEOUT = 15  # seconds maximum for any single search request

# LLM settings
LLM_MAX_TOKENS = 1024
LLM_TEMPERATURE = 0.7

# Caching settings
ENABLE_CACHE = True
CACHE_EXPIRY = 3600  # seconds