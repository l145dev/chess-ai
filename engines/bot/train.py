import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from engines.bot.dataset import ChessDataset
from engines.bot.model import NNUE
import os

def collate_fn(batch):
    indices_list = []
    offsets = [0]
    labels = []
    
    for indices, label in batch:
        indices_list.append(indices)
        offsets.append(offsets[-1] + len(indices))
        labels.append(label)
        
    offsets = torch.tensor(offsets[:-1], dtype=torch.long)
    indices = torch.cat(indices_list)
    labels = torch.cat(labels)
    
    return indices, offsets, labels

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Check if PGN exists
    pgn_path = "data/lichess_db_standard_rated_2013-01.pgn"
    if not os.path.exists(pgn_path):
        print(f"PGN file not found at {pgn_path}")
        return

    # Load dataset with streaming
    # max_games=None means read the whole file
    dataset = ChessDataset(pgn_path, max_games=None) 
    # shuffle=True is not supported for IterableDataset
    dataloader = DataLoader(dataset, batch_size=1024, collate_fn=collate_fn)
    
    model = NNUE().to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    
    epochs = 5
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        batch_count = 0
        for indices, offsets, labels in dataloader:
            indices = indices.to(device)
            offsets = offsets.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model.forward_with_offsets(indices, offsets)
            loss = criterion(outputs.squeeze(), labels.squeeze())
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            batch_count += 1
            
        avg_loss = total_loss / batch_count if batch_count > 0 else 0
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
        
    # Ensure directory exists
    os.makedirs("engines/bot", exist_ok=True)
    torch.save(model.state_dict(), "engines/bot/mlp_model.pth")
    print("Model saved to engines/bot/mlp_model.pth")

if __name__ == "__main__":
    train()
