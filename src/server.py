from flask import Flask, jsonify
from flask import after_this_request
from predict import run_prediction

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/prediction/<event_id>')
def prediction(event_id):
    df = run_prediction(event_id)
    if df is None or df.empty:
        return jsonify({'error': 'prediction failed'}), 404
    data = {
        'Predictions': df['Prediction'].tolist(),
        'Consent': df['Consent'].tolist(),
        'Maybe': df['Maybe'].tolist(),
        'Delta': df['Delta'].tolist(),
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
