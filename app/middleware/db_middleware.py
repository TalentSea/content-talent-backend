from starlette.middleware.base import BaseHTTPMiddleware
from app.database import db_proxy

class PeeweeDBMiddleware(BaseHTTPMiddleware):
    """
    Middleware to manage Peewee database connections per HTTP request.
    Opens a database connection before request processing starts
    and closes it cleanly after the response is returned.
    """
    async def dispatch(self, request, call_next):
        if db_proxy.is_closed():
            db_proxy.connect()
        try:
            response = await call_next(request)
        finally:
            if not db_proxy.is_closed():
                db_proxy.close()
        return response
