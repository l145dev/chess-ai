import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root directory is in sys.path to allow importing from engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.routes import decide, move

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Chess Engine Server is running"}

app.include_router(decide.router)
app.include_router(move.router)

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
