from werkzeug.security import safe_join
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = 'replace_with_a_random_secret_key'

# Set up the API client and force the x-region header to an ASCII value.
client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
)

def call_api_to_edit_file(file_content, instructions):
    prompt = (
        f"Please modify the following file content as per these instructions:\n"
        f"{instructions}\n\n"
        f"Original File Content:\n{file_content}\n\n"
        f"Modified File Content:"
    )
    response = client.complete(
        messages=[UserMessage(prompt)],
        model="DeepSeek-R1",
        max_tokens=2048,
    )
    return response.choices[0].message.content

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        filename = request.form.get('filename')
        if not os.path.exists(filename):
            flash("File not found.", "error")
            return redirect(url_for('index'))
        with open(safe_join(app.root_path, filename), 'r', encoding='utf-8') as f:
            content = f.read()
        return render_template('editor.html', filename=filename, content=content)
    return render_template('index.html')

@app.route('/edit', methods=['POST'])
def edit():
    filename = secure_filename(request.form.get('filename'))
    instructions = request.form.get('instructions')
    if not os.path.exists(filename):
        flash("File not found.", "error")
        return redirect(url_for('index'))

    with open(safe_join(app.root_path, filename), 'r', encoding='utf-8') as f:
        original_content = f.read()

    try:
        edited_content = call_api_to_edit_file(original_content, instructions)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(edited_content)
        flash("File updated successfully.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    return redirect(url_for('index'))

from flask import Flask
app = Flask(__name__)
if __name__ == '__main__':
    app.run()
