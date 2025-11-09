import streamlit as st
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import requests
import PyPDF2
import docx
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from ai import ChimeraAI

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="Chimera AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


class KnowledgeBase:
    def __init__(self):
        self.docs = []
        self.metadatas = []
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.index = None

    def _update_index(self):
        if not self.docs:
            self.index = None
            return
        embeddings = np.array(self.model.encode(self.docs, show_progress_bar=False)).astype("float32")
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def add_text(self, text: str, metadata: dict = None):
        chunks = [c.strip() for c in text.split("\n\n") if c.strip() and len(c.strip()) > 40]
        for chunk in chunks:
            self.docs.append(chunk)
            self.metadatas.append(metadata or {})
        self._update_index()
        return len(chunks)

    def add_pdf(self, file):
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n\n".join([page.extract_text() or "" for page in pdf_reader.pages])
        return self.add_text(text, {"source": file.name, "type": "pdf"})

    def add_docx(self, file):
        doc = docx.Document(file)
        text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return self.add_text(text, {"source": file.name, "type": "docx"})

    def scrape_website(self, url: str):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "form", "aside"]):
                tag.decompose()

            main = soup.find("main") or soup.find("article") or soup.body or soup
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in main.find_all(["p", "h1", "h2", "h3"])
                if len(p.get_text(strip=True)) > 40
            ]
            text = "\n\n".join(paragraphs)
            if not text.strip():
                raise Exception("No meaningful text extracted.")
            return self.add_text(text, {"source": url, "type": "website"})
        except Exception as e:
            raise Exception(f"Scraping failed: {str(e)}")

    def search(self, query: str, n: int = 3, db=None):
        if not self.index or not self.docs:
            return []
        query_emb = np.array(self.model.encode([query])).astype("float32")
        distances, indices = self.index.search(query_emb, min(n, len(self.docs)))
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]

    def get_count(self):
        return len(self.docs)


if "kb" not in st.session_state:
    st.session_state.kb = KnowledgeBase()
if "ai" not in st.session_state:
    st.session_state.ai = ChimeraAI(st.session_state.kb)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def display_message(role: str, content: str):
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <strong>{icon} {role.title()}:</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)


with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=CHIMERA", use_container_width=True)
    st.markdown("### 🤖 Chimera AI Assistant")
    st.markdown("*Standalone Mode - Local AI Engine*")
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
    st.metric("Conversations", stats["total_conversations"])
    st.metric("Messages", stats["total_messages"])
    st.markdown("---")
    st.success("✅ Using local FAISS embeddings (no API costs)")


st.markdown('<div class="main-header">🤖 Chimera AI Assistant</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📚 Knowledge Base", "📊 Analytics", "⚙️ Advanced"])

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


with tab2:
    st.markdown("### 📚 Knowledge Base")
    tab_text, tab_site, tab_pdf, tab_docx = st.tabs(["📝 Text", "🌐 Website", "📄 PDF", "📃 Word"])

    with tab_text:
        text_content = st.text_area("Enter text content:", height=200)
        if st.button("➕ Add Text"):
            if text_content.strip():
                chunks = st.session_state.kb.add_text(text_content, {"type": "text"})
                st.success(f"Added {chunks} chunks to the knowledge base.")
            else:
                st.warning("Please enter text.")

    with tab_site:
        url = st.text_input("Enter website URL:")
        if st.button("🌐 Scrape Website"):
            if url:
                try:
                    chunks = st.session_state.kb.scrape_website(url)
                    st.success(f"Added {chunks} chunks from website.")
                except Exception as e:
                    st.error(f"{str(e)}")

    with tab_pdf:
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if st.button("📄 Process PDF") and pdf_file:
            chunks = st.session_state.kb.add_pdf(pdf_file)
            st.success(f"Added {chunks} chunks from PDF.")

    with tab_docx:
        doc_file = st.file_uploader("Upload DOCX", type=["docx"])
        if st.button("📃 Process DOCX") and doc_file:
            chunks = st.session_state.kb.add_docx(doc_file)
            st.success(f"Added {chunks} chunks from DOCX.")


with tab3:
    st.markdown("### 📊 Analytics")
    msgs = st.session_state.ai.get_conversation(st.session_state.session_id)
    if msgs:
        df = pd.DataFrame(msgs)
        st.metric("Messages", len(df))
        fig = px.bar(df, x=df.index, y=df["content"].apply(len), color="role")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start a chat to see analytics.")


with tab4:
    st.markdown("### ⚙️ Advanced Tools")
    if st.button("🎯 Analyze Lead Quality"):
        if st.session_state.messages:
            last_msg = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
            history = st.session_state.ai.get_conversation(st.session_state.session_id)
            lead = st.session_state.ai._analyze_lead_quality(last_msg, history)
            st.metric("Lead Score", f"{lead['overall_score']}/100")
            st.metric("Qualification", lead["qualification"].upper())
        else:
            st.warning("No conversation yet.")


st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#666;">
<p><strong>Chimera AI Assistant</strong> - Standalone Mode</p>
<p>Local FAISS + Hugging Face Embeddings • No API Quotas</p>
</div>
""", unsafe_allow_html=True)