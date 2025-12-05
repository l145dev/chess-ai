import chess.pgn
import sys
import os

# Settings
INPUT_PGN = "data/lichess_db_raw.pgn"
OUTPUT_PGN = "data/lichess_db.pgn"

MIN_TIME_CONTROL = 180 # seconds
MIN_AVG_ELO = 1600
MIN_MOVES = 20

def filter_pgn():
    if not os.path.exists(INPUT_PGN):
        print(f"Input file {INPUT_PGN} not found.")
        return

    print(f"Filtering {INPUT_PGN} -> {OUTPUT_PGN}")
    print(f"Criteria: TimeControl >= {MIN_TIME_CONTROL}s, Avg ELO > {MIN_AVG_ELO}, Moves > {MIN_MOVES}")

    count_in = 0
    count_out = 0
    
    with open(INPUT_PGN, "r") as f_in, open(OUTPUT_PGN, "w") as f_out:
        while True:
            try:
                # read_headers is faster if we filter by headers, but we need move count too.
                # read_game reads everything.
                # To optimize, we can read headers first, check ELO/TC, then skip if fail.
                # But chess.pgn doesn't support "skip rest of game" easily without reading it.
                # Actually, read_game is fine for offline processing unless it's huge.
                # If it's massive, we might want a custom parser or use chess.pgn.read_headers
                # and then read_game only if headers pass.
                
                # Let's try read_game first.
                offset = f_in.tell()
                headers = chess.pgn.read_headers(f_in)
                if headers is None:
                    break
                    
                # 1. Check ELO
                try:
                    white_elo = int(headers.get("WhiteElo", 0))
                    black_elo = int(headers.get("BlackElo", 0))
                    avg_elo = (white_elo + black_elo) / 2
                    if avg_elo <= MIN_AVG_ELO:
                        count_in += 1
                        continue # Skip
                except ValueError:
                    count_in += 1
                    continue

                # 2. Check Time Control
                # Format: "600+0", "180+2", "-"
                tc = headers.get("TimeControl", "")
                if tc == "" or tc == "-":
                    # Assume correspondence or unknown, skip if we want strict blitz/rapid
                    count_in += 1
                    continue
                
                try:
                    base_time = int(tc.split("+")[0])
                    if base_time < MIN_TIME_CONTROL:
                        count_in += 1
                        continue
                except ValueError:
                    count_in += 1
                    continue

                # If headers pass, we need to check move count.
                # We need to parse the game now.
                # seek back to read the full game? Or is there a way to continue?
                # read_headers consumes headers. The file pointer is at the moves.
                # We can use read_game but we need to seek back to offset.
                f_in.seek(offset)
                game = chess.pgn.read_game(f_in)
                
                # 3. Check Move Count
                # mainline_moves() is an iterator, len() might not work directly without converting to list
                # count moves
                move_count = 0
                for _ in game.mainline_moves():
                    move_count += 1
                    if move_count > MIN_MOVES:
                        break
                
                if move_count <= MIN_MOVES:
                    count_in += 1
                    continue

                # All passed
                print(game, file=f_out, end="\n\n")
                count_out += 1
                count_in += 1
                
                if count_in % 1000 == 0:
                    print(f"Processed {count_in}, Saved {count_out}...", end='\r')

            except Exception as e:
                print(f"Error processing game: {e}")
                continue

    print(f"\nFinished. Processed {count_in}, Saved {count_out}.")

if __name__ == "__main__":
    filter_pgn()
