"""
Job Extractor module for extracting job listings from company career pages.
This module provides functions to scrape and process job listings.
"""
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from llm_manager import query_model
import logging
import json
import re

logger = logging.getLogger(__name__)

def extract_jobs(
    career_page_url: str,
    keywords: str,
    model_name: str,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract job listings from a company's career page that match the given keywords.
    
    Args:
        career_page_url: URL of the company's career page
        keywords: Keywords to filter job listings
        model_name: Name of the LLM model to use
        api_key: API key for the model (if required)
    
    Returns:
        List of job listings that match the keywords
    """
    logger.info(f"Extracting jobs from {career_page_url} with keywords: {keywords}")
    
    # Fetch the career page content
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(career_page_url, headers=headers, timeout=10)
        response.raise_for_status()
        page_content = response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching career page: {str(e)}")
        return []
    
    # Extract raw job listings
    raw_listings = _extract_raw_listings(page_content, career_page_url)
    
    if not raw_listings:
        logger.warning(f"No job listings found on {career_page_url}")
        return []
    
    # Process raw listings to extract structured information
    structured_listings = _process_listings(raw_listings, model_name, api_key)
    
    # Filter listings based on keywords
    if keywords:
        filtered_listings = _filter_by_keywords(structured_listings, keywords, model_name, api_key)
    else:
        filtered_listings = structured_listings
    
    logger.info(f"Found {len(filtered_listings)} matching job listings")
    return filtered_listings

def _extract_raw_listings(page_content: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Extract raw job listings from the HTML content of the career page.
    
    Args:
        page_content: HTML content of the career page
        base_url: Base URL of the career page for resolving relative URLs
    
    Returns:
        List of raw job listings with HTML content and URLs
    """
    soup = BeautifulSoup(page_content, 'html.parser')
    raw_listings = []
    
    # Common job listing selectors
    common_selectors = [
        '.job-card', '.job-listing', '.career-opportunity', '.job-opening',
        'div[class*="job"]', 'div[class*="career"]', 'li[class*="job"]',
        'div[class*="position"]', '.careers-list li', '.job-search-results li',
        '.jobs-grid article', '.job-grid-item'
    ]
    
    # Try each selector until we find job listings
    job_elements = []
    for selector in common_selectors:
        job_elements = soup.select(selector)
        if job_elements:
            logger.info(f"Found {len(job_elements)} job elements using selector: {selector}")
            break
    
    # If no job elements found with common selectors, try to find job tables
    if not job_elements:
        job_tables = soup.select('table:has(tr:has(a[href*="job"]), tr:has(a[href*="career"]))') 
        if job_tables:
            for table in job_tables:
                job_elements.extend(table.find_all('tr')[1:])  # Skip header row
    
    # If still no results, try to use the LLM to identify potential job listings
    if not job_elements:
        logger.info("No job elements found using selectors, trying to identify URLs")
        
        # Find potential job listing URLs
        job_links = _find_job_listing_links(soup, base_url)
        
        # Create pseudo elements from links
        for link in job_links:
            job_elements.append(link.parent)
    
    # Process each job element
    for element in job_elements:
        # Extract title
        title_element = element.select_one('h2, h3, h4, .title, .position, strong, b, a')
        title = title_element.get_text().strip() if title_element else "Unknown Position"
        
        # Extract URL
        url_element = element.select_one('a')
        url = url_element.get('href') if url_element else None
        
        # Resolve relative URLs
        if url and not url.startswith(('http://', 'https://')):
            url = base_url.rstrip('/') + '/' + url.lstrip('/')
        
        # Extract content
        content = element.get_text().strip()
        
        raw_listings.append({
            'title': title,
            'url': url,
            'content': content,
            'html': str(element)
        })
    
    return raw_listings

def _find_job_listing_links(soup: BeautifulSoup, base_url: str) -> List:
    """
    Find potential job listing links in the page.
    
    Args:
        soup: BeautifulSoup object of the career page
        base_url: Base URL of the career page
    
    Returns:
        List of potential job listing link elements
    """
    job_related_terms = ['job', 'career', 'position', 'apply', 'vacancy']
    potential_links = []
    
    # Find links that might be job listings
    for link in soup.find_all('a', href=True):
        link_text = link.get_text().lower()
        link_href = link['href'].lower()
        
        # Check if link text or href contains job-related terms
        if any(term in link_text or term in link_href for term in job_related_terms):
            if not link_href.startswith(('#', 'mailto:', 'tel:')):
                potential_links.append(link)
    
    return potential_links

def _process_listings(
    raw_listings: List[Dict[str, Any]],
    model_name: str,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process raw job listings to extract structured information using LLM.
    
    Args:
        raw_listings: List of raw job listings
        model_name: Name of the LLM model to use
        api_key: API key for the model (if required)
    
    Returns:
        List of structured job listings
    """
    structured_listings = []
    
    for raw_listing in raw_listings:
        # Skip listings with very little content
        if len(raw_listing['content']) < 20:
            continue
            
        prompt = f"""
        Extract the following information from this job listing:
        1. Job Title
        2. Location
        3. Job Description (brief)
        4. Requirements
        5. Experience Level

        Job Listing:
        {raw_listing['content'][:2000]}  # Limit content length to avoid token limits

        Format your response as a JSON object with these fields: 
        {{
            "title": "extracted title", 
            "location": "extracted location", 
            "description": "brief description", 
            "requirements": "key requirements", 
            "experience_level": "senior/mid/junior/etc"
        }}
        Only return the JSON object, nothing else.
        """
        
        try:
            response = query_model(model_name, prompt, api_key)
            
            # Try to parse the response as JSON
            try:
                extracted_data = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON-like content using regex
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    try:
                        extracted_data = json.loads(match.group(0))
                    except json.JSONDecodeError:
                        # Fall back to basic extraction
                        extracted_data = _extract_basic_info(raw_listing)
                else:
                    extracted_data = _extract_basic_info(raw_listing)
            
            # Create structured listing
            structured_listing = {
                'title': extracted_data.get('title') or raw_listing['title'],
                'url': raw_listing['url'],
                'company': extracted_data.get('company', ''),
                'location': extracted_data.get('location', 'Not specified'),
                'description': extracted_data.get('description', 'No description available'),
                'requirements': extracted_data.get('requirements', 'Not specified'),
                'experience_level': extracted_data.get('experience_level', 'Not specified')
            }
            
            structured_listings.append(structured_listing)
            
        except Exception as e:
            logger.error(f"Error processing job listing: {str(e)}")
            # Add basic listing information as fallback
            structured_listings.append({
                'title': raw_listing['title'],
                'url': raw_listing['url'],
                'description': raw_listing['content'][:500] + '...' if len(raw_listing['content']) > 500 else raw_listing['content']
            })
    
    return structured_listings

def _extract_basic_info(raw_listing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract basic information from a raw job listing without using LLM.
    
    Args:
        raw_listing: Raw job listing data
    
    Returns:
        Dictionary with basic extracted information
    """
    content = raw_listing['content']
    
    # Try to extract location using common patterns
    location_match = re.search(r'Location:?\s*([^,\n]+(?:,\s*[^,\n]+)?)', content)
    location = location_match.group(1) if location_match else 'Not specified'
    
    # Try to extract experience level
    experience_patterns = [
        r'(\d+-\d+)\s+years',
        r'(Senior|Junior|Mid|Entry[- ]Level|Principal|Lead)',
        r'Experience:?\s*(\w+)'
    ]
    
    experience_level = 'Not specified'
    for pattern in experience_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            experience_level = match.group(1)
            break
    
    return {
        'title': raw_listing['title'],
        'location': location,
        'description': content[:300] + '...' if len(content) > 300 else content,
        'requirements': 'Not specified',
        'experience_level': experience_level
    }

def _filter_by_keywords(
    listings: List[Dict[str, Any]],
    keywords: str,
    model_name: str,
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter job listings based on keywords using LLM.
    
    Args:
        listings: List of structured job listings
        keywords: Keywords to filter by
        model_name: Name of the LLM model to use
        api_key: API key for the model (if required)
    
    Returns:
        Filtered list of job listings that match the keywords
    """
    filtered_listings = []
    keywords_list = [k.strip().lower() for k in keywords.split(',')]
    
    for listing in listings:
        # Basic keyword matching first
        listing_text = f"{listing['title']} {listing['description']} {listing['requirements']}".lower()
        basic_match = any(keyword in listing_text for keyword in keywords_list)
        
        if basic_match:
            filtered_listings.append(listing)
            continue
        
        # Use LLM for more advanced matching if basic matching fails
        listing_text = f"""
        Title: {listing['title']}
        Description: {listing['description']}
        Requirements: {listing['requirements']}
        """
        
        prompt = f"""
        Determine if this job posting matches the following keywords: {keywords}
        
        Job Posting:
        {listing_text}
        
        Respond with either "yes" or "no".
        """
        
        try:
            response = query_model(model_name, prompt, api_key)
            if response.strip().lower() == 'yes':
                filtered_listings.append(listing)
        except Exception as e:
            logger.error(f"Error filtering job listing: {str(e)}")
    
    return filtered_listings