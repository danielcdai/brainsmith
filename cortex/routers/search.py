from typing import List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from cortex.retrieval.search import SearchRequest, search_by_collection


router = APIRouter(prefix="/search", tags=["Search related functions"])


@router.post("/", response_model=List[str])
async def search(request: SearchRequest):
    """
    POST endpoint to perform a search based on the provided parameters.
    """
    # Perform the search using the provided parameters
    docs = search_by_collection(
        collection_name=request.name, 
        query=request.query, 
        top_k=request.top_k, 
        search_type=request.search_type,
        **request.opts
    )
    if request.content_only:
        # Concise response for later embedding tasks
        return JSONResponse(content=[doc.page_content for doc in docs])
    contents = [{"length": len(doc.page_content), "content": doc.page_content} for doc in docs]
    return JSONResponse(content={"total": len(contents), "contents": contents})