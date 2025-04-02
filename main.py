from fastapi import FastAPI, HTTPException
from pathlib import Path
from pydantic import BaseModel

app = FastAPI()

# Directory where the status files are stored
DATA_DIR = Path("./data")


class AgentRequest(BaseModel):
    agent_name: str


@app.get("/status/{agent_name}")
def get_agent_status(agent_name: str):
    file_path = DATA_DIR / f"{agent_name}.txt"
    if not file_path.exists():
        return {"status_code": 404, "status": ""}
    return {"status_code": 200, "status": file_path.read_text()}


@app.post("/status/")
def get_agent_status_post(request: AgentRequest):
    agent_name = request.agent_name.lower()
    print(agent_name)
    file_path = DATA_DIR / f"{agent_name}.txt"
    if not file_path.exists():
        return {"status_code": 404, "status": ""}
    return {"status_code": 200, "status": file_path.read_text()}


@app.get("/queue")
@app.post("/queue")
def get_queue():
    file_path = DATA_DIR / "queue.txt"
    if not file_path.exists():
        return {"status_code": 404, "queue": ""}
    return {"status_code": 200, "queue": file_path.read_text().splitlines()}


@app.get("/catalogue")
@app.post("/catalogue")
def get_catalogue():
    file_path = DATA_DIR / "catalogue.txt"
    if not file_path.exists():
        return {"status_code": 404, "catalogue": ""}
    return {"status_code": 200, "catalogue": file_path.read_text().splitlines()}
