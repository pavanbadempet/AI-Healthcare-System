# 05 — AI & Chat System (Complete Deep-Dive)

> Everything about how the AI chatbot works — RAG, Gemini, streaming, prompts, fallbacks.

---

## Q: How does the AI chatbot work? Explain the FULL architecture.

### The Complete Flow (7 Steps):

```
User types: "What diet should I follow for diabetes?"
    ↓
Step 1: Frontend sends POST /chat/stream with message + auth token
    ↓
Step 2: Backend extracts user_id from JWT token
    ↓
Step 3: RAG Search — find relevant patient records in vector store
         Query: "diet diabetes" → Finds: "Patient has diabetes prediction: High Risk"
    ↓
Step 4: Prompt Building — combine system prompt + RAG context + user message + history
         System prompt: "You are a medical AI assistant..."
         Context: "This patient was assessed as High Risk for diabetes"
         User: "What diet should I follow for diabetes?"
         History: [previous messages]
    ↓
Step 5: Gemini API Call — send assembled prompt, request streaming
    ↓
Step 6: SSE Streaming — each token streamed back as Server-Sent Event
         data: {"token": "For", "status": "streaming"}
         data: {"token": " diabetes", "status": "streaming"}
         data: {"token": " management", "status": "streaming"}
         ...
         data: {"status": "complete"}
    ↓
Step 7: Frontend renders tokens in real-time as they arrive
```

---

## Q: What is RAG and why do you use it? Explain with a detailed example.

**RAG = Retrieval-Augmented Generation**

### The Problem Without RAG:
```
User: "What should I eat?"
AI (without RAG): "Here's a general healthy diet: fruits, vegetables, lean protein..."
                   ← GENERIC. Doesn't know the patient has diabetes.
```

### The Solution With RAG:
```
User: "What should I eat?"
RAG Search: Finds patient record → "Diabetes: High Risk, BMI: 35, Age: 55"
AI (with RAG): "Given your diabetes risk assessment (High Risk) and BMI of 35, 
                I recommend focusing on low-glycemic foods: non-starchy vegetables,
                whole grains, lean proteins. Avoid sugary drinks and refined carbs.
                Please consult your doctor for a personalized plan."
                ← PERSONALIZED. Knows the patient's actual condition.
```

### How RAG Works Internally:

```python
# Step 1: When a prediction is made, store it as an embedding
def store_health_record(user_id: int, record_type: str, prediction: str):
    text = f"Patient health record: {record_type} assessment result: {prediction}"
    embedding = compute_embedding(text)  # Convert text to 768-dim vector
    vector_store.add(
        embedding=embedding,
        metadata={"user_id": user_id, "type": record_type},
        text=text
    )

# Step 2: When user asks a question, search for relevant records
def search_context(query: str, user_id: int, top_k: int = 5) -> list[str]:
    query_embedding = compute_embedding(query)
    
    # Search vector store — find records most similar to the question
    results = vector_store.search(
        query_embedding,
        filter={"user_id": user_id},  # Only this patient's records!
        top_k=top_k
    )
    
    return [r.text for r in results]
    # Returns: ["Patient health record: diabetes assessment: High Risk",
    #           "Patient health record: heart assessment: Healthy Heart"]

# Step 3: Build the prompt with retrieved context
def build_prompt(user_message: str, context: list[str], history: list) -> str:
    return f"""
{SYSTEM_PROMPT}

=== PATIENT HEALTH CONTEXT ===
{chr(10).join(context)}

=== CONVERSATION HISTORY ===
{format_history(history)}

=== CURRENT QUESTION ===
{user_message}

Remember: Always include a medical disclaimer. Never provide definitive diagnoses.
"""
```

### Why RAG Instead of Fine-Tuning?

| Approach | RAG | Fine-Tuning |
|---|---|---|
| Data needed | Just store records | Thousands of training examples |
| Update speed | Instant (add record → searchable) | Hours/days to retrain |
| Cost | ~$0 (vector store is local) | $100+ per fine-tune |
| Patient-specific | Yes (filter by user_id) | No (model-level) |
| Privacy | Records stay in YOUR database | Records sent to OpenAI/Google |
| My choice | **YES** | No |

