# Chess Data Processor

This is a high-performance C# tool designed to filter massive PGN datasets (100GB+) in minutes. It strips out low-quality games (Bullet, low Elo) to prepare data for NNUE engine training.

> [!NOTE]
> This tool does not support multiple PGN files processing at once.

## Prerequisites

- .NET SDK

## Project Structure & Setup

**Important:** This tool expects a specific folder structure to find your data.

Place your raw `.pgn` file in the parent `data/` folder.

Rename it to `lichess_db_raw.pgn`.

```
data
├── lichess_db_raw.pgn <- Put your big file here
└── /process_data <- This project folder
    ├── Program.cs
    └── chess_data.csproj
```

## Configuration

To change filter settings, open `Program.cs` and edit the constants at the top:

```csharp
const int MinElo = 2100;      // Filter for high tier players
const int MinTimeSec = 180;   // 180s = 3 mins (No Bullet)
```

## How to Run

Navigate to this directory and run in Release mode (crucial for speed):

```bash
dotnet run -c Release
```

Output will be saved to `../elite_data/lichess_db.pgn`.
