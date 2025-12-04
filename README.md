# Chess AI

The worst chess bot ever.

## Requirements

- Python 3.6+
- chess~=1.11
- PyYAML~=6.0
- requests~=2.32
- backoff~=2.2
- rich~=14.1
- torch>=2.0.0
- numpy~=1.26

## Technologies

- Python
- Chess
- Lichess
- PyTorch

## Getting Started

0. Prerequisites

- Have [Python 3.6+](https://www.python.org/) installed with cmd availability `python` or `python3`
- Install a dataset from [lichess database](https://database.lichess.org/#standard_games) and place it in `data` folder

1. Install dependencies:

```
pip install -r requirements.txt
```

2. Set up `config.yml`

- Remove `.example` suffix from `config.yml.example`
- Get token from [lichess](https://lichess.org/) and input it in `token` field in `config.yml` file

2. Run the bot

- **Windows**:

```bash
pwsh start_bot.ps1
```

- **Linux/MacOS (Untested)**:

```bash
./start_bot.sh
```
