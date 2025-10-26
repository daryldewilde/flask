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

## Sécurité

- Protocole HTTPS avec certificats SSL
- Protection contre les attaques CSRF
- Vérification des tokens OAuth2
- Sessions utilisateur sécurisées
- Stockage sécurisé des données utilisateur
- Déconnexion sécurisée avec nettoyage de session

## Note sur les Certificats SSL

En développement, l'application utilise des certificats auto-signés. Vous verrez un avertissement de sécurité dans votre navigateur, c'est normal. Pour le développement :

1. Accédez à https://localhost:5000
2. Cliquez sur "Avancé"
3. Cliquez sur "Continuer vers localhost"

En production, utilisez des certificats SSL valides d'une autorité de certification reconnue.