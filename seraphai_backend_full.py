from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to extract text from uploaded document
def extract_text(file_path, content_type):
    if content_type.endswith('/pdf'):
        with fitz.open(file_path) as doc:
            return '\n'.join([page.get_text() for page in doc])
    elif content_type.startswith('image/'):
        return "Image parsing placeholder (OCR can be added)"
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

# Basic line parser for known terms
def parse_document(text):
    result = {"credit_score": None, "income": None, "dti": None, "ltv": None}
    lines = text.split('\n')
    for line in lines:
        lower = line.lower()
        if 'credit' in lower and not result['credit_score']:
            result['credit_score'] = next((part for part in line.split() if part.isdigit() and len(part) == 3), None)
        if 'income' in lower and not result['income']:
            result['income'] = next((part for part in line.split() if part.replace(',', '').isdigit()), None)
        if 'dti' in lower and not result['dti']:
            result['dti'] = next((part for part in line.split() if part.replace('.', '').isdigit()), None)
        if 'ltv' in lower and not result['ltv']:
            result['ltv'] = next((part for part in line.split() if part.replace('.', '').isdigit()), None)
    return result

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    content_type = file.content_type

    text = extract_text(path, content_type)
    parsed = parse_document(text)
    return jsonify(parsed)

@app.route('/lead-score', methods=['POST'])
def lead_score():
    data = request.json
    credit = int(data.get('credit', 0))
    income = float(data.get('income', 0))
    dti = float(data.get('dti', 100))
    score = 0
    if credit >= 700: score += 0.4
    elif credit >= 660: score += 0.2
    if income >= 80000: score += 0.3
    if dti <= 35: score += 0.3
    elif dti <= 43: score += 0.2
    return jsonify({"score": round(min(score, 1.0), 2)})

@app.route('/underwrite', methods=['POST'])
def underwrite():
    data = request.json
    credit = int(data.get('credit', 0))
    dti = float(data.get('dti', 100))
    ltv = float(data.get('ltv', 100))
    if credit >= 700 and dti <= 43 and ltv <= 80:
        return jsonify({"decision": "Approve"})
    elif credit >= 660 and dti <= 45:
        return jsonify({"decision": "Approve with Conditions"})
    else:
        return jsonify({"decision": "Refer to Manual Review"})

@app.route('/compliance-check', methods=['POST'])
def compliance_check():
    data = request.json
    flags = []
    if float(data.get('dti', 0)) > 43: flags.append('High DTI')
    if float(data.get('ltv', 0)) > 90: flags.append('High LTV')
    if not data.get('respa'): flags.append('Missing RESPA')
    if not data.get('hmda'): flags.append('Missing HMDA')
    if not data.get('income_verified'): flags.append('Unverified Income')
    return jsonify({"flags": flags or ["Compliant"]})

@app.route('/extract-document', methods=['POST'])
def extract_document():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    content_type = file.content_type
    text = extract_text(path, content_type)
    return jsonify({"text": text[:1000]})  # Preview first 1000 characters

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
