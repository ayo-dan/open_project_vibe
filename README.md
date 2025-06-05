Hey there! Here's my fun webcrawler project. Feel free to download the CLI version via "wheres_my_value.py" or check out the web version on Streamlit: https://wheresmyvaluetest.streamlit.app/

Enjoy!

## Getting Started

This project requires **Python 3.10+**. Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Running the CLI

Start the interactive crawler from the command line with:

```bash
python wheres_my_value.py
```

The script will prompt for options such as whether to track visited URLs in a
history file and if the crawler should respect `robots.txt` rules.

## Running the Streamlit App

Launch the web interface with:

```bash
streamlit run wheres_my_value_streamlit.py
```

The Streamlit UI exposes the same configuration settings as the CLI.
