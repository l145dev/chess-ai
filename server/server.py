import sys
import os
import chess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Ensure the root directory is in sys.path to allow importing from engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from engines.bot.main import get_move
except ImportError as e:
    print(f"Error importing engine: {e}")
    print("Make sure you are running this script from the project root using: python -m server.server")
    sys.exit(1)

app = FastAPI()

class MoveRequest(BaseModel):
    fen: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Chess Engine Server is running"}

@app.post("/move")
def predict_move(request: MoveRequest):
    try:
        board = chess.Board(request.fen)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FEN string")

    if board.is_game_over():
         raise HTTPException(status_code=400, detail="Game is already over")

    # Get the best move from the engine
    # Adjust depth if needed, default is 5 in main.py
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

if __name__ == "__main__":
    uvicorn.run("server.server:app", host="0.0.0.0", port=8000, reload=True)
