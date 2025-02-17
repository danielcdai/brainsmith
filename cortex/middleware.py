from fastapi import Request
from cortex.brainsmith_logger import log
import time


async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    process_time_formatted = time.strftime("%H:%M:%S", time.gmtime(process_time)) + f":{int((process_time % 1) * 1000):03d}"
    log_dict = {
        "url": request.url.path,
        "method": request.method,
        "process_time": process_time_formatted,
    }
    log.debug(log_dict)
    return response