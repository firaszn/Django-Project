from django.contrib import admin
from .models import Memory, MemoryPhoto


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'date', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('title', 'description')


@admin.register(MemoryPhoto)
class MemoryPhotoAdmin(admin.ModelAdmin):
    list_display = ('memory', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
