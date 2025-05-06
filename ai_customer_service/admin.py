from django.contrib import admin
from .models import ChatSession, ChatMessage, AIRecommendation

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('session_id', 'user__username')
    date_hierarchy = 'created_at'
    list_per_page = 20

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'message_type', 'content', 'timestamp')
    list_filter = ('message_type', 'timestamp')
    search_fields = ('content', 'session__session_id')
    date_hierarchy = 'timestamp'
    list_per_page = 20

@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('chat_message', 'recommendation_text', 'created_at')
    search_fields = ('recommendation_text', 'chat_message__content')
    date_hierarchy = 'created_at'
    filter_horizontal = ('cars', 'locations')
    list_per_page = 20
