"""
Main Streamlit application for the job search framework.
This module handles the user interface and orchestrates the job search process.
"""

import streamlit as st
import time
from agent import JobSearchAgent
import config

def main():
    # Set page title and description
    st.set_page_config(
        page_title="AI Job Search Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 AI Job Search Assistant")
    st.markdown(
        """
        This application uses AI to help you find relevant job openings on company career pages.
        Enter a company name and your job search keywords to get started.
        """
    )
    
    # Sidebar for model selection and API key
    st.sidebar.title("Settings")
    
    # Model selection
    model_options = {k: v["name"] for k, v in config.SUPPORTED_MODELS.items()}
    selected_model = st.sidebar.selectbox(
        "Select LLM Model",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=0
    )
    
    # API key input (if needed)
    api_key = st.sidebar.text_input(
        "API Key (if required)",
        type="password",
        help="Some LLM services may require an API key. Leave blank if using a local model."
    )
    
    # Information about required software
    st.sidebar.markdown("---")
    st.sidebar.subheader("Required Software")
    st.sidebar.markdown(
        """
        - **Ollama** (for LLAMA 3): [Install Ollama](https://ollama.ai/)
        - Make sure Ollama is running if you select the LLAMA 3 model
        """
    )
    
    # Main search inputs
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("Company Name", placeholder="e.g., Google, Microsoft, Amazon")
    
    with col2:
        keywords = st.text_input("Job Keywords", placeholder="e.g., Python Developer, Data Scientist")
    
    # Search button
    search_button = st.button("Search for Jobs", type="primary", use_container_width=True)
    
    # Results container
    results_container = st.container()
    
    # Status container
    status_container = st.container()
    
    # When search button is clicked
    if search_button and company_name and keywords:
        with status_container:
            status_placeholder = st.empty()
            status_placeholder.info("Initializing job search agent...")
            
            # Initialize agent
            agent = JobSearchAgent(model_type=selected_model, api_key=api_key if api_key else None)
            
            # Perform job search
            with st.spinner("Searching for jobs..."):
                jobs, status_messages = agent.search_jobs(company_name, keywords)
            
            # Display status messages
            if status_messages:
                with st.expander("Search Process Details", expanded=False):
                    for msg in status_messages:
                        st.text(msg)
        
        # Display results
        with results_container:
            if jobs:
                st.subheader(f"Found {len(jobs)} relevant job(s) at {company_name}")
                
                # Display each job
                for i, job in enumerate(jobs):
                    with st.container():
                        st.markdown(f"### {i+1}. {job.get('title', 'No Title')}")
                        
                        # Job metadata
                        col1, col2 = st.columns(2)
                        with col1:
                            if job.get('location'):
                                st.markdown(f"📍 **Location:** {job['location']}")
                        with col2:
                            st.markdown(f"🎯 **Relevance Score:** {job.get('relevance_score', 'N/A')}/10")
                        
                        # Job description
                        if job.get('description'):
                            st.markdown(f"**Description:** {job['description']}")
                        
                        # Job URL
                        if job.get('url'):
                            st.markdown(f"[View Job Details]({job['url']})")
                        
                        st.markdown("---")
            else:
                st.warning("No matching jobs found. Try different keywords or a different company.")
    
    # Display a message if no search has been performed yet
    if not search_button:
        with results_container:
            st.info("Enter a company name and keywords, then click 'Search for Jobs' to start your search.")
    
if __name__ == "__main__":
    main()