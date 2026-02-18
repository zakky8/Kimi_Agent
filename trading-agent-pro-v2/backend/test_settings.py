import requests
try:
    response = requests.get('http://localhost:8000/api/v1/settings/current')
    print(response.status_code)
    print(response.json().get('openrouter_api_key'))
except Exception as e:
    print(e)
