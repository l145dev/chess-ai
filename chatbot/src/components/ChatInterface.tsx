import {
  QueryClient,
  QueryClientProvider,
  useMutation,
} from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
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
      // Data: { type: 'text' | 'fen', content: string, message?: string }
      if (data.type === "fen") {
        // If it's a board, we might also want to trigger the engine?
        // Or just display it.
        // The user flow: "User -> /decide -> Refine to FEN -> /engine (/chat) -> Move"
        // Wait, "use that returned board fen to send to the NNUE model ... /api/engine ... which will give back the next move"

        // So if decides returns a FEN, we should verify/display it OR send it to engine.
        // User said: "returned board fen to send to the NNUE model ... this will give back the next move... ideally the entire board fen ... visualized"

        // So:
        // 1. User says "play e4"
        // 2. Decide API returns FEN (after e4)
        // 3. We display that FEN (User's move)
        // 4. Then we automatically call Engine with that FEN?
        // Or does Decide return the FEN *before* the move and the engine plays?

        // "goal is to have the user say a prompt, i will use a /refine api path which a small llm will refine into a logical board fen representation, this will be returned and i will use that returned board fen to send to the NNUE model ... /chat api path ... this will give back the next move"

        // This implies the Frontend coordinates this.
        // Step 1: /decide -> returns FEN (User's move fully applied, or just the state to analyze?)
        // Let's assume /decide processes the user's intent into a board state (e.g. user says "move pawn to e4", /decide returns board with e4 played).
        // Then we send that to /engine to get the BOT's response.

        const userMoveFen = data.content;

        // Add message with the board (User's move)
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot", // Actually this is the result of the user's action visualized
            content: data.message || "Here is the board:",
            fen: userMoveFen,
          },
        ]);

        // Call Engine
        engineMutation.mutate(userMoveFen);
      } else {
        // Just text response
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
      // Data: { fen: string, move: string, ... }
      if (data.fen) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "bot",
            content: `I played ${data.move || "a move"}.`,
            fen: data.fen,
          },
        ]);
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    // Add User Message
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        role: "user",
        content: inputValue,
      },
    ]);

    decideMutation.mutate(inputValue);
    setInputValue("");
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
              <h1>NNUE ChessBot</h1>
              <p>Start a game or ask a chess question.</p>
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
              <div className="bubble loading">Thinking...</div>
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
        }

        .empty-state {
          text-align: center;
          margin-top: 100px;
          color: rgba(255,255,255,0.7);
          margin-bottom: auto;
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
          border-radius: 18px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #fff;
          font-size: 1rem;
          line-height: 1.5;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .message.user .bubble {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.2);
          border-radius: 18px 18px 4px 18px;
        }

        .message.bot .bubble {
           border-radius: 18px 18px 18px 4px;
        }

        .board-wrapper {
          margin-top: 10px;
          border-radius: 4px;
          overflow: hidden;
        }

        .loading {
          font-style: italic;
          color: #aaa;
        }

        .input-area {
          padding: 20px;
          background: transparent;
          /* background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); */
          position: relative;
          z-index: 2;
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
          border-radius: 24px;
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
          border-radius: 50%;
          display: flex;
          justify-content: center;
          align-items: center;
          transition: background 0.2s, color 0.2s, transform 0.1s;
          flex-shrink: 0;
          padding: 0;
        }

        button:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }
        
        button:active:not(:disabled) {
          transform: scale(0.95);
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
