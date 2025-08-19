import os
import secrets
import requests
from urllib.parse import urlencode

class LinkedInOAuthService:
    def __init__(self):
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:3000/linkedin/callback')
        self.auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
        self.token_url = 'https://www.linkedin.com/oauth/v2/accessToken'

    def get_authorization_url(self, state: str = None) -> str:
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': 'openid email profile w_member_social'
        }

        url = f"{self.auth_url}?{urlencode(params)}"
        print(f"DEBUG: LinkedIn auth URL = {url}")
        return url

    def exchange_code_for_token(self, authorization_code: str) -> dict:
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        print(f"DEBUG: Token exchange request data: {data}")
        print(f"DEBUG: Redirect URI: {self.redirect_uri}")

        try:
            response = requests.post(self.token_url, data=data, headers=headers)
            print(f"DEBUG: LinkedIn response status: {response.status_code}")
            print(f"DEBUG: LinkedIn response: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"DEBUG: Token exchange failed: {str(e)}")
            return {'error': f'Token exchange failed: {str(e)}'}

    def get_linkedin_profile(self, access_token: str) -> dict:
        """Fetch LinkedIn user profile using new /userinfo endpoint"""
        url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            print(f"DEBUG: Calling LinkedIn userinfo API: {url}")
            response = requests.get(url, headers=headers)
            print(f"DEBUG: Profile API response: {response.status_code}")
            print(f"DEBUG: Profile API response body: {response.text[:200]}...")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"DEBUG: Profile API failed: {str(e)}")
            return {'error': f'Failed to fetch profile: {str(e)}'}

