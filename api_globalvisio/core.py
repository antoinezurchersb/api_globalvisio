import pandas as pd
import requests
import json
import pytz
from datetime import datetime, timedelta

token_info = {
    'token': None,
    'expiration': None
}


class Credentials:
    def __init__(self):
        self.identifiant = None
        self.password = None
        self.remaining_day_requests = None
        self.api_key = None

    def set_credentials(self, identifiant, password):
        self.identifiant = identifiant
        self.password = password

    def set_api_key(self, api_key):
        self.api_key = api_key


credentials = Credentials()


def check_user_exists():
    """
    Envoie une requête POST pour obtenir un token d'authentification.
    Gère les erreurs de requête et vérifie l'expiration du token.
    """

    url = 'https://global-visio.com/api/auth/token'
    payload = json.dumps({
        'username': credentials.identifiant,
        'password': credentials.password
    })
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            error_message = f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {response.json()['message']}"
            print(error_message)
            return False, error_message
        response.raise_for_status()  # Gère les autres ERREURs HTTP

        return True, ""

    except requests.RequestException as e:
        error_message = f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {e}"
        print(error_message)
        return False, error_message


def get_token():
    """
    Envoie une requête POST pour obtenir un token d'authentification.
    Gère les erreurs de requête et vérifie l'expiration du token.
    """
    
    paris_timezone = pytz.timezone("Europe/Paris")
    current_time = datetime.now(paris_timezone)

    # Vérifier si le token actuel est toujours valide
    if token_info['token'] and token_info['expiration'] > current_time:
        return token_info['token']

    url = 'https://global-visio.com/api/auth/token'
    payload = json.dumps({
        'username': credentials.identifiant,
        'password': credentials.password
    })
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()  # Gère les autres ERREURs HTTP
        token_info['token'] = response.json()['response']['token']
        token_info['expiration'] = datetime.fromisoformat(response.json()['response']['expiration'])

        return token_info['token']
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {e}")
        return None


