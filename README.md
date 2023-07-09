# Badge Scraper

## Scrapes badges

## Setup
* Create a venv with `python3 -m venv venv`
* Activate it
  * `source venv/bin/activate` on Linux/MacOS
  * `.venv/Scripts/Activate.ps1` on Windows
* Install requirements with `pip install -r requirements.txt`
* Copy the config with `cp config.json.example config.json`
* Edit the config, set the webhook URL, set the thread limit and how many badges will it check per update sent & database save (Batch size)
* Run the scraper with `python main.py`
