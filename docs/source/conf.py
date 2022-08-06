# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'Istio & Envoy 内幕'
copyright = '2021, Mark Zhu'
author = 'Mark Zhu'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'myst_parser'
]

html_title = "Istio & Envoy 内幕"
html_favicon = '_static/favicon.ico'
html_logo = "_static/logo.png"

html_theme_options = {
    "home_page_in_toc": True,
    "github_url": "https://github.com/labilezhu/istio-insider",
    "repository_url": "https://github.com/labilezhu/istio-insider",
    "repository_branch": "master",
    # "path_to_docs": "docs",
    "use_repository_button": True,
    "use_edit_page_button": False,
    "show_navbar_depth": 8,
    "logo_only": True,
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_book_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
