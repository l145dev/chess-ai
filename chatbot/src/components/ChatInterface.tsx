import {
  QueryClient,
  QueryClientProvider,
  useMutation,
} from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import blackQueen from "../assets/pieces-png/black-queen.png";
import whiteKing from "../assets/pieces-png/white-king.png";
import ChessBoard from "./ChessBoard";

const queryClient = new QueryClient();

// Types
type Message = {
  id: string;
  role: "user" | "bot";
  content: string; // text content
  fen?: string; // if present, display board
};

const ChatInterface = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatLogic />
    </QueryClientProvider>
  );
};

const ChatLogic = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle global reset event
  useEffect(() => {
    const handleReset = () => {
      setMessages([]);
      setInputValue("");
    };

    window.addEventListener("reset-chat", handleReset);
    return () => {
      window.removeEventListener("reset-chat", handleReset);
    };
  }, []);

  // Adjust textarea height
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
  };

  const decideMutation = useMutation({
    mutationFn: async (prompt: string) => {
      // Find the last FEN in messages to send as context
      const lastFenMessage = [...messages].reverse().find((m) => m.fen);
      const currentFen = lastFenMessage?.fen;

      const res = await fetch("/api/decide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, currentFen }),
      });
      return res.json();
    },
    onSuccess: (data) => {
      // Data types: "start_game", "fen" (user moved), "text"

      // 1. START GAME
      if (data.type === "start_game") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot",
            content: data.message,
            fen: data.fen,
          },
        ]);

        // If autoPlay (Black side), immediately ask engine for a move
        if (data.autoPlay) {
          engineMutation.mutate(data.fen);
        }
      }

      // 2. FEN (User moved successfully or explicit set)
      else if (data.type === "fen") {
        // Show the board state after user move
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot", // Display as bot message generally, or "result"
            content: data.message || "", // Usually empty for direct move
            fen: data.content, // The FEN after user move
          },
        ]);

        // Now Bot needs to move
        engineMutation.mutate(data.content);
      }

      // 3. TEXT (Question answer)
      else {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot",
            content: data.content,
          },
        ]);
      }
    },
  });

  const engineMutation = useMutation({
    mutationFn: async (fen: string) => {
      const res = await fetch("/api/engine", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen }),
      });
      return res.json();
    },
    onSuccess: (data) => {
      if (data.fen) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot",
            content: `I played ${
              data.san || data.move || "a move"
            }. Your turn!`,
            fen: data.fen,
          },
        ]);
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    sendMessage(inputValue);
    setInputValue("");
  };

  const sendMessage = (text: string) => {
    // Add User Message
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content: text,
      },
    ]);

    decideMutation.mutate(text);
  };

  // Helper handling direct clicks
  const handleDirectSend = (text: string) => {
    // Optional: setInputValue(text) visually if needed, but per logic we just send it.
    // User request: "setInputValue and then trigger submit"
    // We can just call sendMessage which mimics the submit logic.
    sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-area">
        <div className="messages-content">
          {messages.length === 0 && (
            <div className="empty-state">
              <h1>Start a game or ask a chess question.</h1>

              <div className="cards-container">
                {/* Start Game Card */}
                <div className="action-card game-card">
                  <h3>Start game as...</h3>
                  <div className="buttons-row">
                    <button
                      className="game-btn white-btn"
                      onClick={() => handleDirectSend("Start game as white")}
                      title="Play as White"
                    >
                      <img src={whiteKing.src} alt="White King" />
                      <span>W</span>
                    </button>
                    <button
                      className="game-btn black-btn"
                      onClick={() => handleDirectSend("Start game as black")}
                      title="Play as Black"
                    >
                      <img src={blackQueen.src} alt="Black Queen" />
                      <span>B</span>
                    </button>
                    <button
                      className="game-btn random-btn"
                      onClick={() => handleDirectSend("Start game")}
                      title="Random Side"
                    >
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path
                          d="M11.178 19.569a.998.998 0 0 0 1.644 0l9-13A.999.999 0 0 0 21 5H3a1.002 1.002 0 0 0-.822 1.569l9 13z"
                          opacity="0.0"
                        />{" "}
                        {/* Spacer */}
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Preset Questions Card */}
                <div className="action-card presets-card">
                  <div className="presets-list">
                    <button
                      onClick={() => handleDirectSend("Who is Magnus Carlson?")}
                    >
                      Who is Magnus Carlson?
                    </button>
                    <button
                      onClick={() => handleDirectSend("What is En Passant?")}
                    >
                      What is En Passant?
                    </button>
                    <button
                      onClick={() => handleDirectSend("Who created chess?")}
                    >
                      Who created chess?
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <div className="bubble">
                {msg.content && <p>{msg.content}</p>}
                {msg.fen && (
                  <div className="board-wrapper">
                    <ChessBoard fen={msg.fen} />
                  </div>
                )}
              </div>
            </div>
          ))}
          {decideMutation.isPending && (
            <div className="message bot">
              <div className="bubble loading">Deciding...</div>
            </div>
          )}
          {engineMutation.isPending && (
            <div className="message bot">
              <div className="bubble loading">Getting Move...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="input-area">
        <form onSubmit={handleSubmit}>
          <textarea
            ref={textareaRef}
            value={inputValue}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="En Passant"
            rows={1}
            style={{ fieldSizing: "content" }}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!inputValue.trim() || decideMutation.isPending}
          >
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          </button>
        </form>
      </div>

      <style>{`
        .chat-container {
          width: 100%;
          height: 100vh;
          display: flex;
          flex-direction: column;
          position: relative;
          padding-top: 60px; /* Header height */
          box-sizing: border-box;
        }

        .messages-area {
          flex: 1;
          overflow-y: auto;
          width: 100%;
          display: flex;
          flex-direction: column;
          align-items: center; /* Center the inner content */
        }
        
        .messages-content {
           width: 100%;
           max-width: 800px;
           padding: 20px;
           display: flex;
           flex-direction: column;
           gap: 20px;
           box-sizing: border-box;
           flex: 1; /* Allow content to fill area for centering */
        }

        .empty-state {
          text-align: center;
          margin: auto; /* Center vertically and horizontally in flex column */
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
        }

        .cards-container {
          display: flex;
          flex-flow: row wrap;
          gap: 20px;
          justify-content: center;
          margin-top: 20px;
          width: 100%;
        }

        .action-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-width: 250px;
        }

        .game-card {
          background: rgba(20, 20, 20, 0.6); /* Translucent dark similar to bot message */
          backdrop-filter: blur(10px);
          padding: 16px 0;
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }

        .action-card h3 {
          margin: 0 0 16px 0;
          font-size: 1.1rem;
          color: rgba(255,255,255,0.9);
          font-weight: 500;
        }

        .buttons-row {
          display: flex;
          gap: 15px;
        }

        .game-btn {
          width: 60px;
          height: 60px;
          border-radius: 8px;
          border: 1px solid rgba(255,255,255,0.2);
          cursor: pointer;
          display: flex;
          justify-content: center;
          align-items: center;
          transition: border 0.1s, box-shadow 0.2s;
          position: relative;
          overflow: hidden;
          padding: 0;
        }

        .game-btn:hover {
          border: 1px solid rgba(255,255,255,0.6);
        }

        .game-btn:active {
          transform: scale(0.95);
        }

        .game-btn img {
          width: 100%;
          height: 100%;
          object-fit: cover; /* Cover background button */
        }
        
        .game-btn span {
          display: none; /* Hide text, just show icon/color */
        }

        /* White Button: Black Bkg, White King */
        .white-btn {
          background-color: #769656;
        }
        .white-btn:hover {
          background-color: #769656;
        }
        .white-btn img {
           transform: scale(0.8); /* Scale down piece slightly */
        }

        /* Black Button: White Bkg, Black Queen */
        .black-btn {
          background-color: #fff;
        }
        .black-btn:hover {
          background-color: #fff;
          border-color: rgba(0,0,0,0.6);
        }
        .black-btn img {
           transform: scale(0.8);
        }

        /* Random Button */
        .random-btn {
          background: rgba(255,255,255,0.1);
          color: #fff;
        }
        .random-btn svg {
          width: 32px;
          height: 32px;
        }

        .presets-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          width: 100%;
        }

        .presets-list button {
          background: rgba(255,255,255,0.05); /* Very subtle button bg */
          color: rgba(255,255,255,0.9);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255,255,255,0.1);
          border-radius: 8px;
          font-size: 0.95rem;
          cursor: pointer;
          transition: background 0.2s, border-color 0.2s;
          width: 100%;
          text-align: left;
        }

        .presets-list button:hover {
          background: rgba(255,255,255,0.15);
          border-color: rgba(255,255,255,0.3);
        }

        .message {
          display: flex;
          flex-direction: column;
          max-width: 80%;
          animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
          align-self: flex-end;
          align-items: flex-end;
        }

        .message.bot {
          align-self: flex-start;
          align-items: flex-start;
        }

        .bubble {
          background: rgba(40, 40, 40, 0.8);
          backdrop-filter: blur(10px);
          padding: 12px 16px;
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          font-size: 1rem;
          line-height: 1.5;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .message.user .bubble {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.2);
          border-radius: 16px 16px 4px 16px;
        }

        .message.bot .bubble {
           border-radius: 16px 16px 16px 4px;
        }

        .board-wrapper {
          margin-top: 10px;
          border-radius: 4px;
          overflow: hidden;
        }

        .loading {
          color: #aaa;
        }

        .input-area {
          padding: 20px;
          position: relative;
          width: 100%;
          display: flex;
          justify-content: center;
          box-sizing: border-box;
        }

        form {
          display: flex;
          gap: 10px;
          background: rgba(20, 20, 20, 0.8);
          padding: 10px;
          border-radius: 16px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          backdrop-filter: blur(10px);
          align-items: flex-end;
          width: 100%;
          max-width: 800px;
        }

        textarea {
          flex: 1;
          background: transparent;
          border: none;
          color: #fff;
          font-family: inherit;
          font-size: 1rem;
          padding: 8px 12px;
          resize: none;
          max-height: 150px;
          outline: none;
          min-height: 24px;
        }
        
        button {
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.8);
          cursor: pointer;
          width: 40px;
          height: 40px;
          border-radius: 12px;
          display: flex;
          justify-content: center;
          align-items: center;
          transition: background 0.2s, color 0.2s, transform 0.1s;
          flex-shrink: 0;
          padding: 0;
        }

        .send-btn:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }
        
        button:active:not(:disabled) {
          transform: scale(0.98);
        }

        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default ChatInterface;
