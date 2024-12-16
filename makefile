# Project name for virtual environment
PROJECT_NAME := email_unsubscribe

# Define Python and virtual environment paths
PYTHON := python3
VENV_DIR := venv_$(PROJECT_NAME)
VENV_BIN := $(VENV_DIR)/bin

# Default target
.PHONY: all
all: help

# Create virtual environment
.PHONY: venv
venv:
	$(PYTHON) -m venv $(VENV_DIR)

# Install requirements
.PHONY: install
install: venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt

# Run the script with arguments: email, password, and items
run:
	@if [ -z "$(email)" ] || [ -z "$(password)" ] || [ -z "$(items)" ]; then \
		echo "Usage: make run email=<email> password=<password> items=<number_of_items>"; \
		exit 1; \
	fi
	$(VENV_BIN)/python email_unsubscribe.py $(email) $(password) $(items)

# Clean up virtual environment
.PHONY: clean
clean:
	rm -rf $(VENV_DIR)

# Help message
.PHONY: help
help:
	@echo "Usage:"
	@echo "  make venv       - Create a virtual environment named 'venv_<project_name>'"
	@echo "  make install    - Install dependencies into the virtual environment"
	@echo "  make run email=<your_email> password=<your_password> - Run the script with your email and password"
	@echo "  make clean      - Remove the virtual environment"

