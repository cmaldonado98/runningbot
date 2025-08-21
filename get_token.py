import requests
import json

# Datos para intercambiar el código por access token
data = {
    'client_id': '173735',
    'client_secret': '32c6798f5a08290ba837a67e73e41afb0893df89',
    'code': 'ef73a39e35ee142492df3bce0e35c55ea22e9417',
    'grant_type': 'authorization_code'
}

try:
    response = requests.post('https://www.strava.com/oauth/token', data=data)
    result = response.json()
    print("Respuesta de Strava:")
    print(json.dumps(result, indent=2))
    
    if 'access_token' in result:
        print(f"\n✅ ACCESS TOKEN: {result['access_token']}")
        print(f"✅ REFRESH TOKEN: {result['refresh_token']}")
        print(f"✅ EXPIRA EN: {result['expires_at']} segundos")
except Exception as e:
    print(f"Error: {e}")
