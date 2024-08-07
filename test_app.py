import unittest
from unittest.mock import patch, mock_open
from flask import Flask
from flask_testing import TestCase
import json
import logging
import io
from app import app, zap, perform_scan, upload_to_defectdojo, scan_target

class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    def setUp(self):
        self.log_stream = io.StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.logger = logging.getLogger('app')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.log_stream.close()

    @patch('app.requests.post')
    def test_upload_to_defectdojo_success(self, mock_post):
        mock_post.return_value.status_code = 201
        mock_post.return_value.text = 'Success'

        with patch('builtins.open', mock_open(read_data="data")):
            upload_to_defectdojo('path/to/report', 'http://example.com', '123')

        self.handler.flush()
        log_output = self.log_stream.getvalue()
        self.assertIn('Report successfully uploaded to DefectDojo', log_output)

    @patch('app.requests.post')
    def test_upload_to_defectdojo_failure(self, mock_post):
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = 'Failure'

        with patch('builtins.open', mock_open(read_data="data")):
            upload_to_defectdojo('path/to/report', 'http://example.com', '123')

        self.handler.flush()
        log_output = self.log_stream.getvalue()
        self.assertIn('Failed to upload report to DefectDojo', log_output)

    @patch('app.zap.spider.scan')
    @patch('app.zap.spider.status')
    def test_perform_scan(self, mock_status, mock_scan):
        mock_scan.return_value = '1'
        mock_status.return_value = '100'
        result = perform_scan('http://example.com', zap.spider.scan, zap.spider.status)
        self.assertIsInstance(result, list)

    @patch('app.scan_target')
    def test_webhook(self, mock_scan_target):
        data = {
            'image': 'example.com',
            'engagement_id': '123'
        }
        response = self.client.post('/webhook', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'accepted')
        self.assertIn('Scan started for https://example.com', response.json['message'])

    @patch('app.scan_target')
    def test_webhook_missing_data(self, mock_scan_target):
        data = {
            'image': 'example.com'
        }
        response = self.client.post('/webhook', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['status'], 'error')
        self.assertIn('No image or engagement_id specified', response.json['message'])

if __name__ == '__main__':
    unittest.main()
