"""
UI module for the Job Search Agent.
This module contains all Streamlit UI components and rendering functions.
"""
import streamlit as st
from typing import List, Dict, Tuple, Any

def initialize_ui(available_models: List[str]) -> Tuple[str, str, str, str]:
    """
    Initialize the UI components and return user inputs.
    
    Args:
        available_models: List of available LLM models
    
    Returns:
        Tuple containing (selected_model, api_key, company_name, keywords)
    """
    # Create sidebar for settings
    with st.sidebar:
        st.header("Settings")
        
        # Model selection
        selected_model = st.selectbox(
            "Select LLM Model",
            options=available_models,
            help="Choose the LLM model to use for processing"
        )
        
        # API key input (if needed)
        api_key = st.text_input(
            "API Key (if required)",
            type="password",
            help="Enter API key if the selected model requires one"
        )
    
    # Main content area for search inputs
    st.header("Job Search")
    
    # Company name input
    company_name = st.text_input(
        "Company Name",
        help="Enter the name of the company you want to search jobs for"
    )
    
    # Keywords input
    keywords = st.text_input(
        "Job Keywords",
        help="Enter keywords related to the job you're looking for (e.g., 'python developer', 'data scientist')"
    )
    
    return selected_model, api_key, company_name, keywords

def render_results(job_listings: List[Dict[str, Any]]) -> None:
    """
    Render job listing results in the UI.
    
    Args:
        job_listings: List of job listings, where each listing is a dictionary
                     containing job details
    """
    if not job_listings:
        st.info("No job listings found matching your criteria.")
        return
    
    st.header(f"Found {len(job_listings)} Jobs")
    
    # Display each job listing
    for i, job in enumerate(job_listings):
        with st.expander(f"{i+1}. {job.get('title', 'Unnamed Position')}"):
            # Job details
            if 'company' in job:
                st.write(f"**Company:** {job['company']}")
            if 'location' in job:
                st.write(f"**Location:** {job['location']}")
            if 'description' in job:
                st.write("**Description:**")
                st.write(job['description'])
            if 'requirements' in job:
                st.write("**Requirements:**")
                st.write(job['requirements'])
            if 'experience_level' in job:
                st.write(f"**Experience Level:** {job['experience_level']}")
            if 'url' in job:
                st.write(f"**[Apply Here]({job['url']})**")
    
    # Add export option
    if st.button("Export Results as CSV"):
        import pandas as pd
        from io import StringIO
        
        # Convert job listings to DataFrame
        df = pd.DataFrame(job_listings)
        
        # Generate CSV for download
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="job_listings.csv",
            mime="text/csv"
        )