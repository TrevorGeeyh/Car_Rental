from django.db import models
from django.contrib.auth.models import User
from car_rental.models import Car, Location

class ChatSession(models.Model):
    """聊天会话模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', verbose_name='用户')
    session_id = models.CharField(max_length=50, unique=True, verbose_name='会话ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最后活跃时间')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    
    def __str__(self):
        return f"{self.user.username}的会话 ({self.session_id})"
    
    class Meta:
        verbose_name = '聊天会话'
        verbose_name_plural = '聊天会话'

class ChatMessage(models.Model):
    """聊天消息模型"""
    MESSAGE_TYPE_CHOICES = (
        ('user', '用户'),
        ('ai', 'AI客服'),
        ('system', '系统消息'),
    )
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', verbose_name='会话')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, verbose_name='消息类型')
    content = models.TextField(verbose_name='消息内容')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    
    def __str__(self):
        return f"{self.get_message_type_display()} 消息 - {self.session.session_id}"
    
    class Meta:
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        ordering = ['timestamp']

class AIRecommendation(models.Model):
    """AI推荐模型"""
    chat_message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='recommendations', verbose_name='关联消息')
    cars = models.ManyToManyField(Car, related_name='ai_recommendations', verbose_name='推荐车辆')
    locations = models.ManyToManyField(Location, related_name='ai_recommendations', verbose_name='推荐网点')
    recommendation_text = models.TextField(verbose_name='推荐文本')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    def __str__(self):
        return f"AI推荐 - {self.chat_message.session.user.username}"
    
    class Meta:
        verbose_name = 'AI推荐'
        verbose_name_plural = 'AI推荐'
