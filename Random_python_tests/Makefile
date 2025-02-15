.PHONY: all venv install server run

all: venv install server run

venv:
	@if exist venv\Scripts\python.exe ( \
		echo Virtual environment exists. \
	) else ( \
		echo Creating virtual environment... && py -m venv venv \
	)

install:
	@echo Installing dependencies...
	@venv\Scripts\python.exe -m pip install -r requirements.txt

server:
	@echo Starting local LLM server...
	@venv\Scripts\python.exe openai_api.py --cpu-only --server-name 127.0.0.1 --server-port 8000

run:
	@echo Running screen_captioner.py...
	@venv\Scripts\python.exe screen_captioner.py
