#!/bin/bash

# Function to set up the environment on Linux
setup_linux() {
    echo "Setting up environment on Linux..."

    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install pip-tools
    pip install pip-tools

    # Create requirements.in file
    echo -e "scrapy\npandas\nstreamlit" > requirements.in

    # Compile requirements.txt
    pip-compile requirements.in

    # Install dependencies
    pip install -r requirements.txt

    # Start Scrapy project
    scrapy startproject etl_leiloes_veicular
    cd etl_leiloes_veicular

    echo "Setup completed."
}

# Function to set up the environment on Windows using WSL
setup_windows() {
    echo "Setting up environment on Windows using WSL..."

    # Install WSL if not already installed
    if ! grep -q Microsoft /proc/version; then
        echo "Please install WSL and retry."
        exit 1
    fi

    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install pip-tools
    pip install pip-tools

    # Create requirements.in file
    echo -e "scrapy\npandas\nstreamlit" > requirements.in

    # Compile requirements.txt
    pip-compile requirements.in

    # Install dependencies
    pip install -r requirements.txt

    # Start Scrapy project
    scrapy startproject etl_leiloes_veicular
    cd etl_leiloes_veicular

    echo "Setup completed."
}

# Check the operating system and call the appropriate function
if grep -q Microsoft /proc/version; then
    setup_windows
else
    setup_linux
fi
