Plan for MLP project (2-3 day training/time goal):

---

## 1. Data Collection

- Use PGN data from publicly available sources (Lichess database, etc.)

---

## 2. Preprocessing / Feature Encoding

- Encode board as features: e.g., 12 channels (one for each piece type & color), plus extra info like castling rights or side to move.
- Flatten into a vector for MLP input.

---

## 3. Model Architecture (MLP)

- Input layer = size of flattened features
- Hidden layers: e.g., 2 layers of 128 neurons with ReLU
- Output: a single neuron predicting evaluation (regression)

---

## 4. Training

- Loss: MSE (mean squared error) is good for evaluation prediction.
- Optimizer: Adam
- Split data into train / validation.
- Train for enough epochs until loss stabilizes (something like 20–50 could be okay depending on data).

---

## 5. Integration into Chess Engine

- Use `python-chess` to generate board states in your engine.
- At each node (or leaf), call your MLP to evaluate the position.
- Combine with minimax or alpha-beta to pick moves.

---

## 6. Evaluation & Demo

- Play bot against stockfish on lichess.org
