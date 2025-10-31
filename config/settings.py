import os
from pathlib import Path
from django.contrib.messages import constants as messages
from dotenv import load_dotenv

# The project previously used python-decouple's `config` helper. Some
# environments may not have that package installed. Provide a thin
# fallback that reads from environment variables via os.getenv so the
# settings file works in development without extra deps.
def config(key, default=None):
    return os.getenv(key, default)

# A minimal Csv helper to mimic decouple.Csv usage when needed.
def Csv(value):
    if value is None:
        return []
    return [v.strip() for v in str(value).split(',') if v.strip()]


# Import de la configuration email
try:
    from email_config import ACTIVE_EMAIL_CONFIG
    # Appliquer la configuration email
    for key, value in ACTIVE_EMAIL_CONFIG.items():
        globals()[key] = value
except ImportError:
    # Configuration par défaut si le fichier n'existe pas
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Charger les variables d'environnement
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Gemini AI Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    # 'django_cleanup',  # Temporarily disabled
    
    # Local apps
    'users.apps.UsersConfig',
    'journal.apps.JournalConfig',
    'TagsCat',
    'statistics_and_insights',
    'reminder_and_goals.apps.ReminderAndGoalsConfig',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ai_journal_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    }
}

GEMINI_API_KEY = 'AIzaSyCIReSYkG37uyIV-VvU87LObnhPzEJSN9M'
#GEMINI_MODEL="models/text-bison-001"


# Désactiver les messages de validation de mot de passe
AUTH_PASSWORD_VALIDATORS = []

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Authentication settings
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'journal_home'  # Les admins seront redirigés vers le dashboard via le signal
LOGOUT_REDIRECT_URL = 'account_login'

# django-allauth configuration
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Vérification email obligatoire

# Exempter les superusers de la vérification email pour l'admin
ACCOUNT_EMAIL_VERIFICATION_EXEMPT_STAFF = True

# Connexion automatique après confirmation d'email (désactivé - l'utilisateur doit se connecter manuellement)
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False

# Confirmation d'email sur GET (permet de confirmer en cliquant sur le lien)
ACCOUNT_CONFIRM_EMAIL_ON_GET = True

# Configuration de la déconnexion
ACCOUNT_LOGOUT_ON_GET = True  # Permet la déconnexion via GET
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'  # Redirection directe vers login

# Configuration du formulaire d'inscription personnalisé
ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
    'login': 'users.forms.CustomLoginForm',
}

# Adaptateur personnalisé pour la redirection après login
ACCOUNT_ADAPTER = 'users.adapter.CustomAccountAdapter'

# Email settings - Configuration sera surchargée par email_config.py
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Pour la production avec Gmail (décommentez et configurez)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'votre-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-app'  # Utilisez un mot de passe d'application
# DEFAULT_FROM_EMAIL = 'votre-email@gmail.com'

# Pour la production avec un autre service SMTP
# EMAIL_HOST = 'smtp.votre-fournisseur.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'votre-email@votre-domaine.com'
# EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
# DEFAULT_FROM_EMAIL = 'noreply@votre-domaine.com'

# Messages settings
MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Social Account Providers (disabled)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account',  # force le sélecteur de compte Google
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# Configuration pour l'authentification sociale
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Pas de vérification pour les comptes sociaux
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Adapter pour les comptes sociaux
SOCIALACCOUNT_ADAPTER = 'users.adapter.CustomSocialAccountAdapter'

# Configuration API IA (Génération de bio)
# Groq API - Gratuit et rapide : https://console.groq.com/
# IMPORTANT: Ne pas mettre la clé directement dans le code !
# Utilisez la variable d'environnement GROQ_API_KEY ou un fichier .env
GROQ_API_KEY = config('GROQ_API_KEY', default='')

# HuggingFace API (Optionnel - fallback)
HUGGINGFACE_API_KEY = config('HUGGINGFACE_API_KEY', default=None)  # Optionnel : clé HuggingFace si vous en avez une

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY = config('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default='')
