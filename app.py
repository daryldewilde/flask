from flask import Flask, redirect, request, url_for, render_template, session, g, flash
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
    UserMixin
)
import json
import os
import functools
from oauthlib.oauth2 import WebApplicationClient
import requests
from dotenv import load_dotenv
from database import init_db, get_user, create_user, close_db

# Charger les variables d'environnement
load_dotenv()

# Configuration SSL
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS
        )

# Créer une session avec notre adaptateur TLS
session = requests.Session()
session.mount('https://', TLSAdapter())

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"  # URL fixe pour la fiabilité

# Autoriser OAuth sur HTTP pour le développement
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration de l'Application
BASE_URL = "https://localhost:5000"  # Utiliser HTTPS pour OAuth
OAUTH_REDIRECT_PATH = "/callback"  # Le chemin pour le callback OAuth
OAUTH_REDIRECT_URI = f"{BASE_URL}{OAUTH_REDIRECT_PATH}"  # Full callback URI

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Make the current year available in templates
@app.context_processor
def inject_now():
    from datetime import datetime
    return {'now': datetime.utcnow()}

# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Create a session with timeout settings
session = requests.Session()

# Configure direct connection with timeout and retry settings
adapter = requests.adapters.HTTPAdapter(
    max_retries=3,
    pool_connections=10,
    pool_maxsize=10
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Set default timeout
session.request = functools.partial(session.request, timeout=10)

print("\033[94m[DEBUG] Utilisation d'une connexion directe (sans proxy)\033[0m")

# Test connection to Google
try:
    test_response = session.get('https://accounts.google.com', timeout=5)
    print("\033[94m[DEBUG] Connecté avec succès à Google\033[0m")
except Exception as e:
    print(f"\033[91m[ERREUR] Impossible de se connecter à Google: {str(e)}\033[0m")

# User class
class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user = get_user(user_id)
        if not user:
            return None

        return User(
            id_=user["id"],
            name=user["name"],
            email=user["email"],
            profile_pic=user["profile_pic"]
        )
        
        return User(
            id_=user['id'],
            name=user['name'],
            email=user['email'],
            profile_pic=user['profile_pic']
        )

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def get_google_provider_cfg():
    # Default configuration in case the discovery URL is unreachable
    default_config = {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo"
    }

    try:
        print("\033[94m[DEBUG] Récupération de la configuration Google depuis:", GOOGLE_DISCOVERY_URL, "\033[0m")
        # Try to get the configuration from Google
        response = session.get(
            GOOGLE_DISCOVERY_URL,
            allow_redirects=True,  # Follow redirects
            timeout=10  # Explicit timeout
        )
        response.raise_for_status()
        config = response.json()
        print("\033[94m[DEBUG] Configuration Google récupérée avec succès\033[0m")
        return config
    except requests.exceptions.SSLError:
        print("\033[91m[ERREUR] La vérification du certificat SSL a échoué. Utilisation de la configuration par défaut.\033[0m")
        return default_config
    except requests.exceptions.ConnectionError:
        print("\033[91m[ERREUR] Réseau inaccessible. Utilisation de la configuration par défaut.\033[0m")
        return default_config
    except requests.exceptions.Timeout:
        print("\033[91m[ERREUR] Délai d'attente dépassé pour Google. Utilisation de la configuration par défaut.\033[0m")
        return default_config
    except requests.exceptions.RequestException as e:
        print(f"\033[91m[ERREUR] Échec de la récupération de la configuration Google: {e}. Utilisation de la configuration par défaut.\033[0m")
        return default_config
    except Exception as e:
        print(f"\033[91m[ERREUR] Erreur inattendue: {e}. Utilisation de la configuration par défaut.\033[0m")
        return default_config

@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template(
            "index.html",
            user=current_user
        )
    return render_template("login.html")

@app.route("/profile")
@login_required
def profile():
    return render_template(
        "profile.html",
        user=current_user
    )

@app.route("/login")
def login():
    try:
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        if google_provider_cfg is None:
            return render_template(
                "error.html",
                error="Impossible de se connecter aux serveurs Google. Veuillez vérifier votre connexion internet et réessayer."
            )

        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        print("\033[94m[DEBUG] Authorization endpoint:", authorization_endpoint, "\033[0m")
        print("\033[94m[DEBUG] Redirect URI:", OAUTH_REDIRECT_URI, "\033[0m")

        # Use library to construct the request for login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=OAUTH_REDIRECT_URI,
            scope=["openid", "email", "profile"],
            prompt="select_account"  # Force account selection on login
        )
        print("\033[94m[DEBUG] Full authorization URI:", request_uri, "\033[0m")
        return redirect(request_uri)
    except Exception as e:
        print(f"\033[91m[ERROR] Login error: {str(e)}\033[0m")
        return render_template(
            "error.html",
            error="An error occurred during login. Please try again."
        )

