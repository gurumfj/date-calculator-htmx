from fasthtml.common import *
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from .batches_route import app as batches_app
from .resources import common_headers
from .sales_route import app as sales_app

app, rt = fast_app(
    live=True,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=common_headers,
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
    routes=(
        Mount("/batches", batches_app),
        Mount("/sales", sales_app),
        Mount("/static", StaticFiles(directory="src/cleansales_backend/web/static"), name="static"),
    ),
)


@app.get("/")
def index():
    nav_link = {
        "批次": "/batches",
        "銷售": "/sales",
    }
    return Title("Cleansales"), Body(
        Nav(
            Ul(
                Li(
                    A(
                        k,
                        href=v,
                        cls="text-lg font-semibold cursor-pointer",
                    )
                )
                for k, v in nav_link.items()
            ),
        ),
        cls="flex justify-center items-center h-full bg-blue-50 p-2",
    )


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
