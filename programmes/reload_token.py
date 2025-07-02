import os, json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.auth.transport.requests
import pickle

# CONSTANTES
with open("../outis/constantes.json", "r", encoding="utf-8") as f:
    constantes = json.load(f)
    YT_NAME_FILE = constantes["YT_NAME_FILE"]
    SCOPES = constantes["SCOPES"]

def get_authenticated_service(file_client_secret, file_token):
    creds = None

    # Charger les credentials existants s'ils existent
    if os.path.exists(file_token):
        with open(file_token, "rb") as token:
            creds = pickle.load(token)

    # Si les creds n'existent pas ou ne sont pas valides
    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
            else:
                # Authentification via navigateur
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(file_client_secret, SCOPES)
                creds = flow.run_local_server(port=0)

            # Sauvegarde ou remplacement du token
            with open(file_token, "wb") as token:
                pickle.dump(creds, token)

        except Exception as e:
            raise Exception(f"Erreur d'authentification pour {file_token} : {e}")

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def main():
    print("****************************************")

    # On supr les .pickle
    print("Supression de tous les .pickle :")
    for file in YT_NAME_FILE:
        file_path = f"../outis/youtubeAPI/{file}.pickle"
        if os.path.exists(file_path):
            print(f" - Supression de : {file}.pickle")
            os.remove(file_path)

    # Puis on les recréer
    print("Création de tous les .pickle")
    for file in YT_NAME_FILE:
        file_path = f"../outis/youtubeAPI/{file}"
        try:
            print(f" - Tentative avec {file}.pickle")
            get_authenticated_service(f"{file_path}.json", f"{file_path}.pickle")
        except Exception as e:
            print(f"Erreur avec le fichier {file} : {e}")

    print("Tous les tokens on été créer !")

if __name__ == "__main__":
    main()