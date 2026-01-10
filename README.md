# Lichess Bot with NNUE Engine

A custom chess bot designed for Lichess, powered by a hybrid Python/C# architecture. It features a custom NNUE (Efficiently Updatable Neural Network) evaluation engine and a high-performance C# data processing pipeline.

## Features

- **Custom NNUE Engine**: Implements a HalfKP architecture with dual accumulators for efficient evaluation.
- **High-Performance Data Processing**: Uses a dedicated C# tool (.NET 9.0) to filter massive PGN datasets (100GB+) in minutes.
- **Alpha-Beta Search**: Depth-limited search with alpha-beta pruning.
- **Lichess Integration**: Connects directly to Lichess via API using `lichess-bot`.
- **Web Interface**: A modern web-based chat and game interface built with Astro and React.

## Project Structure

- **`engines/`**: Contains the chess engine implementations.
  - **`bot/`**: The main NNUE bot (Python).
  - [Read more](engines/README.md)
- **`data/process_data/`**: The C# tool for filtering raw PGN data.
  - [Read more](data/process_data/README.md)
- **`chatbot/`**: The web-based chat and game interface (Astro/React).
  - [Read more](chatbot/README.md)
- **`lib/`**: Shared libraries and utilities.

## Prerequisites

- **Python 3.6+**
- **Node.js v18+** (for Web Interface)
- **.NET SDK** (for data processing)
- **Lichess Account** (for API token)

## Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/l145dev/chess-ai.git
    cd chess-ai
    ```

2.  **Install Python dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure the bot**:
    - Copy `config.yml.example` to `config.yml`.
    - Add your Lichess API token to `config.yml`.

## Usage Workflow

### 1. Data Preparation (C#)

> [!NOTE]
> Data processing tool does not process multiple PGN files.

Before training, filter your raw PGN data using the high-performance C# tool.

1.  Place your raw PGN file at `data/lichess_db_raw.pgn`.
2.  Run the filter tool:
    ```bash
    cd data/process_data
    dotnet run -c Release
    ```
3.  This generates `data/elite_data/lichess_db.pgn`.

### 2. Training (Python)

Train the NNUE model using the filtered data.

1.  **Preprocess**:
    ```bash
    python -m engines.bot.preprocess
    ```
2.  **Train**:
    ```bash
    python -m engines.bot.train
    ```

### 3. Running the Application

#### Web Interface (Recommended)

Start the full stack (Web Interface + Engine) using the PowerShell script:

```powershell
.\chess_bot_web.ps1
```

This will check for dependencies and launch both the Astro dev server and the Python engine in separate windows. access the interface at `http://localhost:4321`.

#### Lichess Bot

Start the bot to connect to Lichess and play games.

- **Windows (PowerShell)**:

  ```powershell
  pwsh start_bot.ps1
  ```

- **Linux/macOS**:
  ```bash
  ./start_bot.sh
  ```

## License

MIT

## Author

- **Aryan Shah** - [GitHub](https://github.com/l145dev)
