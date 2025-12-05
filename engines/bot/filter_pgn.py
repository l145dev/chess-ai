import chess.pgn
import sys
import os

# Note: This script will be slow in Python, I recommend using a faster language like C#

# Settings
INPUT_PGN = "data/lichess_db_raw.pgn"
OUTPUT_PGN = "data/lichess_db.pgn"

# Strict filtering to get that file size down
MIN_TIME_CONTROL = 180 
MIN_AVG_ELO = 1800
MIN_MOVES = 20

def filter_pgn():
    if not os.path.exists(INPUT_PGN):
        print(f"Input file {INPUT_PGN} not found.")
        return

    print(f"Filtering {INPUT_PGN} -> {OUTPUT_PGN}")
    
    count_total = 0
    count_kept = 0
    
    with open(INPUT_PGN, "r") as f_in, open(OUTPUT_PGN, "w") as f_out:
        while True:
            # Save current position so we can go back if the game is good
            offset = f_in.tell()
            
            try:
                headers = chess.pgn.read_headers(f_in)
                if headers is None:
                    break # End of file
                
                count_total += 1
                
                # Header Checks (Fast)
                
                # Check ELO
                try:
                    w_elo = int(headers.get("WhiteElo", 0))
                    b_elo = int(headers.get("BlackElo", 0))
                    if (w_elo + b_elo) / 2 < MIN_AVG_ELO:
                        # CRITICAL FIX: Skip the moves of this bad game!
                        chess.pgn.skip_game(f_in) 
                        continue
                except ValueError:
                    chess.pgn.skip_game(f_in)
                    continue

                # Check Time Control
                tc = headers.get("TimeControl", "?")
                if tc == "?" or tc == "-" or "+" not in tc:
                    chess.pgn.skip_game(f_in)
                    continue
                    
                try:
                    base_time = int(tc.split("+")[0])
                    if base_time < MIN_TIME_CONTROL:
                        chess.pgn.skip_game(f_in)
                        continue
                except ValueError:
                    chess.pgn.skip_game(f_in)
                    continue

                # Full Game Checks (Slow, only for good headers)
                
                # If we are here, headers are good. Go back and read the full game.
                f_in.seek(offset)
                game = chess.pgn.read_game(f_in)
                
                # Check Move Count
                # Creating a list consumes the iterator, giving us the length
                if len(list(game.mainline_moves())) < MIN_MOVES:
                    continue

                # Save
                exporter = chess.pgn.FileExporter(f_out)
                game.accept(exporter)
                count_kept += 1
                
                if count_total % 5000 == 0:
                    print(f"Processed: {count_total} | Saved: {count_kept}", end='\r')

            except Exception as e:
                print(f"Skipping bad game due to error: {e}")
                continue

    print(f"\nDone. Processed {count_total}, Saved {count_kept}.")

if __name__ == "__main__":
    filter_pgn()