from fastapi import APIRouter
from fastapi.responses import JSONResponse
from cortex.retrieval.stuff import web_stuff_summarization
from cortex.retrieval.stuff import SummarizeRequest, CategorizeRequest
from cortex.tools.categorize import categorize_summary


router = APIRouter(prefix="/summarize", tags=["Search related functions"])


@router.post("/web")
async def summarize(request: SummarizeRequest):
    result = web_stuff_summarization(request.url, request.openai_key)
    return JSONResponse(content={"web": request.url, "summary": result})


@router.post("/categorize")
async def categorize(request: CategorizeRequest):
    result = categorize_summary(request.summary, request.openai_key)
    return JSONResponse(content={"result": result})