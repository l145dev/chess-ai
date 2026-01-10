import type { APIRoute } from "astro";
import { Chess } from "chess.js";
import { groq } from "../../lib/groq";
import { parseFenToText } from "../../utils/fenParser";

// Models
const MODEL_ROUTER = "llama-3.1-8b-instant";
const MODEL_SOLVER = "llama-3.3-70b-versatile";

const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

export const POST: APIRoute = async ({ request }) => {
  try {
    const { prompt, currentFen } = await request.json();

    if (!prompt) {
      return new Response(JSON.stringify({ error: "Prompt is required" }), {
        status: 400,
      });
    }

    // --- STEP 0: DIRECT MOVE CHECK (LAN/SAN) ---
    // If we have a board, checking if the input is a valid move takes precedence.
    if (currentFen) {
      try {
        const chess = new Chess(currentFen);

        // Regex for LAN (e.g., e2e4, a7a8q)
        const lanRegex = /^[a-h][1-8][a-h][1-8][qrbn]?$/;

        let move = null;

        if (lanRegex.test(prompt)) {
          // Parse LAN to { from, to, promotion }
          const from = prompt.substring(0, 2);
          const to = prompt.substring(2, 4);
          const promotion = prompt.length === 5 ? prompt[4] : undefined;

          try {
            move = chess.move({ from, to, promotion });
          } catch (e) {
            move = null;
          }
        } else {
          // Fallback: Try playing it as SAN (User might still type "Nf3")
          try {
            move = chess.move(prompt);
          } catch (e) {
            move = null;
          }
        }

        if (move) {
          return new Response(
            JSON.stringify({
              type: "fen",
              content: chess.fen(),
              move: move.lan, // Return LAN for consistency
              message: null, // No text message needed, just action
            })
          );
        }
      } catch (e) {
        console.error("Chess.js error:", e);
      }
    }

    // --- STEP 1: CLASSIFICATION (ROUTER) ---
    // Classify user intent: START_GAME or QUESTION
    const classificationPrompt = `
      You are a chess assistant router. Classify the user's intent based on the prompt.
      
      Intent Categories:
      1. START_GAME: User wants to start a new game (e.g., "play chess", "start game as white", "I want to be black").
      2. QUESTION: User is asking a question or making a statement (e.g., "Who is Magnus?", "Explain this board").
      
      Output JSON format ONLY:
      {
        "intent": "START_GAME" | "QUESTION",
        "side": "white" | "black" | "random" | null, // Only for START_GAME
        "requiresBoard": boolean // True if the question is about the current board state
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
      const userSide = side ? side.toLowerCase() : "random";
      const finalSide =
        userSide === "random"
          ? Math.random() < 0.5
            ? "white"
            : "black"
          : userSide;

      return new Response(
        JSON.stringify({
          type: "start_game",
          side: finalSide,
          fen: START_FEN,
          // If user is black, they need the bot to move first (autoPlay).
          autoPlay: finalSide === "black",
          message: `Game started! You are playing as ${finalSide}. ${
            finalSide === "white" ? "(Your move)" : "(Bot is moving...)"
          }`,
        })
      );
    }

    // CASE B: QUESTION
    if (intent === "QUESTION") {
      let systemContext =
        'You are a helpful, premium chess assistant. Be concise, professional, and knowledgeable. If the user wants to know what this is, respond saying that you are a custom NNUE engine which the user can play with by saying "start game (as white/black/random)".';

      if (requiresBoard && currentFen) {
        const boardDescription = parseFenToText(currentFen);
        systemContext += `\n\nCURRENT BOARD STATE:\n${boardDescription}\n\nThe user is asking about this specific board position. Use the provided details to reason your answer.`;
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
