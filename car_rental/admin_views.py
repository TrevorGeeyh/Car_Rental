from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_users(request):
    """管理用户列表视图"""
    # 获取筛选参数
    user_type = request.GET.get('user_type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    # 基本查询集
    users = User.objects.all()
    
    # 添加订单统计
    from .models import Rental
    users = users.annotate(rental_count=Count('rentals'))
    
    # 应用筛选条件
    if user_type:
        if user_type == 'admin':
            users = users.filter(is_superuser=True)
        elif user_type == 'staff':
            users = users.filter(is_staff=True, is_superuser=False)
        elif user_type == 'customer':
            users = users.filter(is_staff=False, is_superuser=False)
    
    if status:
        if status == 'active':
            users = users.filter(is_active=True)
        elif status == 'inactive':
            users = users.filter(is_active=False)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) | 
            Q(userprofile__phone__icontains=search)
        )
    
    # 默认按注册日期排序
    users = users.order_by('-date_joined')
    
    # 分页
    paginator = Paginator(users, 10)  # 每页显示10条
    page_number = request.GET.get('page', 1)
    users_page = paginator.get_page(page_number)
    
    # 准备模板上下文
    context = {
        'users': users_page,
        'total_users': users.count(),
        'active_section': 'users',
    }
    
    return render(request, 'car_rental/admin/users.html', context)

@staff_member_required
def admin_add_user(request):
    """添加新用户的视图函数"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        user_role = request.POST.get('user_role')
        
        # 基本验证
        if password != confirm_password:
            messages.error(request, '两次输入的密码不匹配')
            return redirect('car_rental:admin_users')
        
        # 检查用户名和邮箱是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, f'用户名 "{username}" 已被使用')
            return redirect('car_rental:admin_users')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, f'邮箱 "{email}" 已被注册')
            return redirect('car_rental:admin_users')
        
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # 设置用户角色
        if user_role == 'staff':
            user.is_staff = True
            user.save()
        elif user_role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        
        # 如果有电话号码，更新用户个人资料
        if phone:
            try:
                from .models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.phone = phone
                profile.save()
            except:
                # 如果UserProfile模型不存在或出现错误，不影响用户创建
                pass
        
        messages.success(request, f'用户 "{username}" 已成功创建')
    else:
        messages.error(request, '请使用POST方法提交表单')
    
    return redirect('car_rental:admin_users')

@staff_member_required
def admin_edit_user(request, user_id):
    """编辑用户信息的视图函数"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '用户不存在')
        return redirect('car_rental:admin_users')
    
    if request.method == 'POST':
        # 获取表单数据
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        is_active = request.POST.get('is_active') == 'true'
        user_role = request.POST.get('user_role')
        
        # 更新用户信息
        user.email = email
        user.is_active = is_active
        
        # 更新用户角色
        if user_role == 'customer':
            user.is_staff = False
            user.is_superuser = False
        elif user_role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        elif user_role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        
        user.save()
        
        # 更新电话号码（如果UserProfile模型存在）
        try:
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = phone
            profile.save()
        except:
            pass
        
        messages.success(request, f'用户 "{user.username}" 的信息已更新')
    else:
        messages.error(request, '请使用POST方法提交表单')
    
    return redirect('car_rental:admin_users')

@staff_member_required
def admin_toggle_user_status(request, user_id):
    """激活/封禁用户账户"""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '用户不存在')
        return redirect('car_rental:admin_users')
    
    # 切换用户激活状态
    user.is_active = not user.is_active
    user.save()
    
    action = "激活" if user.is_active else "封禁"
    messages.success(request, f'已{action}用户 "{user.username}" 的账户')
    
    return redirect('car_rental:admin_users')

@staff_member_required
def admin_reset_user_password(request, user_id):
    """重置用户密码"""
    if request.method != 'POST':
        messages.error(request, '请使用POST方法提交表单')
        return redirect('car_rental:admin_users')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, '用户不存在')
        return redirect('car_rental:admin_users')
    
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    if not new_password or new_password != confirm_password:
        messages.error(request, '密码为空或两次输入不匹配')
        return redirect('car_rental:admin_users')
    
    user.set_password(new_password)
    user.save()
    
    messages.success(request, f'已重置用户 "{user.username}" 的密码')
    return redirect('car_rental:admin_users') 