from groq import Groq
from typing import List, Dict, Optional
from loguru import logger
from config import settings
from core.persona import CHAIN_OF_THOUGHT_PROMPT, format_response, detect_emergency_keywords, get_emergency_response
import os


class Llama3LLM:
    """Llama 3 LLM integration via Groq API"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.LLAMA_API_KEY)
        self.model = settings.LLAMA_MODEL
        logger.info(f"✓ Llama 3 LLM initialized (model: {self.model})")
    
    def generate_response(
        self,
        query: str,
        context_chunks: List[Dict],
        use_chain_of_thought: bool = True
    ) -> Dict[str, any]:
        """Generate response using retrieved context"""
        
        # Check for emergency
        if detect_emergency_keywords(query):
            return {
                'response': get_emergency_response(),
                'confidence': 1.0,
                'emergency': True
            }
        
        # Prepare context
        context_text = self._format_context(context_chunks)
        
        # Build prompt
        if use_chain_of_thought:
            prompt = CHAIN_OF_THOUGHT_PROMPT.format(
                context=context_text,
                question=query
            )
        else:
            prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            # Generate response using Groq API with Llama 3
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Dr. Asha, an empathetic and knowledgeable medical assistant. Provide detailed, accurate, evidence-based medical information. Explain concepts thoroughly and be helpful. Never diagnose or prescribe, but always provide comprehensive educational information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2048,
                top_p=0.95
            )
            
            # Calculate confidence based on context relevance
            avg_score = sum(chunk['score'] for chunk in context_chunks) / len(context_chunks)
            confidence = min(avg_score, 1.0)
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Format with Dr. Asha persona
            formatted_response = format_response(response_text, confidence)
            
            return {
                'response': formatted_response,
                'raw_response': response_text,
                'confidence': confidence,
                'emergency': False
            }
            
        except Exception as e:
            logger.error(f"✗ LLM generation failed: {e}")
            return {
                'response': "I apologize, but I'm having trouble processing your question right now. Please try again or rephrase your question.",
                'confidence': 0.0,
                'emergency': False,
                'error': str(e)
            }
    
    @staticmethod
    def _format_context(chunks: List[Dict]) -> str:
        """Format context chunks for prompt"""
        formatted = []
        
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"[Source {i}: {chunk['title']}]\n"
                f"{chunk['text']}\n"
                f"(Source: {chunk['source_url']})\n"
            )
        
        return "\n---\n".join(formatted)


llm_service = Llama3LLM()
