import requests
import yaml
import os

class AIMLAPI:
    def __init__(self, config_path="config/config.yaml"):
        # Load configuration from the YAML file
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        self.api_key = config["aiml_api"]["api_key"]
        self.endpoint = config["aiml_api"]["endpoint"]

    def generate_response(self, prompt, max_tokens=150):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens
        }
        response = requests.post(self.endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            # Adjust parsing based on API response structure
            data = response.json()
            return data.get("result", "No result returned")
        else:
            raise Exception(f"API call failed with status code {response.status_code}: {response.text}")

# Example usage (can be removed or placed under a __main__ block):
if __name__ == "__main__":
    aiml_api = AIMLAPI()
    prompt = "User: I'm feeling a bit overwhelmed by everything lately. Describe my emotions and thoughts."
    result = aiml_api.generate_response(prompt)
    print("AIML API Response:", result)
