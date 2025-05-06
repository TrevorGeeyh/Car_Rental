from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, ExpressionWrapper, F, DurationField
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Car, Location, CarCategory, Rental, CarReview
from .forms import RentalForm, CarSearchForm, CarFilterForm, CarReviewForm
from django.urls import reverse
from django.http import HttpResponseRedirect

def home(request):
    """首页视图"""
    # 获取推荐车辆（例如价格最高的几款）
    featured_cars = Car.objects.filter(status='available').order_by('-daily_rate')[:6]
    
    # 获取所有位置
    locations = Location.objects.all()
    
    # 提取不重复的城市列表
    cities = set()
    for location in locations:
        cities.add(location.city)
    
    # 获取不同车辆类别
    categories = CarCategory.objects.all()
    
    context = {
        'featured_cars': featured_cars,
        'locations': locations,
        'cities': cities,
        'categories': categories,
    }
    
    return render(request, 'car_rental/home.html', context)

def car_list(request):
    """车辆列表视图"""
    # 默认获取所有可用车辆
    cars = Car.objects.filter(status='available')
    
    # 获取所有类别和位置，用于过滤选项
    categories = CarCategory.objects.all()
    locations = Location.objects.all()
    
    # 构建过滤表单
    filter_form = CarFilterForm(request.GET)
    
    # 记录是否应用了过滤条件
    is_filtered = False
    category_obj = None
    location_obj = None
    price_min_val = None
    price_max_val = None
    seats_val = None
    transmission_val = None
    fuel_type_val = None
    
    # 应用过滤条件
    if filter_form.is_valid():
        # 按类别过滤
        category = filter_form.cleaned_data.get('category')
        if category:
            cars = cars.filter(category=category)
            category_obj = category
            is_filtered = True
        
        # 按位置过滤
        location = filter_form.cleaned_data.get('location')
        if location:
            cars = cars.filter(location=location)
            location_obj = location
            is_filtered = True
        
        # 按价格范围过滤
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        
        if min_price:
            cars = cars.filter(daily_rate__gte=min_price)
            price_min_val = min_price
            is_filtered = True
        if max_price:
            cars = cars.filter(daily_rate__lte=max_price)
            price_max_val = max_price
            is_filtered = True
        
        # 按座位数过滤
        seats = filter_form.cleaned_data.get('seats')
        if seats:
            cars = cars.filter(seats=seats)
            seats_val = seats
            is_filtered = True
        
        # 按变速箱类型过滤
        transmission = filter_form.cleaned_data.get('transmission')
        if transmission:
            cars = cars.filter(transmission=transmission)
            transmission_val = transmission
            is_filtered = True
        
        # 按燃料类型过滤
        fuel_type = filter_form.cleaned_data.get('fuel_type')
        if fuel_type:
            cars = cars.filter(fuel_type=fuel_type)
            fuel_type_val = fuel_type
            is_filtered = True
    
    # 按位置ID列表过滤（来自快速查询）
    location_ids = request.GET.get('location', '')
    if location_ids:
        try:
            # 位置ID可能是以逗号分隔的多个ID
            location_id_list = [int(loc_id) for loc_id in location_ids.split(',') if loc_id.isdigit()]
            if location_id_list:
                cars = cars.filter(location_id__in=location_id_list)
                is_filtered = True
        except ValueError:
            pass
    
    # 日期过滤（来自快速查询）
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    # 如果提供了日期范围，过滤掉在该日期范围内已被预订的车辆
    if start_date and end_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # 排除在指定日期范围内已被预订的车辆
            cars = cars.exclude(
                rentals__status__in=['confirmed', 'ongoing'],
                rentals__start_date__lte=end_date_obj,
                rentals__end_date__gte=start_date_obj
            )
            is_filtered = True
        except ValueError:
            # 日期格式无效，忽略日期过滤
            pass
    
    # 搜索功能
    search_form = CarSearchForm(request.GET)
    search_query = ''
    if search_form.is_valid() and search_form.cleaned_data.get('query'):
        query = search_form.cleaned_data.get('query')
        search_query = query
        cars = cars.filter(
            Q(name__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(model__icontains=query) |
            Q(description__icontains=query)
        )
        is_filtered = True
    
    # 排序
    sort_by = request.GET.get('sort_by', 'name')
    
    if sort_by == 'price_low':
        cars = cars.order_by('daily_rate')
    elif sort_by == 'price_high':
        cars = cars.order_by('-daily_rate')
    elif sort_by == 'newest':
        cars = cars.order_by('-year')
    else:  # 默认按名称排序
        cars = cars.order_by('name')
    
    # 分页处理
    paginator = Paginator(cars, 9)  # 每页9辆车
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'search_form': search_form,
        'categories': categories,
        'locations': locations,
        'total_cars': cars.count(),
        'sort_by': sort_by,
        'start_date': start_date,
        'end_date': end_date,
        'is_filtered': is_filtered,
        'category': category_obj,
        'location': location_obj,
        'price_min': price_min_val,
        'price_max': price_max_val,
        'seats': seats_val,
        'transmission': transmission_val,
        'fuel_type': fuel_type_val,
        'search_query': search_query,
    }
    
    return render(request, 'car_rental/car_list.html', context)

