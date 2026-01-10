import type { APIRoute } from "astro";

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  // Mock Engine
  // Receives FEN in body
  // Returns next FEN (random move or fixed response for testing)

  try {
    const data = await request.json();
    const fen = data.fen;

    // Really dumb mock: just return the same FEN with a dummy message,
    // or if it matches the start position, play 'e4' (rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1)

    let nextFen = fen;
    let move = "";

    if (fen.startsWith("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")) {
      // e4
      nextFen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1";
      move = "e2e4";
    }

    return new Response(
      JSON.stringify({
        fen: nextFen,
        move: move,
        evaluation: 0.5,
      })
    );
  } catch (e) {
    return new Response(JSON.stringify({ error: "Server Error" }), {
      status: 500,
    });
  }
};
