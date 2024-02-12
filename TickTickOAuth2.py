"""This file contains the definition of the <TickTickOAuth2> class, which
manages the authentication process with the TickTick API"""

import json
import os.path
import sys
import webbrowser
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlparse

import requests
from colorama import Fore

# The two urls involved in the authentication process
OAUTH_AUTHORIZE_URL = "https://ticktick.com/oauth/authorize"
OAUTH_TOKEN_URL = "https://ticktick.com/oauth/token"


class TickTickOAuth2:
    TOKEN_FILE_PATH = "./token.json"  # Path of the file containing token info

    # Values used for the authentication parameters
    SCOPE = "tasks:write tasks:read"
    GRANT_TYPE = "authorization_code"
    RESPONSE_TYPE = "code"

    def __init__(self, client_id, client_secret, redirect_uri):
        """Stores the client credentials and makes sure
        there is a valid token for authentication"""

        # Initialisation of the attributes
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # We check whether the stored token is valid and change it if necessary
        if self.validate_stored_token():
            stored_token_info = self.retrieve_local_client_token()

            self.token = stored_token_info[0]
            self.token_expire_date = stored_token_info[1]

            print(Fore.GREEN + "Données de connexion valides\n")

        else:
            # If the token is incorrect for some reason, we refresh it
            self.get_new_token()

    @property
    def auth_header(self):
        """Returns the appropriate auth header to be sent
        with requests to TickTick's API"""

        return {"Authorization": f"Bearer {self.token}"}

    def get_new_token(self):
        """Asks TickTick API to refresh the access token"""

        # First, we need to redirect the user to TickTick's web page
        authorize_payload = {
            "client_id": self.client_id,
            "scope": TickTickOAuth2.SCOPE,
            "response_type": TickTickOAuth2.RESPONSE_TYPE,
            "redirect_url": self.redirect_uri,
            "state": None,
        }

        webbrowser.open(
            f"{OAUTH_AUTHORIZE_URL}?{urlencode(authorize_payload)}"
        )  # Opens the tab in the browser

        # We get the code from the URL where the user has been redirected
        redirected_url = input("Veuillez entrer l'URL où vous avez été redirigé(e) : ")
        url_params = dict(parse_qsl(urlparse(redirected_url).query))

        # Finally, we request the new access token
        access_token_request_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": url_params["code"],
            "grant_type": TickTickOAuth2.GRANT_TYPE,
            "scope": TickTickOAuth2.SCOPE,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(OAUTH_TOKEN_URL, data=access_token_request_data)

        # We check if the request failed
        if response.status_code != requests.codes.ok:
            print(Fore.RED + "Erreur fatale : impossible de s'authentifier")
            sys.exit(1)

        # If everything went good, we can update the token
        token_info = response.json()

        self.token = token_info["access_token"]
        self.token_expire_date = (
            int(datetime.now().timestamp()) + token_info["expires_in"]
        )

        self.refresh_stored_token()
        print(Fore.GREEN + "Token récupéré avec succès\n")

    def refresh_stored_token(self):
        """Saves the current access token into the local storage file"""
        token_file_data = self.retrieve_token_file_data()

        # If the file did not exist, we start from an empty dict
        if token_file_data is None:
            token_file_data = {}

        token_file_data[self.client_id] = {
            "access_token": self.token,
            "expire_date": self.token_expire_date,
        }

        # Here we effectively change the file (it is created if it was missing)
        with open(TickTickOAuth2.TOKEN_FILE_PATH, "w", encoding="utf8") as file:
            json.dump(token_file_data, file, ensure_ascii=False)

    def validate_stored_token(self):
        """Checks wether there exists a valid access token or not"""

        stored_token_info = self.retrieve_token_file_data()

        # Checks wether the token exists
        if stored_token_info is not None:
            expire_date = datetime.fromtimestamp(
                stored_token_info[self.client_id]["expire_date"]
            )

            # Checks whether the token is expired
            if datetime.today() < expire_date:
                return True

            else:
                print(Fore.RED + "Token périmé")
                return False

        else:
            print(Fore.RED + "Fichier de token invalide")
            return False

    def retrieve_local_client_token(self):
        """Retrieves the token associated with the
        client from the local storage file"""

        token_file_info = self.retrieve_token_file_data()

        if (
            (token_file_info is not None)
            and (self.client_id in token_file_info)
            and all(
                key in token_file_info[self.client_id]
                for key in ("access_token", "expire_date")
            )
        ):
            return (
                token_file_info[self.client_id]["access_token"],
                token_file_info[self.client_id]["expire_date"],
            )

        else:
            return None

    @staticmethod
    def retrieve_token_file_data():
        """Retrieves the content of the token file"""

        # We check wether the file exists
        if os.path.isfile(TickTickOAuth2.TOKEN_FILE_PATH):
            with open(TickTickOAuth2.TOKEN_FILE_PATH, encoding="utf8") as file:
                try:
                    return json.load(file)

                except json.JSONDecodeError:
                    return None

        else:
            return None
