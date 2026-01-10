# NNUE ChessBot Web Interface

A modern, interactive web interface for the Neural Network Updated Evaluation (NNUE) ChessBot.

## Features

- **Interactive Chat Interface**: Talk to the bot, ask chess questions, or command it to start games.
- **Custom Chess Board**: A lightweight, custom-built React chessboard that renders FEN states dynamically.
- **Start Game Cards**: Quick actions to start a game as White, Black, or Random side directly from the empty state.
- **Preset Questions**: One-click common chess questions to demonstrate the bot's knowledge.
- **State Management**: Uses **TanStack Query** for efficient server state management.
- **AI Integration**: Powered by **Groq** for conversational capabilities.
- **Responsive Design**: Fully responsive UI with a premium, dark-themed aesthetic.
- **Reset Functionality**: Click the Rook icon (top-left) to instantly reset the chat and game state.

## Tech Stack

- **Framework**: [Astro](https://astro.build/) (Static Site Generation / SSR)
- **UI Library**: [React](https://reactjs.org/)
- **State Management**: [TanStack Query (React Query)](https://tanstack.com/query/latest)
- **Styling**: Vanilla CSS, Scoped CSS Modules
- **LLM Provider**: [Groq](https://groq.com/)
- **Server**: [FastAPI](https://fastapi.tiangolo.com/) (Python)

## Project Structure

- `src/components/`: React components (`ChatInterface`, `ChessBoard`).
- `src/layouts/`: Astro layouts (`Layout.astro`).
- `src/pages/`: Astro pages and API endpoints (`api/decide.ts`, `api/engine.ts`).
- `src/lib/`: Utilities and SDK clients (`groq.ts`).
- `src/styles/`: Global and shared styles.

## Getting Started

### Prerequisites

- Node.js (v18+)
- Python 3.6+ (for the backend engine)
- API Key (Groq)

### Configuration

Create a `.env` file in the `chatbot/` directory with your Groq API Key:

```env
GROQ_API_KEY=gsk_your_key_here
```

> [!TIP]
> You can get a free Groq API key at [https://console.groq.com/keys](https://console.groq.com/keys).

### Running the Application

You can start the entire stack (web interface + python engine) using the provided PowerShell script in the root directory:

```powershell
# From the project root
.\chess_bot_web.ps1
```

Or run them manually:

1.  **Web Interface**:

    ```bash
    cd chatbot
    npm install
    npm run dev
    ```

2.  **Backend Engine**:
    ```bash
    # From project root
    python -m server.server
    ```

Access the web interface at `http://localhost:4321`.
