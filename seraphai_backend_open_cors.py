from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Add services directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.crypto_prospecting import CryptoProspectingService
from dataclasses import asdict

app = Flask(__name__)
CORS(app)  # Allow all origins for testing

# Initialize crypto prospecting service
crypto_prospecting = CryptoProspectingService()


# ============================================
# CRYPTO PROSPECTING ENDPOINTS (Permissionless)
# ============================================

@app.route('/prospect/analyze', methods=['POST'])
def prospect_analyze():
    """
    Analyze a single wallet address for mortgage qualification.
    No wallet connection required - uses public blockchain data.

    Request body:
    {
        "wallet_address": "0x..."
    }
    """
    print("Received /prospect/analyze request")
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')

        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400

        # Validate address format
        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return jsonify({'error': 'Invalid Ethereum address format'}), 400

        # Analyze wallet
        metrics = crypto_prospecting.analyze_wallet(wallet_address)
        return jsonify(asdict(metrics))

    except Exception as e:
        print(f"Error in /prospect/analyze: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/prospect/score', methods=['POST'])
def prospect_score():
    """
    Calculate mortgage qualification score for a wallet.
    Returns comprehensive scoring with risk tier and recommendations.

    Request body:
    {
        "wallet_address": "0x..."
    }
    """
    print("Received /prospect/score request")
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')

        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400

        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return jsonify({'error': 'Invalid Ethereum address format'}), 400

        # Score wallet
        score = crypto_prospecting.score_for_mortgage(wallet_address)
        return jsonify(asdict(score))

    except Exception as e:
        print(f"Error in /prospect/score: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/prospect/report', methods=['POST'])
def prospect_report():
    """
    Generate comprehensive prospect report combining analysis and scoring.

    Request body:
    {
        "wallet_address": "0x..."
    }
    """
    print("Received /prospect/report request")
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')

        if not wallet_address:
            return jsonify({'error': 'wallet_address is required'}), 400

        if not wallet_address.startswith('0x') or len(wallet_address) != 42:
            return jsonify({'error': 'Invalid Ethereum address format'}), 400

        # Generate full report
        report = crypto_prospecting.generate_prospect_report(wallet_address)
        return jsonify(report)

    except Exception as e:
        print(f"Error in /prospect/report: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/prospect/batch', methods=['POST'])
def prospect_batch():
    """
    Batch analyze multiple wallets and rank by qualification score.
    Useful for analyzing lead lists or token holder snapshots.

    Request body:
    {
        "wallet_addresses": ["0x...", "0x...", ...]
    }
    """
    print("Received /prospect/batch request")
    try:
        data = request.get_json()
        addresses = data.get('wallet_addresses', [])

        if not addresses:
            return jsonify({'error': 'wallet_addresses array is required'}), 400

        if len(addresses) > 50:
            return jsonify({'error': 'Maximum 50 addresses per batch'}), 400

        # Validate all addresses
        for addr in addresses:
            if not addr.startswith('0x') or len(addr) != 42:
                return jsonify({'error': f'Invalid address format: {addr}'}), 400

        # Batch analyze
        results = crypto_prospecting.batch_analyze(addresses)
        return jsonify({
            'total_analyzed': len(results),
            'prospects': results
        })

    except Exception as e:
        print(f"Error in /prospect/batch: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/prospect/discover', methods=['POST'])
def prospect_discover():
    """
    Discover qualified prospects from a list of addresses.
    Filters by minimum value and score thresholds.

    Request body:
    {
        "wallet_addresses": ["0x...", ...],
        "min_value_usd": 50000,  // optional, default 50000
        "min_score": 60  // optional, default 60
    }
    """
    print("Received /prospect/discover request")
    try:
        data = request.get_json()
        addresses = data.get('wallet_addresses', [])
        min_value = float(data.get('min_value_usd', 50000))
        min_score = float(data.get('min_score', 60))

        if not addresses:
            return jsonify({'error': 'wallet_addresses array is required'}), 400

        if len(addresses) > 100:
            return jsonify({'error': 'Maximum 100 addresses per discovery'}), 400

        # Discover qualified prospects
        prospects = crypto_prospecting.discover_prospects(
            min_value_usd=min_value,
            min_score=min_score,
            sample_addresses=addresses
        )

        return jsonify({
            'total_scanned': len(addresses),
            'qualified_count': len(prospects),
            'filters': {
                'min_value_usd': min_value,
                'min_score': min_score
            },
            'prospects': [asdict(p) for p in prospects]
        })

    except Exception as e:
        print(f"Error in /prospect/discover: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/prospect/demo', methods=['GET'])
def prospect_demo():
    """
    Demo endpoint showing prospecting capabilities with a known wallet.
    Returns a sample analysis without requiring any input.
    """
    print("Received /prospect/demo request")
    try:
        # Use a well-known wallet for demo (Vitalik's)
        demo_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        report = crypto_prospecting.generate_prospect_report(demo_address)
        report['demo_note'] = "This is a demo using a well-known public wallet address."

        return jsonify(report)

    except Exception as e:
        print(f"Error in /prospect/demo: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================
# EXISTING ENDPOINTS
# ============================================

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
