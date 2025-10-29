from django.contrib import admin
from .models import Journal, JournalImage


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'entry_date', 'hidden', 'created_at')
	list_filter = ('hidden', 'entry_date', 'created_at')
	search_fields = ('title', 'description', 'user__email')


@admin.register(JournalImage)
class JournalImageAdmin(admin.ModelAdmin):
	list_display = ['title', 'user', 'category', 'created_at', 'is_public']
	list_filter = ['user', 'category', 'is_public', 'created_at']
	search_fields = ['title', 'content', 'user__email']
	readonly_fields = ['created_at', 'updated_at']
	filter_horizontal = ['tags']
