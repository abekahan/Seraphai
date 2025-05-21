from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, origins=["https://abekahan.github.io"])

@app.route('/upload', methods=['POST'])
def upload():
    print("Received /upload request")
    return jsonify({
        'credit_score': 720,
        'income': 95000,
        'dti': 35,
        'ltv': 78
    })

@app.route('/lead-score', methods=['POST'])
def lead_score():
    print("Received /lead-score request")
    data = request.get_json()
    credit = int(data.get('credit', 0))
    income = float(data.get('income', 0))
    dti = float(data.get('dti', 0))
    score = min(1.0, (credit - 600) / 200 * 0.4 + (income / 100000) * 0.3 + (1 - dti / 50) * 0.3)
    return jsonify({'score': round(score, 2)})

@app.route('/underwrite', methods=['POST'])
def underwrite():
    print("Received /underwrite request")
    data = request.get_json()
    credit = int(data.get('credit', 0))
    dti = float(data.get('dti', 0))
    ltv = float(data.get('ltv', 0))
    decision = 'Approve' if credit > 680 and dti < 40 and ltv < 80 else 'Refer to Manual Underwriting'
    return jsonify({'decision': decision})

@app.route('/compliance-check', methods=['POST'])
def compliance_check():
    print("Received /compliance-check request")
    data = request.get_json()
    flags = []
    if float(data.get('dti', 0)) > 43:
        flags.append('High DTI')
    if float(data.get('ltv', 0)) > 85:
        flags.append('High LTV')
    if not data.get('respa'):
        flags.append('Missing RESPA')
    if not data.get('hmda'):
        flags.append('Missing HMDA')
    if not data.get('income_verified'):
        flags.append('Unverified Income')
    return jsonify({'flags': flags})

@app.route('/extract-document', methods=['POST'])
def extract_document():
    print("Received /extract-document request")
    file = request.files['file']
    content = file.read(1000).decode(errors='ignore')
    return jsonify({'text': content})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
