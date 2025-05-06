from django.urls import path
from . import views

app_name = 'ai_customer_service'

urlpatterns = [
    # AI客服聊天
    path('chat/', views.chat_interface, name='chat_interface'),
    path('send-message/', views.send_message, name='send_message'),
    path('chat-history/', views.get_chat_history, name='chat_history'),
    path('start-chat/', views.start_chat_session, name='start_chat'),
    path('clear-chat-history/', views.clear_chat_history, name='clear_chat_history'),
    
    # AI推荐
    path('rent-recommended-car/<int:car_id>/', views.rent_recommended_car, name='rent_recommended_car'),
    path('ai-recommend/', views.ai_recommend_cars, name='ai_recommend'),
] 