@app.route("/callback")
def callback():
    try:
        # Get authorization code Google sent back
        code = request.args.get("code")
        if not code:
            return "Authentication failed: No code received.", 400

        print("\033[94m[DEBUG] Received code in callback\033[0m")

        # Get token endpoint
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        print("\033[94m[DEBUG] Token endpoint:", token_endpoint, "\033[0m")
        print("\033[94m[DEBUG] Auth Response URL:", request.url, "\033[0m")
        print("\033[94m[DEBUG] Redirect URI:", OAUTH_REDIRECT_URI, "\033[0m")

        # Prepare and send token request
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=OAUTH_REDIRECT_URI,
            code=code
        )
        
        print("\033[94m[DEBUG] Token request URL:", token_url, "\033[0m")
        print("\033[94m[DEBUG] Token request headers:", headers, "\033[0m")
        print("\033[94m[DEBUG] Token request body:", body, "\033[0m")

        token_response = session.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
            verify=True,
            timeout=10
        )
        
        print("\033[94m[DEBUG] Token response status:", token_response.status_code, "\033[0m")
        print("\033[94m[DEBUG] Token response:", token_response.text, "\033[0m")

        # Parse the tokens
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        
        print("\033[94m[DEBUG] Userinfo request URL:", uri, "\033[0m")
        userinfo_response = session.get(uri, headers=headers, data=body)
        
        if userinfo_response.json().get("email_verified"):
            unique_id = userinfo_response.json()["sub"]
            users_email = userinfo_response.json()["email"]
            users_name = userinfo_response.json()["name"]
            picture = userinfo_response.json()["picture"]
            
            # Create or update user
            if not create_user(unique_id, users_name, users_email, picture):
                return "Error creating user", 500
            
            # Create user instance
            user_instance = User(
                id_=unique_id,
                name=users_name,
                email=users_email,
                profile_pic=picture
            )
            
            # Begin user session
            login_user(user_instance)
            return redirect(url_for("index"))
        else:
            return "User email not available or not verified by Google.", 400

    except Exception as e:
        print(f"\033[91m[ERROR] Callback error: {str(e)}\033[0m")
        return render_template(
            "error.html",
            error="An error occurred during authentication. Please try again."
        )
        login_user(user_instance)

        return redirect(url_for("index"))
    else:
        return "User email not available or not verified by Google.", 400

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Initialisation et nettoyage de la base de données
@app.before_request
def setup_db():
    if not hasattr(g, 'db_initialized'):
        init_db()
        g.db_initialized = True

@app.teardown_appcontext
def cleanup(error):
    close_db()

if __name__ == "__main__":
    # Initialiser la base de données
    init_db()
    
    # Utiliser HTTPS avec nos certificats générés
    ssl_context = ('cert.pem', 'key.pem')
    
    # Configurer la journalisation
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('werkzeug')
    logger.setLevel(logging.INFO)
    
    # Afficher le message de démarrage
    print("\n" + "="*50)
    print("🚀 L'application Flask sécurisée démarre!")
    print("🔒 HTTPS activé avec certificat SSL")
    print("🌐 Le serveur sera disponible à: https://localhost:5000")
    print("⚠️  Comme nous utilisons un certificat auto-signé, vous pourriez voir un avertissement de sécurité dans votre navigateur.")
    print("   C'est normal en développement. Vous pouvez continuer en toute sécurité.")
    print("="*50 + "\n")
    
    try:
        # Configuration SSL pour le développement
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain('cert.pem', 'key.pem')
        
        app.run(
            host="0.0.0.0",  # Autoriser les connexions externes
            port=5000,
            debug=True,
            ssl_context=ssl_context  # Utiliser notre contexte SSL configuré
        )
    except Exception as e:
        print(f"\n❌ Erreur de démarrage du serveur: {str(e)}")
        print("💡 Assurez-vous que cert.pem et key.pem existent dans le répertoire courant")
        print("   Vous pouvez les générer en utilisant la commande:")
        print("   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj '/CN=localhost'\n")