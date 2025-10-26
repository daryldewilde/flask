# Application Flask avec Authentification Google

Application Flask sécurisée permettant l'authentification via Google OAuth2. Interface entièrement en français avec gestion des sessions et stockage SQLite.

## Prérequis

- Python 3.12 ou supérieur
- OpenSSL pour les certificats SSL
- SQLite3 (inclus avec Python)

## Dépendances Principales

- Flask 3.0.0
- Flask-Login 0.6.3
- Requests 2.31.0
- python-dotenv 1.0.0
- pyOpenSSL 23.3.0
- oauthlib 3.2.2
- requests-oauthlib 1.3.1

## Configuration Initiale

1. Configuration Google OAuth2
   - Accédez à la [Console Google Cloud](https://console.cloud.google.com/)
   - Créez un projet ou sélectionnez un projet existant
   - Dans "APIs et Services" > "Identifiants"
   - Créez un ID client OAuth 2.0
   - Ajoutez `https://localhost:5000/callback` aux URIs de redirection autorisées

2. Installation de l'Environnement
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

3. Variables d'Environnement
   Créez un fichier `.env` avec :
   ```
   GOOGLE_CLIENT_ID=votre_client_id
   GOOGLE_CLIENT_SECRET=votre_client_secret
   SECRET_KEY=votre_clé_secrète
   ```

4. Certificats SSL (Développement)
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes \
     -out cert.pem \
     -keyout key.pem \
     -days 365 \
     -subj "/C=FR/ST=Paris/L=Paris/O=Development/OU=IT/CN=localhost"
   ```

## Structure du Projet
```
/flask
├── app.py              # Application principale Flask
├── database.py         # Gestion de la base de données SQLite
├── routes.py           # Routes de l'application
├── requirements.txt    # Dépendances du projet
├── users.db           # Base de données SQLite
├── cert.pem           # Certificat SSL
├── key.pem            # Clé privée SSL
└── templates/
    ├── base.html      # Template de base
    ├── error.html     # Page d'erreur
    ├── index.html     # Page d'accueil
    ├── login.html     # Page de connexion
    └── profile.html   # Page de profil
```

## Démarrage

1. Activez l'environnement virtuel :
   ```bash
   source venv/bin/activate
   ```

2. Lancez l'application :
   ```bash
   python app.py
   ```

3. Accédez à l'application :
   ```
   https://localhost:5000
   ```

## Fonctionnalités

- Authentification Google OAuth2 sécurisée
- Interface utilisateur en français
- Sélection de compte Google à chaque connexion
- Affichage du profil utilisateur (nom, email, photo)
- Stockage persistant des données utilisateur en SQLite
- Sessions sécurisées avec Flask-Login
- Certificats SSL pour HTTPS

## Architecture d'Authentification

### OAuth 2.0 avec Google
L'application utilise le protocole OAuth 2.0 pour l'authentification via Google, suivant le flux "Authorization Code" :

1. Flux d'Authentification
   ```
   [Application] -> [Google Authorization Endpoint]
   -> [Utilisateur s'authentifie]
   -> [Callback avec code]
   -> [Échange code contre tokens]
   -> [Récupération informations utilisateur]
   ```

2. Points de Terminaison Utilisés
   - Authorization Endpoint : `https://accounts.google.com/o/oauth2/v2/auth`
   - Token Endpoint : `https://oauth2.googleapis.com/token`
   - Userinfo Endpoint : `https://openidconnect.googleapis.com/v1/userinfo`

### OpenID Connect
OpenID Connect est utilisé en complément d'OAuth 2.0 pour :
- Obtenir les informations d'identité vérifiées (email, nom, photo)
- Recevoir un ID Token (JWT) de Google
- Vérifier l'authenticité des informations utilisateur

### JSON Web Tokens (JWT)
Les JWT sont utilisés dans l'ID Token de Google pour :
1. Vérification de l'Identité
   - `iss` : Confirme que le token vient de Google
   - `aud` : Vérifie que le token est destiné à notre application
   - `exp` : Contrôle la validité temporelle du token
   - `sub` : Identifiant unique de l'utilisateur

2. Informations Utilisateur
   ```json
   {
     "iss": "https://accounts.google.com",
     "sub": "user-unique-id",
     "aud": "your-client-id",
     "email": "user@example.com",
     "email_verified": true,
     "name": "User Name",
     "picture": "profile-picture-url",
     "iat": timestamp,
     "exp": timestamp
   }
   ```

### Cycle de Vie de l'Authentification
1. **Connexion Initiale**
   - Redirection vers Google avec `scope=["openid", "email", "profile"]`
   - Réception du code d'autorisation
   - Échange contre Access Token et ID Token
   - Vérification du JWT et extraction des informations

2. **Session Utilisateur**
   - Création d'une session Flask sécurisée
   - Stockage des informations utilisateur en base SQLite
   - Gestion de la session via Flask-Login

3. **Déconnexion**
   - Nettoyage de la session Flask
   - Révocation des tokens OAuth
   - Redirection vers la page de connexion

## Sécurité

- Protocole HTTPS avec certificats SSL
- Protection contre les attaques CSRF
- Vérification des tokens OAuth2 et JWT
- Sessions utilisateur sécurisées
- Stockage sécurisé des données utilisateur
- Déconnexion sécurisée avec nettoyage de session
- Vérification de l'email et de l'intégrité des tokens

## Note sur les Certificats SSL

En développement, l'application utilise des certificats auto-signés. Vous verrez un avertissement de sécurité dans votre navigateur, c'est normal. Pour le développement :

1. Accédez à https://localhost:5000
2. Cliquez sur "Avancé"
3. Cliquez sur "Continuer vers localhost"

En production, utilisez des certificats SSL valides d'une autorité de certification reconnue.