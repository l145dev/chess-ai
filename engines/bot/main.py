import chess
import numpy as np

def get_move(board: chess.Board) -> chess.Move:
    legal_moves_count = board.legal_moves.count()
    random_move = np.random.randint(0, legal_moves_count)

    to_play_uci = list(board.legal_moves)[random_move]

    print(to_play_uci)

    return to_play_uci