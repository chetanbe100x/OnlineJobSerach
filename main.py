"""
Main entry point for the Job Search Agent framework.
This module initializes and runs the Streamlit application,
connecting all components together.
"""
import streamlit as st
from ui import initialize_ui, render_results
from llm_manager import get_available_models
from search_engine import find_career_page
from job_extractor import extract_jobs
from utils import setup_logging
from config import APP_TITLE, APP_DESCRIPTION

def main():
    """
    Main function that initializes and runs the application.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Job Search Agent")
    
    # Initialize Streamlit UI
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.markdown(APP_DESCRIPTION)
    
    # Get UI inputs
    selected_model, api_key, company_name, keywords = initialize_ui(get_available_models())
    
    # Process search when requested
    if st.button("Search Jobs"):
        if not company_name:
            st.error("Please enter a company name")
            return
            
        with st.spinner("Searching for company career page..."):
            career_page_url = find_career_page(company_name, selected_model, api_key)
        
        if career_page_url:
            with st.spinner(f"Extracting job listings from {career_page_url}..."):
                job_listings = extract_jobs(career_page_url, keywords, selected_model, api_key)
            
            # Display results
            render_results(job_listings)
        else:
            st.error(f"Could not find career page for {company_name}")

if __name__ == "__main__":
    main()