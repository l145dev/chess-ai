import chess
import torch
import numpy as np
import os
from engines.bot.model import NNUE
from engines.bot.dataset import get_halfkp_features

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = NNUE().to(device)
model_path = os.path.join(os.path.dirname(__file__), "mlp_model.pth")

if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print(f"Loaded model from {model_path}")
else:
    print(f"Model not found at {model_path}, using random moves.")
    model = None

def get_move(board: chess.Board) -> chess.Move:
    if model is None:
        legal_moves = list(board.legal_moves)
        return legal_moves[np.random.randint(0, len(legal_moves))]

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    best_move = None
    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')

    # Evaluate each move
    # For efficiency, we should batch this.
    
    batch_indices = []
    batch_offsets = [0]
    
    for move in legal_moves:
        board.push(move)
        features = get_halfkp_features(board)
        board.pop()
        
        batch_indices.extend(features)
        batch_offsets.append(batch_offsets[-1] + len(features))
        
    # Convert to tensors
    indices_tensor = torch.tensor(batch_indices, dtype=torch.long).to(device)
    offsets_tensor = torch.tensor(batch_offsets[:-1], dtype=torch.long).to(device)
    
    with torch.no_grad():
        scores = model.forward_with_offsets(indices_tensor, offsets_tensor).squeeze()
        
    # If only one move, scores might be a scalar (0-d tensor)
    if len(legal_moves) == 1:
        return legal_moves[0]
        
    scores = scores.cpu().numpy()
    
    if board.turn == chess.WHITE:
        best_idx = np.argmax(scores)
    else:
        best_idx = np.argmin(scores)
        
    best_move = legal_moves[best_idx]
    # print(f"Best move: {best_move}, Score: {scores[best_idx]:.4f}")
    
    return best_move