def car_detail(request, car_id):
    """车辆详情视图"""
    car = get_object_or_404(Car, id=car_id)
    
    # 获取相同类别的推荐车辆
    similar_cars = Car.objects.filter(
        category=car.category, 
        status='available'
    ).exclude(id=car.id)[:3]
    
    # 创建租车表单
    form = RentalForm(initial={
        'car': car,
        'pickup_location': car.location,
        'return_location': car.location,
    })
    
    context = {
        'car': car,
        'similar_cars': similar_cars,
        'form': form,
    }
    
    return render(request, 'car_rental/car_detail.html', context)

def car_search(request):
    """车辆搜索视图 - 处理首页快速查询或搜索框查询"""
    if request.method == 'GET':
        # 处理搜索词查询
        query = request.GET.get('query', '')
        
        # 处理首页快速查询参数
        city = request.GET.get('city', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # 构建重定向URL参数
        params = {}
        
        if query:
            params['query'] = query
        
        if city:
            # 获取该城市的所有网点，用于过滤
            locations = Location.objects.filter(city=city).values_list('id', flat=True)
            if locations:
                params['location'] = ",".join(map(str, locations))
        
        if start_date:
            params['start_date'] = start_date
        
        if end_date:
            params['end_date'] = end_date
        
        # 使用reverse获取基础URL，然后添加查询参数
        base_url = reverse('car_rental:car_list')
        query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
        
        if query_string:
            redirect_url = f"{base_url}?{query_string}"
        else:
            redirect_url = base_url
            
        return HttpResponseRedirect(redirect_url)
    
    return redirect('car_rental:car_list')

def car_filter(request):
    """车辆过滤视图 - 重定向到car_list并附加过滤参数"""
    # 保留所有GET查询参数
    query_params = request.GET.urlencode()
    redirect_url = reverse('car_rental:car_list')
    
    # 如果有查询参数，添加到URL
    if query_params:
        redirect_url = f"{redirect_url}?{query_params}"
    
    return HttpResponseRedirect(redirect_url)

def location_list(request):
    """网点列表视图"""
    locations = Location.objects.all()
    
    # 获取所有城市并计算每个城市的网点数量
    city_list = []
    city_counts = {}
    for location in locations:
        if location.city not in city_list:
            city_list.append(location.city)
            city_counts[location.city] = 1
        else:
            city_counts[location.city] += 1
    
    # 按城市对网点进行分组
    locations_by_city = {}
    for location in locations:
        if location.city not in locations_by_city:
            locations_by_city[location.city] = []
        locations_by_city[location.city].append(location)
    
    # 创建城市数据列表，每个城市包含名称和数量
    cities_data = [{'name': city, 'count': city_counts[city]} for city in city_list]
    
    context = {
        'locations': locations,
        'locations_by_city': locations_by_city,
        'city_list': city_list,
        'city_counts': city_counts,
        'cities_data': cities_data
    }
    
    return render(request, 'car_rental/location_list.html', context)

def location_search(request):
    """网点搜索视图"""
    query = request.GET.get('query', '')
    locations = Location.objects.all()
    
    if query:
        # 按名称或地址搜索网点
        locations = locations.filter(
            Q(name__icontains=query) | 
            Q(address__icontains=query) |
            Q(city__icontains=query)
        )
    
    # 获取所有城市并计算每个城市的网点数量
    city_list = []
    city_counts = {}
    for location in locations:
        if location.city not in city_list:
            city_list.append(location.city)
            city_counts[location.city] = 1
        else:
            city_counts[location.city] += 1
    
    # 按城市对网点进行分组
    locations_by_city = {}
    for location in locations:
        if location.city not in locations_by_city:
            locations_by_city[location.city] = []
        locations_by_city[location.city].append(location)
    
    # 创建城市数据列表，每个城市包含名称和数量
    cities_data = [{'name': city, 'count': city_counts[city]} for city in city_list]
    
    context = {
        'locations': locations,
        'locations_by_city': locations_by_city,
        'city_list': city_list,
        'city_counts': city_counts,
        'cities_data': cities_data,
        'search_query': query
    }
    
    return render(request, 'car_rental/location_list.html', context)

def location_detail(request, location_id):
    """网点详情视图"""
    location = get_object_or_404(Location, id=location_id)
    
    # 获取该网点的可用车辆
    available_cars = Car.objects.filter(location=location, status='available')
    
    context = {
        'location': location,
        'available_cars': available_cars,
    }
    
    return render(request, 'car_rental/location_detail.html', context)

@login_required
def rent_car(request, car_id):
    """租车流程视图"""
    car = get_object_or_404(Car, id=car_id)
    
    if car.status != 'available':
        messages.error(request, '抱歉，该车辆当前不可用')
        return redirect('car_rental:car_detail', car_id=car_id)
    
    if request.method == 'POST':
        # 打印提交的表单数据，帮助调试
        print("提交的表单数据:", request.POST)
        
        form = RentalForm(request.POST)
        
        if form.is_valid():
            print("表单验证通过!")
            rental = form.save(commit=False)
            rental.user = request.user
            rental.car = car
            rental.status = 'pending'
            
            # 确保start_date和end_date不为空
            start_date = form.cleaned_data.get('start_date') or timezone.now()
            end_date = form.cleaned_data.get('end_date') or (timezone.now() + timedelta(days=1))
            
            # 计算总价（天数 * 日租金）
            days = max(1, (end_date - start_date).days + 1)
            rental.total_price = car.daily_rate * days
            
            # 确保日期被正确设置
            rental.start_date = start_date
            rental.end_date = end_date
            
            try:
                rental.save()
                
                # 更新车辆状态
                car.status = 'rented'
                car.save()
                
                messages.success(request, '租车订单已创建，请确认订单信息')
                return redirect('car_rental:confirm_rental', rental_id=rental.id)
            except Exception as e:
                print(f"保存订单时出错: {str(e)}")
                messages.error(request, f'创建订单时出错: {str(e)}')
        else:
            # 打印表单错误信息，帮助调试
            print("表单验证失败:", form.errors)
            
            # 尝试手动创建订单
            try:
                # 从POST数据中获取信息
                pickup_location_id = request.POST.get('pickup_location') or car.location.id
                return_location_id = request.POST.get('return_location') or car.location.id
                notes = request.POST.get('notes', '')
                
                # 使用默认日期
                start_date = timezone.now()
                end_date = timezone.now() + timedelta(days=1)
                
                # 创建租车订单
                rental = Rental.objects.create(
                    user=request.user,
                    car=car,
                    pickup_location_id=pickup_location_id,
                    return_location_id=return_location_id,
                    start_date=start_date,
                    end_date=end_date,
                    total_price=car.daily_rate,
                    status='pending',
                    notes=notes
                )
                
                # 更新车辆状态
                car.status = 'rented'
                car.save()
                
                messages.success(request, '租车订单已创建（使用默认日期），请确认订单信息')
                return redirect('car_rental:confirm_rental', rental_id=rental.id)
            except Exception as e:
                print(f"手动创建订单时出错: {str(e)}")
                messages.error(request, f'创建订单时出错: {str(e)}')
    else:
        form = RentalForm(initial={
            'car': car,
            'pickup_location': car.location,
            'return_location': car.location,
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=1),
        })
    
    context = {
        'form': form,
        'car': car,
    }
    
    return render(request, 'car_rental/rent_car.html', context)

