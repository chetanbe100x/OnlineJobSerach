"""
Utilities module for common helper functions.
"""
import logging
from typing import Any, Dict, List, Optional
import json
import os
import time
import datetime

def setup_logging() -> logging.Logger:
    """
    Set up and configure logging for the application.
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('job_search_agent')
    logger.setLevel(logging.INFO)
    
    # Check if logger already has handlers to avoid duplicates
    if not logger.handlers:
        # Create console handler and set level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create file handler for logging to a file
        current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(f'logs/job_search_{current_time}.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def save_to_json(data: Any, filename: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filename: Name of the file to save to
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_from_json(filename: str) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        filename: Name of the file to load from
    
    Returns:
        Loaded data
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def rate_limit(calls_per_minute: int = 10) -> None:
    """
    Simple rate limiter to prevent overloading APIs.
    
    Args:
        calls_per_minute: Maximum API calls per minute
    """
    time.sleep(60 / calls_per_minute)

def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace newlines and multiple spaces with a single space
    cleaned = ' '.join(text.split())
    return cleaned

def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain name from a URL.
    
    Args:
        url: URL to extract domain from
    
    Returns:
        Domain name or None if extraction fails
    """
    if not url:
        return None
    
    try:
        # Remove protocol (http://, https://)
        domain = url.split('://')[-1]
        
        # Remove path, query parameters, etc.
        domain = domain.split('/')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception:
        return None

def generate_search_queries(company_name: str) -> List[str]:
    """
    Generate search queries for finding a company's career page.
    
    Args:
        company_name: Name of the company
    
    Returns:
        List of search queries
    """
    return [
        f"{company_name} careers",
        f"{company_name} jobs",
        f"{company_name} job openings",
        f"{company_name} job listings",
        f"{company_name} employment opportunities",
        f"{company_name} work with us"
    ]

def format_job_listing_for_export(listings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Format job listings for export to various formats.
    
    Args:
        listings: List of job listings
    
    Returns:
        Dictionary with formatted job listings
    """
    formatted_listings = []
    
    for listing in listings:
        formatted_listing = {
            'Title': listing.get('title', ''),
            'Company': listing.get('company', ''),
            'Location': listing.get('location', ''),
            'Description': listing.get('description', ''),
            'Requirements': listing.get('requirements', ''),
            'Experience Level': listing.get('experience_level', ''),
            'URL': listing.get('url', '')
        }
        formatted_listings.append(formatted_listing)
    
    return {'job_listings': formatted_listings}