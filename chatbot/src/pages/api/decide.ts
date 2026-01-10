import type { APIRoute } from "astro";
import { groq } from "../../lib/groq";
import { parseFenToText } from "../../utils/fenParser";

export const prerender = false;

// Models
const MODEL_ROUTER = "llama-3.1-8b-instant";
const MODEL_SOLVER = "llama-3.3-70b-versatile";

export const POST: APIRoute = async ({ request }) => {
  try {
    const { prompt, currentFen } = await request.json();

    if (!prompt) {
      return new Response(JSON.stringify({ error: "Prompt is required" }), {
        status: 400,
      });
    }

    // --- STEP 1: CLASSIFICATION (ROUTER) ---
    // Classify user intent: START_GAME or QUESTION
    const classificationPrompt = `
      You are a chess assistant router. Classify the user's intent based on the prompt.
      
      Intent Categories:
      1. START_GAME: User wants to start a new game (e.g., "play chess", "start game as white", "I want to be black").
      2. QUESTION: User is asking a question or making a statement (e.g., "Who is Magnus?", "Explain this board", "What's the best move?", "pawn to e4"). Note: "pawn to e4" is arguably a move, but for now treat it as a statement unless explicitly starting a game.
      
      Output JSON format ONLY:
      {
        "intent": "START_GAME" | "QUESTION",
        "side": "white" | "black" | "random" | null, // Only for START_GAME
        "requiresBoard": boolean // True if the question is about the current board state (e.g., "best move?", "eval?", "what piece is this?")
      }

      User Prompt: "${prompt}"
    `;

    const routerCompletion = await groq.chat.completions.create({
      messages: [
        { role: "system", content: "You are a JSON-only response bot." },
        { role: "user", content: classificationPrompt },
      ],
      model: MODEL_ROUTER,
      temperature: 0,
      response_format: { type: "json_object" },
    });

    const routerResponse = JSON.parse(
      routerCompletion.choices[0]?.message?.content || "{}"
    );
    const { intent, side, requiresBoard } = routerResponse;

    // --- STEP 2: EXECUTION (SOLVER) ---

    // CASE A: START GAME
    if (intent === "START_GAME") {
      // For now, return the starting FEN constant.
      // In the future, this might set up a session or configure the engine side.
      const START_FEN =
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
      return new Response(
        JSON.stringify({
          type: "fen",
          content: START_FEN,
          message: `Game started! You are playing as ${
            side || "random"
          }. Good luck!`,
        })
      );
    }

    // CASE B: QUESTION
    if (intent === "QUESTION") {
      let systemContext =
        "You are a helpful, premium chess assistant. Be concise, professional, and knowledgeable.";

      if (requiresBoard && currentFen) {
        const boardDescription = parseFenToText(currentFen);
        systemContext += `\n\nCURRENT BOARD STATE:\n${boardDescription}\n\nThe user is asking about this specific board position. Use the provided details to reason your answer.`;
      } else if (requiresBoard && !currentFen) {
        // User asked about board but no FEN provided (start of chat maybe?)
        // context += "\n\n(No active board state provided, answer generally)";
      }

      const solverCompletion = await groq.chat.completions.create({
        messages: [
          { role: "system", content: systemContext },
          { role: "user", content: prompt },
        ],
        model: MODEL_SOLVER,
        temperature: 0.5,
        max_tokens: 500,
      });

      const answer =
        solverCompletion.choices[0]?.message?.content ||
        "I couldn't process that request.";

      return new Response(
        JSON.stringify({
          type: "text",
          content: answer,
        })
      );
    }

    // Fallback
    return new Response(
      JSON.stringify({
        type: "text",
        content: "I'm unsure how to proceed with that request.",
      })
    );
  } catch (error) {
    console.error("Error in /api/decide:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), {
      status: 500,
    });
  }
};