@login_required
def confirm_rental(request, rental_id):
    """确认订单视图"""
    rental = get_object_or_404(Rental, id=rental_id)
    
    # 确保只有订单所有者或管理员才能确认订单
    if request.user != rental.user and not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作')
        return redirect('car_rental:my_rentals')
    
    # 确保订单状态为已支付且处于待处理状态
    if rental.payment_status != 'paid' or rental.status != 'pending':
        messages.error(request, '只能确认已支付且待处理的订单')
        return redirect('car_rental:rental_detail', order_id=rental.order_id)
    
    if request.method == 'POST':
        # 更新订单状态为已确认
        rental.status = 'confirmed'
        rental.save()
        
        messages.success(request, '订单已成功确认，请按预定时间前往取车')
    
    return redirect('car_rental:rental_detail', order_id=rental.order_id)

@login_required
def pickup_car(request, rental_id):
    """取车视图"""
    rental = get_object_or_404(Rental, id=rental_id)
    
    # 确保只有订单所有者或管理员才能操作
    if request.user != rental.user and not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作')
        return redirect('car_rental:my_rentals')
    
    # 确保订单状态为已确认
    if rental.status != 'confirmed':
        messages.error(request, '只有已确认的订单才能进行取车操作')
        return redirect('car_rental:rental_detail', order_id=rental.order_id)
    
    if request.method == 'POST':
        # 获取表单数据
        pickup_condition = request.POST.get('pickup_condition')
        pickup_fuel_level = request.POST.get('pickup_fuel_level')
        pickup_odometer = request.POST.get('pickup_odometer')
        
        if not pickup_condition or not pickup_fuel_level or not pickup_odometer:
            messages.error(request, '请填写完整的取车信息')
            return redirect('car_rental:rental_detail', order_id=rental.order_id)
        
        # 更新订单信息
        rental.status = 'ongoing'
        
        # 添加取车记录到备注
        rental.notes = f"{rental.notes or ''}\n\n取车记录：\n" \
                      f"状态：{pickup_condition}\n" \
                      f"油量：{pickup_fuel_level}\n" \
                      f"里程表读数：{pickup_odometer}公里\n" \
                      f"取车时间：{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        rental.save()
        
        messages.success(request, '取车成功！祝您用车愉快')
    
    return redirect('car_rental:rental_detail', order_id=rental.order_id)

