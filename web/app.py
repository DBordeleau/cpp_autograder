# FastAPI setup -- Creates admin account on startup if one does not already exist

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import WEB_DIR, SUBMISSIONS_DIR, DATA_DIR
from .database import init_db
from .config_loader import load_config_to_database, create_admin_if_not_exists
from .routes import auth_routes, student_routes, admin_routes

SUBMISSIONS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
init_db()
load_config_to_database()

app = FastAPI(title="C++ Autograder")

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

app.include_router(auth_routes.router)
app.include_router(student_routes.router)
app.include_router(admin_routes.router)

@app.on_event("startup")
async def startup_event():
    create_admin_if_not_exists()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)