import argparse
from src.aiml_api import AIMLAPI
from src.utils import clean_text  # Assume you have some utility functions

def main():
    # Optionally, use argparse to process command-line arguments
    parser = argparse.ArgumentParser(description="Emotion and Thought Analyzer")
    parser.add_argument("--input", type=str, required=True, help="User input text")
    args = parser.parse_args()

    # Clean the input text if needed
    user_input = clean_text(args.input)

    # Initialize the AIML API interface
    aiml_api = AIMLAPI()
    
    # Craft a prompt that instructs the API on what to do
    prompt = (
        f"User Input: {user_input}\n"
        "Analyze the user's emotions and underlying thoughts. Provide a detailed description."
    )
    
    try:
        response = aiml_api.generate_response(prompt)
        print("AI Analysis:\n", response)
    except Exception as e:
        print("Error while calling AIML API:", str(e))

if __name__ == "__main__":
    main()
