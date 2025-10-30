from django.contrib import admin
from .models import Journal, JournalImage

@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'entry_date', 'hidden', 'created_at')
    list_filter = ('hidden', 'entry_date', 'created_at')
    search_fields = ('title', 'description', 'user__email')
    filter_horizontal = ['tags']  
    readonly_fields = ['created_at', 'updated_at']  

@admin.register(JournalImage)
class JournalImageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'journal', 'uploaded_at']  # Use actual fields from JournalImage
    list_filter = ['uploaded_at', 'journal']  # Use actual fields
    search_fields = ['journal__title', 'journal__user__email']  # Search through related fields
    readonly_fields = ['uploaded_at']  # Only use fields that exist on JournalImage