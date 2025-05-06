from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    """用户注册表单"""
    email = forms.EmailField(label='电子邮箱', help_text='请输入有效的电子邮箱地址')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': '用户名',
            'password1': '密码',
            'password2': '确认密码',
        }
        help_texts = {
            'username': '请输入不超过150个字符的用户名。只能包含字母、数字和符号（@/./+/-/_）。',
        }
    
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        # 自定义密码帮助文本
        self.fields['password1'].help_text = '密码不能与个人信息太相似，至少包含8个字符，不能是常见密码，不能全是数字。'
        self.fields['password2'].help_text = '请再次输入密码，以确认两次输入一致。'

class UserLoginForm(forms.Form):
    """用户登录表单"""
    username = forms.CharField(label='用户名')
    password = forms.CharField(label='密码', widget=forms.PasswordInput)

class UserProfileForm(forms.ModelForm):
    """用户个人资料表单"""
    first_name = forms.CharField(max_length=30, required=False, label='名')
    last_name = forms.CharField(max_length=30, required=False, label='姓')
    email = forms.EmailField(required=False, label='电子邮箱')
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'address', 'id_card', 'driver_license', 'profile_picture']
        labels = {
            'phone_number': '电话号码',
            'address': '地址',
            'id_card': '身份证号',
            'driver_license': '驾驶证号',
            'profile_picture': '头像',
        }
        help_texts = {
            'id_card': '请输入18位有效身份证号',
            'driver_license': '请输入有效的驾驶证号码',
        }
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        } 