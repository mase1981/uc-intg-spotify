#!/bin/bash

cd /app
pip install --no-cache-dir -q -r requirements.txt
python -m uc_intg_spotify
