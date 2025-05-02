import sys, os
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Tourist agency consultant'
copyright = '2025, edikis, Cherry-pashka, DmitryKRX, 1makeyourdreams1'
author = 'edikis, Cherry-pashka, DmitryKRX, 1makeyourdreams1'
release = "'1.0.0'"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc', 
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'autodocsumm',
    'sphinx.ext.coverage'
]

sys.path.insert(0, '../agent')
sys.path.insert(0, '../../agent')
sys.path.insert(0, '../../../agent')
sys.path.insert(0, '../bot')
sys.path.insert(0, '../../bot')
sys.path.insert(0, '../../../bot')
sys.path.insert(0, '../faiss')
sys.path.insert(0, '../../faiss')
sys.path.insert(0, '../../../faiss')


# add in this line for the autosummary functionality
auto_doc_default_options = {'autosummary': True}

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
