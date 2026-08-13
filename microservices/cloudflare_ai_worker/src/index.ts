/**
 * AI Healthcare System - Cloudflare Workers AI Endpoint
 * Native @cloudflare/ai deployment for:
 * - OpenAI-compatible /v1/chat/completions (Llama 3.1 8B / Llama 4 Scout)
 * - Dense Vector Embeddings /embed (BAAI BGE-base-en-v1.5)
 * - Semantic Cross-Encoder Reranking /rerank (BAAI BGE-reranker-base)
 * - Voice Dictation /v1/audio/transcriptions (OpenAI Whisper)
 * - Multilingual Translation /translate (Meta M2M-100)
 */

export interface Env {
  AI: any;
  GROQ_API_KEY?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Handle CORS preflight requests
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Handle Health check and Root endpoint
    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/health" || url.pathname === "/healthz")) {
      return new Response(JSON.stringify({
        status: "healthy",
        service: "AI Healthcare System - Cloudflare Workers AI Edge Inference",
        version: "3.0.0",
        endpoints: [
          "/chat/completions",
          "/v1/chat/completions",
          "/embed",
          "/rerank",
          "/translate",
          "/v1/audio/transcriptions"
        ],
        models: {
          llm: "@cf/meta/llama-3.1-8b-instruct",
          embeddings: "@cf/baai/bge-base-en-v1.5",
          reranker: "@cf/baai/bge-reranker-base",
          speech_to_text: "@cf/openai/whisper",
          translation: "@cf/meta/m2m100-1.2b"
        }
      }), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }

    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    try {
      // 1. EMBEDDINGS ENDPOINT
      if (url.pathname === "/embed") {
        const body: any = await request.json();
        const embedResponse = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
          text: body.text
        });
        
        return new Response(JSON.stringify(embedResponse), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }
      
      // 2. RERANKING ENDPOINT
      if (url.pathname === "/rerank") {
        const body: any = await request.json();
        const contexts = (body.sentences || []).map((text: string) => ({ text }));
        const rerankResponse = await env.AI.run('@cf/baai/bge-reranker-base', {
          query: body.query,
          contexts: contexts
        });
        
        return new Response(JSON.stringify(rerankResponse), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }

      // 3. TRANSLATION ENDPOINT
      if (url.pathname === "/translate") {
        const body: any = await request.json();
        const translationResponse = await env.AI.run('@cf/meta/m2m100-1.2b', {
          text: body.text,
          source_lang: body.source_lang || "en",
          target_lang: body.target_lang || "es"
        });

        return new Response(JSON.stringify(translationResponse), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }

      // 4. WHISPER AUDIO TRANSCRIPTION ENDPOINT
      if (url.pathname === "/v1/audio/transcriptions" || url.pathname === "/audio/transcriptions") {
        const arrayBuffer = await request.arrayBuffer();
        const audioBytes = new Uint8Array(arrayBuffer);
        const transcriptResponse = await env.AI.run('@cf/openai/whisper', {
          audio: [...audioBytes]
        });

        return new Response(JSON.stringify(transcriptResponse), {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }

      // 5. CHAT COMPLETIONS ENDPOINT
      if (url.pathname === "/v1/chat/completions" || url.pathname === "/chat/completions") {
        const body: any = await request.json();
        const isStream = body.stream === true;
        const messages = body.messages || [];
        
        // If Groq API Key is configured in the Cloudflare Worker secrets, route through Groq
        if (env.GROQ_API_KEY) {
          const groqBody = {
            model: "llama-3.1-8b-instant",
            messages: messages,
            temperature: body.temperature || 0.7,
            stream: isStream
          };
          
          const groqRequest = new Request("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${env.GROQ_API_KEY}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify(groqBody)
          });
          
          const groqResponse = await fetch(groqRequest);
          const newHeaders = new Headers(groqResponse.headers);
          newHeaders.set("Access-Control-Allow-Origin", "*");
          return new Response(groqResponse.body, {
            status: groqResponse.status,
            headers: newHeaders
          });
        }
        
        // Native Cloudflare Workers AI Model
        const model = '@cf/meta/llama-3.1-8b-instruct';
        
        if (isStream) {
          const stream = await env.AI.run(model, {
            messages: messages,
            stream: true
          });
          
          return new Response(stream, {
            headers: {
              "Content-Type": "text/event-stream",
              "Access-Control-Allow-Origin": "*"
            }
          });
        } else {
          const response = await env.AI.run(model, {
            messages: messages,
          });
          
          const openAiResponse = {
            id: "chatcmpl-" + Math.random().toString(36).substring(2),
            object: "chat.completion",
            created: Math.floor(Date.now() / 1000),
            model: model,
            choices: [
              {
                index: 0,
                message: {
                  role: "assistant",
                  content: response.response,
                },
                finish_reason: "stop",
              },
            ],
            usage: {
              prompt_tokens: 0,
              completion_tokens: 0,
              total_tokens: 0,
            },
          };
          
          return new Response(JSON.stringify(openAiResponse), {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "Access-Control-Allow-Origin": "*"
            }
          });
        }
      }

      return new Response("Not Found", { status: 404 });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), { 
        status: 500,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }
  },
};
