from django.contrib import admin
from .models import Journal, JournalImage


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'entry_date', 'hidden', 'created_at')
	list_filter = ('hidden', 'entry_date', 'created_at')
	search_fields = ('title', 'description', 'user__email')


@admin.register(JournalImage)
class JournalImageAdmin(admin.ModelAdmin):
	list_display = ('journal', 'image', 'uploaded_at')
	search_fields = ('journal__title',)
