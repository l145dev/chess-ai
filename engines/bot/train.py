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
        batch: List of tuples (indices_us, indices_them, label) yielded by the dataset
    
    Returns:
        batch_indices_us: 1D tensor
        batch_offsets_us: 1D tensor
        batch_indices_them: 1D tensor
        batch_offsets_them: 1D tensor
        batch_labels: 1D tensor of labels
    """
    indices_us_list = []
    indices_them_list = []
    labels_list = []
    
    offsets_us_list = [0]
    current_offset_us = 0
    
    offsets_them_list = [0]
    current_offset_them = 0
    
    for indices_us, indices_them, label in batch:
        indices_us_list.append(indices_us)
        indices_them_list.append(indices_them)
        labels_list.append(label)
        
        current_offset_us += len(indices_us)
        offsets_us_list.append(current_offset_us)
        
        current_offset_them += len(indices_them)
        offsets_them_list.append(current_offset_them)
        
    # Concatenate everything into batch tensors
    batch_indices_us = torch.cat(indices_us_list)
    batch_offsets_us = torch.tensor(offsets_us_list[:-1], dtype=torch.long)
    
    batch_indices_them = torch.cat(indices_them_list)
    batch_offsets_them = torch.tensor(offsets_them_list[:-1], dtype=torch.long)
    
    batch_labels = torch.cat(labels_list)
    
    return batch_indices_us, batch_offsets_us, batch_indices_them, batch_offsets_them, batch_labels

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
        for indices_us, offsets_us, indices_them, offsets_them, labels in dataloader:
            indices_us = indices_us.to(device)
            offsets_us = offsets_us.to(device)
            indices_them = indices_them.to(device)
            offsets_them = offsets_them.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model.forward_with_offsets(indices_us, offsets_us, indices_them, offsets_them)
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
