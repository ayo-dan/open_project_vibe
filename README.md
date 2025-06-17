# Where's My Value?

This project contains a basic web crawler that runs from the command line. A separate UI will be built using shadcn components.

## Installation

Python 3.10 or newer is required. Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # downloads packages from PyPI
```

## Running the CLI Crawler

Start the crawler interactively:

```bash
python wheres_my_value.py
```

The script prompts for configuration options. To keep track of visited pages, answer `y` when asked about history tracking. A file named `crawler_history.json` will be created and used on subsequent runs.

Choose `y` when prompted to export results in order to generate a timestamped text report after the crawl.

Example session:

```text
$ python wheres_my_value.py
Base URL: https://example.com
Search values (comma separated): contact, form
Track visited URL history? [y/N]: y
Export results to a file? [y/N]: y
```

## Running Tests

Execute the unit test suite with pytest:

```bash
pytest
```

## Running the Development Servers

Start the FastAPI server:

```bash
uvicorn api.server:app
```

The frontend code lives in the `ui` directory. If you have initialized a Next.js
project there, run its dev server from inside that folder:

```bash
cd ui
npm run dev
```


## Starting the Web Server

Run the API server and open the UI:

```bash
uvicorn api.server:app --reload
```

Visit `http://localhost:8000` in your browser to use the form interface.

An example configuration using the previous layout is available in
`examples/server.py`.


## Netlify Deployment
The repo includes _headers and _redirects for Netlify as well as a .env.example to document build-time variables.

A `netlify.toml` file is provided to build the Next.js frontend and deploy Netlify functions. The configuration assumes the UI lives in `ui/` and publishes the `.next` output. The Next.js Netlify plugin is listed in `ui/package.json` as a development dependency.

Deploy using the Netlify CLI or connect this repository through the Netlify web UI.


