import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure the root directory is in sys.path to allow importing from engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.routes import decide, move

load_dotenv()

app = FastAPI()

origins = ["https://www.l145.be", "https://l145.be"]

if os.getenv("ENVIRONMENT") == "development":
    origins.append("http://localhost:4321")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
