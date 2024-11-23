from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import routers as auth_routers
from .admin.router import routers as admin_routers
from .users.router import routers as users_routers
from .teams.router import routers as teams_routers
from .matches.router import routers as matches_routers


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,  # Type: ignore
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def app_include_routers(_app: FastAPI, routers: list[APIRouter]):
    for router in routers:
        _app.include_router(router)


app_include_routers(app, auth_routers)
app_include_routers(app, admin_routers)
app_include_routers(app, users_routers)
app_include_routers(app, teams_routers)
app_include_routers(app, matches_routers)