---

## Q: How does SSE streaming work? Show the real implementation.

### What is SSE?

**SSE (Server-Sent Events)** = Server pushes data to client over a standard HTTP connection. Unlike WebSocket, it's unidirectional (server → client only).

### Backend Implementation:

```python
# backend/streaming_chat.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

router = APIRouter()

class ChatStreamRequest(BaseModel):
    message: str
    history: list = []

@router.post("/chat/stream")
async def stream_chat(request: ChatStreamRequest):
    """Stream AI response token-by-token via SSE."""
    
    async def generate():
        try:
            # 1. RAG: Find relevant patient context
            context = rag_search(request.message, user_id=get_current_user_id())
            
            # 2. Build prompt from registry (NEVER inline prompts)
            prompt = prompt_registry.build_chat_prompt(
                user_message=request.message,
                context=context,
                history=request.history
            )
            
            # 3. Call Gemini via core_ai.py (NEVER call API directly)
            model = core_ai.get_model()
            response = model.generate_content(prompt, stream=True)
            
            # 4. Stream each token as SSE event
            for chunk in response:
                if chunk.text:
                    event_data = json.dumps({
                        "token": chunk.text,
                        "status": "streaming"
                    })
                    yield f"data: {event_data}\n\n"
            
            # 5. Send completion signal
            yield f"data: {json.dumps({'status': 'complete'})}\n\n"
            
        except Exception as e:
            # Stream error to client instead of breaking connection
            error_data = json.dumps({
                "error": "AI service temporarily unavailable",
                "status": "error"
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )
```

### Frontend Implementation:

```typescript
// frontend/src/lib/api.ts

export async function streamChat(
    message: string,
    history: ChatMessage[],
    onToken: (token: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders(),
        },
        body: JSON.stringify({ message, history }),
    });

    if (!response.ok) {
        onError('Failed to connect to AI');
        return;
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.status === 'streaming' && data.token) {
                    onToken(data.token);  // Append token to chat UI
                } else if (data.status === 'complete') {
                    onComplete();
                } else if (data.status === 'error') {
                    onError(data.error);
                }
            }
        }
    }
}
```

### Why SSE Over WebSocket?

| Feature | SSE | WebSocket |
|---|---|---|
| Direction | Server → Client only | Bidirectional |
| Protocol | Standard HTTP | WebSocket upgrade handshake |
| Auto-reconnect | Built-in | Must implement manually |
| Proxy support | Works through all proxies | Some proxies block |
| Complexity | Simple | Complex |
| My use case | Chat streaming (server sends tokens) | Not needed |

**Decision**: Chat is unidirectional — the server streams tokens to the client. SSE is simpler, auto-reconnects, and works through all HTTP proxies. WebSocket adds complexity with zero benefit for this use case.

---

## Q: What is core_ai.py and why can't route handlers call AI directly?

### The Rule (from AGENTS.md):
> "All AI inference must go through `backend/core_ai.py` — never call provider APIs directly."

### What core_ai.py Does:

```python
# backend/core_ai.py

import google.generativeai as genai
import os
import logging

logger = logging.getLogger(__name__)

_model = None

def get_model():
    """Singleton pattern — one model instance for the entire app."""
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-pro")
        logger.info("Gemini model initialized")
    return _model

def generate(prompt: str, stream: bool = False):
    """Central AI gateway — all AI calls go through here."""
    model = get_model()
    try:
        return model.generate_content(prompt, stream=stream)
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        # Fallback to Ollama local LLM
        return _fallback_ollama(prompt)

def _fallback_ollama(prompt: str):
    """If Gemini is down, try local Ollama."""
    try:
        import requests
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama2", "prompt": prompt},
            timeout=30
        )
        return response.json()["response"]
    except Exception:
        return "AI service is temporarily unavailable. Your prediction results are still accessible."
```

### Why This Pattern? 5 Reasons:

1. **Provider abstraction**: Switch from Gemini to OpenAI by changing ONE function. No route handler changes.

2. **Centralized error handling**: Retries, timeouts, and fallback chain (Gemini → Ollama → error message) in one place.

