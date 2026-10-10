# Sphinx configuration -- IAM docs, English translation (Read the Docs)
# Mirrors docs/conf.py; kept as a separate, self-contained config (not shared via import) so this
# tree can be a fully independent Sphinx project for Read the Docs' Translations feature.

project = "IAM — SAP Authorization Analysis with Neo4j"
author = "Mirko Prehn"
copyright = "2026, Mirko Prehn"
release = "0.1"

language = "en"

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

myst_heading_anchors = 3

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "legacy",
]

html_theme = "sphinx_rtd_theme"
html_title = "IAM Docs"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
