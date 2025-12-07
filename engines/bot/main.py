import chess
from engines.bot.search import Searcher

# Global Instance
searcher = Searcher()

# Main function for getting move
def get_move(board: chess.Board, depth=5) -> chess.Move:
    # Adapt simple signature to usage of Searcher
    return searcher.get_move(board, depth=depth)
