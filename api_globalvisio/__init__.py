from .core import *

"""
Réinstallation d'un package Python localement:

Étape 1: Naviguer vers le répertoire racine du package.
- Assurez-vous que vous êtes dans le répertoire racine de votre package, là où se trouve votre fichier 'setup.py'.

Étape 2: Désinstaller l'ancienne version du package.
- Avant de réinstaller votre package, il est conseillé de désinstaller la version précédente pour éviter tout conflit.
- Utilisez la commande suivante dans votre terminal:
    pip uninstall nom_de_votre_package

Étape 3: Réinstaller le package.
- Après avoir désinstallé l'ancienne version, vous pouvez réinstaller le package en exécutant:
    pip install .

Étape 4: Vérification.
- Après l'installation, vérifiez que le package est correctement installé en utilisant:
    pip show nom_de_votre_package
- Cette commande donnera des informations sur le package installé, y compris la version, les dépendances et l'emplacement de l'installation.

Utilisation du mode éditable:
- Si vous prévoyez de continuer à développer et tester votre package, considérez l'installation en mode éditable. Cela permet à Python de charger le package directement depuis le répertoire source sans nécessiter de réinstallation après chaque modification.
- Pour installer en mode éditable, utilisez:
    pip install -e .
"""