@login_required
def return_car(request, rental_id):
    """还车视图"""
    rental = get_object_or_404(Rental, id=rental_id)
    
    # 确保只有订单所有者或管理员才能操作
    if request.user != rental.user and not request.user.is_staff:
        messages.error(request, '您没有权限执行此操作')
        return redirect('car_rental:my_rentals')
    
    # 确保订单状态为进行中
    if rental.status != 'ongoing':
        messages.error(request, '只有进行中的订单才能进行还车操作')
        return redirect('car_rental:rental_detail', order_id=rental.order_id)
    
    if request.method == 'POST':
        # 获取表单数据
        return_condition = request.POST.get('return_condition')
        return_fuel_level = request.POST.get('return_fuel_level')
        return_odometer = request.POST.get('return_odometer')
        return_notes = request.POST.get('return_notes', '')
        
        if not return_condition or not return_fuel_level or not return_odometer:
            messages.error(request, '请填写完整的还车信息')
            return redirect('car_rental:rental_detail', order_id=rental.order_id)
        
        # 更新订单信息
        rental.status = 'completed'
        
        # 添加还车记录到备注
        rental.notes = f"{rental.notes or ''}\n\n还车记录：\n" \
                      f"状态：{return_condition}\n" \
                      f"油量：{return_fuel_level}\n" \
                      f"里程表读数：{return_odometer}公里\n" \
                      f"备注：{return_notes}\n" \
                      f"还车时间：{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
        rental.save()
        
        # 将车辆状态改为可用
        car = rental.car
        car.status = 'available'
        car.save()
        
        messages.success(request, '还车成功！感谢您的使用')
    
    return redirect('car_rental:rental_detail', order_id=rental.order_id)

@login_required
def payment(request, rental_id):
    """付款视图"""
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)
    
    if rental.payment_status != 'pending':
        messages.info(request, '该订单已完成付款')
        return redirect('car_rental:rental_detail', order_id=rental.order_id)
    
    if request.method == 'POST':
        # 处理付款逻辑
        # 这里简化处理，实际应该对接支付网关
        rental.payment_status = 'paid'
        rental.status = 'confirmed'
        rental.save()
        
        messages.success(request, '付款成功！您的租车订单已确认')
        return redirect('car_rental:rental_success', order_id=rental.order_id)
    
    # 计算租期天数
    rental_days = (rental.end_date - rental.start_date).days + 1
    
    context = {
        'rental': rental,
        'rental_days': rental_days,
    }
    
    return render(request, 'car_rental/payment.html', context)

