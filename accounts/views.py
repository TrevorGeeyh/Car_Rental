from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm

def register(request):
    """用户注册视图"""
    if request.user.is_authenticated:
        return redirect('car_rental:home')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # 创建用户资料
            UserProfile.objects.create(user=user)
            
            # 登录用户
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, f'账户已成功创建，欢迎 {username}!')
            return redirect('car_rental:home')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """用户登录视图"""
    if request.user.is_authenticated:
        return redirect('car_rental:home')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}!')
                
                # 如果有next参数，跳转到对应页面
                next_page = request.GET.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect('car_rental:home')
            else:
                messages.error(request, '用户名或密码不正确!')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def profile(request):
    """用户个人资料视图"""
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    """编辑用户个人资料视图"""
    # 获取或创建用户资料
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # 更新用户名和邮箱
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            messages.success(request, '个人资料已成功更新!')
            return redirect('accounts:profile')
    else:
        # 为表单初始化一些用户数据
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserProfileForm(instance=profile, initial=initial_data)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})
