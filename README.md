# Strava club - Week's Leaderboard

A Python code for scraping data from Strava club leaderboards using Selenium.

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)

## Introduction

* This Python code allows you to scrape data from Strava club leaderboards, providing information about club members, such as rank, distance. It uses [Selenium](https://www.selenium.dev/) to automate interactions with the [Strava](https://www.strava.com/) website.
* Creates posters (images) from the received information using [Pillow](https://python-pillow.org/).
* The created posters are sent to the Telegram `chat_id` specified by you (channel/chat/private message). [Aiogram](https://aiogram.dev/) is used.

* [![https://imgur.com/vK7rIuQ.png](https://imgur.com/vK7rIuQ.png)](https://imgur.com/vK7rIuQ.png)
## Installation
1. **Clone this repository:**

    ```bash
    git clone https://github.com/sergbondckua/strava_club_last_week_leaderboard.git
    ```
2. **Copy .env.template to .env and fill in the necessary data:**
   ```bash
   cp .env.template .env
   ```
3. **Without Docker:**
   1. Create a [venv](https://docs.python.org/3/library/venv.html)
       ```bash
       cd strava_club_last_week_leaderboard/
       ```
       ```bash
       python3 -m venv venv
       ```
       ```bash
       source venv/bin/activate
       ```
   2. **Upgrade** `pip`:
      ```bash
       pip install --upgrade pip
      ```
   3. **Install dependencies from** `requirements.txt`:
      ```bash
      pip install -r requirements.txt
      ```
   4. **Run the project:**
      ```bash
      python aps_run.py
      ```
      OR
      ```bash
      python main.py
      ```
4. **Docker:**
   1. You can directly run the project with Docker. If you don't have Docker installed, you can [download and install it](https://docs.docker.com/get-docker/).
   2. Run the project with the command: `docker-compose up` or `docker-compose up -d`