@login_required
def rental_success(request, order_id):
    """租车成功视图"""
    rental = get_object_or_404(Rental, order_id=order_id, user=request.user)
    
    # 计算租期天数
    rental_days = (rental.end_date - rental.start_date).days + 1
    
    # 添加支付方式信息（实际中应该从支付系统获取）
    payment_method = "微信支付"
    
    context = {
        'rental': rental,
        'rental_days': rental_days,
        'payment_method': payment_method,
    }
    
    return render(request, 'car_rental/rental_success.html', context)

@login_required
def my_rentals(request):
    """用户租车订单列表视图"""
    # 管理员可以查看所有订单，普通用户只能查看自己的订单
    if request.user.is_staff:
        rentals = Rental.objects.all().order_by('-created_at')
    else:
        rentals = Rental.objects.filter(user=request.user).order_by('-created_at')
    
    # 按状态过滤
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        rentals = rentals.filter(status=status_filter)
    
    # 订单统计
    if request.user.is_staff:
        orders_completed = Rental.objects.filter(status='completed').count()
        orders_ongoing = Rental.objects.filter(status__in=['confirmed', 'ongoing']).count()
        orders_upcoming = Rental.objects.filter(status='pending').count()
        orders_cancelled = Rental.objects.filter(status='cancelled').count()
    else:
        orders_completed = Rental.objects.filter(user=request.user, status='completed').count()
        orders_ongoing = Rental.objects.filter(user=request.user, status__in=['confirmed', 'ongoing']).count()
        orders_upcoming = Rental.objects.filter(user=request.user, status='pending').count()
        orders_cancelled = Rental.objects.filter(user=request.user, status='cancelled').count()
    
    # 添加日志
    print(f"当前用户: {request.user.username}, 是否管理员: {request.user.is_staff}")
    print(f"订单总数: {rentals.count()}")
    print(f"订单列表: {[str(rental.order_id) for rental in rentals[:5]]}")
    
    # 分页处理
    paginator = Paginator(rentals, 10)  # 每页10条订单
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'rentals': page_obj.object_list,  # 添加rentals到上下文
        'status_filter': status_filter or 'all',
        'orders_completed': orders_completed,
        'orders_ongoing': orders_ongoing,
        'orders_upcoming': orders_upcoming,
        'orders_cancelled': orders_cancelled,
    }
    
    return render(request, 'car_rental/my_rentals.html', context)

@login_required
def rental_detail(request, order_id):
    """租车订单详情视图"""
    # 管理员可以查看任何订单，普通用户只能查看自己的订单
    if request.user.is_staff:
        rental = get_object_or_404(Rental, order_id=order_id)
    else:
        rental = get_object_or_404(Rental, order_id=order_id, user=request.user)
    
    # 计算租期天数
    rental_days = (rental.end_date - rental.start_date).days + 1
    
    context = {
        'rental': rental,
        'rental_days': rental_days,
    }
    
    return render(request, 'car_rental/rental_detail.html', context)

@login_required
def cancel_rental(request, rental_id):
    """取消租车订单"""
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)
    
    # 只允许取消待处理或已确认的订单
    if rental.status not in ['pending', 'confirmed']:
        messages.error(request, '只能取消待处理或已确认的订单')
        return redirect('car_rental:my_rentals')
    
    if request.method == 'POST':
        # 获取取消原因
        cancel_reason = request.POST.get('cancel_reason', '')
        cancel_comment = request.POST.get('cancel_comment', '')
        
        # 更新订单状态
        rental.status = 'cancelled'
        rental.notes = f"订单取消原因: {cancel_reason}\n补充说明: {cancel_comment}"
        rental.save()
        
        # 将车辆状态改回可用
        car = rental.car
        car.status = 'available'
        car.save()
        
        messages.success(request, '订单已成功取消')
        return redirect('car_rental:my_rentals')
    
    return redirect('car_rental:rental_detail', order_id=rental.order_id)

