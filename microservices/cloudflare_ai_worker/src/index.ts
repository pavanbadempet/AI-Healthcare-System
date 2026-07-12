/**
 * AI Healthcare System - Cloudflare Workers AI Endpoint
 * Native @cloudflare/ai deployment for OpenAI-compatible /v1/chat/completions
 */

export interface Env {
  AI: any;
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

    // Only allow POST to /chat/completions or /v1/chat/completions
    if (request.method !== "POST" || (url.pathname !== "/v1/chat/completions" && url.pathname !== "/chat/completions")) {
      return new Response("Not Found", { status: 404 });
    }

    try {
      const body: any = await request.json();
      
      const requestedModel = body.model || '';
      // Cloudflare Workers AI natively supports Llama 3.1 8B. We force this model
      // so that it runs the most powerful edge model regardless of what the backend sends.
      const model = '@cf/meta/llama-4-scout-17b-16e-instruct';
      const messages = body.messages || [];
      
      // We stream if requested, but for now we'll just return the full response 
      // (The backend pseudo-streams the whole response anyway if cloudflare doesn't SSE)
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
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), { 
        status: 500,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }
  },
};
