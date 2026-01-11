import os
import time
import torch
import numpy as np
import chess
import chess.polyglot
from engines.bot.model import NNUE
from engines.bot.dataset import get_halfkp_features, get_feature_deltas

# Constants & Configuration
INF = 99999 # INF scores for special cases (e.g. checkmate)
MATE_SCORE = 99000 # Mate score for "Mate" case
TT_SIZE = 1_000_000 # Used for caching

# Most Valuable Victim - Least Valuable Attacker (MVV-LVA) Values
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

class Searcher:
    def __init__(self, model_path=None):
        self.device = torch.device("cpu") # Force CPU for sequential search (faster than GPU)
        self.model = NNUE().to(self.device)
        self.model_loaded = False
        
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "model", "mlp_model.pth")
            
        self.load_model(model_path)
        
        # Search State
        self.tt = {} # Transposition Table: key -> (depth, score, flag, move)
        self.history = {} # [color][from][to] -> score
        self.killers = {} # [depth] -> [move1, move2]
        
        self.nodes = 0 # Nodes searched
        self.start_time = 0 # Start time of search
        self.time_limit = 5.0 # Time limit for search
        self.stopped = False # Whether search has been stopped
        
        # Precomputed Tables
        self.reduction_table = [[0] * 64 for _ in range(64)]
        self._init_lmr_table()

    # Late Move Reduction (LMR) Table
    def _init_lmr_table(self):
        for depth in range(1, 64):
            for moves in range(1, 64):
                # Basic LMR formula: log(depth) * log(moves) / 2
                self.reduction_table[depth][moves] = int(0.5 + np.log(depth) * np.log(moves) / 2)

    # Model Loading
    def load_model(self, path):
        if os.path.exists(path):
            try:
                self.model.load_state_dict(torch.load(path, map_location=self.device))
                self.model.eval()
                self.model_loaded = True
                print(f"Loaded model from {path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print(f"Model not found at {path}")

    # NNUE Wrappers
    def get_accumulators(self, board, move, acc_w, acc_b):
        """Calculates new accumulators efficiently."""
        deltas = get_feature_deltas(board, move)
        
        # Full Recompute -> If the move is not a capture, we need to recompute the accumulators from scratch
        if deltas is None:
            board.push(move)
            f_w = get_halfkp_features(board, perspective=chess.WHITE)
            f_b = get_halfkp_features(board, perspective=chess.BLACK)
            board.pop()
            with torch.no_grad():
                new_w = self.model.get_accumulator(torch.tensor(f_w, dtype=torch.long, device=self.device))
                new_b = self.model.get_accumulator(torch.tensor(f_b, dtype=torch.long, device=self.device))
            return new_w, new_b

        # Incremental Update -> If the move is a capture, we can update the accumulators incrementally
        added_w, removed_w, added_b, removed_b = deltas
        with torch.no_grad():
            t_add_w = torch.tensor(added_w, dtype=torch.long, device=self.device)
            t_rem_w = torch.tensor(removed_w, dtype=torch.long, device=self.device)
            new_w = self.model.update_accumulator(acc_w.clone(), t_add_w, t_rem_w)

            t_add_b = torch.tensor(added_b, dtype=torch.long, device=self.device)
            t_rem_b = torch.tensor(removed_b, dtype=torch.long, device=self.device)
            new_b = self.model.update_accumulator(acc_b.clone(), t_add_b, t_rem_b)
        return new_w, new_b

    # Evaluation -> Evaluate the board position using the NNUE model
    def evaluate(self, board, acc_w, acc_b):
        """NNUE Evaluation + Mop-up"""
        turn = board.turn
        active_acc = acc_w if turn == chess.WHITE else acc_b
        inactive_acc = acc_b if turn == chess.WHITE else acc_w
        
        with torch.no_grad():
            score = self.model.forward_network(active_acc, inactive_acc).item()
            
        # Mop-up Term logic
        if score < 0.5: return score

        winning_factor = (score - 0.5) * 2
        
        us = turn
        them = not us
        k_us = board.king(us)
        k_them = board.king(them)
        
        if k_us is None or k_them is None: return score
        
        # Center Manhattan Distance
        f_them, r_them = chess.square_file(k_them), chess.square_rank(k_them)
        cmd = abs(f_them - 3.5) + abs(r_them - 3.5)
        
        # Distance between kings
        f_us, r_us = chess.square_file(k_us), chess.square_rank(k_us)
        dist = abs(f_us - f_them) + abs(r_us - r_them)
        
        mopup = 4.7 * cmd + 1.6 * (14 - dist)
        
        # Pawn push bonus
        pawn_bonus = 0
        for sq in board.pieces(chess.PAWN, us):
            r = chess.square_rank(sq) if us == chess.WHITE else 7 - chess.square_rank(sq)
            pawn_bonus += r * 0.01

        final_score = score + (mopup * 0.05 + pawn_bonus) * winning_factor
        return final_score

    # Helpers

    # Time Management
    def check_time(self):
        if self.nodes % 2048 == 0:
            if time.time() - self.start_time > self.time_limit:
                self.stopped = True

    # Most Valuable Victim - Least Valuable Aggressor (MVV-LVA)
    def mvv_lva(self, board, move):
        victim = board.piece_at(move.to_square)
        if not victim: return 0
        aggressor = board.piece_at(move.from_square)
        v_val = PIECE_VALUES.get(victim.piece_type, 0)
        a_val = PIECE_VALUES.get(aggressor.piece_type, 0) if aggressor else 0
        return v_val * 10 - a_val

    # Move Scoring -> Score moves based on transposition table, killers, history, and MVV-LVA
    def score_move(self, board, move, tt_move, ply):
        if move == tt_move:
            return 2_000_000
        
        if board.is_capture(move):
            return 1_000_000 + self.mvv_lva(board, move)
            
        # Killers
        if ply in self.killers and move in self.killers[ply]:
            return 900_000
            
        # History
        key = (board.turn, move.from_square, move.to_square)
        return self.history.get(key, 0)

    # Quiescence Search (Search captures only) -> Search captures only to avoid infinite search
    def quiescence(self, board, alpha, beta, acc_w, acc_b):
        self.check_time()
        if self.stopped: return 0

        in_check = board.is_check()

        # 1. Stand Pat: Only allowed if NOT in check
        # (If we are in check, we can't just "stand still", we must move)
        if not in_check:
            stand_pat = self.evaluate(board, acc_w, acc_b)
            if stand_pat >= beta:
                return beta
            if stand_pat > alpha:
                alpha = stand_pat

        # 2. Move Gen: All moves if in check, only captures if safe
        if in_check:
             moves = list(board.legal_moves)
        else:
             moves = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        
        if not moves: 
            # If in check and no moves -> Checkmate (return bad score)
            # If not in check and no moves -> Quiet position (return alpha)
            return -MATE_SCORE if in_check else alpha
            
        # 3. Sort and loop
        moves.sort(key=lambda m: self.mvv_lva(board, m), reverse=True)
        
        for move in moves:
            nw, nb = self.get_accumulators(board, move, acc_w, acc_b)
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, nw, nb)
            board.pop()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    # Helper to check for non-pawn pieces (Zugzwang protection -> NMP hallucination fix)
    def has_non_pawn_material(self, board, color):
        # Check if there is at least one Knight, Bishop, Rook, or Queen
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if board.pieces(piece_type, color):
                return True
        return False

    # Principal Variation Search (PVS) -> Search the best move first
    def pvs(self, board, depth, alpha, beta, acc_w, acc_b, ply, can_null=True):
        self.check_time()
        if self.stopped: return 0
        
        self.nodes += 1

        # Check for draw by repetition or 50-move rule
        # We return 0 (Draw score)
        if board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
            return 0
        
        # TT Probe -> Probe the transposition table for the best move
        key = chess.polyglot.zobrist_hash(board)
        tt_move = None
        if key in self.tt:
            t_depth, t_score, t_flag, t_move = self.tt[key]
            if t_depth >= depth:
                if t_flag == 0: return t_score # 0 = EXACT
                if t_flag == 1 and t_score <= alpha: return t_score # 1 = ALPHA/UPPER
                if t_flag == 2 and t_score >= beta: return t_score # 2 = BETA/LOWER
            tt_move = t_move

        if board.is_game_over():
            if board.is_checkmate(): return -MATE_SCORE + ply
            return 0

        if depth <= 0:
            return self.quiescence(board, alpha, beta, acc_w, acc_b)

        # Null Move Pruning (NMP) -> Prune branches that are not promising
        # Conditions: depth >= 3, not in check, not PV node (beta-alpha > 1 usually implies PV, but here simply if not root/check)
        if can_null and depth >= 3 and not board.is_check() and beta < MATE_SCORE:
            # Check if we have non-pawn material (Zugzwang protection)
            if self.has_non_pawn_material(board, board.turn):
                # Static eval check
                static_eval = self.evaluate(board, acc_w, acc_b)
                if static_eval >= beta:
                    R = 2 if depth > 6 else 2 # Reduction
                    board.push(chess.Move.null())
                    # Pass same accumulators as pieces didn't move
                    score = -self.pvs(board, depth - 1 - R, -beta, -beta + 1, acc_w, acc_b, ply + 1, can_null=False)
                    board.pop()
                    if score >= beta:
                        return beta

        # Move Ordering -> Order moves to try the best moves first
        moves = list(board.legal_moves)
        moves.sort(key=lambda m: self.score_move(board, m, tt_move, ply), reverse=True)
        
        best_score = -INF
        best_move = None
        start_alpha = alpha
        
        for i, move in enumerate(moves):
            nw, nb = self.get_accumulators(board, move, acc_w, acc_b)
            board.push(move)
            
            # Principal Variation Search (PVS) Logic
            if i == 0:
                score = -self.pvs(board, depth - 1, -beta, -alpha, nw, nb, ply + 1)
            else:
                # Late Move Reduction (LMR) -> Prune branches that are not promising
                reduction = 0
                if depth >= 3 and i >= 3 and not board.is_capture(move) and not board.is_check():
                     prior = self.history.get((board.turn, move.from_square, move.to_square), 0)
                     # reduction = self.reduction_table[depth][i]... simplified:
                     reduction = 1
                     if i > 8: reduction = 2
                
                # Search with null window -> Search with a smaller window to prune branches that are not promising
                score = -self.pvs(board, depth - 1 - reduction, -alpha - 1, -alpha, nw, nb, ply + 1)
                
                # Re-search if failed high or reduced -> Re-search if the score is higher than the alpha or if the reduction was too high
                if score > alpha and (score < beta or reduction > 0):
                    score = -self.pvs(board, depth - 1, -beta, -alpha, nw, nb, ply + 1)
            
            board.pop()
            
            if self.stopped: return 0
            
            if score > best_score:
                best_score = score
                best_move = move
                
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    # Beta Cutoff -> Prune branches that are not promising
                    # Update Killers -> Update killers to keep track of the best moves
                    if not board.is_capture(move):
                        if ply not in self.killers: self.killers[ply] = [None, None]
                        self.killers[ply][1] = self.killers[ply][0]
                        self.killers[ply][0] = move
                        
                        # Update History -> Update history to keep track of the best moves
                        k = (board.turn, move.from_square, move.to_square)
                        self.history[k] = self.history.get(k, 0) + depth * depth
                        
                    # Store TT BETA -> Store the beta value in the transposition table
                    self.tt[key] = (depth, best_score, 2, move) # 2 = BETA
                    return beta
        
        # Store TT
        flag = 0 if best_score > start_alpha else 1 # 0=EXACT, 1=ALPHA
        self.tt[key] = (depth, best_score, flag, best_move)
        return best_score

    # Gets move for board
    def get_move(self, board, depth=5):
        if not self.model_loaded:
            l = list(board.legal_moves)
            return l[0] if l else None

        self.nodes = 0
        self.start_time = time.time()
        self.stopped = False
        self.killers = {}
        
        best_move_global = None
        
        # Root Accumulators -> Get the accumulators for the root position (NNUE)
        f_w = get_halfkp_features(board, perspective=chess.WHITE)
        f_b = get_halfkp_features(board, perspective=chess.BLACK)
        with torch.no_grad():
            rw = self.model.get_accumulator(torch.tensor(f_w, dtype=torch.long, device=self.device))
            rb = self.model.get_accumulator(torch.tensor(f_b, dtype=torch.long, device=self.device))

        # Iterative Deepening -> Search deeper and deeper until the time runs out
        for d in range(1, depth + 1):
            score = self.pvs(board, d, -INF, INF, rw, rb, 0)
            
            if self.stopped:
                break
                
            # Retrieve best move from TT for this position -> Retrieve the best move from the transposition table for this position
            key = chess.polyglot.zobrist_hash(board)
            if key in self.tt:
                _, _, _, m = self.tt[key]
                best_move_global = m
                print(f"Info: Depth {d} Score {score:.2f} Move {m} Nodes {self.nodes} Time {time.time()-self.start_time:.2f}s")
            
        return best_move_global
