import os

# Read API keys from environment variables
apiKey = os.getenv('ZAP_API_KEY','')
dojo_api_key = os.getenv('DOJO_API_KEY','')

# DefectDojo settings
dojo_url = os.getenv('DOJO_URL', '')
dojo_test_type = os.getenv('DOJO_TEST_TYPE', 'ZAP Scan')  
proxy_url = 'http://localhhost:8090' 