import logging
from datetime import datetime, timedelta

from fasthtml.common import *
from fasthtml.oauth import GoogleAppClient, OAuth
from rich.logging import RichHandler
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from cleansales_backend.core.config import get_settings

from .batch_route_v2 import app as batch_route_v2_app
from .batches_route import app as batches_app
from .date_calculator import app as date_calculator_app
from .file_upload_handler import app as upload_app
from .resources import common_headers
from .sales_route import app as sales_app

# logger config with rich
logger = logging.getLogger(__name__)
logger.addHandler(RichHandler(level=logging.DEBUG))
# logger.addHandler(logging.StreamHandler())

google_client = GoogleAppClient(
    client_id=get_settings().GOOGLE_CLIENT_ID,
    client_secret=get_settings().GOOGLE_CLIENT_SECRET,
    )

db = create_engine('sqlite:///user.db')

# Create tables

def get_session():
    return Session(db)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    name: str
    scope: str

SQLModel.metadata.create_all(db)

class MyAuth(OAuth):
    def get_auth(self, info, ident, session, state):
        # Store user info in session if needed
        session['user_info'] = dict(info)
        new_user = User(
            email=info.get('email'),
            name=info.get('name'),
            scope='pending',
        )
        with get_session() as conn:
            query = select(User).where(User.email == info.get('email'))
            existing_user = conn.exec(query).one_or_none()
            if not existing_user:
                conn.add(new_user)
                conn.commit()
        # Return where to redirect after successful auth
        return RedirectResponse('/')

def auth_before(req: Request, sess):
    req.scope['auth'] = sess.get('auth', None)
    if not req.scope['auth']:
        return RedirectResponse('/login')

def scope_check_before(req: Request, sess: dict):
    user_info = sess.get('user_info')
    if not user_info:
        return RedirectResponse('/login')
    
    user_email = user_info.get('email')
    if not user_email:
        return RedirectResponse('/login')
    
    with get_session() as conn:
        query = select(User).where(User.email == user_email)
        user = conn.exec(query).one_or_none()
        
        if not user or user.scope == 'pending':
            return Response("Access denied: pending approval", status_code=403)
        
        req.scope['user'] = user

# batches_app.before.append(Beforeware(auth_before, skip=(r'/login', r'^/static/.*')))
# batches_app.before.append(Beforeware(scope_check_before, skip=(r'/login', r'^/static/.*')))
# sales_app.before.append(Beforeware(auth_before, skip=(r'/login', r'^/static/.*')))
# sales_app.before.append(Beforeware(scope_check_before, skip=(r'/login', r'^/static/.*')))

    
app, rt = fast_app(
    live=get_settings().WEB_LIVE,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=86400,
    hdrs=common_headers,
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
    routes=(
        Mount("/batches", batches_app),
        Mount("/new_batch_route", batch_route_v2_app),
        Mount("/sales", sales_app),
        Mount("/date_calculator", date_calculator_app),
        Mount("/upload", upload_app),
        Mount("/static", StaticFiles(directory="src/cleansales_backend/web/static"), name="static"),
    ),
)
# auth = MyAuth(app, google_client)

# app.before = Beforeware(auth_before, skip=(r'/login', r'^/static/.*'))




totoist_token = get_settings().TODOIST_API_TOKEN
if not totoist_token:
    raise ValueError("TODOIST_API_TOKEN is not set")
todoist = TodoistAPI(totoist_token)


class TodoistService:
    def __init__(self, api: TodoistAPI):
        self.api = api

    def _create_time_range(self, since: datetime, until: datetime):
        while since < until:
            yield (since, since + timedelta(days=30))
            since += timedelta(days=30)

    def get_completed_items(self) -> list[Task]:
        try:
            since = datetime.now() - timedelta(days=30)
            until = datetime.now()
            items: list[Task] = []
            for since, until in self._create_time_range(since, until):
                for item in self.api.get_completed_tasks_by_completion_date(since=since, until=until):
                    items.extend(item)

            return items
        except Exception as e:
            logger.error(e)
            return []


todoist_service = TodoistService(todoist)

# @rt('/login')
# def login(request: Request):
#     return Titled(
#         "Login",
#         Container(
#             H1("Login"),
#             A("Login with Google", href=auth.login_link(request), state='/', cls="button")
#         )
#     )

@app.get("/")
def index() -> Any:
    nav_link = {
        "批次": "/batches",
        "批次 v2": "/new_batch_route",
        "銷售": "/sales",
        "日期計算": "/date_calculator",
        "檔案上傳": "/upload",
        "待辦事項": "/todo",
    }
    return Title("Cleansales"), Body(
        Nav(
            Ul(
                Li(
                    A(
                        k,
                        href=v,
                        state=v,
                        cls="text-lg font-semibold cursor-pointer",
                    )
                )
                for k, v in nav_link.items()
            ),
        ),
        cls="flex justify-center items-center h-full bg-blue-50 p-2",
    )


@app.get("/todo")
def todo() -> Any:
    items = todoist_service.get_completed_items()
    logger.info(items)
    return Title("Todoist"), Body(
        Nav(
            Ul(
                Li(
                    A(
                        "Todoist",
                        href="/todo",
                        cls="text-lg font-semibold cursor-pointer",
                    )
                )
            ),
        ),
        Div(*[Li(item.content) for item in items]),
        cls="flex justify-center items-center h-full bg-blue-50 p-2",
    )


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
