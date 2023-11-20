from flask import Flask, request, jsonify, render_template
import requests
import os


application = Flask(__name__)

conversation_history = []

         #   "Om det är en mattefråga, guida eleverna genom att ställa uppföljande frågor."
INITIAL_PROMPT = ("Du är en svensk mattelärare. "
                  "Ge inte svar på matematikfrågor direkt, utan ställ vägledande frågor för att hjälpa eleverna att lösa det själva."
                  "Annars, svara direkt. Alltid svara på svenska."
                  "Undvik hälsningar.")

user_turns_since_last_prompt = 0
MAX_TURNS_BEFORE_REPROMPT = 5
MAX_TURNS = 10

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/send_text', methods=['POST'])
def send_text():
    
    data = request.json
    

    conversation_history = data["messages"]

    response = requests.post(
        "https://17zayxht82.execute-api.eu-west-1.amazonaws.com/llama2-test/generate",
        headers={
            "Content-Type": "application/json",
            "X-Amzn-SageMaker-Custom-Attributes": "accept_eula=true"
        },
        json={
            "inputs": [conversation_history],
            "parameters": {"max_new_tokens": 200, "temperature": 0.05}  # Reduced tokens for conciseness
        }
    )

    response_json = response.json()
    ai_response = response_json[0].get('generation', {}).get('content', '') if isinstance(response_json, list) and len(response_json) > 0 else ""

    # Append assistant's response to conversation history
    conversation_history.append({"role": "assistant", "content": ai_response})

    while len(conversation_history) > MAX_TURNS:
        conversation_history.pop(0)  # Maintain a window of the latest turns

    print(ai_response)
    return jsonify({"response": ai_response})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    application.run(debug=True, host='0.0.0.0', port=port)

