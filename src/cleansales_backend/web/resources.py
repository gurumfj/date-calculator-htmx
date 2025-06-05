"""Shared web resources for the application."""

from fasthtml.components import Link, Script, Style

# TailwindCSS CDN
tailwind_cdn = Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4")

# SVG favicon link
favicon_link = Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg")

# Custom CSS styles
custom_style = Style("""
.rotate-180 {
    transform: rotate(180deg);
}


""")

# Common headers bundle
common_headers = (tailwind_cdn, favicon_link, custom_style)