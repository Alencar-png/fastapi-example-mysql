
from fastapi.middleware.cors import CORSMiddleware
from routers.users import user
from routers.security import security
from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="FastApiExample",
    docs_url="/api/docs", 
    redoc_url="/api/redoc",  
    openapi_url="/api/openapi.json"
)
app.include_router(security, prefix='/api', tags=['security'])
app.include_router(user, prefix='/api', tags=['users'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4200)
