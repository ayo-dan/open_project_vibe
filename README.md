# Where's My Value?

This project contains a basic web crawler that runs from the command line. A separate UI will be built using shadcn components.

## Installation

Python 3.10 or newer is required. Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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

## Running the Development Servers

Start the FastAPI server:

```bash
uvicorn api.server:app
```

Start the Next.js dev server:

```bash
npm run dev
```


## Starting the Web Server

Run the API server and open the UI:

```bash
uvicorn server:app --reload
```

Visit `http://localhost:8000` in your browser to use the form interface.

