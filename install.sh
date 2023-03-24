#!/bin/bash

# Check if Python 3.10 is installed
if ! command -v python3.10 &> /dev/null; then
    echo "Python 3.10 is not installed. Please install it first."
    exit 1
fi

pip install -r requirements.txt