import streamlit as st
from crew_setup import setup_legal_crew
import tempfile
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialize
load_dotenv()
st.set_page_config(
    layout="wide", 
    page_title="Legal AI", 
    page_icon="⚖️",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
    }
    [data-testid="stSidebar"] {
        background-color: #9f9bcc !important;
    }
    [data-testid="stSidebar"] .stRadio label, 
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: white !important;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .reference-card {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
    }
    .legal-principle {
        background-color: #eef7ff;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'legal_references' not in st.session_state:
    st.session_state.legal_references = []

# Supported countries
SUPPORTED_COUNTRIES = [
    "India", "United States", "United Kingdom", "Canada",
    "Australia", "Germany", "France"
]

# Sidebar configuration
with st.sidebar:
    st.markdown("<h2 style='color:white;'>⚖️ Legal AI Configuration</h2>", unsafe_allow_html=True)
    
    country = st.selectbox("Select Jurisdiction", SUPPORTED_COUNTRIES, index=0)
    model_choice = st.radio("AI Model", ["Gemini", "Groq(experimental**)"])
    rag_enabled = st.checkbox("Enable Legal Database (YAML)", True)
    
    if rag_enabled:
        st.info("Using YAML-based legal reference system")
        n_rag_results = st.slider("Number of Legal References", 1, 5, 3)
    
    output_format = st.radio("Output Format", ["Full Report", "Summary"])
    debug_mode = st.checkbox("Show Debug Information", False)

# Main UI
st.markdown(f"""
<div style="background-color:#3498db;padding:1rem;border-radius:8px;margin-bottom:2rem">
    <h1 style="color:white;margin:0;">⚖️ {country} Legal Analysis System</h1>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 Case Input", "📊 Analysis Results"])

with tab1:
    input_method = st.radio("Input Type", ["Text", "Image Upload"], horizontal=True)
    case_input = ""
    
    if input_method == "Text":
        case_input = st.text_area(
            f"Describe your {country} legal case", 
            height=200,
            placeholder=f"Enter details about your {country} legal matter..."
        )
    else:
        with st.container():
            st.markdown("### 📄 Upload Legal case image")
            img_file = st.file_uploader(
                "Choose a file",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )
            
            if img_file:
                with st.spinner("Processing document..."):
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp.write(img_file.read())
                        img_path = tmp.name
                    
                    try:
                        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        file_ext = os.path.splitext(img_file.name)[1].lower()
                        mime_type = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.pdf': 'application/pdf'
                        }.get(file_ext, 'application/octet-stream')
                        
                        img = genai.upload_file(img_path, mime_type=mime_type)
                        response = model.generate_content([
                            f"Extract all text from this {country} legal document.", 
                            img
                        ])
                        case_input = response.text
                        
                        with st.expander("📋 Extracted Document Text", expanded=True):
                            st.text_area(
                                "Extracted Content", 
                                value=case_input, 
                                height=200,
                                label_visibility="collapsed"
                            )
                    except Exception as e:
                        st.error(f"Document processing failed: {str(e)}")
                    finally:
                        os.unlink(img_path)

if st.button(f"🔍 Analyze Under {country} Law", type="primary"):
    if not case_input:
        st.warning(f"Please provide {country} case details")
        st.stop()

    with st.spinner(f"🧠 Analyzing under {country} law using {model_choice}..."):
        try:
            # Initialize RAG if enabled
            if rag_enabled:
                try:
                    from crew_setup import create_legal_reference_tool
                    legal_tool = create_legal_reference_tool(country)
                    rag_results = legal_tool.run(f"Search for relevant laws about: {case_input}")
                    
                    st.session_state.legal_references = rag_results
                    
                    with tab2:
                        if rag_results and "No matching laws" not in rag_results:
                            st.markdown(f"""
                            <div style="background-color:#d4edda;padding:1rem;border-radius:8px;margin-bottom:1rem">
                                <h3>🔍 Found {country} Legal References</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="legal-principle">
                                <pre>{rag_results}</pre>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"No specific legal references found for this case in {country} law")
                except Exception as e:
                    st.warning(f"Legal reference search failed: {str(e)}")
                    rag_enabled = False

            # Run analysis - this now uses the modified setup_legal_crew
            results = setup_legal_crew(
                case_input, 
                model_choice, 
                country, 
                rag_enabled
            )
            
            if not results.get('success', False):
                error_msg = results.get('error', 'Unknown error occurred')
                st.error(f"❌ {country} analysis failed: {error_msg}")
                if debug_mode:
                    st.error(f"Full error details: {error_msg}")
                st.stop()

            # Store results
            st.session_state.results = results

            # Display results with enhanced styling
            with tab2:
                if output_format in ["Full Report"]:
                    st.markdown(f"""
                    <div style="background-color:#f8f9fa;padding:1rem;border-radius:8px;margin-bottom:2rem">
                        <h2>📄 {country} Legal Analysis Report</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display the report content directly from results
                    st.markdown(results['report'])
                    
                    st.download_button(
                        "💾 Download Full Report",
                        data=results['report'],
                        file_name=f"{country}_legal_analysis.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                if output_format in ["Summary"] and 'summary' in results:
                    st.markdown(f"""
                    <div style="background-color:#f8f9fa;padding:1rem;border-radius:8px;margin-top:2rem;margin-bottom:1rem">
                        <h2>📝 {country} Executive Summary</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(results['summary'])
                    
                    st.download_button(
                        "💾 Download Summary",
                        data=results['summary'],
                        file_name=f"{country}_legal_summary.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

        except Exception as e:
            st.error(f"❌ {country} legal analysis failed: {str(e)}")
            if debug_mode:
                st.exception(e)

# Debug view with improved layout
# Debug view with improved layout
if debug_mode and st.session_state.get("results"):
    with st.expander("🔧 Debug Details", expanded=False):
        st.markdown("""
        <div style="background-color:#f0f0f0;padding:1rem;border-radius:8px;">
            <h3>Technical Information</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Country Selected", country)
            st.metric("AI Model Used", model_choice)
        with col2:
            st.metric("RAG Enabled", "Yes" if rag_enabled else "No")
            st.metric("Report Length", f"{len(st.session_state.results.get('report', ''))} chars")
        
        st.markdown("### Task Outputs")
        
        # Create tabs for each task output instead of nested expanders
        task_tabs = st.tabs([task.capitalize() for task in ["analysis", "research", "document", "summary"]])
        
        for i, task in enumerate(["analysis", "research", "document", "summary"]):
            if task in st.session_state.results:
                with task_tabs[i]:
                    content = st.session_state.results[task]
                    if content:
                        st.code(content[:1500] + ("..." if len(content) > 1500 else ""))
                    else:
                        st.warning(f"No {task} content available")