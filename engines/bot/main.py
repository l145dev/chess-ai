import chess
import torch
import numpy as np
import os
from engines.bot.model import NNUE
from engines.bot.dataset import get_halfkp_features, get_feature_deltas

# Setup & Config
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = os.path.join(os.path.dirname(__file__), "model", "mlp_model.pth")

# Load Model globally once
model = NNUE().to(device)
if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print(f"Loaded model from {model_path}")
else:
    print(f"Model not found at {model_path}, operating in Random Mode.")
    model = None

# Helper Functions

def get_next_accumulators(board, move, acc_w, acc_b):
    """
    Calculates the new accumulators for a move. 
    Tries incremental update first; falls back to full recompute if necessary.
    """
    deltas = get_feature_deltas(board, move)
    
    # CASE A: Full Recompute (Slow, but safe for non-reversible moves like castling/captures sometimes)
    if deltas is None:
        board.push(move)
        f_w = get_halfkp_features(board, perspective=chess.WHITE)
        f_b = get_halfkp_features(board, perspective=chess.BLACK)
        board.pop()
        
        with torch.no_grad():
            new_acc_w = model.get_accumulator(torch.tensor(f_w, dtype=torch.long, device=device))
            new_acc_b = model.get_accumulator(torch.tensor(f_b, dtype=torch.long, device=device))
        return new_acc_w, new_acc_b

    # CASE B: Incremental Update (Fast)
    added_w, removed_w, added_b, removed_b = deltas
    
    t_add_w = torch.tensor(added_w, dtype=torch.long, device=device)
    t_rem_w = torch.tensor(removed_w, dtype=torch.long, device=device)
    new_acc_w = model.update_accumulator(acc_w.clone(), t_add_w, t_rem_w)

    t_add_b = torch.tensor(added_b, dtype=torch.long, device=device)
    t_rem_b = torch.tensor(removed_b, dtype=torch.long, device=device)
    new_acc_b = model.update_accumulator(acc_b.clone(), t_add_b, t_rem_b)
    
    return new_acc_w, new_acc_b

def evaluate(acc_white, acc_black, turn):
    """
    Runs the final feed-forward layer on the accumulators to get a score.
    """
    # Select the accumulator for the side to move (NNUE convention)
    # usually we combine them, but this depends on your specific NNUE forward implementation.
    # Assuming standard halfkp: we usually concat [us, them]
    
    # NOTE: Adjust 'forward_network' call based on your model's specific input requirement
    # Standard NNUE often takes (acc_us, acc_them)
    active_acc = acc_white if turn == chess.WHITE else acc_black
    inactive_acc = acc_black if turn == chess.WHITE else acc_white
    
    with torch.no_grad():
        # If your model just takes one accumulator, keep your original line:
        # score = model.forward_network(active_acc).item()
        
        # If your model combines perspectives (Standard NNUE):
        score = model.forward_network(active_acc, inactive_acc).item()

    return score # Returns score from perspective of side to move

