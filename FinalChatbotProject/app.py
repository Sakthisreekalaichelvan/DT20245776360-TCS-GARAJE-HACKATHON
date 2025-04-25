import os
import openai
from flask import Flask, render_template, request, jsonify, send_file
from googletrans import Translator
from fpdf import FPDF
import uuid

openai.api_key = ''  # Replace with your OpenAI key

app = Flask(__name__)
translator = Translator()

def load_knowledge_base(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

knowledge_base = load_knowledge_base('knowledge_base/knowledge_base.txt')

def generate_answer(retrieved_text, query):
    prompt = f"Given the following information, answer the insurance query:\n{retrieved_text}\nQuestion: {query}\nAnswer:"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an insurance assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        temperature=0.7,
    )
    return response['choices'][0]['message']['content'].strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    language = request.form['language']

    # List of trigger keywords
    trigger_keywords = ['legal', 'complaint', 'issue', 'spam']

    # Check for any trigger keyword (case-insensitive)
    if any(word in query.lower() for word in trigger_keywords):
        response = "I will connect you to a human agent."
        if language != 'en':
            response = translator.translate(response, src='en', dest=language).text
        return jsonify({'response': response})

    # Translate query to English if needed
    if language != 'en':
        query = translator.translate(query, src=language, dest='en').text

    # Use OpenAI to get answer
    answer = generate_answer(knowledge_base, query)

    # Translate answer back to original language if needed
    if language != 'en':
        answer = translator.translate(answer, src='en', dest=language).text

    return jsonify({'response': answer})


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    response_text = request.form['response']
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, response_text)

    filename = f"response_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join("static", filename)
    pdf.output(filepath)

    return jsonify({'pdf_url': f"/static/{filename}"})

if __name__ == '__main__':
    app.run(debug=True)
