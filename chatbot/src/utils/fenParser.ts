export const parseFenToText = (fen: string): string => {
  try {
    const parts = fen.split(" ");
    const board = parts[0];
    const turn = parts[1] === "w" ? "White" : "Black";
    const castling = parts[2];
    const enPassant = parts[3];
    const halfMove = parts[4];
    const fullMove = parts[5];

    let description = `Current Turn: ${turn}.\n`;
    description += `Castling Rights: ${
      castling !== "-" ? castling : "None"
    }.\n`;
    description += `En Passant Target: ${
      enPassant !== "-" ? enPassant : "None"
    }.\n`;
    description += `Half Turn Clock: ${halfMove}, Full Turn Number: ${fullMove}.\n\n`;
    description += "Board State:\n";

    const rows = board.split("/");
    const PieceNames: Record<string, string> = {
      p: "Black Pawn",
      r: "Black Rook",
      n: "Black Knight",
      b: "Black Bishop",
      q: "Black Queen",
      k: "Black King",
      P: "White Pawn",
      R: "White Rook",
      N: "White Knight",
      B: "White Bishop",
      Q: "White Queen",
      K: "White King",
    };

    rows.forEach((row, rowIndex) => {
      let colIndex = 0;
      for (const char of row) {
        if (/\d/.test(char)) {
          colIndex += parseInt(char, 10);
        } else {
          const file = String.fromCharCode(97 + colIndex);
          const rank = 8 - rowIndex;
          const piece = PieceNames[char] || "Unknown Piece";
          description += `- ${piece} at ${file}${rank}\n`;
          colIndex++;
        }
      }
    });

    return description;
  } catch (e) {
    return "Invalid FEN string provided.";
  }
};
