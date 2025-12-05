import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from engines.bot.dataset import PreprocessedDataset
from engines.bot.model import NNUE
import os

def collate_fn(batch):
    """
    Custom collate function to handle variable-length sequences (sparse features).
    
    Args:
        batch: List of tuples (indices, label) yielded by the dataset
    
    Returns:
        batch_indices: 1D tensor of all features in the batch concatenated
        batch_offsets: 1D tensor of where each sample starts in batch_indices
        batch_labels: 1D tensor of labels
    """
    indices_list = []
    labels_list = []
    offsets_list = [0]
    current_offset = 0
    
    for indices, label in batch:
        indices_list.append(indices)
        labels_list.append(label)
        
        current_offset += len(indices)
        offsets_list.append(current_offset)
        
    # Concatenate everything into batch tensors
    batch_indices = torch.cat(indices_list)
    batch_labels = torch.cat(labels_list)
    # Remove last offset because pytorch embeddingbag breaks without it idk why tbh, probably intentional behavior for some use cases
    batch_offsets = torch.tensor(offsets_list[:-1], dtype=torch.long) # .long() for embeddingbag
    
    return batch_indices, batch_offsets, batch_labels

def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Check if processed data exists
    data_dir = "data/processed_chunks"
    if not os.path.exists(data_dir) or not os.listdir(data_dir):
        print(f"Processed data not found at {data_dir}. Please run engines/bot/preprocess.py first.")
        return

    # Load dataset
    dataset = PreprocessedDataset(data_dir, shuffle=True) 
    # shuffle=True is not supported for IterableDataset
    dataloader = DataLoader(dataset, batch_size=1024, num_workers=4, collate_fn=collate_fn, pin_memory=True)
    
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
    os.makedirs("engines/bot/model", exist_ok=True)
    torch.save(model.state_dict(), "engines/bot/model/mlp_model.pth")
    print("Model saved to engines/bot/model/mlp_model.pth")

if __name__ == "__main__":
    train()
