# .github/workflows/bot-run.yml

name: Run Discord Bot

on: 
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install discord.py aiohttp requests

      - name: Run Discord bot
        env:
          DToken: ${{ secrets.DToken }}
          GToken: ${{ secrets.GToken }}
        run: |
          python bot.py
