from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors_middleware(app: FastAPI):
    """
    Configures and registers Cross-Origin Resource Sharing (CORS) middleware.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