@login_required
def review_rental(request, rental_id):
    """评价租车订单视图"""
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)
    
    # 检查订单是否已完成
    if rental.status != 'completed':
        messages.error(request, '只能评价已完成的订单')
        return redirect('car_rental:rental_detail', order_id=rental.order_id)
    
    # 检查是否已评价
    try:
        review = rental.review
        messages.info(request, '您已经评价过此订单')
        return redirect('car_rental:my_reviews')
    except CarReview.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = CarReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.rental = rental
            review.user = request.user
            review.car = rental.car
            review.save()
            
            messages.success(request, '感谢您的评价！')
            return redirect('car_rental:my_reviews')
    else:
        form = CarReviewForm()
    
    return render(request, 'car_rental/review_rental.html', {
        'form': form,
        'rental': rental
    })

@login_required
def my_reviews(request):
    """用户评价列表视图"""
    # 获取用户的所有评价
    reviews = CarReview.objects.filter(user=request.user).select_related('car', 'rental')
    
    # 获取可评价的订单（已完成但未评价）
    completed_rentals = Rental.objects.filter(
        user=request.user,
        status='completed'
    ).exclude(
        id__in=CarReview.objects.filter(user=request.user).values_list('rental_id', flat=True)
    )
    
    return render(request, 'car_rental/my_reviews.html', {
        'reviews': reviews,
        'completed_rentals': completed_rentals
    })

# 管理员视图
@staff_member_required
def admin_dashboard(request):
    """管理员控制面板"""
    # 统计数据
    total_cars = Car.objects.count()
    available_cars = Car.objects.filter(status='available').count()
    total_rentals = Rental.objects.count()
    active_rentals = Rental.objects.filter(status__in=['confirmed', 'ongoing']).count()
    total_users = Rental.objects.values('user').distinct().count()
    
    # 最近的订单
    recent_rentals = Rental.objects.order_by('-created_at')[:5]
    
    # 需要维护的车辆
    maintenance_cars = Car.objects.filter(status='maintenance')
    
    context = {
        'total_cars': total_cars,
        'available_cars': available_cars,
        'total_rentals': total_rentals,
        'active_rentals': active_rentals,
        'total_users': total_users,
        'recent_rentals': recent_rentals,
        'maintenance_cars': maintenance_cars,
    }
    
    return render(request, 'car_rental/admin/dashboard.html', context)

@staff_member_required
def admin_cars(request):
    """管理员车辆管理"""
    cars = Car.objects.all().order_by('id')
    
    # 按状态过滤
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        cars = cars.filter(status=status_filter)
    
    # 按类别过滤
    category_filter = request.GET.get('category')
    if category_filter:
        cars = cars.filter(category_id=category_filter)
    
    # 按位置过滤
    location_filter = request.GET.get('location')
    if location_filter:
        cars = cars.filter(location_id=location_filter)
    
    # 分页处理
    paginator = Paginator(cars, 20)  # 每页20辆车
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取所有类别和位置，用于过滤
    categories = CarCategory.objects.all()
    locations = Location.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'locations': locations,
        'status_filter': status_filter or 'all',
        'category_filter': category_filter,
        'location_filter': location_filter,
    }
    
    return render(request, 'car_rental/admin/cars.html', context)

@staff_member_required
def admin_add_car(request):
    """管理员添加车辆"""
    if request.method == 'POST':
        try:
            # 创建新车辆
            car = Car(
                name=request.POST.get('name'),
                brand=request.POST.get('brand'),
                model=request.POST.get('model'),
                year=int(request.POST.get('year')),
                license_plate=request.POST.get('license_plate'),
                category_id=int(request.POST.get('category')),
                location_id=int(request.POST.get('location')),
                seats=int(request.POST.get('seats')),
                transmission=request.POST.get('transmission'),
                fuel_type=request.POST.get('fuel_type'),
                daily_rate=float(request.POST.get('daily_rate')),
                mileage=int(request.POST.get('mileage')),
                status=request.POST.get('status'),
                description=request.POST.get('description'),
                features=request.POST.get('features')
            )
            
            # 处理图片上传
            if 'image' in request.FILES:
                car.image = request.FILES['image']
            
            # 保存车辆
            car.save()
            
            messages.success(request, f'车辆 "{car.name}" 添加成功')
            return redirect('car_rental:admin_cars')
        except Exception as e:
            messages.error(request, f'添加车辆时出错: {str(e)}')
    
    # 准备页面上下文
    categories = CarCategory.objects.all()
    locations = Location.objects.all()
    
    context = {
        'categories': categories,
        'locations': locations,
        'status_choices': Car.CAR_STATUS_CHOICES,
        'transmission_choices': Car.TRANSMISSION_CHOICES,
        'fuel_type_choices': Car.FUEL_TYPE_CHOICES,
    }
    
    return render(request, 'car_rental/admin/add_car.html', context)

