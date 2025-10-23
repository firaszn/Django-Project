# Django-Project

## Instructions de démarrage

### Prérequis
- Python 3.8+ installé sur votre système
- Git installé

### Installation et démarrage du projet

1. **Cloner le projet** (si pas déjà fait)
   ```bash
   git clone <url-du-repo>
   cd "Projet Django"
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Activer l'environnement virtuel**
   
   Sur Windows (PowerShell) :
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
   
   Sur Windows (CMD) :
   ```bash
   venv\Scripts\activate.bat
   ```

4. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

5. **Appliquer les migrations de base de données**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur** (optionnel)
   ```bash
   python manage.py createsuperuser
   ```

7. **Collecter les fichiers statiques**
   ```bash
   python manage.py collectstatic
   ```

8. **Démarrer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

9. **Accéder à l'application**
   - Ouvrir votre navigateur à l'adresse : `http://127.0.0.1:8000/`
   - Interface d'administration : `http://127.0.0.1:8000/admin/`

### Notes importantes
- Assurez-vous que l'environnement virtuel est activé avant d'installer les dépendances
- Si vous rencontrez des erreurs de permissions sur Windows, exécutez PowerShell en tant qu'administrateur
- La base de données SQLite sera créée automatiquement lors de la première migration
