import pandas as pd
import requests
import json
import pytz
from datetime import datetime, timedelta


class GlobalVisioAPI:
    """-
    Classe pour interagir avec l'API de GlobalVisio.
    Elle permet d'obtenir un token d'authentification, de récupérer l'historique des points,
    et de rechercher des points en fonction de caractères spécifiques.
    """

    def __init__(self):
        """
        Initialisation de la classe avec les informations du token.
        """
        self.token_info = {
            'token': None,
            'expiration': None
        }

    def get_token(self):
        """
        Envoie une requête POST pour obtenir un token d'authentification.
        Gère les erreurs de requête et vérifie l'expiration du token.
        """
        paris_timezone = pytz.timezone("Europe/Paris")
        current_time = datetime.now(paris_timezone)

        # Vérifier si le token actuel est toujours valide
        if self.token_info['token'] and self.token_info['expiration'] > current_time:
            return self.token_info['token']

        url = 'https://global-visio.com/api/auth/token'
        payload = json.dumps({
            'username': 'a.zurcher',
            'password': 'aeY2dT_U3BG-VJF'
        })
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code != 200:
                print(
                    f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {response.json()['message']}")
                return None
            response.raise_for_status()  # Gère les autres ERREURs HTTP
            self.token_info['token'] = response.json()['response']['token']
            self.token_info['expiration'] = datetime.fromisoformat(response.json()['response']['expiration'])

            return self.token_info['token']
        except requests.RequestException as e:
            print(f"ERREUR lors de la requête d'authentification avec l'API de GlobalVisio: {e}")
            return None

    def get_history(self, point_id, start, end):
        """
        Récupère l'historique horaire en kWh d'un point via des requêtes GET.
        Gère les périodes de plus de 3 mois en divisant la requête en plusieurs sous-requêtes.
        Dates au format 'yyyy-mm-dd'.
        """
        self.get_token()
        if self.token_info['token'] is None:
            return None

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

            url = f'https://global-visio.com/api/points/history/{point_id}?dateStart={sub_start}&dateEnd={sub_end}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token_info["token"]}'
            }

            try:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"ERREUR lors de la requête d'historique avec l'API de GlobalVisio: {response.json()['message']}")
                    return None
                response.raise_for_status()

                # Traitement et stockage des données reçues
                if response.json()['response']['history']:
                    sub_data = pd.DataFrame(response.json()['response']['history'])
                    sub_data = sub_data[['date', 'value']]
                    sub_data['date'] = pd.to_datetime(sub_data['date'], utc=True)
                    sub_data = sub_data[sub_data['date'].dt.second == 0]
                    sub_data = sub_data.sort_values(by=['date', 'value'], ascending=[True, True])
                    sub_data['date'] = sub_data['date'].dt.tz_convert('Europe/Paris')
                    sub_data.drop_duplicates(subset='date', keep='first', inplace=True)
                    sub_data.set_index('date', inplace=True)
                    sub_data['unit'] = response.json()['response']['point']['unit']['symbole']
                    data_frames.append(sub_data)
                else:
                    print(f"ERREUR lors de la requête d'historique avec l'API de GlobalVisio: données inexistantes pour le point {point_id} entre {sub_start} et {sub_end}")

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
            df_concat = df_concat[df_concat['value'] != 0.0]
            # Si les valeurs sont un index
            if df_concat['value'].is_monotonic_increasing:
                df_concat = df_concat[(df_concat.index.minute == 0) & (df_concat.index.second == 0)]
                df_concat['value'] = df_concat.iloc[:, 0].diff()
                df_concat.iloc[0, 0] = 0.0
            # Si les valeurs sont des consommations horaires ou moins
            else:
                unit = df_concat.iloc[0, 1]
                df_concat = df_concat['value'].resample('h').mean()
                df_concat['unit'] = unit

            return df_concat
        else:
            return None

    def get_consumption_day(self, point_id, start, end):
        """
        Récupère l'historique journalier en kWh d'un point via des requêtes GET.
        Gère les périodes de plus de 1 an en divisant la requête en plusieurs sous-requêtes.
        Dates au format 'yyyy-mm-dd'.
        """
        self.get_token()
        if self.token_info['token'] is None:
            return None

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

            url = f'https://global-visio.com/api/points/consumption/{point_id}?dateStart={sub_start}&dateEnd={sub_end}&period=2'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.token_info["token"]}'
            }

            try:
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"ERREUR lors de la requête de consommation journalière avec l'API de GlobalVisio: {response.json()['message']}")
                    return None
                response.raise_for_status()

                # Traitement et stockage des données reçues
                if response.json()['response']['history']:
                    sub_data = pd.DataFrame(response.json()['response']['history'])
                    sub_data = sub_data[['date', 'value']]
                    sub_data['unit'] = response.json()['response']['point']['unit']['symbole']
                    sub_data['date'] = pd.to_datetime(sub_data['date'], utc=True)
                    sub_data['date'] = sub_data['date'].dt.tz_convert('Europe/Paris')
                    sub_data.drop_duplicates(subset='date', keep='first', inplace=True)
                    sub_data.set_index('date', inplace=True)
                    data_frames.append(sub_data)
                else:
                    print(f"ERREUR lors de la requête de consommation journalière avec l'API de GlobalVisio: données inexistantes pour le point {point_id} entre {sub_start} et {sub_end}")

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
            df_concat['value'] = df_concat.iloc[:, 0].diff()
            df_concat.iloc[0, 0] = 0.0
            return df_concat
        else:
            return None

    def get_site_id_from_char(self, char):
        """
        Récupère le site dont le nom contient les caractères spécifiés via une requête GET.
        char est une liste de mots.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        self.get_token()
        if self.token_info['token'] is None:
            return None

        url = f"https://global-visio.com/api/sites/index?page=0&perPage=100"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token_info["token"]}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
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

    def get_device_id_from_char(self, site_id, char):
        """
        Récupère la liste d'équipements dont le nom contient les caractères spécifiés via une requête GET.
        char est une liste de mots.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        self.get_token()
        if self.token_info['token'] is None:
            return None

        url = f"https://global-visio.com/api/devices/listBySite/{site_id}"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token_info["token"]}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
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
                    print(f"ERREUR lors de la requête d'équipements du site {site_id} car aucun ne possède ces caractères: {char}")
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

    def get_points_id_from_char(self, device_id, char):
        """
        Récupère la liste de points dont le nom contient les caractères spécifiés via une requête GET.
        char est une liste de mots.
        Gère les erreurs 404 et d'autres erreurs potentielles.
        """
        self.get_token()
        if self.token_info['token'] is None:
            return None

        url = f"https://global-visio.com/api/devices/index/{device_id}"
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token_info["token"]}'
        }

        try:
            response = requests.get(url, headers=headers, data=payload)
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
