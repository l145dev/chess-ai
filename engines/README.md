# Chess Engines

This directory contains the chess engines used by the bot.

## MLP/NNUE Bot (`engines/bot`)

This is a custom chess engine powered by a Multi-Layer Perceptron (MLP) with an NNUE (Efficiently Updatable Neural Network) architecture. It evaluates board positions to select the best move.

### Architecture

The model uses a simplified **HalfKP** feature set and a standard NNUE architecture:

1.  **Input**:

    - **HalfKP Features**: The board is represented by the interaction between the friendly King and every other piece on the board.
    - **Feature Indexing**: `KingSquare * 640 + PieceSquare * 10 + PieceType`.
    - Total features: ~41k sparse inputs.

2.  **Feature Transformer**:

    - **EmbeddingBag**: Efficiently sums the weights of active features.
    - Projects the sparse input into a dense 256-dimensional vector.

3.  **Network Layers**:
    - **Hidden Layers**: 256 -> 32 -> 32.
    - **Output**: 1 neuron (Evaluation score).
    - **Activation**: `ClippedReLU` (clamped between 0 and 1).

### Files

- **`dataset.py`**: Handles PGN parsing and board encoding.
  - `ChessDataset`: Loads games from PGN, extracts board positions, and computes HalfKP feature indices.
- **`model.py`**: Defines the `NNUE` PyTorch model.
- **`train.py`**: Training script.
  - Loads data, initializes the model, and runs the training loop using CUDA (if available).
  - Saves the trained model to `mlp_model.pth`.
- **`main.py`**: The engine interface.
  - `get_move(board)`: Generates legal moves, evaluates them using the trained model, and returns the best move.

### Usage

1.  **Training**:
    To retrain the model, run:

    ```bash
    python -m engines.bot.train
    ```

    Ensure you have the PGN data in `data/lichess_db_standard_rated_2013-01.pgn`.

2.  **Running the Bot**:
    The bot is integrated into `homemade.py`. You can start it using the provided PowerShell script:
    ```powershell
    pwsh start_bot.ps1
    ```
    This script sets up the environment and runs `lichess-bot.py`, which uses the `PyBot` class in `homemade.py`, which in turn calls `engines.bot.main.get_move`.

### Requirements

- Python 3.x
- `torch` (with CUDA recommended for training)
- `python-chess`
- `numpy`
