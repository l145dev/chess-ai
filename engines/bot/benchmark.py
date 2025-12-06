import chess
import time
from engines.bot.main import get_move

def benchmark():
    board = chess.Board()
    # A slightly complex position to avoid instant book/draws
    board.set_fen("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3")
    
    print("Starting Benchmark...")
    start_time = time.time()
    
    # Run depth 3 for speed check
    move = get_move(board, depth=3)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Time taken: {duration:.4f} seconds")
    print(f"Move found: {move}")

if __name__ == "__main__":
    benchmark()
