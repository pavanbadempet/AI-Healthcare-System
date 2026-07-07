/**
 * AI Healthcare System - Cloudflare Workers AI Endpoint
 * Exposes an OpenAI-compatible /v1/chat/completions API route
 * powered by Cloudflare's Edge GPUs (@cf/meta/llama-3-8b-instruct)
 */

export interface Env {
  AI: any;
  // Optional: add a secret token to protect your endpoint
  // CUSTOM_AUTH_TOKEN: string;
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

    // Only allow POST to /v1/chat/completions
    if (request.method !== "POST" || url.pathname !== "/v1/chat/completions") {
      return new Response("Not Found", { status: 404 });
    }

    try {
      const body: any = await request.json();
      
      // Cloudflare Workers AI expects messages in the { role, content } format
      const messages = body.messages || [];
      
      // If no model is specified, default to Llama 3 8B
      const model = body.model || "@cf/meta/llama-3-8b-instruct";

      // Run Inference on Cloudflare Edge GPUs
      const response = await env.AI.run(model, {
        messages: messages
      });

      // Format response to be OpenAI-compatible
      const openAiResponse = {
        id: crypto.randomUUID(),
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: model,
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: response.response || ""
            },
            finish_reason: "stop"
          }
        ],
        usage: {
          prompt_tokens: 0,
          completion_tokens: 0,
          total_tokens: 0
        }
      };

      return new Response(JSON.stringify(openAiResponse), {
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
