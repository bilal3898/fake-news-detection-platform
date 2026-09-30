from fastapi.responses import JSONResponse
from fastapi import Request, FastAPI

async def http_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal Server Error: {exc}"}
    )

def add_error_handlers(app: FastAPI):
    app.add_exception_handler(Exception, http_error_handler)