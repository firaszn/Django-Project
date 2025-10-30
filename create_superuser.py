#!/usr/bin/env python
"""Script pour créer un superutilisateur Django avec variables d'environnement"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if username and email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'Superutilisateur {username} créé avec succès.')
    else:
        print(f'Le superutilisateur {username} existe déjà.')
else:
    print('Variables d\'environnement manquantes pour créer le superutilisateur.')

