import os
import time
import threading
import requests
import logging
from flask import Flask, request, jsonify
from zapv2 import ZAPv2
import config  

app = Flask(__name__)

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка прокси для ZAP
zap = ZAPv2(apikey=config.apiKey, proxies={'http': config.proxy_url, 'https': config.proxy_url})

def upload_to_defectdojo(report_path, target, engagement_id):
    headers = {
        'Authorization': f'Token {config.dojo_api_key}',
    }
    
    files = {
        'file': open(report_path, 'rb'),
        'engagement': (None, engagement_id),
        'test_type': (None, config.dojo_test_type),
        'scan_date': (None, time.strftime('%Y-%m-%d')),
        'scan_type': (None, 'ZAP Scan'),
        'minimum_severity': (None, 'Low'),
        'active': (None, 'true'),
        'verified': (None, 'true'),
    }
    
    response = requests.post(f'{config.dojo_url}/import-scan/', headers=headers, files=files)
    
    if response.status_code == 201:
        logger.info('Report successfully uploaded to DefectDojo')
    else:
        logger.error('Failed to upload report to DefectDojo')
        logger.error(response.text)

def save_scan_results(scan_results, file_path):
    with open(file_path, 'w') as f:
        f.write('\n'.join(scan_results))

def save_alerts(alerts, file_path):
    with open(file_path, 'w') as f:
        f.write(str(alerts))

def perform_scan(target, scan_function, status_function, wait_time=1):
    scanID = scan_function(target)
    while int(status_function(scanID)) < 100:
        logger.info(f'Scan progress %: {status_function(scanID)}')
        time.sleep(wait_time)
    logger.info(f'Scan completed for {target}!')
    return zap.core.alerts(baseurl=target) if scan_function == zap.ascan.scan else zap.spider.results(scanID)

def scan_target(target, engagement_id):
    logger.info(f'Spidering target {target}')
    
    target_name = target.replace('https://', '').replace('http://', '').replace('/', '_')
    report_dir = os.path.join('import', 'time', target_name)
    os.makedirs(report_dir, exist_ok=True)

    spider_results = perform_scan(target, zap.spider.scan, zap.spider.status)
    save_scan_results(spider_results, os.path.join(report_dir, 'spider_results.txt'))

    logger.info(f'Active scanning target {target}')
    alerts = perform_scan(target, zap.ascan.scan, zap.ascan.status, wait_time=5)
    save_alerts(alerts, os.path.join(report_dir, 'alerts.json'))
    
    logger.info(f'Results saved in {report_dir}')
    upload_to_defectdojo(os.path.join(report_dir, 'alerts.json'), target, engagement_id)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    image = data.get('image')
    engagement_id = data.get('engagement_id')
    
    if not image or not engagement_id:
        return jsonify({'status': 'error', 'message': 'No image or engagement_id specified'}), 400

    target = f'https://{image}'
    logger.info(f'Received webhook for target: {target}')
    
    # Запуск сканирования в отдельном потоке
    threading.Thread(target=scan_target, args=(target, engagement_id)).start()
    
    return jsonify({'status': 'accepted', 'message': f'Scan started for {target}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
