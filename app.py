from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

conversation_history = []  # To keep track of conversation history





INITIAL_PROMPT = ("Du är en svensk mattelärare och svarar enbart på svenska."
                  "För mattefrågor, istället för att direkt ge svaret, guida eleverna genom att ställa uppföljande frågor för att hjälpa dem komma fram till svaret själva."
                  "Håll ditt svar kort och inom en mening.")


# INITIAL_PROMPT = ("Du är en svensk mattelärare och svarar enbart på svenska."
#                   "Hjälp eleverna med deras mattefrågor genom att guida dem med stödjande och pedagogiska frågor, istället för att direkt ge svaret."
#                   "Ditt svar ska vara koncist och korrekt, helst inom en meningar."
#                   "Hjälp eleverna pedagogiskt utan att ge direkt svar.")

MAX_TURNS = 10  # For 5 user messages and 5 assistant messages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_text', methods=['POST'])
def send_text():
    global conversation_history
    data = request.json
    user_message = data["message"] + "(Som svensk mattelärare, svara på svenska. Hjälp eleverna med deras mattefrågor genom att guida dem med stödjande och pedagogiska frågor. Håll ditt svar kort, helst inom en meningar.)"  # append the initial prompt to user message

    # If the conversation history is empty or ends with an assistant's response, just append the user message
    if not conversation_history or conversation_history[-1]["role"] == "assistant":
        conversation_history.append({"role": "user", "content": user_message})
    else:
        # If the last message was from the user, replace it with the new user message
        conversation_history[-1] = {"role": "user", "content": user_message}

    # If there's no system message in the conversation history, prepend it
    if not any(message["role"] == "system" for message in conversation_history):
        conversation_history.insert(0, {"role": "system", "content": INITIAL_PROMPT})

    # Send request to LLM
    response = requests.post(
        "https://17zayxht82.execute-api.eu-west-1.amazonaws.com/llama2-test/generate",
        headers={
            "Content-Type": "application/json",
            "X-Amzn-SageMaker-Custom-Attributes": "accept_eula=true"
        },
        json={
            "inputs": [conversation_history],
            "parameters": {"max_new_tokens": 150, "temperature": 0.1}
        }
    )

    response_json = response.json()

    # Append assistant's response to conversation history
    ai_response = response_json[0].get('generation', {}).get('content', '') if isinstance(response_json, list) and len(response_json) > 0 else ""
    conversation_history.append({"role": "assistant", "content": ai_response})

    # Maintain a sliding window of conversation turns
    while len(conversation_history) > MAX_TURNS:
        conversation_history.pop(0)  # Remove the oldest turn

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    app.run(debug=True)
