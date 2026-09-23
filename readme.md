# arXiv RSS Reader

An experimental desktop research utility for searching arXiv, saving papers to a local SQLite database, maintaining author/topic subscriptions, and exploring semantic relationships between saved abstracts.

## Status

This is a personal research tool under development. The Tkinter interface and core data code are not yet packaged as a stable public API. Known limitations include synchronous work in parts of the GUI, limited migration support for existing databases, and incomplete automated coverage outside the arXiv query layer.

## Features

- fielded arXiv search by author, title, abstract, or all fields;
- optional publication-date filtering;
- local paper collection and subscription/digest views;
- PDF links and paper metadata;
- optional sentence-transformer embeddings and similarity visualization.

The embedding stack is comparatively large and may download a model on first use.

## Requirements

- Python 3.10 or newer;
- Tkinter supplied by your Python/system installation; and
- the packages in `requirements.txt`.

Tkinter is not installed from PyPI. On Linux it may need to be installed with the operating system's package manager.

## Install and run

```bash
git clone https://github.com/marcCarnovale/arXivRss.git
cd arXivRss
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The application creates a local database when it starts. Personal databases, caches, and downloaded artifacts are excluded from version control.

## Development

Core tests use local Atom fixtures and do not contact arXiv:

```bash
python -m pip install -r requirements-dev.txt
pytest -q
ruff check --select E4,E7,E9,F,I arxiv_query.py boolean_parser.py tests
```

Network access identifies the client, uses HTTPS and a timeout, and spaces paginated requests. Live arXiv behavior is intentionally outside the ordinary test suite.

## Known limitations

- Query/parser and database behavior need broader characterization tests.
- Some operations can block the GUI while network or model work completes.
- Semantic similarity is exploratory and should not be interpreted as a citation or quality metric.
- Import/export and accessibility work remain incomplete.

## License

The repository is distributed under the included MIT license.
