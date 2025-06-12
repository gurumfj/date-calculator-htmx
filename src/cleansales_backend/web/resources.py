"""Shared web resources for the application."""

from fasthtml.components import Link, Script

# TailwindCSS CDN
tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")
typography_cdn = Link(
    rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@tailwindcss/typography@latest/dist/typography.min.css"
)

# SVG favicon link
favicon_link = Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg")

# Custom CSS styles
# custom_style = Style("""
# .rotate-180 {
#     transform: rotate(180deg);
# }

# """)
alpine_cdn = Script(src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True)

# Common headers bundle
common_headers = (tailwind_cdn, typography_cdn, favicon_link, alpine_cdn)
