from fastapi import APIRouter
import chess
import re
import json
import random
from server.models import DecideRequest
from server.utils.llm import client, MODEL_ROUTER, MODEL_SOLVER, START_FEN

router = APIRouter()

@router.post("/decide")
async def decide(request: DecideRequest):
    prompt = request.prompt
    current_fen = request.currentFen

    # --- STEP 0: DIRECT MOVE CHECK (LAN/SAN) ---
    if current_fen:
        try:
            board = chess.Board(current_fen)
            move = None
            
            # LAN Regex (e.g. e2e4)
            if re.match(r"^[a-h][1-8][a-h][1-8][qrbn]?$", prompt):
                 try:
                    move = chess.Move.from_uci(prompt)
                    if move not in board.legal_moves:
                        move = None
                 except:
                    pass
            
            # SAN Fallback
            if not move:
                try:
                    move = board.parse_san(prompt)
                except:
                    pass
            
            if move:
                 board.push(move)
                 return {
                    "type": "fen",
                    "content": board.fen(),
                    "move": move.uci(),
                    "message": None
                 }
        except Exception as e:
            print(f"Chess error: {e}")

    # --- STEP 1: CLASSIFICATION ---
    classification_prompt = f"""
    You are a chess assistant router. Classify the user's intent based on the prompt.
    
    Intent Categories:
    1. START_GAME: User wants to start a new game.
    2. QUESTION: User is asking a question.
    3. PLAY_MOVE: User wants to play a move described in natural language (e.g., "play e2 to e4", "move knight to f3"). Only use this if the prompt is clearly an attempt to make a specific move.

    Output JSON format ONLY:
    {{
        "intent": "START_GAME" | "QUESTION" | "PLAY_MOVE",
        "side": "white" | "black" | "random" | null, // Only for START_GAME
        "requiresBoard": boolean // True if the question is about the current board state
    }}

    User Prompt: "{prompt}"
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only response bot."},
                {"role": "user", "content": classification_prompt},
            ],
            model=MODEL_ROUTER,
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        router_response = json.loads(completion.choices[0].message.content)
        intent = router_response.get("intent")
    except Exception as e:
        print(f"Router error: {e}")
        return {"type": "text", "content": "I encountered an error processing your request."}

    # --- STEP 2: EXECUTION ---

    # CASE A: START GAME
    if intent == "START_GAME":
        side = router_response.get("side", "random").lower()
        if side == "random":
            final_side = "white" if random.choice([True, False]) else "black"
        else:
            final_side = side
        
        auto_play = (final_side == "black")
        
        return {
            "type": "start_game",
            "side": final_side,
            "fen": START_FEN,
            "autoPlay": auto_play,
            "message": f"Game started! You are playing as {final_side}. {'(Your move)' if final_side == 'white' else '(Bot is moving...)'}"
        }

    # CASE B: PLAY MOVE (LLM Extraction)
    if intent == "PLAY_MOVE" and current_fen:
        extraction_prompt = f"""
        Extract the chess move from the user's natural language prompt.
        Return the move in UCI format (e.g., "e2e4", "g1f3").
        If the move is invalid or ambiguous, return null.

        User Prompt: "{prompt}"
        Current FEN: "{current_fen}"
        
        Output JSON: {{ "move": "uci_string" | null }}
        """
        
        try:
            extraction = client.chat.completions.create(
                 messages=[
                    {"role": "system", "content": "You are a JSON-only move extractor."},
                    {"role": "user", "content": extraction_prompt},
                ],
                model=MODEL_ROUTER, # Use smaller model for extraction
                temperature=0,
                response_format={"type": "json_object"},
            )
            move_data = json.loads(extraction.choices[0].message.content)
            uci_move = move_data.get("move")
            
            if uci_move:
                board = chess.Board(current_fen)
                try:
                    move = chess.Move.from_uci(uci_move)
                    if move in board.legal_moves:
                        board.push(move)
                        return {
                            "type": "fen",
                            "content": board.fen(),
                            "move": uci_move,
                            "message": None
                        }
                    else:
                        # Move extracted but illegal
                        return {
                            "type": "text",
                            "content": f"I understood you want to play **{uci_move}**, but that move is not legal in the current position. Please try a valid move."
                        }
                except:
                     pass
            
            # If we reach here, extraction failed or produced garbage
            return {
                "type": "text",
                "content": f"I couldn't quite understand which move you want to play from: \"{prompt}\".\n\nCould you please specify the move clearly? For example: **\"play e2 to e4\"** or **\"Nf3\"**."
            }

        except Exception as e:
             print(f"Extraction error: {e}")
             return {
                 "type": "text",
                 "content": "I encountered an error trying to process your move. Please try again."
             }

    # CASE C: QUESTION (or Fallback from PLAY_MOVE failure)
    system_context = 'You are a helpful, premium chess assistant. Be concise, professional, and knowledgeable. If the user wants to know what this is, respond saying that you are a custom NNUE engine which the user can play with by saying "start game (as white/black/random)". If user asks about chess moves, always answer in LAN algebraic notation instead of SAN.\n\nIMPORTANT: You must format your response using Markdown. Use bolding, lists, and code blocks where appropriate to make the text easy to read.'

    if router_response.get("requiresBoard") and current_fen:
        system_context += f"\n\nCURRENT BOARD STATE (FEN): {current_fen}\nThe user is asking about this specific board position."

    try:
        solver_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt},
            ],
            model=MODEL_SOLVER,
            temperature=0.5,
            max_tokens=500,
        )
        answer = solver_completion.choices[0].message.content
        return {"type": "text", "content": answer}
    except Exception as e:
        return {"type": "text", "content": "I couldn't process that request."}
