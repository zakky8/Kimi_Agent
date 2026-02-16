"""
AI Client Module
Unified interface for multiple AI providers
"""
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import json
import httpx
import asyncio

from ..config import settings, AI_PROVIDERS

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    GROQ = "groq"
    BASETEN = "baseten"


@dataclass
class AIResponse:
    """AI response structure"""
    content: str
    provider: str
    model: str
    usage: Dict[str, int]
    timestamp: str


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "system", "user", "assistant"
    content: str
    image_url: Optional[str] = None  # For vision models


class AIClient:
    """
    Unified AI client supporting multiple providers
    """
    
    def __init__(
        self,
        provider: str = None,
        model: str = None,
        api_key: str = None
    ):
        self.provider = provider or settings.DEFAULT_AI_PROVIDER
        self.model = model or settings.DEFAULT_AI_MODEL
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Initialize provider-specific clients
        self._init_provider()
    
    def _init_provider(self):
        """Initialize the selected provider"""
        if self.provider == AIProvider.GEMINI.value:
            self._init_gemini()
        elif self.provider == AIProvider.GROQ.value:
            self._init_groq()
        elif self.provider == AIProvider.BASETEN.value:
            self._init_baseten()
        # OpenRouter uses direct HTTP requests
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            import google.generativeai as genai
            api_key = self.api_key or settings.GEMINI_API_KEY
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(self.model or 'gemini-pro')
            else:
                logger.warning("Gemini API key not configured")
        except ImportError:
            logger.error("Google Generative AI package not installed")
    
    def _init_groq(self):
        """Initialize Groq client"""
        try:
            from groq import Groq
            api_key = self.api_key or settings.GROQ_API_KEY
            if api_key:
                self.groq_client = Groq(api_key=api_key)
            else:
                logger.warning("Groq API key not configured")
        except ImportError:
            logger.error("Groq package not installed")
    
    def _init_baseten(self):
        """Initialize Baseten client"""
        api_key = self.api_key or settings.BASETEN_API_KEY
        if not api_key:
            logger.warning("Baseten API key not configured")
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> AIResponse:
        """
        Get chat completion from AI
        """
        if self.provider == AIProvider.OPENROUTER.value:
            return await self._openrouter_chat(messages, temperature, max_tokens, stream)
        elif self.provider == AIProvider.GEMINI.value:
            return await self._gemini_chat(messages, temperature, max_tokens)
        elif self.provider == AIProvider.GROQ.value:
            return await self._groq_chat(messages, temperature, max_tokens, stream)
        elif self.provider == AIProvider.BASETEN.value:
            return await self._baseten_chat(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _openrouter_chat(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> AIResponse:
        """OpenRouter chat completion"""
        api_key = self.api_key or settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trading-agent.local",
            "X-Title": "AI Trading Agent"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                provider="openrouter",
                model=self.model,
                usage=data.get("usage", {}),
                timestamp=data.get("created", "")
            )
        except Exception as e:
            logger.error(f"OpenRouter error: {e}")
            raise
    
    async def _gemini_chat(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Gemini chat completion"""
        try:
            import google.generativeai as genai
            
            # Convert messages to Gemini format
            chat = self.gemini_model.start_chat(history=[])
            
            # Send messages
            for msg in messages:
                if msg.role == "user":
                    response = chat.send_message(msg.content)
            
            return AIResponse(
                content=response.text,
                provider="gemini",
                model=self.model,
                usage={},
                timestamp=""
            )
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
    
    async def _groq_chat(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> AIResponse:
        """Groq chat completion"""
        try:
            # Use synchronous client in async context
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.model or "llama-3.1-70b-versatile",
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider="groq",
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                timestamp=""
            )
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise
    
    async def _baseten_chat(
        self,
        messages: List[ChatMessage],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Baseten chat completion"""
        api_key = self.api_key or settings.BASETEN_API_KEY
        if not api_key:
            raise ValueError("Baseten API key not configured")
        
        # Baseten uses model-specific endpoints
        model_id = self.model or "llama-3.1-70b"
        url = f"https://model-{model_id}.api.baseten.co/production/predict"
        
        headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for Baseten
        prompt = self._format_messages_for_baseten(messages)
        
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data.get("completion", ""),
                provider="baseten",
                model=self.model,
                usage={},
                timestamp=""
            )
        except Exception as e:
            logger.error(f"Baseten error: {e}")
            raise
    
    def _format_messages_for_baseten(self, messages: List[ChatMessage]) -> str:
        """Format messages for Baseten"""
        formatted = []
        for msg in messages:
            if msg.role == "system":
                formatted.append(f"System: {msg.content}")
            elif msg.role == "user":
                formatted.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                formatted.append(f"Assistant: {msg.content}")
        return "\n\n".join(formatted) + "\n\nAssistant:"
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        mime_type: str = "image/png"
    ) -> AIResponse:
        """
        Analyze image using vision-capable models
        """
        if self.provider == AIProvider.GEMINI.value:
            return await self._gemini_vision(image_data, prompt, mime_type)
        elif self.provider == AIProvider.OPENROUTER.value:
            return await self._openrouter_vision(image_data, prompt, mime_type)
        else:
            raise ValueError(f"Provider {self.provider} does not support vision")
    
    async def _gemini_vision(
        self,
        image_data: bytes,
        prompt: str,
        mime_type: str
    ) -> AIResponse:
        """Gemini vision analysis"""
        try:
            import google.generativeai as genai
            
            vision_model = genai.GenerativeModel('gemini-pro-vision')
            
            response = vision_model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_data}
            ])
            
            return AIResponse(
                content=response.text,
                provider="gemini",
                model="gemini-pro-vision",
                usage={},
                timestamp=""
            )
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            raise
    
    async def _openrouter_vision(
        self,
        image_data: bytes,
        prompt: str,
        mime_type: str
    ) -> AIResponse:
        """OpenRouter vision analysis"""
        import base64
        
        api_key = self.api_key or settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OpenRouter API key not configured")
        
        url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
        
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "anthropic/claude-3-opus" if "opus" in self.model else "anthropic/claude-3.5-sonnet",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    }
                ]
            }]
        }
        
        try:
            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                provider="openrouter",
                model=self.model,
                usage=data.get("usage", {}),
                timestamp=""
            )
        except Exception as e:
            logger.error(f"OpenRouter vision error: {e}")
            raise
    
    async def analyze_chart(
        self,
        image_data: bytes,
        symbol: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Specialized chart analysis
        """
        prompt = f"""Analyze this {symbol} {timeframe} chart for trading signals.

Please provide:
1. Current trend direction (bullish/bearish/neutral)
2. Key support and resistance levels
3. Any visible chart patterns
4. Potential entry/exit points
5. Risk assessment

Be concise and actionable."""
        
        response = await self.analyze_image(image_data, prompt)
        
        return {
            "analysis": response.content,
            "symbol": symbol,
            "timeframe": timeframe,
            "provider": response.provider,
            "model": response.model
        }
    
    def get_available_models(self) -> List[str]:
        """Get available models for current provider"""
        provider_config = AI_PROVIDERS.get(self.provider, {})
        return provider_config.get("models", [])
    
    @staticmethod
    def get_available_providers() -> Dict[str, Any]:
        """Get all available providers"""
        return AI_PROVIDERS
    
    async def close(self):
        """Close client"""
        await self.client.aclose()


# Singleton instance
_ai_client: Optional[AIClient] = None


def get_ai_client(
    provider: str = None,
    model: str = None
) -> AIClient:
    """Get or create AI client singleton"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient(provider, model)
    return _ai_client
