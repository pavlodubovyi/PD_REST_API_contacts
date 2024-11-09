# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# Path setup
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(1, os.path.abspath('../app'))
sys.path.insert(2, os.path.abspath('../utils'))

# Project information
project = 'Contact List REST API on FastAPI'
copyright = '2024, Pavlo Dubovyi'
author = 'Pavlo Dubovyi'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Autodoc options ---------------------------------------------------------
# Document members and functions even if they lack docstrings.
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}

autosummary_generate = True
autodoc_typehints = "description"
autodoc_members_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": -1
}
html_static_path = ['_static']
