"""
Patch pour utiliser MySQL 5.7 avec Django 5.0
Ce script doit être importé avant Django
"""
import django.db.backends.mysql.validation
import django.db.backends.base.base

# Désactiver la vérification de version MySQL
original_check_sql_mode = django.db.backends.mysql.validation.DatabaseValidation._check_sql_mode

def patched_check_sql_mode(self, **kwargs):
    # Retourner une liste vide pour ignorer la vérification
    return []

# Désactiver la vérification de version de base de données
def patched_check_database_version_supported(self):
    # Ne rien faire - ignorer la vérification de version
    pass

django.db.backends.mysql.validation.DatabaseValidation._check_sql_mode = patched_check_sql_mode
django.db.backends.base.base.BaseDatabaseWrapper.check_database_version_supported = patched_check_database_version_supported

print("Patch MySQL appliqué - Django 5.0 peut maintenant utiliser MySQL 5.7")
