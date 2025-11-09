"""
ai.py - Chimera AI Module
Contains the core AI logic for the Chimera assistant

This module handles:
- AI response generation using Gemini
- Conversation management
- Context-aware responses using RAG (FAISS + Hugging Face)
- Lead qualification logic
"""

import os
import faiss
import numpy as np
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


# ------------------------------
# FAISS + Hugging Face Knowledge Base
# ------------------------------

class KnowledgeBase:
    """
    Lightweight FAISS-based knowledge base with Hugging Face embeddings.
    """

    def __init__(self, docs: List[str]):
        """
        Initialize FAISS index with embeddings.
        Args:
            docs: List of text chunks or paragraphs to index.
        """
        self.docs = docs
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        print("🔹 Building FAISS index for knowledge base...")

        # Compute embeddings
        self.embeddings = self.model.encode(docs, show_progress_bar=True)
        self.embeddings = np.array(self.embeddings).astype("float32")

        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

        print(f"✅ Knowledge base initialized with {len(docs)} documents.")

    def search(self, query: str, n: int = 3, db=None) -> List[str]:
        """
        Retrieve top-n most relevant chunks for a query.
        Args:
            query: User's query text.
            n: Number of chunks to return.
            db: (Optional) Ignored; for interface compatibility.
        Returns:
            List of top-n relevant text chunks.
        """
        query_emb = self.model.encode([query])
        query_emb = np.array(query_emb).astype("float32")

        distances, indices = self.index.search(query_emb, n)
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]


# ------------------------------
# Main Chimera AI Assistant
# ------------------------------

class ChimeraAI:
    """
    Main AI assistant class for Chimera
    Handles conversation management and response generation
    """

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.conversations = {}

        self.system_prompt = """You are Chimera, an intelligent AI sales assistant. Your role:

1. Answer visitor questions accurately using the provided context
2. Be conversational, helpful, and professional
3. Qualify leads by understanding their needs and pain points
4. Guide visitors toward booking meetings or providing contact information
5. Stay in character as a knowledgeable sales representative

Guidelines:
- Use the context to give specific, accurate answers
- If information isn't in the context, politely say so and offer to help differently
- Ask clarifying questions to better understand visitor needs
- Be concise but thorough - aim for 2-4 sentences unless more detail is needed
- Show genuine enthusiasm about helping
- When appropriate, suggest next steps (demo, meeting, consultation)
- Focus on understanding the visitor's pain points and how the product/service solves them"""

        self.lead_qualification_prompt = """
Additionally, assess the lead quality based on:
- Company size and industry (if mentioned)
- Budget indicators
- Decision-making authority
- Timeline for implementation
- Specific pain points mentioned

If the visitor seems like a qualified lead, gently guide them toward scheduling a meeting or demo.
"""

    # ------------------------------
    # Conversation Management
    # ------------------------------

    def get_conversation(self, session_id: str) -> List[Dict]:
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        return self.conversations[session_id]

    def clear_conversation(self, session_id: str) -> bool:
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False

    # ------------------------------
    # Prompt Construction Helpers
    # ------------------------------

    def _build_context_string(self, context_chunks: List[str]) -> str:
        if not context_chunks:
            return "No specific context found. Use general sales and service knowledge."
        return "\n\n".join([f"[Context {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])

    def _build_history_string(self, history: List[Dict], max_exchanges: int = 3) -> str:
        if not history:
            return "This is the start of the conversation."
        recent = history[-(max_exchanges * 2):]
        return "\n\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in recent])

    # ------------------------------
    # Lead Qualification Logic
    # ------------------------------

    def _analyze_lead_quality(self, message: str, history: List[Dict]) -> Dict:
        indicators = {
            'high_intent': ['price', 'cost', 'buy', 'purchase', 'demo', 'meeting', 'schedule'],
            'decision_maker': ['I need', 'we need', 'looking for', 'interested in', 'evaluate'],
            'budget': ['budget', 'pricing', 'investment', 'cost'],
            'timeline': ['soon', 'asap', 'urgent', 'this week', 'this month', 'quarter']
        }

        convo = " ".join([msg['content'].lower() for msg in history] + [message.lower()])

        score = {
            'high_intent': any(w in convo for w in indicators['high_intent']),
            'decision_maker': any(w in convo for w in indicators['decision_maker']),
            'budget_discussed': any(w in convo for w in indicators['budget']),
            'has_timeline': any(w in convo for w in indicators['timeline']),
            'message_count': len(history) // 2
        }

        overall = (
            (score['high_intent'] * 30)
            + (score['decision_maker'] * 25)
            + (score['budget_discussed'] * 20)
            + (score['has_timeline'] * 15)
            + (min(score['message_count'] * 2, 10))
        )

        score['overall_score'] = overall
        score['qualification'] = 'hot' if overall >= 60 else 'warm' if overall >= 30 else 'cold'
        return score

    # ------------------------------
    # Response Generation (RAG)
    # ------------------------------

    def generate_response(self, message: str, session_id: str, db: Optional[object] = None, enable_lead_qualification: bool = False) -> Dict[str, any]:
        history = self.get_conversation(session_id)
        context_chunks = self.kb.search(message, n=3, db=db)
        context_str = self._build_context_string(context_chunks)
        history_str = self._build_history_string(history)

        prompt = "\n".join([
            self.system_prompt,
            "",
            "RELEVANT KNOWLEDGE BASE CONTEXT:",
            context_str,
            "",
            "CONVERSATION HISTORY:",
            history_str,
            "",
            self.lead_qualification_prompt if enable_lead_qualification else "",
            f"User: {message}",
            "",
            "Assistant (Chimera):"
        ])

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    max_output_tokens=500,
                ),
            )

            assistant_msg = response.text.strip()
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": assistant_msg})

            result = {
                "response": assistant_msg,
                "session_id": session_id,
                "context_used": len(context_chunks) > 0,
            }

            if enable_lead_qualification:
                result["lead_score"] = self._analyze_lead_quality(message, history)

            return result

        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")

    # ------------------------------
    # Utility Functions
    # ------------------------------

    def generate_summary(self, session_id: str) -> str:
        history = self.get_conversation(session_id)
        if not history:
            return "No conversation to summarize."

        convo_text = "\n".join([f"{m['role'].title()}: {m['content']}" for m in history])
        summary_prompt = f"""Summarize this sales conversation including:
1. Main topics discussed
2. Customer needs/pain points
3. Products/services of interest
4. Next steps
5. Overall lead quality

Conversation:
{convo_text}

Provide a concise summary:"""

        try:
            response = self.model.generate_content(summary_prompt)
            return response.text.strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def get_statistics(self) -> Dict:
        total_conversations = len(self.conversations)
        total_messages = sum(len(conv) for conv in self.conversations.values())
        avg = total_messages / total_conversations if total_conversations else 0
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_messages_per_conversation": round(avg, 2),
            "active_sessions": list(self.conversations.keys()),
        }


# Factory function
def create_ai_assistant(knowledge_base) -> ChimeraAI:
    return ChimeraAI(knowledge_base)
