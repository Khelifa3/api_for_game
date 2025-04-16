import json
from pathlib import Path
import aiofiles
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Union
import datetime
from uuid import uuid4

# FastAPI App
app = FastAPI(title="Data Query API")

# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
AIREPORTS_DIR = DATA_DIR / "aireports"
METADATA_FILE = BASE_DIR / "metadata.json"
TWEETS_DIR = DATA_DIR / "tweets"


# Helper Functions
async def read_data_file(filepath: Path) -> tuple:
    """Reads content from a file and returns (content, status_code)"""
    if not filepath.is_file():
        return f"File '{filepath.name}' not found", 404
    async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
        return await f.read(), 200


async def save_tweet_to_file(tweet_id: str, content: str) -> None:
    """Save tweet content to a file"""
    timestamp = datetime.datetime.now().isoformat()
    tweet_data = {"id": tweet_id, "content": content, "timestamp": timestamp}

    filepath = TWEETS_DIR / f"{tweet_id}.txt"
    async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(tweet_data, indent=2))


# Pydantic Models
class RootResponse(BaseModel):
    message: str
    status_code: int = Field(200, description="HTTP status code")


class StatusResponse(BaseModel):
    agent_name: str
    status: str
    status_code: int = Field(200, description="HTTP status code")


class QueueResponse(BaseModel):
    queue_content: List[str]
    status_code: int = Field(200, description="HTTP status code")


class CatalogueResponse(BaseModel):
    catalogue_content: List[str]
    status_code: int = Field(200, description="HTTP status code")


class DocumentContentResponse(BaseModel):
    document_name: str
    content: str
    status_code: int = Field(200, description="HTTP status code")


class AiReportResponse(BaseModel):
    report_name: str
    content: str
    status_code: int = Field(200, description="HTTP status code")


class DocumentQueryRequest(BaseModel):
    document_name: str = Field(..., description="Name of the document to query")


class AiReportQueryRequest(BaseModel):
    report_name: str = Field(..., description="Name of the AI report to query")


class AgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent")


class TweetRequest(BaseModel):
    tweet: str = Field(..., description="Content of the tweet to post")


class TweetReplyRequest(BaseModel):
    tweet_id: str = Field(..., description="ID of the tweet to reply to")
    reply: str = Field(..., description="Content of the reply")


class TweetResponse(BaseModel):
    tweet_id: str
    message: str
    status_code: int = Field(200, description="HTTP status code")


# API Endpoints
@app.post("/status", response_model=StatusResponse)
async def get_agent_status_post(request: AgentRequest):
    """Get agent status"""
    status_content, status_code = await read_data_file(
        DATA_DIR / f"{request.agent_name}.txt"
    )
    return StatusResponse(
        agent_name=request.agent_name, status=status_content, status_code=status_code
    )


@app.post("/queue", response_model=QueueResponse)
async def get_queue():
    """Get queue content"""
    queue_content, status_code = await read_data_file(DATA_DIR / "queue.txt")
    return QueueResponse(
        queue_content=queue_content.splitlines() if status_code == 200 else [],
        status_code=status_code,
    )


@app.post("/catalogue", response_model=CatalogueResponse)
async def get_catalogue():
    """Get catalogue content"""
    catalogue_content, status_code = await read_data_file(DATA_DIR / "catalogue.txt")
    return CatalogueResponse(
        catalogue_content=catalogue_content.splitlines() if status_code == 200 else [],
        status_code=status_code,
    )


@app.post("/documents", response_model=Dict[str, Union[str, int]])
async def list_documents():
    """List available documents from metadata.json file"""
    if not METADATA_FILE.is_file():
        return {"status_code": 404, "message": "Metadata file not found"}
    try:
        async with aiofiles.open(METADATA_FILE, mode="r", encoding="utf-8") as f:
            content = await f.read()
            result = json.loads(content) if content else {}
            result["status_code"] = 200
            return result
    except Exception as e:
        return {"status_code": 404, "message": str(e)}


@app.post("/document/query", response_model=DocumentContentResponse)
async def query_document(query: DocumentQueryRequest):
    """Query document content by name"""
    content, status_code = await read_data_file(DOCUMENTS_DIR / query.document_name)
    return DocumentContentResponse(
        document_name=query.document_name, content=content, status_code=status_code
    )


@app.post("/aireport/query", response_model=AiReportResponse)
async def query_aireport(query: AiReportQueryRequest):
    """Query AI report content by name"""
    filepath = AIREPORTS_DIR / f"{query.report_name}.txt"
    content, status_code = await read_data_file(filepath)
    return AiReportResponse(
        report_name=query.report_name, content=content, status_code=status_code
    )


class AiReportsListResponse(BaseModel):
    reports: List[str]
    status_code: int = Field(200, description="HTTP status code")


@app.post("/aireports", response_model=AiReportsListResponse)
async def list_aireports():
    """List available AI reports"""
    if not AIREPORTS_DIR.exists():
        return AiReportsListResponse(reports=[], status_code=404)
    return AiReportsListResponse(
        reports=[f.stem for f in AIREPORTS_DIR.glob("*.txt")], status_code=200
    )


@app.post("/post_tweet", response_model=TweetResponse)
async def post_tweet(request: TweetRequest):
    """Post a new tweet"""
    try:
        # Generate a unique tweet ID
        tweet_id = f"tweet_{uuid4().hex[:8]}"

        # Save tweet content to file
        await save_tweet_to_file(tweet_id, request.tweet)

        # Return success response
        return TweetResponse(
            tweet_id=tweet_id, message="Tweet posted successfully", status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reply_tweet", response_model=TweetResponse)
async def reply_tweet(request: TweetReplyRequest):
    """Reply to an existing tweet"""
    try:
        # Generate a unique reply ID
        reply_id = f"reply_{uuid4().hex[:8]}"

        # Create reply content with reference to original tweet
        reply_content = {"reply_to": request.tweet_id, "content": request.reply}

        # Save reply to file
        await save_tweet_to_file(reply_id, json.dumps(reply_content))

        # Return success response
        return TweetResponse(
            tweet_id=reply_id,
            message=f"Reply to tweet {request.tweet_id} posted successfully",
            status_code=200,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_model=RootResponse)
async def root():
    return RootResponse(message="Data Query API is running", status_code=200)


# Create directories if they don't exist
@app.on_event("startup")
async def startup_event():
    """Create necessary directories on startup"""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    AIREPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TWEETS_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
