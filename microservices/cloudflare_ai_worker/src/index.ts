/**
 * AI Healthcare System - Cloudflare Workers AI Endpoint
 * Exposes an OpenAI-compatible /v1/chat/completions API route
 * powered by Groq (acting as a fast edge proxy like the portfolio).
 */

export interface Env {
  GROQ_API_KEY: string;
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

    if (!env.GROQ_API_KEY) {
      return new Response(JSON.stringify({ error: "Worker missing GROQ_API_KEY secret" }), {
        status: 500,
        headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
      });
    }

    try {
      const body: any = await request.json();
      
      const upstreamReq = {
         model: body.model || 'llama-3.3-70b-versatile',
         messages: body.messages || [],
         temperature: body.temperature || 0.4,
         max_tokens: body.max_tokens || 1000
      };
      
      const upstream = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + env.GROQ_API_KEY,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(upstreamReq),
      });
      
      const responseData = await upstream.json();
      
      return new Response(JSON.stringify(responseData), {
        status: upstream.status,
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
