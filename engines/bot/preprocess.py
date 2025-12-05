import chess.pgn
import torch
import os
import sys
from tqdm import tqdm

# Ensure we can import from engines.bot
sys.path.append(os.getcwd())
from engines.bot.dataset import get_halfkp_features

# Settings
PGN_PATH = "data/lichess_db.pgn"
OUTPUT_DIR = "data/processed_chunks"
CHUNK_SIZE = 1000000 # estimated 1.5gb RAM per chunks

os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_chunk(indices_us, offsets_us, indices_them, offsets_them, labels, chunk_id):
    """
    Saves data in a 'Compressed Sparse Row' (CSR) style format.
    """
    data = {
        # 1. The giant 1D list of all feature indices
        "indices_us": torch.tensor(indices_us, dtype=torch.int32),
        "offsets_us": torch.tensor(offsets_us, dtype=torch.int32),
        
        "indices_them": torch.tensor(indices_them, dtype=torch.int32),
        "offsets_them": torch.tensor(offsets_them, dtype=torch.int32),
        
        # 3. The scores
        "values": torch.tensor(labels, dtype=torch.float32)
    }
    
    path = f"{OUTPUT_DIR}/chunk_{chunk_id}.pt"
    torch.save(data, path)
    print(f"Saved chunk {chunk_id}: {len(labels)} positions.")

def parse_and_save():
    print(f"Parsing {PGN_PATH}...")
    pgn = open(PGN_PATH)
    
    # Storage buffers
    indices_us = [] 
    offsets_us = [0]
    
    indices_them = []
    offsets_them = [0]
    
    labels = []        # Scores
    
    chunk_id = 0
    game_count = 0
    
    while True:
        try:
            game = chess.pgn.read_game(pgn)
        except Exception:
            break
            
        if game is None: break
        
        # Get result
        result_header = game.headers.get("Result", "*")
        if result_header == "1-0": game_result = 1.0
        elif result_header == "0-1": game_result = 0.0
        elif result_header == "1/2-1/2": game_result = 0.5
        else: continue # Skip unfinished games
            
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
            
            # Get Features for US (side to move)
            feats_us = get_halfkp_features(board, perspective=board.turn)
            indices_us.extend(feats_us)
            offsets_us.append(len(indices_us))
            
            # Get Features for THEM (opponent)
            feats_them = get_halfkp_features(board, perspective=not board.turn)
            indices_them.extend(feats_them)
            offsets_them.append(len(indices_them))
            
            # Add Label
            if board.turn == chess.WHITE:
                labels.append(game_result)
            else:
                labels.append(1.0 - game_result)
            
            # Check Buffer
            if len(labels) >= CHUNK_SIZE:
                save_chunk(indices_us, offsets_us, indices_them, offsets_them, labels, chunk_id)
                
                # Reset buffers
                indices_us = []
                offsets_us = [0]
                indices_them = []
                offsets_them = [0]
                labels = []
                chunk_id += 1
                
        game_count += 1
        if game_count % 100 == 0:
            print(f"Processed {game_count} games...", end='\r')

    # Save remaining data
    if len(labels) > 0:
        save_chunk(indices_us, offsets_us, indices_them, offsets_them, labels, chunk_id)
        
    print(f"\nFinished! Processed {game_count} games.")

if __name__ == "__main__":
    parse_and_save()