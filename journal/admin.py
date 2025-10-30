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
    list_display = ('id', 'get_journal_title', 'get_user', 'get_category', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    list_filter = ('journal__user', 'journal__category', 'uploaded_at')

    def get_journal_title(self, obj):
        return obj.journal.title
    get_journal_title.short_description = 'Journal Title'

    def get_user(self, obj):
        return obj.journal.user
    get_user.short_description = 'User'

    def get_category(self, obj):
        return obj.journal.category
    get_category.short_description = 'Category'
