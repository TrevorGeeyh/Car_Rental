from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'user_type', 'id_card', 'driver_license')
    list_filter = ('user_type',)
    search_fields = ('user__username', 'user__email', 'phone_number', 'id_card', 'driver_license')
    list_per_page = 20
