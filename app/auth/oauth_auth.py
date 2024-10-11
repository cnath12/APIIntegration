from flask import jsonify, current_app, url_for
from authlib.integrations.flask_client import OAuth
from .jwt_auth import create_access_token

class OAuthAuth:
    def __init__(self, app):
        self.oauth = OAuth(app)
        self.github = self.oauth.register(
            name='github',
            client_id=app.config['GITHUB_CLIENT_ID'],
            client_secret=app.config['GITHUB_CLIENT_SECRET'],
            access_token_url='https://github.com/login/oauth/access_token',
            access_token_params=None,
            authorize_url='https://github.com/login/oauth/authorize',
            authorize_params=None,
            api_base_url='https://api.github.com/',
            client_kwargs={'scope': 'user:email'},
        )

    def oauth_login(self):
        redirect_uri = url_for('auth.github_callback', _external=True)
        return self.github.authorize_redirect(redirect_uri)

    def oauth_callback(self):
        try:
            token = self.github.authorize_access_token()
            resp = self.github.get('user', token=token)
            github_user = resp.json()
            
            # Use the GitHub username as the identity for the JWT
            access_token = create_access_token(identity=github_user['login'])
            
            return jsonify(
                message="Successfully authenticated with GitHub",
                github_username=github_user['login'],
                access_token=access_token
            ), 200
        except Exception as e:
            current_app.logger.error(f"OAuth callback error: {str(e)}")
            return jsonify(error="Authentication failed"), 400