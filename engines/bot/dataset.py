import chess
import chess.pgn
import torch
from torch.utils.data import Dataset
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ChessDataset(torch.utils.data.IterableDataset):
    def __init__(self, pgn_file, max_games=None):
        self.pgn_file = pgn_file
        self.max_games = max_games

    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        if worker_info is not None:
            # Multi-worker support is complex for PGN, sticking to single worker for now.
            pass
        
        print(f"Streaming games from {self.pgn_file}...")
        pgn = open(self.pgn_file)
        game_count = 0
        
        while True:
            if self.max_games and game_count >= self.max_games:
                break
            
            offset = pgn.tell()
            try:
                game = chess.pgn.read_game(pgn)
            except Exception:
                break
            
            if game is None:
                break
            
            result_str = game.headers.get("Result", "*")
            if result_str == "1-0":
                result = 1.0
            elif result_str == "0-1":
                result = 0.0
            elif result_str == "1/2-1/2":
                result = 0.5
            else:
                continue
                
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                features = get_halfkp_features(board)
                yield torch.tensor(features, dtype=torch.long), torch.tensor([result], dtype=torch.float32)
            
            game_count += 1
            if game_count % 100 == 0:
                print(f"Streamed {game_count} games.")
        
        pgn.close()

def get_halfkp_features(board: chess.Board):
    """
    Generate HalfKP features for the given board.
    
    HalfKP architecture usually views the board from the perspective of the side to move.
    It computes features for the friendly king and all other pieces.
    
    For this MVP, we will simplify:
    We always view from White's perspective and Black's perspective separately?
    Or just standard NNUE:
    Two accumulators: one for White, one for Black.
    
    Let's return a list of active feature indices.
    Index = KingSq * 640 + PieceSq * 10 + PieceType
    (KingSq: 0-63, PieceSq: 0-63, PieceType: 0-9 (P, N, B, R, Q for both colors))
    
    Total features: 64 * 640 = 40960.
    
    We need to return indices for both 'White King' perspective and 'Black King' perspective?
    Standard NNUE inputs are usually (White features, Black features).
    
    Let's stick to a single perspective for the 'active' side if we want a simple MLP,
    but for NNUE we usually want both.
    
    Let's implement:
    Output: indices for the side to move.
    If it's black to move, we flip the board?
    
    Let's try a simpler approach for the MVP:
    Always encode from White's perspective and Black's perspective, concatenate them?
    
    Let's use the standard:
    Feature index = Orient(KingSq) * 640 + Orient(PieceSq) * 10 + PieceType
    
    PieceType mapping:
    WP: 0, WN: 1, WB: 2, WR: 3, WQ: 4
    BP: 5, BN: 6, BB: 7, BR: 8, BQ: 9
    (King is implicit in the block)
    """
    
    active_indices = []
    
    # We need to compute features for the side to move.
    # But wait, NNUE evaluates static position, usually from both perspectives.
    # Let's just return the indices for the side to move's king.
    
    # Actually, let's do a simpler "Dense" encoding if HalfKP is too complex to get right quickly without a reference.
    # But user asked for NNUE.
    # Okay, let's do:
    # Input is a sparse vector of size 41024.
    # We return a list of active indices.
    
    turn = board.turn
    
    # Perspective: Side to move
    us = turn
    them = not turn
    
    k_sq = board.king(us)
    if k_sq is None:
        return []

    # Orient squares if black
    def orient(sq, color):
        return sq if color == chess.WHITE else sq ^ 56

    k_sq_orient = orient(k_sq, us)
    
    # Iterate over all pieces
    for sq, piece in board.piece_map().items():
        if piece.piece_type == chess.KING and piece.color == us:
            continue
            
        # Calculate feature index
        # PieceType: 0-4 for ours, 5-9 for theirs
        if piece.color == us:
            pt_idx = piece.piece_type - 1 # P=0, N=1, ...
        else:
            pt_idx = piece.piece_type - 1 + 5
            
        p_sq_orient = orient(sq, us)
        
        feature_idx = k_sq_orient * 640 + p_sq_orient * 10 + pt_idx
        active_indices.append(feature_idx)
        
    return active_indices
