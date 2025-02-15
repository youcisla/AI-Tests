.PHONY: all install run debug

# 'all' will install dependencies and run the project.
all: install run

# Check and install dependencies from requirements.txt.
install:
	@echo "Checking and installing dependencies..."
	python -m pip install -r requirements.txt

# Run the project. If it errors, automatically jump into debugging.
run:
	@echo "Launching project..."
	@python api.py || $(MAKE) debug

# Debug mode: launches the Python debugger on the project.
debug:
	@echo "An error occurred. Launching debugger..."
	python -m pdb api.py
