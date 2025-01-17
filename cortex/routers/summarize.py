from fastapi import APIRouter
from fastapi.responses import JSONResponse
from cortex.retrieval.stuff import web_stuff_summarization
from cortex.retrieval.stuff import SummarizeRequest


router = APIRouter()


@router.post("/summarize/web")
async def summarize(request: SummarizeRequest):
    result = web_stuff_summarization(request.url, request.openai_key)
    return JSONResponse(content={"web": request.url, "summary": result})