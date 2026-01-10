import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  // Receives FEN in body
  // Returns next FEN (random move or fixed response for testing)

  try {
    const data = await request.json();

    // Forward to Python Engine Server
    const response = await fetch("http://localhost:8000/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fen: data.fen }),
    });

    if (!response.ok) {
      throw new Error(`Engine Server Error: ${response.statusText}`);
    }

    const result = await response.json();
    return new Response(JSON.stringify(result));
  } catch (e) {
    console.error("Engine API Error:", e);
    return new Response(
      JSON.stringify({
        error:
          "Failed to connect to Chess Engine. Is the python server running?",
      }),
      { status: 500 }
    );
  }
};
