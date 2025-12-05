import torch
import torch.nn as nn

class ClippedReLU(nn.Module):
    def __init__(self):
        super().__init__()
        
    def forward(self, x):
        return torch.clamp(x, 0.0, 1.0)

class NNUE(nn.Module):
    def __init__(self, feature_count=40960, hidden_dim=256):
        super().__init__()
        
        # Feature Transformer
        # We use EmbeddingBag to efficiently sum the weights of active features
        self.feature_transformer = nn.EmbeddingBag(feature_count, hidden_dim, mode='sum')
        
        # Network
        # Input to l1 is now hidden_dim * 2 because we concat [us, them]
        self.l1 = nn.Linear(hidden_dim * 2, 32)
        self.l2 = nn.Linear(32, 32)
        self.output = nn.Linear(32, 1)
        
        self.activation = ClippedReLU()
        
    def forward(self, active_features):
        # active_features is a list of indices, or a padded tensor of indices.
        # EmbeddingBag expects a 1D tensor of indices and a 1D tensor of offsets, 
        # OR a 2D tensor if all samples have same length (they don't).
        # So we need to handle the input format in the training loop or here.
        
        # Let's assume input is (batch_size, max_features) with padding, or we use offsets.
        # For simplicity in the Dataset, we returned a tensor. 
        # But since the number of features varies, we should probably use a custom collate_fn 
        # to create the batch for EmbeddingBag.
        
        # However, for this MVP, let's assume we handle the offsets in the training loop 
        # and pass (input, offsets) to forward, or just use a simple approach.
        
        # If we use a custom collate_fn, we can pass (indices, offsets).
        pass

    def forward_with_offsets(self, indices_us, offsets_us, indices_them, offsets_them):
        # indices: 1D tensor of all active indices in the batch
        # offsets: 1D tensor of starting indices for each sample
        
        acc_us = self.feature_transformer(indices_us, offsets_us)
        acc_them = self.feature_transformer(indices_them, offsets_them)
        
        return self.forward_network(acc_us, acc_them)

    def forward_network(self, acc_us, acc_them):
        # Concatenate [us, them]
        x = torch.cat([acc_us, acc_them], dim=1)
        
        x = self.activation(x)
        
        x = self.l1(x)
        x = self.activation(x)
        
        x = self.l2(x)
        x = self.activation(x)
        
        x = self.output(x)
        return x

    def get_accumulator(self, indices):
        # Returns the accumulator for a single sample (or batch if indices is appropriate)
        # For single sample, indices is 1D tensor.
        # EmbeddingBag expects 1D indices and 1D offsets.
        if indices.dim() == 1:
            offsets = torch.tensor([0], device=indices.device)
            return self.feature_transformer(indices, offsets)
        else:
            # Assume batch
            pass

    def update_accumulator(self, accumulator, added_indices, removed_indices):
        # accumulator: (batch, hidden_dim) or (hidden_dim)
        # added_indices: 1D tensor of indices to add
        # removed_indices: 1D tensor of indices to remove
        
        # We need to handle batching if we want to evaluate multiple moves from same root.
        # But for now let's assume single accumulator and we update it.
        
        # Weights: (num_features, hidden_dim)
        weights = self.feature_transformer.weight
        
        if added_indices.numel() > 0:
            accumulator = accumulator + weights[added_indices].sum(dim=0)
            
        if removed_indices.numel() > 0:
            accumulator = accumulator - weights[removed_indices].sum(dim=0)
            
        return accumulator
