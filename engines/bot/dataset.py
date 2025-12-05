import chess
import chess.pgn
import torch
from torch.utils.data import Dataset
import numpy as np
import logging
import os
import random

logger = logging.getLogger(__name__)

class PreprocessedDataset(torch.utils.data.IterableDataset):
    def __init__(self, data_dir, shuffle=True):
        self.data_dir = data_dir
        self.chunk_files = sorted([f for f in os.listdir(data_dir) if f.endswith('.pt')])
        self.shuffle = shuffle
        
    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        
        # Simple sharding for multi-worker
        if worker_info is not None:
            per_worker = int(np.ceil(len(self.chunk_files) / float(worker_info.num_workers)))
            worker_id = worker_info.id
            iter_start = worker_id * per_worker
            iter_end = min(iter_start + per_worker, len(self.chunk_files))
            my_chunks = self.chunk_files[iter_start:iter_end]
        else:
            my_chunks = self.chunk_files

        # Shuffle chunks
        if self.shuffle:
            random.shuffle(my_chunks)
            
        print(f"Worker {worker_info.id if worker_info else 'main'} loading {len(my_chunks)} chunks...")
        
        for chunk_file in my_chunks:
            chunk_path = os.path.join(self.data_dir, chunk_file)
            try:
                # Load the optimized Flat + Offset dictionary
                data = torch.load(chunk_path)
                
                indices = data['indices']
                offsets = data['offsets']
                values = data['values']
                
                num_samples = len(values)

                # Since we can't shuffle globally, we must shuffle the buffer, this prevents overfitting from batches
                sample_order = torch.randperm(num_samples) if self.shuffle else torch.arange(num_samples)
                
                # Loop through the chunk and reconstruct individual samples
                for i in sample_order:
                    start = offsets[i]
                    end = offsets[i+1]
                    
                    # Slice the 1D array to get the features for this specific board
                    # .long() is usually required for Embedding layers
                    sample_indices = indices[start:end].long() 
                    
                    # Get label
                    label = values[i:i+1] 
                    
                    yield sample_indices, label
                    
            except Exception as e:
                print(f"Error loading chunk {chunk_file}: {e}")
                continue

def get_halfkp_features(board: chess.Board, perspective=None):
    """
    Generate HalfKP features for the given board.
    If perspective is None, uses board.turn.
    """
    active_indices = []
    
    turn = board.turn if perspective is None else perspective
    us = turn
    
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

def get_feature_deltas(board: chess.Board, move: chess.Move):
    """
    Returns (added, removed) indices for both perspectives.
    Returns None if full recompute is needed (e.g. King move).
    
    Returns: (added_white, removed_white, added_black, removed_black)
    """
    # Check for King move
    piece = board.piece_at(move.from_square)
    if piece.piece_type == chess.KING:
        return None # Full recompute needed for the side moving the king
        # Actually, if White King moves, White features need recompute.
        # Black features (opponent King) only need incremental update for the moving piece.
        # But for simplicity, let's return None to force full recompute of everything or handle separately.
        # Let's return None for simplicity.
        
    # Check for Castling (King move involved)
    if board.is_castling(move):
        return None

    added_w, removed_w = [], []
    added_b, removed_b = [], []
    
    # Helper to get feature index
    def get_idx(sq, p, perspective):
        us = perspective
        k_sq = board.king(us)
        if k_sq is None: return -1
        
        def orient(s, c): return s if c == chess.WHITE else s ^ 56
        
        k_sq_orient = orient(k_sq, us)
        p_sq_orient = orient(sq, us)
        
        if p.color == us:
            pt_idx = p.piece_type - 1
        else:
            pt_idx = p.piece_type - 1 + 5
            
        return k_sq_orient * 640 + p_sq_orient * 10 + pt_idx

    # 1. Remove moving piece from old square
    idx_w = get_idx(move.from_square, piece, chess.WHITE)
    idx_b = get_idx(move.from_square, piece, chess.BLACK)
    if idx_w != -1: removed_w.append(idx_w)
    if idx_b != -1: removed_b.append(idx_b)
    
    # 2. Add moving piece to new square
    # Note: If promotion, piece type changes
    new_piece = piece
    if move.promotion:
        new_piece = chess.Piece(move.promotion, piece.color)
        
    idx_w = get_idx(move.to_square, new_piece, chess.WHITE)
    idx_b = get_idx(move.to_square, new_piece, chess.BLACK)
    if idx_w != -1: added_w.append(idx_w)
    if idx_b != -1: added_b.append(idx_b)
    
    # 3. Handle Capture
    if board.is_capture(move):
        # If en passant, captured piece is at different square
        if board.is_en_passant(move):
            ep_sq = move.to_square ^ 8 # rank 5->4 or 4->5
            captured_piece = board.piece_at(ep_sq)
            cap_sq = ep_sq
        else:
            captured_piece = board.piece_at(move.to_square)
            cap_sq = move.to_square
            
        if captured_piece:
            # If captured piece is King (should not happen in legal chess), we are in trouble.
            # But we assume legal moves.
            idx_w = get_idx(cap_sq, captured_piece, chess.WHITE)
            idx_b = get_idx(cap_sq, captured_piece, chess.BLACK)
            if idx_w != -1: removed_w.append(idx_w)
            if idx_b != -1: removed_b.append(idx_b)
            
    return (added_w, removed_w, added_b, removed_b)
