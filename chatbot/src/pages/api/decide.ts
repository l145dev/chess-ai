import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  try {
    const data = await request.json();
    const prompt = data.prompt?.toLowerCase() || "";

    // Mock logic:
    // If prompt contains "play", "move", "game", "e4", etc., return a new game or move.
    // Else return text.

    // For manual verification flow:
    // User: "start game" -> Returns start FEN
    // User: "e4" -> Returns FEN with e4 played (simplified mock)

    if (prompt.includes("start") || prompt.includes("play")) {
      return new Response(
        JSON.stringify({
          type: "fen",
          content: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
          message: "Let's play! I'm ready.",
        })
      );
    }

    // Default text response
    return new Response(
      JSON.stringify({
        type: "text",
        content: `I'm a chess bot. You said: "${data.prompt}". Ask me to start a game!`,
      })
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: "Invalid request" }), {
      status: 400,
    });
  }
};
