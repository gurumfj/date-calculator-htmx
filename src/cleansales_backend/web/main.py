from fasthtml.common import fast_app, serve
from fasthtml.components import Script, Style
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.routing import Mount

from .batches_route import app as batches_app

# 添加 TailwindCSS CDN 和自定義樣式
tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

# 自定義樣式 CSS
custom_style = Style("""
.rotate-180 {
    transform: rotate(180deg);
}


""")

app, rt = fast_app(
    live=True,
    key_fname=".sesskey",
    session_cookie="cleansales",
    max_age=3600,
    hdrs=(tailwind_cdn, custom_style),
    pico=False,
    middleware=(Middleware(GZipMiddleware),),
    routes=(Mount("/batches", batches_app),),
)


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
