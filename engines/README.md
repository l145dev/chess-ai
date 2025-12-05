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

### Features

- **NNUE Architecture**: Efficiently Updatable Neural Network for fast evaluation.
- **Incremental Updates**: Calculates feature deltas (added/removed pieces) to update the accumulator instead of recomputing from scratch.
- **Alpha-Beta Search**: Implements a depth-limited search (currently depth 3) with alpha-beta pruning.
- **Preprocessed Data**: Uses a compressed sparse row format for efficient data loading during training.

### Files

- **`dataset.py`**: Handles data loading.
  - `PreprocessedDataset`: Loads precomputed features/labels from `.pt` chunks.
  - `get_halfkp_features`: Computes HalfKP feature indices.
  - `get_feature_deltas`: Computes incremental changes for a move.
- **`model.py`**: Defines the `NNUE` PyTorch model.
  - `NNUE`: The main model class.
  - `update_accumulator`: Efficiently updates the feature transformer state.
- **`preprocess.py`**: Converts PGN games into efficient preprocessed chunks.
- **`train.py`**: Training script.
  - Uses `PreprocessedDataset` to train the model on the precomputed data.
  - Saves the model to `engines/bot/model/mlp_model.pth`.
- **`main.py`**: The engine interface.
  - Loads the model from `engines/bot/model/mlp_model.pth`.
  - `get_move(board)`: Performs Alpha-Beta search with incremental updates to find the best move.

### Usage

1.  **Preprocessing**:
    To preprocess the PGN data, run:

    ```bash
    python -m engines.bot.preprocess
    ```

    This will create a directory `data/processed_chunks` containing the preprocessed data.

2.  **Training**:
    To retrain the model, run:

    ```bash
    python -m engines.bot.train
    ```

    Ensure you have the PGN data in `data/lichess_db.pgn`.

3.  **Running the Bot**:
    The bot is integrated into `homemade.py`. You can start it using the provided PowerShell script:

    - **PowerShell**:

    ```powershell
    pwsh start_bot.ps1
    ```

    - **Bash**:

    ```bash
    ./start_bot.sh
    ```

    This script sets up the environment and runs `lichess-bot.py`, which uses the `PyBot` class in `homemade.py`, which in turn calls `engines.bot.main.get_move`.

### Requirements

- Python 3.x
- `torch` (with CUDA recommended for training)
- `python-chess`
- `numpy`
- `tqdm`

### Next Steps

- Implement iterative deepening for better time management.
- Add a transposition table to cache search results.
- Tune search parameters and move ordering.
