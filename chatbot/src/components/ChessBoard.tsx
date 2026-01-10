// Import piece assets
import bB from "../assets/pieces-png/black-bishop.png";
import bK from "../assets/pieces-png/black-king.png";
import bN from "../assets/pieces-png/black-knight.png";
import bP from "../assets/pieces-png/black-pawn.png";
import bQ from "../assets/pieces-png/black-queen.png";
import bR from "../assets/pieces-png/black-rook.png";

import wB from "../assets/pieces-png/white-bishop.png";
import wK from "../assets/pieces-png/white-king.png";
import wN from "../assets/pieces-png/white-knight.png";
import wP from "../assets/pieces-png/white-pawn.png";
import wQ from "../assets/pieces-png/white-queen.png";
import wR from "../assets/pieces-png/white-rook.png";

const pieceImages: Record<string, string> = {
  r: bR.src,
  n: bN.src,
  b: bB.src,
  q: bQ.src,
  k: bK.src,
  p: bP.src,
  R: wR.src,
  N: wN.src,
  B: wB.src,
  Q: wQ.src,
  K: wK.src,
  P: wP.src,
};

interface ChessBoardProps {
  fen: string;
}

const ChessBoard = ({ fen }: ChessBoardProps) => {
  // Parse FEN
  // Example FEN: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
  // We only care about the piece placement part (index 0)
  const piecePlacement = fen.split(" ")[0];
  const rows = piecePlacement.split("/");

  const board: (string | null)[][] = [];

  rows.forEach((rowStr) => {
    const row: (string | null)[] = [];
    for (const char of rowStr) {
      if (/\d/.test(char)) {
        const emptyCount = parseInt(char, 10);
        for (let i = 0; i < emptyCount; i++) {
          row.push(null);
        }
      } else {
        row.push(char);
      }
    }
    board.push(row);
  });

  return (
    <div
      style={{
        width: "400px",
        height: "400px",
        display: "grid",
        gridTemplateColumns: "repeat(8, 1fr)",
        gridTemplateRows: "repeat(8, 1fr)",
        border: "10px solid #333",
        backgroundColor: "#333",
      }}
    >
      {board.map((row, rowIndex) =>
        row.map((piece, colIndex) => {
          const isDark = (rowIndex + colIndex) % 2 === 1;
          const squareColor = isDark ? "#b58863" : "#f0d9b5"; // Standard wood-ish colors, or maybe use "Chess.com" style green/white or "Lichess" generic
          // User asked for "premium". Let's stick to neutral or allow CSS override.
          // Or matching the "abstract black" background, maybe something grayscale or high contrast?
          // The image snippet showed a standard board.
          // Let's use a standard nice styling.
          // I'll inline styles for simplicity as requested "board itself can be made with css in the component".

          return (
            <div
              key={`${rowIndex}-${colIndex}`}
              style={{
                backgroundColor: isDark ? "#769656" : "#eeeed2", // Lichess-like green
                width: "100%",
                height: "100%",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                position: "relative",
              }}
            >
              {/* Coordinate labels (Rank and File) */}
              {colIndex === 0 && (
                <span
                  style={{
                    position: "absolute",
                    top: "2px",
                    left: "2px",
                    fontSize: "10px",
                    fontWeight: "bold",
                    color: isDark ? "#eeeed2" : "#769656",
                  }}
                >
                  {8 - rowIndex}
                </span>
              )}
              {rowIndex === 7 && (
                <span
                  style={{
                    position: "absolute",
                    bottom: "2px",
                    right: "2px",
                    fontSize: "10px",
                    fontWeight: "bold",
                    color: isDark ? "#eeeed2" : "#769656",
                  }}
                >
                  {String.fromCharCode(97 + colIndex)}
                </span>
              )}

              {piece && pieceImages[piece] && (
                <img
                  src={pieceImages[piece]}
                  alt={piece}
                  style={{ width: "100%", height: "100%" }}
                />
              )}
            </div>
          );
        })
      )}
    </div>
  );
};

export default ChessBoard;
