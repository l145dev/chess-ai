from pydantic import BaseModel

class MoveRequest(BaseModel):
    fen: str

class DecideRequest(BaseModel):
    prompt: str
    currentFen: str | None = None
