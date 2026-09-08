# -*- coding: utf-8 -*-
"""OpenAI-compatible LLM generator provider for Mnemos."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from mnemos.core.config import LLMConfig
from mnemos.core.exceptions import ProviderError

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


class OpenAICompatibleGenerator:
    """LLM provider using the OpenAI SDK.
    
    Supports OpenAI, OpenRouter, vLLM, or any compatible backend.
    """

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self._cfg = config or LLMConfig()
        if OpenAI is None:
            raise ProviderError("openai package is required for OpenAICompatibleGenerator")
            
        self._client = OpenAI(
            api_key=self._cfg.api_key or "sk-mock",
            base_url=self._cfg.base_url,
            timeout=self._cfg.timeout,
        )

    def generate(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate text from prompt.
        
        If schema is provided, uses structured outputs (json_schema format).
        """
        temp = temperature if temperature is not None else self._cfg.temperature
        tokens = max_tokens if max_tokens is not None else self._cfg.max_tokens
        
        messages = []
        if self._cfg.system_prompt:
            messages.append({"role": "system", "content": self._cfg.system_prompt})
        messages.append({"role": "user", "content": prompt})

        params: Dict[str, Any] = {
            "model": self._cfg.model_name,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        if schema is not None:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": schema,
                    "strict": True,
                },
            }

        try:
            resp = self._client.chat.completions.create(**params)
            text = resp.choices[0].message.content or ""
            
            # Remove reasoning tags if any (e.g., from deepseek r1)
            if "</think>" in text:
                text = text.split("</think>")[-1].strip()
                
            out: Dict[str, Any] = {"text": text, "json": None}
            
            if schema is not None:
                try:
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    if start >= 0 and end > start:
                        out["json"] = json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return out
        except Exception as exc:
            raise ProviderError(f"OpenAI generation failed: {exc}") from exc
