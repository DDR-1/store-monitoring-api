from flask import Flask, request, jsonify, send_file, abort
from sqlalchemy import func
from models import db, StoreStatus
from config import Config
from utils import generate_report
from dataload import load_data_from_csv
from datetime import datetime
import os
import concurrent.futures
import uuid 

app = Flask(__name__)
app.config.from_object(Config)
executor = concurrent.futures.ThreadPoolExecutor()
reports_status = {}

db.init_app(app)

with app.app_context():
    db.create_all()
    load_data_from_csv()

@app.route('/')
def home():
    return 'App is loaded'

@app.route('/trigger_report')
def trigger_report():
    try:
        # current_time = datetime.now()
        current_time = db.session.query(func.max(StoreStatus.timestamp_utc)).scalar()
        report_id = uuid.uuid4().hex[:6].upper()
        future = executor.submit(generate_report, app, current_time, report_id)
        reports_status[report_id] = future
        return {"report_id" : report_id}
    except Exception as e:
        return jsonify({'error': f'Failed to generate report: {str(e)}'}), 500

@app.route('/get_report', methods=['GET'])
def get_report():
    report_id = request.args.get('report_id')
    future = reports_status.get(report_id)
    
    if not report_id:
        return jsonify({'error': 'report_id is required'}), 400
    
    if future == "Running" or not future.done():
        return jsonify({'status': 'Running'}), 200
    
    try:
        result = future.result()
        if os.path.exists(result):
            return send_file(result, as_attachment=True, download_name=f"{report_id}.csv")
        else:
            return jsonify({'error': 'Report generation failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug = True)
