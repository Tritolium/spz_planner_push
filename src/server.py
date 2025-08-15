from flask import Flask, jsonify
from predict import run_prediction

app = Flask(__name__)

@app.route('/prediction/<event_id>')
def prediction(event_id):
    df = run_prediction(event_id)
    if df is None or df.empty:
        return jsonify({'error': 'prediction failed'}), 404
    return jsonify({'columns': df.columns.tolist(), 'rows': len(df)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
