# journal/admin.py
from django.contrib import admin
from .models import Journal, JournalImage

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'is_public', 'created_at')
    list_filter = ('user', 'category', 'is_public', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('tags', 'related_goals')
    ordering = ('-created_at',)

    def get_tags(self, obj):
        return ", ".join(obj.get_tags_list())
    get_tags.short_description = 'Tags'


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

    

    def get_category(self, obj):
        return obj.journal.category if getattr(obj, 'journal', None) else ''
    get_category.short_description = 'Category'