3. **Cost control**: Add rate limiting, usage tracking, token counting in one place:
   ```python
   def generate(prompt, stream=False):
       if daily_token_count > MAX_DAILY_TOKENS:
           raise QuotaExceeded("Daily AI quota reached")
       # ... generate
   ```

4. **Testing**: Mock ONE function to disable all AI in tests:
   ```python
   @pytest.fixture
   def mock_ai(monkeypatch):
       monkeypatch.setattr("backend.core_ai.generate", lambda p, **k: "Mock response")
   ```

5. **API key safety**: Key is loaded once in core_ai, never scattered across route files.

---

## Q: What are system prompts and how does prompt_registry.py work?

### The Rule:
> "Prompts are owned by `prompt_registry.py` — never inline system prompts in route handlers."

### How It Works:

```python
# backend/prompt_registry.py

HEALTH_CHAT_SYSTEM_PROMPT = """You are a medical AI assistant for the AI Healthcare System.

RULES YOU MUST FOLLOW:
1. Always include a medical disclaimer at the end of your response
2. Never provide definitive diagnoses — say "may indicate" not "you have"
3. Recommend consulting a healthcare professional for serious concerns
4. Use evidence-based information from medical literature
5. Be empathetic and supportive in tone
6. If patient context is provided, personalize your response
7. For medication questions, always say "consult your doctor"
8. Never share or reference other patients' data

DISCLAIMER TO INCLUDE:
"Note: This is AI-generated health information, not medical advice. 
Please consult a qualified healthcare professional for clinical decisions."
"""

HEALTH_CHAT_WITH_CONTEXT = """
{system_prompt}

=== PATIENT HEALTH CONTEXT ===
The following are this patient's health assessment results from our system:
{context}

=== CONVERSATION HISTORY ===
{history}

=== PATIENT'S QUESTION ===
{user_message}
"""

def build_chat_prompt(user_message: str, context: list[str], history: list) -> str:
    """Build a complete prompt from components. SINGLE SOURCE OF TRUTH."""
    return HEALTH_CHAT_WITH_CONTEXT.format(
        system_prompt=HEALTH_CHAT_SYSTEM_PROMPT,
        context="\n".join(context) if context else "No health records found.",
        history=_format_history(history),
        user_message=user_message
    )
```

### Why a Registry?

| Without Registry | With Registry |
|---|---|
| Prompts scattered across 10+ files | Single file, easy to find |
| Duplicate disclaimers | Disclaimer defined once |
| Hard to A/B test prompts | Swap prompts in one place |
| Inconsistent tone | Consistent medical guidelines |
| No version control for prompts | Full git history of prompt changes |

---

## Q: How does the Ollama fallback work? Show the complete chain.

```
User sends message
    ↓
Try Gemini API (cloud)
    ├── Success → Stream response back
    └── Fail (timeout, API key invalid, quota exceeded)
        ↓
    Try Ollama (local LLM on localhost:11434)
        ├── Success → Return local response
        └── Fail (Ollama not running)
            ↓
        Return friendly error:
        "AI chat is temporarily unavailable. 
         Your prediction results are still accessible."
```

**Key insight**: Prediction endpoints DON'T need Gemini. They use LOCAL ML models (.pkl files in RAM). Only the chat feature depends on the AI API. So even if both Gemini AND Ollama are down, users can still:
- Run disease predictions
- View their health records
- Manage their profile
- See previous prediction results

This means the system **degrades gracefully** instead of going completely down.

---

## Q: What's the difference between a chat response and a prediction response?

| | Chat Response | Prediction Response |
|---|---|---|
| Source | Gemini AI (cloud) or Ollama (local) | XGBoost/SVM model (.pkl in RAM) |
| Latency | 2-10 seconds (LLM generation) | ~9ms (model inference) |
| Streaming | Yes (SSE, token-by-token) | No (single JSON response) |
| Deterministic | No (LLM is probabilistic) | Yes (same input = same output) |
| Internet needed | Yes (for Gemini) | No (model is local) |
| Cost | ~$0.001 per query (Gemini tokens) | $0 (local computation) |
| Personalized | Yes (RAG context from records) | No (purely input-based) |
| Disclaimer | In the AI response text | In the JSON response field |
