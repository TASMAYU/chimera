import os
import faiss
import numpy as np
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class KnowledgeBase:
    def __init__(self, docs: List[str]):
        self.docs = docs
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.embeddings = np.array(self.model.encode(docs, show_progress_bar=True)).astype("float32")
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def search(self, query: str, n: int = 3, db=None) -> List[str]:
        query_emb = np.array(self.model.encode([query])).astype("float32")
        distances, indices = self.index.search(query_emb, n)
        return [self.docs[i] for i in indices[0] if i < len(self.docs)]


class ChimeraAI:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.conversations = {}

        self.system_prompt = """You are Chimera, an intelligent AI sales assistant.

1. Answer visitor questions using the provided context.
2. Be conversational, helpful, and professional.
3. Qualify leads by understanding their needs and goals.
4. Encourage visitors to schedule a demo or share contact details.
5. Stay consistent with the role of a friendly and informed representative.

Guidelines:
- Use the given context whenever possible.
- If the context doesn’t contain the answer, politely say so.
- Keep responses natural and clear, 2–4 sentences unless more detail is needed.
- Ask questions to better understand the visitor’s needs.
- Maintain a tone of genuine enthusiasm and helpfulness."""

        self.lead_qualification_prompt = """
Also, assess the lead quality based on:
- Company size or industry (if mentioned)
- Budget indicators
- Decision-making authority
- Timeline urgency
- Specific pain points

If the lead seems qualified, gently suggest scheduling a call or demo."""

    def get_conversation(self, session_id: str) -> List[Dict]:
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        return self.conversations[session_id]

    def clear_conversation(self, session_id: str) -> bool:
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False

    def _build_context_string(self, context_chunks: List[str]) -> str:
        if not context_chunks:
            return "No relevant context found. Use general knowledge."
        return "\n\n".join([f"[Context {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])

    def _build_history_string(self, history: List[Dict], max_exchanges: int = 3) -> str:
        if not history:
            return "This is the start of the conversation."
        recent = history[-(max_exchanges * 2):]
        return "\n\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in recent])

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

        total = (
            (score['high_intent'] * 30)
            + (score['decision_maker'] * 25)
            + (score['budget_discussed'] * 20)
            + (score['has_timeline'] * 15)
            + (min(score['message_count'] * 2, 10))
        )

        score['overall_score'] = total
        score['qualification'] = 'hot' if total >= 60 else 'warm' if total >= 30 else 'cold'
        return score

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

            reply = response.text.strip()
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": reply})

            result = {
                "response": reply,
                "session_id": session_id,
                "context_used": len(context_chunks) > 0,
            }

            if enable_lead_qualification:
                result["lead_score"] = self._analyze_lead_quality(message, history)

            return result

        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")

    def generate_summary(self, session_id: str) -> str:
        history = self.get_conversation(session_id)
        if not history:
            return "No conversation to summarize."

        convo = "\n".join([f"{m['role'].title()}: {m['content']}" for m in history])
        summary_prompt = f"""Summarize this sales conversation, covering:
1. Key discussion points
2. Customer needs and concerns
3. Products or services mentioned
4. Next actions or follow-ups
5. Lead quality overview

Conversation:
{convo}

Provide a short, clear summary:"""

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


def create_ai_assistant(knowledge_base) -> ChimeraAI:
    return ChimeraAI(knowledge_base)
