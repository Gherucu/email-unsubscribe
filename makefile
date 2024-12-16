# Variables
VENV_NAME = venv_email_unsubscribe
PYTHON = python3
PIP = $(VENV_NAME)/bin/pip
PYTHON_BIN = $(VENV_NAME)/bin/python
REQUIREMENTS = requirements.txt
SCRIPT = email_unsubscribe.py

# Default target: Run all steps
all: clean venv install

# Clean: Remove the virtual environment and temporary files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_NAME)
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -exec rm -f {} +
	find . -name "*.pyo" -exec rm -f {} +

# Create a virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	$(PIP) install -r $(REQUIREMENTS)

# Run the script
run:
	@echo "Running the script..."
	$(PYTHON_BIN) $(SCRIPT) $(email) $(password) $(items)

# Help message
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make venv       - Create a virtual environment named 'venv_<project_name>'"
	@echo "  make install    - Install dependencies into the virtual environment"
	@echo "  make run email=<your_email> password=<your_password> - Run the script with your email and password"
	@echo "  make clean      - Remove the virtual environment"

