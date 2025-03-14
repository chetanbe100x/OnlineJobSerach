"""
Web Scraping Module for the job search framework.
This module is responsible for fetching and parsing content from company career pages.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import config

class WebScraper:
    """Web scraper for job listings on company career pages."""
    
    def __init__(self):
        """Initialize the web scraper with default headers."""
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def fetch_page(self, url, timeout=10):
        """
        Fetch the content of a web page.
        
        Args:
            url (str): The URL to fetch.
            timeout (int, optional): Request timeout in seconds.
            
        Returns:
            tuple: (status_code, content) where status_code is the HTTP status code
                  and content is the page content.
        """
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=timeout
            )
            return response.status_code, response.text
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None, None
    
    def test_career_urls(self, company_name):
        """
        Test multiple potential career page URLs to find a working one.
        
        Args:
            company_name (str): The name of the company.
            
        Returns:
            str: The first working career page URL, or None if none work.
        """
        potential_urls = config.construct_career_urls(company_name)
        
        for url in potential_urls:
            print(f"Testing URL: {url}")
            status_code, _ = self.fetch_page(url, timeout=5)
            
            if status_code == 200:
                print(f"Found working URL: {url}")
                return url
            
            # Add a small delay to avoid aggressive scraping
            time.sleep(random.uniform(0.5, 1.5))
        
        return None
    
    def search_jobs(self, url, keywords, llm_handler=None):
        """
        Search for jobs on a career page based on keywords.
        
        Args:
            url (str): The career page URL.
            keywords (str): The search keywords.
            llm_handler (LLMHandler, optional): An LLM handler for extracting job listings.
            
        Returns:
            list: A list of job listings.
        """
        status_code, content = self.fetch_page(url)
        
        if status_code != 200 or not content:
            print(f"Failed to fetch content from {url}")
            return []
        
        # Use LLM to extract jobs if an LLM handler is provided
        if llm_handler:
            # Extract the company name from the URL
            # This is a simple heuristic and may not always be accurate
            company_name = url.split("//")[1].split(".")[0]
            if company_name == "www":
                company_name = url.split("//")[1].split(".")[1]
            
            jobs = llm_handler.extract_jobs_from_html(company_name, keywords, content)
            return jobs
        
        # Fallback to basic parsing if no LLM handler is provided
        return self._basic_job_extraction(content, keywords)
    
    def _basic_job_extraction(self, html_content, keywords):
        """
        Basic extraction of job listings from HTML content using BeautifulSoup.
        This is a fallback method if LLM extraction fails.
        
        Args:
            html_content (str): The HTML content to parse.
            keywords (str): The search keywords.
            
        Returns:
            list: A list of job listings.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        jobs = []
        
        # Look for common job listing patterns
        # This is a simplified approach and may not work for all career pages
        
        # Method 1: Look for job cards/divs
        job_elements = soup.find_all(['div', 'article', 'section'], 
                                  class_=lambda c: c and any(term in c.lower() 
                                                        for term in ['job', 'position', 'opening', 'career', 'listing']))
        
        # Method 2: Look for job titles in headings
        if not job_elements:
            job_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'], 
                                       class_=lambda c: c and any(term in c.lower() 
                                                             for term in ['job', 'position', 'title']))
        
        # Method 3: Look for links that might be job listings
        if not job_elements:
            job_elements = soup.find_all('a', 
                                      href=lambda h: h and any(term in h.lower() 
                                                         for term in ['job', 'career', 'position', 'apply']))
        
        # Process the found elements
        for element in job_elements[:config.MAX_JOBS_TO_DISPLAY]:
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or element
            
            # Get the job title
            title = config.clean_text(title_element.get_text())
            
            # Get the job description (if available)
            description_element = element.find(['p', 'div'], 
                                            class_=lambda c: c and any(term in c.lower() 
                                                                  for term in ['desc', 'summary', 'detail']))
            description = config.clean_text(description_element.get_text()) if description_element else ""
            
            # Get the job URL
            url = None
            link_element = element.find('a') if element.name != 'a' else element
            if link_element and link_element.has_attr('href'):
                url = link_element['href']
                # Convert relative URLs to absolute
                if url.startswith('/'):
                    base_url = "/".join(url.split('/')[:3])
                    url = base_url + url
            
            # Check if the job matches any of the keywords
            keywords_list = keywords.lower().split()
            relevance_score = sum(1 for kw in keywords_list 
                                if kw in title.lower() or kw in description.lower())
            
            # Only include jobs with some relevance
            if relevance_score > 0:
                jobs.append({
                    'title': title,
                    'description': description[:200] + '...' if len(description) > 200 else description,
                    'url': url,
                    'location': '',  # This would require more sophisticated parsing
                    'relevance_score': min(10, relevance_score * 2)  # Scale up to max 10
                })
        
        return jobs