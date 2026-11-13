#!/bin/bash

# Function to set up the environment on Linux
setup_linux() {
    echo "Setting up environment on Linux..."

    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install pip-tools
    pip install pip-tools

    # Create requirements.in file with actual dependencies
    echo -e "scrapy\npandas\ndash\ndash-bootstrap-components" > requirements.in

    # Compile requirements.txt
    pip-compile requirements.in

    # Install dependencies
    pip install -r requirements.txt

    # Create data directory if it doesn't exist
    mkdir -p data

    echo "Setup completed."
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment: source .venv/bin/activate"
    echo "2. Run web scraping: cd src && scrapy crawl parque_leiloes -O ../../data/data.json"
    echo "3. Run transformation: python3 src/transformacao/main.py"
    echo "4. Run dashboard: cd src/dashboard && python3 app.py"
    echo "5. Open browser at http://127.0.0.1:8050/"
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

    # Create requirements.in file with actual dependencies
    echo -e "scrapy\npandas\ndash\ndash-bootstrap-components" > requirements.in

    # Compile requirements.txt
    pip-compile requirements.in

    # Install dependencies
    pip install -r requirements.txt

    # Create data directory if it doesn't exist
    mkdir -p data

    echo "Setup completed."
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment: source .venv/bin/activate"
    echo "2. Run web scraping: cd src && scrapy crawl parque_leiloes -O ../../data/data.json"
    echo "3. Run transformation: python3 src/transformacao/main.py"
    echo "4. Run dashboard: cd src/dashboard && python3 app.py"
    echo "5. Open browser at http://127.0.0.1:8050/"
}

# Check the operating system and call the appropriate function
if grep -q Microsoft /proc/version; then
    setup_windows
else
    setup_linux
fi
