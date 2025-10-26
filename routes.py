# Routes with proper error handling and debugging
@app.route("/login")
def login():
    try:
        # Find out what URL to hit for Google login
        google_provider_cfg = get_google_provider_cfg()
        if google_provider_cfg is None:
            return render_template(
                "error.html",
                error="Cannot connect to Google servers. Please check your internet connection and try again."
            )

        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        print("\033[94m[DEBUG] Authorization endpoint:", authorization_endpoint, "\033[0m")
        print("\033[94m[DEBUG] Redirect URI:", OAUTH_REDIRECT_URI, "\033[0m")

        # Use library to construct the request for login
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=OAUTH_REDIRECT_URI,
            scope=["openid", "email", "profile"],
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
            user = User(
                id_=unique_id,
                name=users_name,
                email=users_email,
                profile_pic=picture
            )
            
            # Begin user session
            login_user(user)
            return redirect(url_for("index"))
        else:
            return "User email not available or not verified by Google.", 400

    except Exception as e:
        print(f"\033[91m[ERROR] Callback error: {str(e)}\033[0m")
        return render_template(
            "error.html",
            error="An error occurred during authentication. Please try again."
        )