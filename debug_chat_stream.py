import asyncio
import os
from unittest.mock import patch, MagicMock
from backend.core_ai import chat_stream

async def mock_stream_gemini(*args, **kwargs):
    yield "Patient's email is john"
    yield ".doe@gmail"
    yield ".com and SSN is "
    yield "111-22"
    yield "-3333."

async def run_test():
    with patch('backend.core_ai.get_ollama_models', return_value=[]), \
         patch('backend.core_ai.has_gemini_api_key', return_value=True), \
         patch('backend.core_ai._stream_gemini', side_effect=mock_stream_gemini), \
         patch.dict(os.environ, {'SEMANTIC_CACHE_ENABLED': 'false'}):
        
        chunks = []
        try:
            async for chunk in chat_stream([{'role': 'user', 'content': 'Can I get contact details?'}]):
                chunks.append(chunk)
            print(''.join(chunks))
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(run_test())
