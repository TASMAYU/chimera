"""
frontend_standalone.py - Chimera Streamlit Frontend (Standalone)
Direct connection to AI module without backend API

Install: 
pip install streamlit plotly pandas faiss-cpu sentence-transformers PyPDF2 python-docx beautifulsoup4 requests python-dotenv google-generativeai
Run: 
streamlit run frontend_standalone.py
"""

import streamlit as st
import os
from typing import List, Dict
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
import docx
from bs4 import BeautifulSoup
import requests
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load environment and configure Gemini (for text generation only)
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Import AI module
from ai import ChimeraAI

# Streamlit page config
st.set_page_config(
    page_title="Chimera AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #1a1a1a;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #1a1a1a;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# --- Knowledge Base using FAISS + Hugging Face ---
# --- Knowledge Base using FAISS + Hugging Face ---
class KnowledgeBase:
    def __init__(self):
        """Initialize FAISS-based local knowledge base."""
        self.docs = []
        self.metadatas = []
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.index = None

    def _update_index(self):
        """Rebuild FAISS index when documents are added."""
        if not self.docs:
            self.index = None
            return
        embeddings = np.array(self.model.encode(self.docs, show_progress_bar=False)).astype("float32")
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def add_text(self, text: str, metadata: dict = None):
        """Add raw text, split into chunks, and update FAISS index."""
        # Clean and chunk text
        chunks = [c.strip() for c in text.split('\n\n') if c.strip() and len(c.strip()) > 40]
        for chunk in chunks:
            self.docs.append(chunk)
            self.metadatas.append(metadata or {})
        self._update_index()
        return len(chunks)

    def add_pdf(self, file):
        """Extract text from a PDF and add to knowledge base."""
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        return self.add_text(text, {"source": file.name, "type": "pdf"})

    def add_docx(self, file):
        """Extract text from a Word document and add to knowledge base."""
        doc = docx.Document(file)
        text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return self.add_text(text, {"source": file.name, "type": "docx"})

    def scrape_website(self, url: str):
        """Scrape and clean readable website text (auto-detects main content)."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
                    "Gecko/20100101 Firefox/121.0"
                )
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts, navbars, and repetitive tags
            for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside"]):
                tag.decompose()

            # Extract main readable content
            main = soup.find("main") or soup.find("article") or soup.body or soup
            paragraphs = [
                p.get_text(separator=" ", strip=True)
                for p in main.find_all(["p", "h1", "h2", "h3"])
                if len(p.get_text(strip=True)) > 40
            ]
            text = "\n\n".join(paragraphs)

            if not text.strip():
                raise Exception("No meaningful text extracted from page")

            return self.add_text(text, {"source": url, "type": "website"})
        except Exception as e:
            raise Exception(f"Scraping failed: {str(e)}")

    def search(self, query: str, n: int = 3, db=None):
        """Retrieve top-n most relevant text chunks from FAISS index."""
        if not self.index or not self.docs:
            return []
        query_emb = np.array(self.model.encode([query])).astype("float32")
        distances, indices = self.index.search(query_emb, min(n, len(self.docs)))
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]

    def get_count(self):
        """Return number of stored text chunks."""
        return len(self.docs)


# --- Initialize session state ---
if 'kb' not in st.session_state:
    st.session_state.kb = KnowledgeBase()
if 'ai' not in st.session_state:
    st.session_state.ai = ChimeraAI(st.session_state.kb)
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# --- Helper function ---
def display_message(role: str, content: str):
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.title()}:</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=CHIMERA", use_container_width=True)
    st.markdown("### 🤖 Chimera AI Assistant")
    st.markdown("*Standalone Mode - Direct AI Connection*")
    st.markdown("---")
    st.text_input("Session ID", value=st.session_state.session_id, disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New"):
            st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🗑️ Clear"):
            st.session_state.ai.clear_conversation(st.session_state.session_id)
            st.session_state.messages = []
            st.success("Cleared!")
            st.rerun()

    st.markdown("---")
    st.metric("Documents", st.session_state.kb.get_count())
    stats = st.session_state.ai.get_statistics()
    st.metric("Conversations", stats['total_conversations'])
    st.metric("Messages", stats['total_messages'])
    st.markdown("---")
    st.success("✅ Local FAISS embeddings (no API costs)")

# --- Main Header ---
st.markdown('<div class="main-header">🤖 Chimera AI Assistant</div>', unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📚 Knowledge Base", "📊 Analytics", "⚙️ Advanced"])

# --- Chat Tab ---
with tab1:
    st.markdown("### Chat with Chimera")
    for msg in st.session_state.messages:
        display_message(msg["role"], msg["content"])

    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("Type your message:", key="user_input", label_visibility="collapsed")
    with col2:
        send = st.button("Send", type="primary")

    if send and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("🤖 Chimera is thinking..."):
            try:
                result = st.session_state.ai.generate_response(user_input, st.session_state.session_id)
                st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            except Exception as e:
                st.error(f"Error: {str(e)}")
        st.rerun()

# --- Knowledge Base Tab ---
with tab2:
    st.markdown("### 📚 Knowledge Base Management")
    tab_text, tab_site, tab_pdf, tab_docx = st.tabs(["📝 Text", "🌐 Website", "📄 PDF", "📃 Word"])

    with tab_text:
        text_content = st.text_area("Enter text content:", height=200)
        if st.button("➕ Add Text"):
            if text_content.strip():
                chunks = st.session_state.kb.add_text(text_content, {"type": "text"})
                st.success(f"✅ Added {chunks} text chunks!")
            else:
                st.warning("Please enter text.")

    with tab_site:
        url = st.text_input("Enter website URL:")
        if st.button("🌐 Scrape Website"):
            if url:
                try:
                    chunks = st.session_state.kb.scrape_website(url)
                    st.success(f"✅ Added {chunks} chunks from website!")
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    with tab_pdf:
        pdf_file = st.file_uploader("Upload PDF", type=['pdf'])
        if st.button("📄 Process PDF") and pdf_file:
            chunks = st.session_state.kb.add_pdf(pdf_file)
            st.success(f"✅ Added {chunks} chunks from PDF!")

    with tab_docx:
        doc_file = st.file_uploader("Upload DOCX", type=['docx'])
        if st.button("📃 Process DOCX") and doc_file:
            chunks = st.session_state.kb.add_docx(doc_file)
            st.success(f"✅ Added {chunks} chunks from DOCX!")

# --- Analytics Tab ---
with tab3:
    st.markdown("### 📊 Conversation Analytics")
    msgs = st.session_state.ai.get_conversation(st.session_state.session_id)
    if msgs:
        df = pd.DataFrame(msgs)
        st.metric("Messages", len(df))
        fig = px.bar(df, x=df.index, y=df['content'].apply(len), color='role')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start a chat to see analytics.")

# --- Advanced Tab ---
with tab4:
    st.markdown("### ⚙️ Advanced Tools")
    if st.button("🎯 Analyze Lead Quality"):
        if st.session_state.messages:
            last_user_msg = next((m['content'] for m in reversed(st.session_state.messages) if m['role'] == 'user'), "")
            history = st.session_state.ai.get_conversation(st.session_state.session_id)
            lead = st.session_state.ai._analyze_lead_quality(last_user_msg, history)
            st.metric("Lead Score", f"{lead['overall_score']}/100")
            st.metric("Qualification", lead['qualification'].upper())
        else:
            st.warning("No conversation yet.")

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#666;">
<p><strong>Chimera AI Assistant</strong> - Standalone Mode</p>
<p>Local FAISS + Hugging Face Embeddings • No API Quotas</p>
</div>
""", unsafe_allow_html=True)