def evaluate_mopup(board, score):
    # Only mop-up if we have a winning advantage (score > 1.0 roughly, tuned to 0.8 here)
    # The NNUE output for winning positions is often around 0.9-1.0 if using sigmoid/clipped relu.
    if score < 0.8:
        return score
        
    # Mop-up evaluation to force checkmate
    # Encourage pushing enemy king to edges/corners
    # Encourage bringing our king closer
    
    us = board.turn
    them = not us
    
    king_us_sq = board.king(us)
    king_them_sq = board.king(them)
    
    if king_us_sq is None or king_them_sq is None:
        return score
        
    # Center Manhattan Distance of enemy king
    # Center is 3.5, 3.5. 
    # File: 0..7 => dist to 3.5 is abs(file - 3.5)
    # Rank: 0..7 => dist to 3.5 is abs(rank - 3.5)
    
    file_them = chess.square_file(king_them_sq)
    rank_them = chess.square_rank(king_them_sq)
    
    # 0.5, 1.5, 2.5, 3.5
    cmd = abs(file_them - 3.5) + abs(rank_them - 3.5) 
    # Range: 1.0 (center) to 7.0 (corner)
    
    # Distance between kings (Manhattan is fine approx or Chebyshev)
    # Using Manhattan for simplicity
    file_us = chess.square_file(king_us_sq)
    rank_us = chess.square_rank(king_us_sq)
    
    dist_kings = abs(file_us - file_them) + abs(rank_us - rank_them)
    
    # Formula: 4.7 * cmd + 1.6 * (14 - dist_kings)
    # This is a classic mopup heuristic
    mopup_score = 4.7 * cmd + 1.6 * (14 - dist_kings)
    
    # Pawn Promotion Incentive
    # Encourages pushing pawns to the 8th rank
    pawn_score = 0
    for sq in board.pieces(chess.PAWN, us):
        rank = chess.square_rank(sq) if us == chess.WHITE else (7 - chess.square_rank(sq))
        pawn_score += rank * 0.02

    # Scale it down so it doesn't override main evaluation too much, 
    # but acts as a decisive tiebreaker.
    # Increased weight because 0.001 was too small to break NNUE plateaus.
    
    return score + mopup_score * 0.05 + pawn_score

# Search Logic
def alpha_beta(board, depth, alpha, beta, acc_w, acc_b):
    # Check Extension (Horizon)
    # If we are at depth 0 (or less) and in check, extend by 1 ply to try to find a mate/escape
    if depth <= 0 and board.is_check():
        depth = 1

    # Draw detection, avoids infinite repetition
    if board.is_repetition(2) or board.is_fifty_moves() or board.is_insufficient_material():
        return 0.0

    # Base case
    if depth == 0 or board.is_game_over():
        # If is_game_over is True here, it's likely Checkmate or Stalemate
        if board.is_checkmate():
            # Large negative score because the side to move has been mated
            return -99999.0 + depth # +depth favors faster mates
        if board.is_stalemate():
            return 0.0
            
        score = evaluate(acc_w, acc_b, board.turn)
        return evaluate_mopup(board, score)

    legal_moves = list(board.legal_moves)
    # Move ordering: captures first
    legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    best_score = -float('inf')

    for move in legal_moves:
        # 1. Update Neural Network State
        new_acc_w, new_acc_b = get_next_accumulators(board, move, acc_w, acc_b)

        # 2. Recursion
        board.push(move)
        score = -alpha_beta(board, depth - 1, -beta, -alpha, new_acc_w, new_acc_b)
        board.pop()

        # 3. Pruning
        if score > best_score:
            best_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best_score

# Main Function

def get_move(board: chess.Board, depth=4) -> chess.Move:
    # Fallback if model failed to load
    if model is None:
        legal_moves = list(board.legal_moves)
        return legal_moves[np.random.randint(0, len(legal_moves))] if legal_moves else None

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    # Initial Root Accumulator Calculation
    f_w = get_halfkp_features(board, perspective=chess.WHITE)
    f_b = get_halfkp_features(board, perspective=chess.BLACK)
    
    with torch.no_grad():
        root_acc_w = model.get_accumulator(torch.tensor(f_w, dtype=torch.long, device=device))
        root_acc_b = model.get_accumulator(torch.tensor(f_b, dtype=torch.long, device=device))

    # Root Search
    best_move = None
    alpha = -float('inf')
    beta = float('inf')
    
    legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    print(f"Starting search at depth {depth}...")

    for move in legal_moves:
        new_acc_w, new_acc_b = get_next_accumulators(board, move, root_acc_w, root_acc_b)

        board.push(move)
        # Note: We pass -beta, -alpha because we flipped the perspective
        score = -alpha_beta(board, depth - 1, -beta, -alpha, new_acc_w, new_acc_b)
        board.pop()

        if score > alpha:
            alpha = score
            best_move = move
            print(f"New best move: {move} Score: {score:.4f}")

    if best_move is None:
        best_move = legal_moves[0]

    return best_move
