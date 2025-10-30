from django.contrib import admin
from .models import Journal, JournalImage


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'entry_date', 'hidden', 'created_at')
	list_filter = ('hidden', 'entry_date', 'created_at')
	search_fields = ('title', 'description', 'user__email')


@admin.register(JournalImage)
class JournalImageAdmin(admin.ModelAdmin):
	# JournalImage only has: id, journal (FK), image, uploaded_at
	# Show useful related info via helper methods instead of referencing non-existent fields
	list_display = ('id', 'journal_title', 'journal_user', 'uploaded_at')
	list_filter = ('uploaded_at',)
	search_fields = ('journal__title', 'journal__user__email')
	readonly_fields = ('uploaded_at',)

	def journal_title(self, obj):
		return obj.journal.title if obj.journal else ''
	journal_title.short_description = 'Journal'

	def journal_user(self, obj):
		user = getattr(obj.journal, 'user', None)
		return getattr(user, 'email', str(user)) if user else ''
	journal_user.short_description = 'User'
