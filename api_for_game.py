import json
from pathlib import Path
import aiofiles
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
AIREPORTS_DIR = DATA_DIR / "aireports"
METADATA_FILE = BASE_DIR / "metadata.json"


# Helper Functions
async def read_data_file(filepath: Path) -> str:
    """Reads content from a file"""
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filepath.name}' not found")
    async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
        return await f.read()


# FastAPI App
app = FastAPI(title="Data Query API", version="1.0.0")


# Pydantic Models
class StatusResponse(BaseModel):
    agent_name: str
    status: str


class QueueResponse(BaseModel):
    queue_content: List[str]


class CatalogueResponse(BaseModel):
    catalogue_content: List[str]


class DocumentContentResponse(BaseModel):
    document_name: str
    content: str


class AiReportResponse(BaseModel):
    report_name: str
    content: str


class DocumentQueryRequest(BaseModel):
    document_name: str = Field(..., description="Name of the document to query")


class AiReportQueryRequest(BaseModel):
    report_name: str = Field(..., description="Name of the AI report to query")


class AgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")


# API Endpoints
@app.post("/status", response_model=StatusResponse)
async def get_agent_status_post(request: AgentRequest):
    """Get agent status"""
    status_content = await read_data_file(DATA_DIR / request.agent_name)
    return StatusResponse(agent_name=request.agent_name, status=status_content)


@app.post("/queue", response_model=QueueResponse)
async def get_queue():
    """Get queue content"""
    queue_content = await read_data_file(DATA_DIR / "queue")
    return QueueResponse(queue_content=queue_content.splitlines())


@app.post("/catalogue", response_model=CatalogueResponse)
async def get_catalogue():
    """Get catalogue content"""
    catalogue_content = await read_data_file(DATA_DIR / "catalogue")
    return CatalogueResponse(catalogue_content=catalogue_content.splitlines())


@app.post("/documents", response_model=Dict[str, str])
async def list_documents():
    """List available documents from metadata.json file"""
    if not METADATA_FILE.is_file():
        return {}
    async with aiofiles.open(METADATA_FILE, mode="r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content) if content else {}


@app.post("/documents/query", response_model=DocumentContentResponse)
async def query_document(query: DocumentQueryRequest):
    """Query document content by name"""
    content = await read_data_file(DOCUMENTS_DIR / query.document_name)
    return DocumentContentResponse(document_name=query.document_name, content=content)


@app.post("/aireports/query", response_model=AiReportResponse)
async def query_aireport(query: AiReportQueryRequest):
    """Query AI report content by name"""
    filepath = AIREPORTS_DIR / f"{query.report_name}.txt"
    content = await read_data_file(filepath)
    return AiReportResponse(report_name=query.report_name, content=content)


@app.post("/aireports", response_model=List[str])
async def list_aireports():
    """List available AI reports"""
    if not AIREPORTS_DIR.exists():
        return []
    return [f.stem for f in AIREPORTS_DIR.glob("*.txt")]


@app.get("/")
async def root():
    return {"message": "Data Query API is running"}


# Create directories if they don't exist
@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup"""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    AIREPORTS_DIR.mkdir(parents=True, exist_ok=True)