@staff_member_required
def admin_edit_car(request, car_id):
    """管理员编辑车辆"""
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == 'POST':
        # 处理表单提交
        try:
            # 获取表单数据
            car.name = request.POST.get('name')
            car.brand = request.POST.get('brand')
            car.model = request.POST.get('model')
            car.year = int(request.POST.get('year'))
            car.license_plate = request.POST.get('license_plate')
            car.category_id = int(request.POST.get('category'))
            car.location_id = int(request.POST.get('location'))
            car.seats = int(request.POST.get('seats'))
            car.transmission = request.POST.get('transmission')
            car.fuel_type = request.POST.get('fuel_type')
            car.daily_rate = float(request.POST.get('daily_rate'))
            car.mileage = int(request.POST.get('mileage'))
            car.status = request.POST.get('status')
            car.description = request.POST.get('description')
            car.features = request.POST.get('features')
            
            # 处理图片上传
            if 'image' in request.FILES:
                car.image = request.FILES['image']
            
            # 保存更改
            car.save()
            
            messages.success(request, f'车辆 "{car.name}" 的信息已成功更新')
            return redirect('car_rental:admin_cars')
        except Exception as e:
            messages.error(request, f'更新车辆信息时出错: {str(e)}')
    
    # 准备页面上下文
    categories = CarCategory.objects.all()
    locations = Location.objects.all()
    
    context = {
        'car': car,
        'categories': categories,
        'locations': locations,
        'status_choices': Car.CAR_STATUS_CHOICES,
        'transmission_choices': Car.TRANSMISSION_CHOICES,
        'fuel_type_choices': Car.FUEL_TYPE_CHOICES,
    }
    
    return render(request, 'car_rental/admin/edit_car.html', context)