def get_all_sites():
    """
    Récupère tous les sites via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/sites/index?page=0&perPage=100"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['sites']:
            data = pd.DataFrame(response.json()['response']['sites'])

            if len(data):
                return data
            else:
                print(f"ERREUR lors de la requête de tous les sites car aucun site n'est trouvable.")
                return None
        else:
            print(
                f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


def get_site_id_from_char(char):
    """
    Récupère le site dont le nom contient les caractères spécifiés via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/sites/index?page=0&perPage=100"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['sites']:
            data = pd.DataFrame(response.json()['response']['sites'])

            # Utilisation d'une compréhension de liste pour vérifier la présence de tous les mots
            # dans la colonne 'nom' pour chaque ligne
            condition = data['nom'].apply(lambda x: all(word.lower() in x.lower() for word in char))

            if condition.sum() > 1:
                print(f"ERREUR lors de la requête du site car plusieurs sites possèdent ces caractères: {char}")
                return None
            elif condition.sum() == 1:
                site_id = data[condition]['id'].astype(int).iloc[0]
                return site_id
            else:
                print(f"ERREUR lors de la requête du site car aucun site ne possède ces caractères: {char}")
                return None

        else:
            print(
                f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête des sites avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


class Site:
    """
    Classe pour interagir avec un site de l'API de GlobalVisio.
    """

    def __init__(self, site_id):
        """
        Initialisation de la classe avec les informations du site.
        """
        self.id = site_id
        self.nom = None
        self.adresse = None
        self.adresse2 = None
        self.code_postal = None
        self.ville = None
        self.pays = None
        self.start = None

        self.get_site_attributes()

    def get_site_attributes(self):
        """
        Récupère les attributs d'un site spécifié via une requête GET.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        

        url = f"https://global-visio.com/api/sites/index/{self.id}"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {credentials.api_key}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
            if 'X-RateLimit-Remaining' in response.headers:
                credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
            if response.status_code != 200:
                print(
                    f"ERREUR lors de la requête d'attributs du site {self.id} avec l'API de GlobalVisio: {response.json()['message']}")
                return None
            response.raise_for_status()

            if response.json()['response']['site']:

                self.nom = response.json()['response']['site']['nom']
                self.adresse = response.json()['response']['site']['adresse']
                self.adresse2 = response.json()['response']['site']['adresse2']
                self.code_postal = response.json()['response']['site']['codePostal']
                self.ville = response.json()['response']['site']['ville']
                self.pays = response.json()['response']['site']['pays']
                self.start = response.json()['response']['site']['start']
            else:
                print(
                    f"ERREUR lors de la requête d'attributs du site {self.id} avec l'API de GlobalVisio: données inexistantes")
                return None
        except requests.RequestException as e:
            print(f"ERREUR lors de la requête d'attributs du site {self.id} avec l'API de GlobalVisio: {e}")
            return None
        except json.JSONDecodeError:
            print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
            return None
        except KeyError:
            print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
            return None


class Equipement:
    """
    Classe pour interagir avec un équipement de l'API de GlobalVisio.
    """

    def __init__(self, device_id):
        """
        Initialisation de la classe avec les informations du site.
        """
        self.id = device_id
        self.site_id = None
        self.mnemonique = None
        self.nom = None
        self.installation_debut = None
        self.installation_fin = None
        self.derniere_connexion = None
        self.frequence_communication = None
        self.df_points = None

        self.get_device_attributes()

    def get_device_attributes(self):
        """
        Récupère les attributs d'un site spécifié via une requête GET.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        

        url = f"https://global-visio.com/api/devices/index/{self.id}"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {credentials.api_key}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
            if 'X-RateLimit-Remaining' in response.headers:
                credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
            if response.status_code != 200:
                print(
                    f"ERREUR lors de la requête d'attributs de l'équipement {self.id} avec l'API de GlobalVisio: {response.json()['message']}")
                return None
            response.raise_for_status()

            if response.json()['response']['device']:
                self.site_id = response.json()['response']['device']['site']['id']
                self.mnemonique = response.json()['response']['device']['mnemonique']
                self.nom = response.json()['response']['device']['nom']
                self.installation_debut = response.json()['response']['device']['installationDebut']
                self.installation_fin = response.json()['response']['device']['installationFin']
                self.derniere_connexion = response.json()['response']['device']['derniereConnexion']
                self.frequence_communication = response.json()['response']['device']['frequenceCommunication']
                self.df_points = pd.DataFrame(response.json()['response']['device']['points'])
            else:
                print(
                    f"ERREUR lors de la requête d'attributs de l'équipement {self.id} avec l'API de GlobalVisio: données inexistantes")
                return None
        except requests.RequestException as e:
            print(f"ERREUR lors de la requête d'attributs de l'équipement {self.id} avec l'API de GlobalVisio: {e}")
            return None
        except json.JSONDecodeError:
            print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
            return None
        except KeyError:
            print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
            return None


class Point:
    """
    Classe pour interagir avec un point de l'API de GlobalVisio.
    """

    def __init__(self, point_id):
        """
        Initialisation de la classe avec les informations du site.
        """
        self.id = point_id
        self.device_id = None
        self.site_id = None
        self.label_automate = None
        self.label_humain = None
        self.last_value = None
        self.last_value_date = None
        self.type = None
        self.subtype = None
        self.unit = None

    def get_point_attributes(self):
        """
        Récupère les attributs d'un site spécifié via une requête GET.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        

        url = f"https://global-visio.com/api/points/index/{self.id}"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {credentials.api_key}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
            if 'X-RateLimit-Remaining' in response.headers:
                credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
            if response.status_code != 200:
                print(
                    f"ERREUR lors de la requête d'attributs du point {self.id} avec l'API de GlobalVisio: {response.json()['message']}")
                return None
            response.raise_for_status()

            if response.json()['response']['point']:
                self.device_id = response.json()['response']['point']['device']['id']
                self.site_id = response.json()['response']['point']['device']['site']['id']
                if response.json()['response']['point']['labelAutomate']:
                    self.label_automate = response.json()['response']['point']['labelAutomate']
                if response.json()['response']['point']['labelHumain']:
                    self.label_humain = response.json()['response']['point']['labelHumain']
                if response.json()['response']['point']['lastValue']:
                    self.last_value = response.json()['response']['point']['lastValue']
                if response.json()['response']['point']['lastValueDate']:
                    self.last_value_date = response.json()['response']['point']['lastValueDate']
                if response.json()['response']['point']['type']:
                    self.type = response.json()['response']['point']['type']['nom']
                if response.json()['response']['point']['subtype']:
                    self.subtype = response.json()['response']['point']['subtype']['nom']
                if response.json()['response']['point']['unit']:
                    self.unit = response.json()['response']['point']['unit']['symbole']
            else:
                print(
                    f"ERREUR lors de la requête d'attributs du point {self.id} avec l'API de GlobalVisio: données inexistantes")
                return None
        except requests.RequestException as e:
            print(f"ERREUR lors de la requête d'attributs du point {self.id} avec l'API de GlobalVisio: {e}")
            return None
        except json.JSONDecodeError:
            print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
            return None
        except KeyError:
            print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
            return None

    def get_history(self, start, end):
        """
        Récupère l'historique horaire en kWh d'un point via des requêtes GET.
        Gère les périodes de plus de 3 mois en divisant la requête en plusieurs sous-requêtes.
        Dates au format 'yyyy-mm-dd'.
        """
        

        # Convertir les chaînes de dates en objets datetime
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
        max_diff = timedelta(days=88)  # 3 mois maximum
        data_frames = []  # Pour stocker les résultats de chaque sous-requête

        while start_date < end_date:
            # Calculer la fin de la période de sous-requête
            sub_end_date = min(start_date + max_diff, end_date)
            # Formater les dates pour l'URL
            sub_start = start_date.strftime('%Y-%m-%d')
            sub_end = sub_end_date.strftime('%Y-%m-%d')

            url = f'https://global-visio.com/api/points/history/{self.id}?dateStart={sub_start}&dateEnd={sub_end}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {credentials.api_key}'
            }

            try:
                response = requests.get(url, headers=headers)
                if 'X-RateLimit-Remaining' in response.headers:
                    credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
                if response.status_code != 200:
                    print(
                        f"ERREUR lors de la requête d'historique avec l'API de GlobalVisio: {response.json()['message']}")
                    return None
                response.raise_for_status()

                # Traitement et stockage des données reçues
                if response.json()['response']['history']:
                    sub_data = pd.DataFrame(response.json()['response']['history'])
                    sub_data = sub_data[['date', 'value']]
                    sub_data['date'] = pd.to_datetime(sub_data['date'], utc=True)
                    # sub_data = sub_data[sub_data['date'].dt.second == 0]
                    sub_data = sub_data.sort_values(by=['date', 'value'], ascending=[True, True])
                    sub_data['date'] = sub_data['date'].dt.tz_convert('Europe/Paris')
                    sub_data.drop_duplicates(subset='date', keep='first', inplace=True)
                    sub_data.set_index('date', inplace=True)
                    # sub_data['unit'] = response.json()['response']['point']['unit']['symbole']
                    data_frames.append(sub_data)
                else:
                    print(
                        f"ERREUR lors de la requête d'historique avec l'API de GlobalVisio: données inexistantes pour le point {self.id} entre {sub_start} et {sub_end}")

            except requests.RequestException as e:
                print(f"ERREUR lors de la requête d'historique avec l'API de GlobalVisio: {e}")
                return None
            except json.JSONDecodeError:
                print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
                return None
            except KeyError:
                print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
                return None

            # Préparer la date de début pour la prochaine sous-requête
            start_date = sub_end_date + timedelta(days=1)

        # Fusionner les résultats de toutes les sous-requêtes
        if data_frames:
            df_concat = pd.concat(data_frames)
            # df_concat = df_concat[df_concat['value'] != 0.0]
            # Si les valeurs sont un index
            if df_concat['value'].is_monotonic_increasing:
                df_concat = df_concat[(df_concat.index.minute == 0) & (df_concat.index.second == 0)]
                df_concat['value'] = df_concat.iloc[:, 0].diff()
                if not df_concat.empty:
                    df_concat.iloc[0, 0] = 0.0
            # Si les valeurs sont des consommations horaires ou moins
            else:
                # unit = df_concat.iloc[0, 1]
                df_concat = df_concat['value'].resample('h').mean().to_frame()
                # df_concat['unit'] = unit

            return df_concat
        else:
            return None

    def get_consumption_day(self, start, end):
        """
        Récupère l'historique journalier en kWh d'un point via des requêtes GET.
        Gère les périodes de plus de 1 an en divisant la requête en plusieurs sous-requêtes.
        Dates au format 'yyyy-mm-dd'.
        """
        

        # Convertir les chaînes de dates en objets datetime
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
        max_diff = timedelta(days=364)  # 1 an maximum
        data_frames = []  # Pour stocker les résultats de chaque sous-requête

        while start_date < end_date:
            # Calculer la fin de la période de sous-requête
            sub_end_date = min(start_date + max_diff, end_date)
            # Formater les dates pour l'URL
            sub_start = start_date.strftime('%Y-%m-%d')
            sub_end = sub_end_date.strftime('%Y-%m-%d')

            url = f'https://global-visio.com/api/points/consumption/{self.id}?dateStart={sub_start}&dateEnd={sub_end}&period=2'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {credentials.api_key}'
            }

            try:
                response = requests.get(url, headers=headers)
                if 'X-RateLimit-Remaining' in response.headers:
                    credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
                if response.status_code != 200:
                    print(
                        f"ERREUR lors de la requête de consommation journalière avec l'API de GlobalVisio: {response.json()['message']}")
                    return None
                response.raise_for_status()

                # Traitement et stockage des données reçues
                if response.json()['response']['consumption']:
                    sub_data = pd.DataFrame(response.json()['response']['consumption'])
                    sub_data = sub_data[['date', 'value']]
                    # sub_data['unit'] = response.json()['response']['point']['unit']['symbole']
                    sub_data['date'] = pd.to_datetime(sub_data['date'], utc=True)
                    sub_data['date'] = sub_data['date'].dt.tz_convert('Europe/Paris')
                    sub_data.drop_duplicates(subset='date', keep='first', inplace=True)
                    sub_data.set_index('date', inplace=True)
                    data_frames.append(sub_data)
                else:
                    print(
                        f"ERREUR lors de la requête de consommation journalière avec l'API de GlobalVisio: données inexistantes pour le point {self.id} entre {sub_start} et {sub_end}")

            except requests.RequestException as e:
                print(f"ERREUR lors de la requête de consommation journalière avec l'API de GlobalVisio: {e}")
                return None
            except json.JSONDecodeError:
                print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
                return None
            except KeyError:
                print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
                return None

            # Préparer la date de début pour la prochaine sous-requête
            start_date = sub_end_date + timedelta(days=1)

        # Fusionner les résultats de toutes les sous-requêtes
        if data_frames:
            df_concat = pd.concat(data_frames)
            return df_concat
        else:
            return None

    def save_history(self, data):
        """
        Enregistre l'historique d'un point virtuel dont le nom contient 'API' via des requêtes POST.
        La fonction itère sur chaque ligne du dataframe `data` pour envoyer les valeurs historiques
        avec les dates correspondantes.
        """
        if ' API'.lower() in self.label_automate.lower() or ' API'.lower() in self.label_humain.lower():

            url = f"https://global-visio.com/api/points/saveConsumption/{self.id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {credentials.api_key}'
            }

            # data['value'].replace(0, 0.0000000001, inplace=True)

            data_list = []  # Liste pour stocker les dictionnaires avant la conversion en JSON

            for index, row in data.iterrows():
                # Création du dictionnaire pour chaque ligne et ajout à la liste
                data_list.append({
                    "datetime": index.strftime('%Y-%m-%d %H:%M:%S'),  # Formatage de l'index datetime
                    "value": row['value']  # Utilisation de la valeur de la colonne 'value'
                })

            # Création de la charge utile JSON après la boucle
            payload = json.dumps({
                "modeSave": "history",
                "data": data_list
            })

            try:
                response = requests.request("POST", url, headers=headers, data=payload)
                if 'X-RateLimit-Remaining' in response.headers:
                    credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
                if response.status_code != 200:
                    print(
                        f"ERREUR lors de la requête d'enregistrement de données sur le point {self.id} avec "
                        f"l'API de GlobalVisio: {response.json().get('message', '')}")
                response.raise_for_status()

            except requests.RequestException as e:
                print(f"ERREUR lors de la requête d'enregistrement de données sur le point {self.id} avec "
                      f"l'API de GlobalVisio: {e}")
            except json.JSONDecodeError:
                print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
            except KeyError:
                print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        else:
            print(f'ERREUR: vous essayez de modifier la valeur d\'un point de l\'équipement non dédié '
                  f'à l\'API: {self.label_humain}')
            return None


def get_device_id_from_char(site_id, char):
    """
    Récupère la liste d'équipements dont le nom contient les caractères spécifiés via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/devices/listBySite/{site_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['devices']:
            data = pd.DataFrame(response.json()['response']['devices'])

            # Utilisation d'une compréhension de liste pour vérifier la présence de tous les mots
            # dans la colonne 'labelHumain' pour chaque ligne
            condition = data['nom'].apply(lambda x: all(word.lower() in x.lower() for word in char))
            if condition.sum():
                devices_id_list = sorted(data[condition]['id'].astype(int).to_list())
                return devices_id_list
            else:
                print(
                    f"ERREUR lors de la requête d'équipements du site {site_id} car aucun ne possède ces caractères: {char}")
                return None
        else:
            print(
                f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


def get_all_devices(site_id):
    """
    Récupère la liste d'équipements dont le nom contient les caractères spécifiés via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/devices/listBySite/{site_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['devices']:
            data = pd.DataFrame(response.json()['response']['devices'])

            if len(data):
                return data
            else:
                print(
                    f"ERREUR lors de la requête d'équipements du site {site_id} car aucun n'est trouvable.'")
                return None
        else:
            print(
                f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête d'équipements du site {site_id} avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


def get_points_id_from_char(device_id, char):
    """
    Récupère la liste de points dont le nom contient les caractères spécifiés via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/devices/index/{device_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['device']:
            data = pd.DataFrame(response.json()['response']['device']['points'])

            # Utilisation d'une compréhension de liste pour vérifier la présence de tous les mots
            # dans la colonne 'labelHumain' pour chaque ligne
            condition = data['labelHumain'].apply(lambda x: all(word.lower() in x.lower() for word in char))

            points_id_list = sorted(data[condition]['id'].astype(int).to_list())

            return points_id_list
        else:
            print(
                f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


def get_all_points(device_id):
    """
    Récupère la liste de points dont le nom contient les caractères spécifiés via une requête GET.
    char est une liste de mots.
    Gère les erreurs 404 et d'autres erreurs potentielles.
    """
    

    url = f"https://global-visio.com/api/devices/index/{device_id}"
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {credentials.api_key}'
    }

    try:
        response = requests.get(url, headers=headers, data=payload)
        if 'X-RateLimit-Remaining' in response.headers:
            credentials.remaining_day_requests = response.headers['X-RateLimit-Remaining']
        if response.status_code != 200:
            print(
                f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: {response.json()['message']}")
            return None
        response.raise_for_status()

        if response.json()['response']['device']:
            data = pd.DataFrame(response.json()['response']['device']['points'])

            if len(data):
                return data
            else:
                print(
                    f"ERREUR lors de la requête des points l'équipement {device_id} car aucun n'est trouvable.'")
                return None

        else:
            print(
                f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: données inexistantes")
            return None
    except requests.RequestException as e:
        print(f"ERREUR lors de la requête de points de l'équipement {device_id} avec l'API de GlobalVisio: {e}")
        return None
    except json.JSONDecodeError:
        print('ERREUR de décodage JSON. Vérifiez le format de la réponse.')
        return None
    except KeyError:
        print('ERREUR dans la structure de données reçue. Vérifiez le format des données.')
        return None


def get_all_points_from_site(site_id):
    data_devices = get_all_devices(site_id)

    if data_devices is not None:

        list_devices_id = data_devices['id'].tolist()

        # Initialiser une liste vide pour stocker tous les DataFrame de chaque appareil
        all_data_points = []

        for device_id in list_devices_id:
            data_points = get_all_points(device_id)
            # Ajouter le DataFrame à la liste
            all_data_points.append(data_points)

        # Concaténer tous les DataFrame dans un seul DataFrame
        combined_data_points = pd.concat(all_data_points, ignore_index=True)

        return combined_data_points

    else:
        return None




