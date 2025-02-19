from api import get_ai_response

def chat():
    print("Welcome to the AI Chatbot! (type 'exit' to quit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        print("AI: ", end="")
        get_ai_response(user_input)
