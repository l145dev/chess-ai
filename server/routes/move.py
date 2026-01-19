from fastapi import APIRouter, HTTPException
import chess
import sys
import os

# Add project root to sys.path to find engines module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from engines.bot.main import get_move
except ImportError as e:
    print(f"Error importing engine: {e}")
    # We might want to handle this more gracefully or just fail hard since engine is core
    pass

from server.models import MoveRequest

router = APIRouter()

@router.post("/move")
def predict_move(request: MoveRequest):
    try:
        board = chess.Board(request.fen)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FEN string")

    if board.is_game_over():
         raise HTTPException(status_code=400, detail="Game is already over")

    # Get the best move from the engine
    try:
        move = get_move(board)
        san_move = board.san(move)
        board.push(move)
        
        return {
            "move": move.uci(),
            "fen": board.fen(),
            "san": san_move
        }
    except Exception as e:
        print(f"Engine Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
