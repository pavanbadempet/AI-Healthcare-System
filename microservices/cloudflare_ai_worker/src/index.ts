/**
 * AI Healthcare System - Cloudflare Workers AI Endpoint
 * Native @cloudflare/ai deployment for OpenAI-compatible /v1/chat/completions
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
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    // Only allow POST to /chat/completions, /v1/chat/completions, /rerank, or /embed
    if (request.method !== "POST" || (url.pathname !== "/v1/chat/completions" && url.pathname !== "/chat/completions" && url.pathname !== "/rerank" && url.pathname !== "/embed")) {
      return new Response("Not Found", { status: 404 });
    }

    try {
      const body: any = await request.json();
      
      if (url.pathname === "/embed") {
        // Handle embedding request
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
      
      if (url.pathname === "/rerank") {
        // Handle reranking request
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

      const isStream = body.stream === true;
      const messages = body.messages || [];
      
      // If Groq API Key is configured in the Cloudflare Worker secrets, use Groq
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
        
        // Pass through the response (handles both stream and non-stream seamlessly)
        const newHeaders = new Headers(groqResponse.headers);
        newHeaders.set("Access-Control-Allow-Origin", "*");
        return new Response(groqResponse.body, {
          status: groqResponse.status,
          headers: newHeaders
        });
      }
      
      // Fallback to Cloudflare AI if Groq is not configured
      const model = '@cf/meta/llama-4-scout-17b-16e-instruct';
      
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
        
        // Format as OpenAI compatible response
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
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), { 
        status: 500,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }
  },
};
