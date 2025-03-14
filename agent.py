"""
Agent Logic Module for the job search framework.
This module orchestrates the entire job search process.
"""

import time
from llm_module import LLMHandler
from web_scraper import WebScraper
import config

class JobSearchAgent:
    """Agent that orchestrates the job search process."""
    
    def __init__(self, model_type="llama3", api_key=None):
        """
        Initialize the job search agent.
        
        Args:
            model_type (str): The type of LLM model to use.
            api_key (str, optional): API key for the LLM service, if needed.
        """
        self.llm_handler = LLMHandler(model_type, api_key)
        self.web_scraper = WebScraper()
        self.status_messages = []
        
    def add_status(self, message):
        """
        Add a status message to track the agent's progress.
        
        Args:
            message (str): The status message to add.
        """
        self.status_messages.append(message)
        print(message)
        
    def get_status_messages(self):
        """
        Get all status messages.
        
        Returns:
            list: A list of status messages.
        """
        return self.status_messages
        
    def search_jobs(self, company_name, keywords):
        """
        Search for jobs based on the company name and keywords.
        
        Args:
            company_name (str): The name of the company.
            keywords (str): The search keywords.
            
        Returns:
            tuple: (jobs, status_messages) where jobs is a list of job listings
                  and status_messages is a list of status messages.
        """
        self.status_messages = []
        self.add_status(f"Starting job search for {company_name} with keywords: {keywords}")
        
        # Step 1: Refine the search query using the LLM
        self.add_status("Refining search query...")
        refined_keywords = self.llm_handler.refine_search_query(company_name, keywords)
        self.add_status(f"Refined query: {refined_keywords}")
        
        # Step 2: Find the company's career page
        self.add_status(f"Finding career page for {company_name}...")
        
        # First try using the LLM to predict the URL
        career_url = self.llm_handler.find_career_url(company_name)
        self.add_status(f"LLM suggested URL: {career_url}")
        
        # Test if the suggested URL works
        status_code, _ = self.web_scraper.fetch_page(career_url, timeout=5)
        
        # If the suggested URL doesn't work, try common patterns
        if status_code != 200:
            self.add_status("Suggested URL not accessible, trying alternative URLs...")
            career_url = self.web_scraper.test_career_urls(company_name)
            
            if not career_url:
                self.add_status("Could not find a working career page. Please check the company name or try a different approach.")
                return [], self.status_messages
        
        self.add_status(f"Found working career page: {career_url}")
        
        # Step 3: Scrape job listings from the career page
        self.add_status("Searching for jobs matching your keywords...")
        jobs = self.web_scraper.search_jobs(career_url, refined_keywords, self.llm_handler)
        
        if not jobs:
            self.add_status("No matching jobs found. Try different keywords or a different company.")
            return [], self.status_messages
        
        # Step 4: Sort jobs by relevance
        jobs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Limit the number of jobs to display
        jobs = jobs[:config.MAX_JOBS_TO_DISPLAY]
        
        self.add_status(f"Found {len(jobs)} relevant job(s).")
        
        return jobs, self.status_messages