@staff_member_required
def toggle_car_status(request, car_id):
    """切换车辆状态（可用/维护中）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '仅支持POST请求'}, status=400)
    
    try:
        car = get_object_or_404(Car, id=car_id)
        
        # 切换状态
        if car.status == 'available':
            car.status = 'maintenance'
            status_message = '维护中'
        else:
            car.status = 'available'
            status_message = '可用'
        
        car.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'车辆状态已更新为{status_message}',
            'new_status': car.status,
            'status_display': car.get_status_display()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'更新车辆状态时出错: {str(e)}'}, status=500)

@staff_member_required
def admin_rentals(request):
    """管理员订单管理"""
    rentals = Rental.objects.all().order_by('-created_at')
    
    # 按状态过滤
    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        rentals = rentals.filter(status=status_filter)
    
    # 按付款状态过滤
    payment_filter = request.GET.get('payment')
    if payment_filter and payment_filter != 'all':
        rentals = rentals.filter(payment_status=payment_filter)
    
    # 按日期范围过滤
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        rentals = rentals.filter(created_at__gte=date_from)
    if date_to:
        rentals = rentals.filter(created_at__lte=date_to)
    
    # 分页处理
    paginator = Paginator(rentals, 20)  # 每页20条订单
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter or 'all',
        'payment_filter': payment_filter or 'all',
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'car_rental/admin/rentals.html', context)

@staff_member_required
def admin_stats(request):
    """管理员统计分析"""
    # 收入统计
    total_revenue = Rental.objects.filter(payment_status='paid').aggregate(Sum('total_price'))
    total_revenue_value = total_revenue['total_price__sum'] or 0
    
    # 车辆数量
    total_cars = Car.objects.count()
    
    # 计算每辆车平均收入
    car_avg_revenue = 0
    if total_cars > 0:
        car_avg_revenue = round(total_revenue_value / total_cars, 2)
    
    # 订单完成率
    total_orders = Rental.objects.count()
    completed_orders = Rental.objects.filter(status='completed').count()
    completion_rate = 0
    if total_orders > 0:
        completion_rate = round((completed_orders / total_orders) * 100, 1)
    
    # 平均租期
    avg_days_result = Rental.objects.filter(status='completed').annotate(
        rental_days=ExpressionWrapper(
            F('end_date') - F('start_date'),
            output_field=DurationField()
        )
    ).aggregate(avg_days=Avg('rental_days'))
    
    avg_rental_days = 0
    if avg_days_result['avg_days']:
        # 转换为天数
        avg_rental_days = round(avg_days_result['avg_days'].total_seconds() / (3600 * 24), 1)
    
    # 车辆类别分布
    categories = CarCategory.objects.all()
    category_stats = []
    
    for category in categories:
        car_count = Car.objects.filter(category=category).count()
        available_count = Car.objects.filter(category=category, status='available').count()
        available_percent = 0
        if car_count > 0:
            available_percent = round((available_count / car_count) * 100)
        
        percentage = 0
        if total_cars > 0:
            percentage = round((car_count / total_cars) * 100)
        
        category_stats.append({
            'name': category.name,
            'car_count': car_count,
            'percentage': percentage,
            'available_percent': available_percent
        })
    
    # 热门车型
    popular_cars_raw = Car.objects.annotate(rental_count=Count('rentals')).order_by('-rental_count')[:10]
    max_rentals = popular_cars_raw.first().rental_count if popular_cars_raw.exists() else 1
    
    popular_cars = []
    for car in popular_cars_raw:
        popularity_percent = round((car.rental_count / max_rentals) * 100) if max_rentals > 0 else 0
        popular_cars.append({
            'id': car.id,
            'brand': car.brand,
            'model': car.model,
            'rental_count': car.rental_count,
            'popularity_percent': popularity_percent
        })
    
    # 热门地点
    locations = Location.objects.all()
    popular_locations = []
    
    for location in locations:
        pickup_count = Rental.objects.filter(pickup_location=location).count()
        return_count = Rental.objects.filter(return_location=location).count()
        car_count = Car.objects.filter(location=location).count()
        total_operations = pickup_count + return_count
        
        # 计算使用率（基于取还车总次数）
        max_operations = 1  # 避免除以零
        if locations.exists():
            max_loc = max(locations, key=lambda x: Rental.objects.filter(Q(pickup_location=x) | Q(return_location=x)).count())
            max_operations = max(Rental.objects.filter(Q(pickup_location=max_loc) | Q(return_location=max_loc)).count(), 1)
        
        usage_percent = round((total_operations / max_operations) * 100) if max_operations > 0 else 0
        
        popular_locations.append({
            'id': location.id,
            'name': location.name,
            'city': location.city,
            'pickup_count': pickup_count,
            'return_count': return_count,
            'car_count': car_count,
            'usage_percent': usage_percent
        })
    
    # 按操作总数排序
    popular_locations.sort(key=lambda x: x['pickup_count'] + x['return_count'], reverse=True)
    popular_locations = popular_locations[:10]  # 取前10个
    
    # 按月统计订单数和收入（最近12个月）
    current_date = timezone.now().date()
    month_stats = []
    
    for i in range(11, -1, -1):
        # 计算月份的开始和结束日期
        month_start = (current_date.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        if i > 0:
            next_month = month_start.replace(month=month_start.month+1) if month_start.month < 12 else month_start.replace(year=month_start.year+1, month=1)
            month_end = next_month - timedelta(days=1)
        else:
            month_end = current_date
        
        # 查询该月的订单
        month_rentals = Rental.objects.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
        month_count = month_rentals.count()
        month_revenue = month_rentals.filter(payment_status='paid').aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        month_stats.append({
            'month': month_start.strftime('%Y-%m'),
            'display_month': month_start.strftime('%m月'),
            'count': month_count,
            'revenue': month_revenue
        })
    
    context = {
        'total_revenue': total_revenue,
        'car_avg_revenue': car_avg_revenue,
        'completion_rate': completion_rate,
        'avg_rental_days': avg_rental_days,
        'category_stats': category_stats,
        'popular_cars': popular_cars,
        'popular_locations': popular_locations,
        'month_stats': month_stats,
        'total_cars': total_cars,
        'total_orders': total_orders,
        'completed_orders': completed_orders
    }
    
    return render(request, 'car_rental/admin/stats.html', context)
