# 05 — AI & Chat System

## Q: How does the AI chatbot work?

Architecture: **RAG + Gemini + SSE Streaming**

```
User Message → RAG Search → Build Prompt → Gemini API → SSE Stream → Frontend
```

1. User sends a health question
2. **RAG search**: Find relevant patient records/medical knowledge using vector similarity
3. **Prompt building**: System prompt + RAG context + user message + chat history
4. **Gemini API**: Send to Google Gemini for generation
5. **SSE streaming**: Stream response token-by-token to frontend

## Q: What is RAG and why do you use it?

**RAG = Retrieval-Augmented Generation**

**Problem without RAG:** LLMs don't know the patient's history. If a diabetic patient asks "what should I eat?", a generic AI gives generic advice.

**With RAG:** We search the patient's health records for relevant context, inject it into the prompt, so the AI gives **personalized** advice based on their actual condition.

```python
# 1. Store patient records as embeddings
def add_record(user_id, record_type, data):
    text = f"Patient has {record_type}: {data}"
    embedding = compute_embedding(text)
    store.add(embedding, metadata={"user_id": user_id})

# 2. At chat time, search for relevant records
def search_context(query, user_id):
    query_embedding = compute_embedding(query)
    results = store.search(query_embedding, filter={"user_id": user_id})
    return [r.text for r in results[:5]]  # Top 5 relevant records

# 3. Build prompt with context
context = search_context("what should I eat?", user_id=42)
prompt = f"""
{SYSTEM_PROMPT}

Patient Context:
{context}

User Question: what should I eat?
"""
```

## Q: How does SSE streaming work on the backend?

```python
@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    async def generate():
        # Build prompt with RAG context
        context = rag.search(request.message, user_id)
        prompt = build_prompt(request.message, context, request.history)
        
        # Stream from Gemini
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            token = chunk.text
            yield f"data: {json.dumps({'token': token, 'status': 'streaming'})}\n\n"
        
        yield f"data: {json.dumps({'status': 'complete'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Q: What is core_ai.py and why can't route handlers call AI directly?

**Rule**: All AI calls go through `core_ai.py`. Never call `genai.GenerativeModel` in a route handler.

**Reasons:**
1. **Provider abstraction** — Switch from Gemini to OpenAI by changing one file
2. **Centralized error handling** — Retries, timeouts, graceful fallbacks
3. **Cost control** — Rate limiting and usage tracking in one place
4. **Testing** — Mock one function to disable all AI in tests
5. **Fallback chain** — Gemini → Ollama (local) → graceful error message

## Q: What are the system prompts?

All prompts live in `prompt_registry.py` (never inline):

```python
HEALTH_CHAT_PROMPT = """You are a medical AI assistant for the AI Healthcare System.
- Always include a medical disclaimer
- Never provide definitive diagnoses
- Recommend consulting a healthcare professional for serious concerns
- Use evidence-based information
- Be empathetic and supportive"""
```

**Why a registry?**
- Version control for prompts
- A/B testing different prompts
- No prompt duplication across handlers
- Medical disclaimers enforced consistently

## Q: How does the Ollama fallback work?

```python
# ollama_routes.py — Local LLM support
# If Gemini API is down, use locally running Ollama
@router.post("/chat/local")
def chat_local(request: ChatRequest):
    response = requests.post("http://localhost:11434/api/generate",
        json={"model": "llama2", "prompt": request.message})
    return {"reply": response.json()["response"]}
```

This means the system can work **completely offline** using a local LLM.
