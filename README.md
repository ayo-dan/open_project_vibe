# Where's My Value?

This project contains a basic web crawler that can be operated from the command line or via a Streamlit interface.

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

## Launching the Streamlit App

Run the web interface with:

```bash
streamlit run wheres_my_value_streamlit.py
```

The interface provides checkboxes for the same options as the CLI. Enable **Use visited history** to store progress in `crawler_history.json` and **Export results to file** to save a report when the crawl finishes.
