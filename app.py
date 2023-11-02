from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

conversation_history = []

INITIAL_PROMPT = ("Du är en svensk mattelärare. "
                  "Om det är en mattefråga, guida eleverna genom att ställa uppföljande frågor."
                  "Annars, svara direkt. Alltid svara på svenska."
                  "Undvik hälsningar.")

user_turns_since_last_prompt = 0
MAX_TURNS_BEFORE_REPROMPT = 5
MAX_TURNS = 10

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_text', methods=['POST'])
def send_text():
    global conversation_history, user_turns_since_last_prompt
    data = request.json
    
    user_message = data["message"] + " (svara ENDAST på svenska. Var koncis; svara med en eller två meningar om möjligt.)"
    conversation_history.append({"role": "user", "content": user_message})

    user_turns_since_last_prompt += 1

    # Reprompt every MAX_TURNS_BEFORE_REPROMPT user turns
    if user_turns_since_last_prompt >= MAX_TURNS_BEFORE_REPROMPT:
        conversation_history.insert(0, {"role": "system", "content": INITIAL_PROMPT})
        user_turns_since_last_prompt = 0  # Reset the counter

    # Send request to LLM with a modified max_new_tokens
    response = requests.post(
        "https://17zayxht82.execute-api.eu-west-1.amazonaws.com/llama2-test/generate",
        headers={
            "Content-Type": "application/json",
            "X-Amzn-SageMaker-Custom-Attributes": "accept_eula=true"
        },
        json={
            "inputs": [conversation_history],
            "parameters": {"max_new_tokens": 80, "temperature": 0.05}  # Reduced tokens for conciseness
        }
    )

    response_json = response.json()
    ai_response = response_json[0].get('generation', {}).get('content', '') if isinstance(response_json, list) and len(response_json) > 0 else ""

    # Append assistant's response to conversation history
    conversation_history.append({"role": "assistant", "content": ai_response})

    while len(conversation_history) > MAX_TURNS:
        conversation_history.pop(0)  # Maintain a window of the latest turns

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)
