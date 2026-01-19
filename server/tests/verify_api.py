import requests
import json
import time

# Note: Server must be running on http://localhost:8000

BASE_URL = "http://localhost:8000"

def test_root():
    print("Testing Root...")
    try:
        res = requests.get(f"{BASE_URL}/")
        print(res.json())
        assert res.status_code == 200
    except Exception as e:
        print(f"Failed: {e}")

def test_decide_start_game():
    print("\nTesting Decide: Start Game...")
    payload = {
        "prompt": "Start game as white",
        "currentFen": None
    }
    try:
        res = requests.post(f"{BASE_URL}/decide", json=payload)
        data = res.json()
        print(json.dumps(data, indent=2))
        assert data["type"] == "start_game"
        assert data["side"] == "white"
    except Exception as e:
        print(f"Failed: {e}")

def test_decide_question():
    print("\nTesting Decide: Question...")
    payload = {
        "prompt": "Who is the world chess champion?",
        "currentFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }
    try:
        res = requests.post(f"{BASE_URL}/decide", json=payload)
        data = res.json()
        print(f"Response: {data['content'][:100]}...") # Print first 100 chars
        assert data["type"] == "text"
    except Exception as e:
        print(f"Failed: {e}")

def test_decide_move_direct():
    print("\nTesting Decide: Direct Move (SAN)...")
    payload = {
        "prompt": "e4",
        "currentFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }
    try:
        res = requests.post(f"{BASE_URL}/decide", json=payload)
        data = res.json()
        print(json.dumps(data, indent=2))
        assert data["type"] == "fen"
        assert "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1" in data["content"]
    except Exception as e:
        print(f"Failed: {e}")

def test_decide_play_move_intent():
    print("\nTesting Decide: Play Move Intent (Natural Language)...")
    payload = {
        "prompt": "play pawn to e4",
        "currentFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }
    try:
        res = requests.post(f"{BASE_URL}/decide", json=payload)
        data = res.json()
        print(json.dumps(data, indent=2))
        assert data["type"] == "fen"
        assert "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1" in data["content"]
    except Exception as e:
        print(f"Failed: {e}")

def test_decide_play_move_invalid():
    print("\nTesting Decide: Play Move Invalid (Smart Error Handling)...")
    payload = {
        "prompt": "play king to center", # Ambiguous/Invalid
        "currentFen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    }
    try:
        res = requests.post(f"{BASE_URL}/decide", json=payload)
        data = res.json()
        print(json.dumps(data, indent=2))
        assert data["type"] == "text"
        assert "understand" in data["content"] or "legal" in data["content"]
        print("Passed Smart Error Handling")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_root()
    test_decide_start_game()
    test_decide_question()
    test_decide_move_direct()
    test_decide_play_move_intent()
    test_decide_play_move_invalid()
