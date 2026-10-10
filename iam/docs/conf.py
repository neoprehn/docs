# Sphinx-Konfiguration — IAM-Doku (Read the Docs)
# Markdown-Quellen über MyST. Build: sphinx-build -b html docs docs/_build/html

project = "IAM — SAP-Berechtigungsanalyse mit Neo4j"
author = "Mirko Prehn"
copyright = "2026, Mirko Prehn"
release = "0.1"

language = "de"

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx_copybutton",
]

# MyST-Erweiterungen: Doppelpunkt-Fences (```{note}), Definitionslisten
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# Tiefe der automatisch erzeugten Anker-Slugs für Querverweise auf Überschriften
myst_heading_anchors = 3

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "legacy",
]

html_theme = "sphinx_rtd_theme"
html_title = "IAM-Doku"
# Tiefere Navigation im linken Menue (Standard des Themes ist maxdepth 2) -- passend zu den
# verschachtelten toctree-Captions in index.md (Handbuch/Technik/Entwicklungsverlauf).
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
}
# Lesebereich verbreitern (Theme-Standard ist schmal) -- docs/_static/custom.css
html_static_path = ["_static"]
html_css_files = ["custom.css"]
