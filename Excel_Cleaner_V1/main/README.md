# Excel Cleaner Tool

This tool cleans Excel and CSV files according to configurable rules.  
It supports:
- Allowing date-formatted cells and names inside parentheses
- Auto-fix and dry-run modes
- A dynamic file list and embedded report viewer

## Project Structure

- **config.json** – Configuration settings  
- **requirements.txt** – Python dependencies  
- **RUN_HERE.bat** – Batch script to run the UI  
- **Makefile** – For installing dependencies and running the app  
- **src/**
  - **config_manager.py** – Centralized configuration loading/saving  
  - **cleaner.py** – Core cleaning logic (invoked from the UI or command line)  
  - **ui.py** – The main user interface with debugging/logging

## How to Run

Use the Makefile or run `RUN_HERE.bat` to launch the application.
