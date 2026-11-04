import json, os, time
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parents[2] / '.env')

class LLMError(RuntimeError): pass

class LLMClient:
    def __init__(self, api_key: str, model: str, max_retries: int=3, temperature: float=0.0,
                 min_request_interval_seconds: float=13.0, rate_limit_retry_seconds: float=65.0):
        self.model=model; self.max_retries=max_retries; self.temperature=temperature
        self.min_interval=min_request_interval_seconds; self.rate_wait=rate_limit_retry_seconds
        self.client=genai.Client(api_key=api_key); self._last_request_time=0.0

    @classmethod
    def from_config(cls, cfg: dict[str, Any]):
        key=os.environ.get(cfg.get('api_key_env','GEMINI_API_KEY'),'').strip()
        model=os.environ.get(cfg.get('model_env','GEMINI_MODEL'),'').strip()
        missing=[]
        if not key: missing.append(cfg.get('api_key_env','GEMINI_API_KEY'))
        if not model: missing.append(cfg.get('model_env','GEMINI_MODEL'))
        if missing: raise LLMError('Missing required environment variable(s): '+', '.join(missing))
        return cls(key, model, int(cfg.get('max_retries',3)), float(cfg.get('temperature',0.0)),
                   float(cfg.get('min_request_interval_seconds',13)), float(cfg.get('rate_limit_retry_seconds',65)))

    def _wait(self):
        remaining=self.min_interval-(time.monotonic()-self._last_request_time)
        if remaining>0: time.sleep(remaining)
        self._last_request_time=time.monotonic()

    def classify_json(self, prompt: str) -> dict[str, Any]:
        last=None
        for attempt in range(1,self.max_retries+1):
            try:
                self._wait()
                response=self.client.models.generate_content(model=self.model, contents=prompt,
                    config=types.GenerateContentConfig(temperature=self.temperature,response_mime_type='application/json'))
                text=(response.text or '').strip()
                if not text: raise LLMError('Gemini returned an empty response.')
                parsed=json.loads(text)
                if not isinstance(parsed,dict): raise LLMError('Gemini JSON response is not an object.')
                return parsed
            except Exception as exc:
                last=exc
                if attempt<self.max_retries:
                    time.sleep(self.rate_wait if ('429' in str(exc) or 'RESOURCE_EXHAUSTED' in str(exc)) else min(2**(attempt-1),8))
        raise LLMError(f'Gemini request failed after {self.max_retries} attempts: {last}')
