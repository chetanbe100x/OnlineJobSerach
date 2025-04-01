"""
Search Engine module for discovering company career pages.
This module provides functions to find company career pages
using real web search engines and intelligent discovery methods.
"""
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
from llm_manager import query_model
import logging
from googlesearch import search
import re
import time
import random

logger = logging.getLogger(__name__)

def find_career_page(company_name: str, model_name: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Find the career page URL for the specified company using web search.
    
    Args:
        company_name: Name of the company
        model_name: Name of the LLM model to use
        api_key: API key for the model (if required)
    
    Returns:
        URL of the company's career page, or None if not found
    """
    logger.info(f"Finding career page for: {company_name}")
    
    # Try multiple methods to find the career page, prioritizing web search
    methods = [
        _google_search,
        _direct_url_construction,
        _llm_based_search
    ]
    
    for method in methods:
        url = method(company_name, model_name, api_key)
        if url:
            logger.info(f"Found career page for {company_name}: {url}")
            # Validate that the URL actually contains career information
            if validate_career_page(url):
                return url
    
    logger.warning(f"Could not find career page for {company_name}")
    return None

def _direct_url_construction(company_name: str, model_name: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Try to construct the career page URL directly using common patterns.
    
    Args:
        company_name: Name of the company
        model_name: Name of the LLM model (not used in this method)
        api_key: API key (not used in this method)
    
    Returns:
        Constructed URL if successful, None otherwise
    """
    # Clean company name for URL construction
    clean_name = company_name.lower().replace(" ", "").replace(",", "").replace(".", "")
    
    # Common career page URL patterns
    patterns = [
        f"https://{clean_name}.com/careers",
        f"https://{clean_name}.com/jobs",
        f"https://www.{clean_name}.com/careers",
        f"https://www.{clean_name}.com/jobs",
        f"https://{clean_name}.com/about/careers",
        f"https://careers.{clean_name}.com"
    ]
    
    # Try each pattern
    for url in patterns:
        try:
            logger.info(f"Trying URL pattern: {url}")
            response = requests.head(url, timeout=5)
            if response.status_code < 400:  # Any successful response
                return url
        except requests.RequestException:
            continue
    
    return None

def _google_search(company_name: str, model_name: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Use Google Search to find the company's career page.
    
    Args:
        company_name: Name of the company
        model_name: Name of the LLM model (not used in this method)
        api_key: API key (not used in this method)
    
    Returns:
        URL found from search results, or None if not found
    """
    search_queries = [
        f"{company_name} careers",
        f"{company_name} jobs",
        f"{company_name} career opportunities",
        f"{company_name} careers apply"
    ]
    
    try:
        logger.info(f"Searching web for {company_name} career page")
        
        for query in search_queries:
            # Use googlesearch-python to search for career pages
            # The search function returns an iterator of URLs
            results = search(
                query, 
                num_results=5,  # Limit to first 5 results
                lang="en",
                advanced=True  # Use advanced search features
            )
            
            # Add a small random delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 3.0))
            
            # Look through the results for likely career pages
            for url in results:
                logger.info(f"Evaluating search result: {url}")
                
                # Skip social media or review sites
                if any(site in url.lower() for site in ["linkedin", "glassdoor", "indeed", "facebook", "twitter"]):
                    continue
                
                # Check if URL contains career-related keywords
                if any(keyword in url.lower() for keyword in ["career", "job", "employ", "work", "join", "apply"]):
                    return url
                
                # If it's a company domain, check if it's a careers page
                company_domain = _extract_company_domain(company_name)
                if company_domain and company_domain in url.lower():
                    # Check the content of the page to see if it's careers-related
                    if is_career_page_content(url):
                        return url
            
        return None
    
    except Exception as e:
        logger.error(f"Error in Google search: {str(e)}")
        return None


def _extract_company_domain(company_name: str) -> Optional[str]:
    """
    Attempt to extract likely company domain from company name.
    
    Args:
        company_name: Name of the company
    
    Returns:
        Likely domain name or None
    """
    # Clean company name and return simplified domain
    domain = company_name.lower().replace(" ", "").replace(",", "").replace(".", "")
    return domain


def is_career_page_content(url: str) -> bool:
    """
    Check if a page's content is related to careers/jobs.
    
    Args:
        url: URL to check
    
    Returns:
        True if the page appears to be a career page
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check page title for career-related terms
        if soup.title:
            title_text = soup.title.get_text().lower()
            if any(term in title_text for term in ["career", "job", "employ", "work", "join", "apply"]):
                return True
        
        # Check main content for career-related terms
        content_text = soup.get_text().lower()
        career_terms = ["career", "job", "position", "opening", "vacancy", "apply", "join our team", "work with us"]
        
        if any(term in content_text for term in career_terms):
            # Check for multiple occurrences of job-related terms
            count = sum(content_text.count(term) for term in ["job", "career", "position", "apply"])
            if count >= 3:  # If these terms appear at least 3 times
                return True
        
        # Check for application forms or job listings
        if soup.find_all('form') and any(term in content_text for term in ["apply", "submit", "application"]):
            return True
            
        if len(soup.find_all(["table", "ul", "div"], class_=lambda c: c and any(term in str(c).lower() for term in ["job", "career", "position"]))) > 0:
            return True
            
        return False
    
    except Exception as e:
        logger.error(f"Error checking page content: {str(e)}")
        return False

def _llm_based_search(company_name: str, model_name: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Use an LLM to predict the most likely career page URL.
    
    Args:
        company_name: Name of the company
        model_name: Name of the LLM model to use
        api_key: API key for the model (if required)
    
    Returns:
        URL predicted by the LLM, or None if prediction fails
    """
    prompt = f"""
    What is the most likely URL for the careers or jobs page of {company_name}?
    Please provide only the full URL without any additional text or explanation.
    """
    
    try:
        logger.info(f"Using LLM to predict career page URL for {company_name}")
        response = query_model(model_name, prompt, api_key)
        
        # Extract URL from response (assuming the LLM returns just the URL)
        url = response.strip()
        
        # Basic validation of URL format
        if url.startswith(("http://", "https://")):
            # Verify the URL exists
            try:
                response = requests.head(url, timeout=5)
                if response.status_code < 400:
                    return url
            except requests.RequestException:
                pass
    
    except Exception as e:
        logger.error(f"Error in LLM-based search: {str(e)}")
    
    return None

def validate_career_page(url: str) -> bool:
    """
    Validate if a URL is likely a career page by checking for job-related keywords.
    
    Args:
        url: URL to validate
    
    Returns:
        True if the URL is likely a career page, False otherwise
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Keywords that suggest this is a career page
        job_keywords = ['job', 'career', 'position', 'opening', 'vacancy', 'employment', 'hiring', 'apply']
        
        # Check if any job keywords are present in the page text
        return any(keyword in page_text for keyword in job_keywords)
    
    except Exception as e:
        logger.error(f"Error validating career page: {str(e)}")
        return False