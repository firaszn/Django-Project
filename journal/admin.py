from django.contrib import admin
from .models import JournalEntry


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'created_at', 'is_public']
    list_filter = ['user', 'category', 'is_public', 'created_at']
    search_fields = ['title', 'content', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['tags']
