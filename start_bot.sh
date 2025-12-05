#!/bin/bash

if command -v python3 &> /dev/null; then
    python3 lichess-bot.py
elif command -v python &> /dev/null; then
    python lichess-bot.py
else
    echo "Error: Neither python nor python3 found in PATH"
    exit 1
fi