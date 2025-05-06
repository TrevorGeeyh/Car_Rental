from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('admin', '管理员'),
        ('customer', '普通用户'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name='电话号码')
    address = models.TextField(blank=True, null=True, verbose_name='地址')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer', verbose_name='用户类型')
    id_card = models.CharField(max_length=18, blank=True, null=True, verbose_name='身份证号')
    driver_license = models.CharField(max_length=20, blank=True, null=True, verbose_name='驾驶证号')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, verbose_name='头像')
    
    def __str__(self):
        return f"{self.user.username}的个人资料"
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
