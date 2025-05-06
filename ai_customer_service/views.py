from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json
import uuid
from .models import ChatSession, ChatMessage, AIRecommendation
from car_rental.models import Car, Location
import logging
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db.models import Q
import re

@login_required
def chat_interface(request):
    """AI客服聊天界面视图"""
    # 获取或创建用户的聊天会话
    try:
        session = ChatSession.objects.filter(user=request.user, is_active=True).latest('created_at')
    except ChatSession.DoesNotExist:
        session_id = str(uuid.uuid4())
        session = ChatSession.objects.create(
            user=request.user,
            session_id=session_id,
            is_active=True
        )
    
    # 获取当前会话的消息历史，仅加载最近的10条消息
    messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:10]
    messages = reversed(list(messages))  # 反转顺序以便按时间顺序显示
    
    # 获取当前时间
    current_time = timezone.now()
    
    context = {
        'session': session,
        'messages': messages,
        'current_time': current_time
    }
    
    return render(request, 'ai_customer_service/chat_interface.html', context)

@csrf_exempt
def send_message(request):
    """
    处理用户发送的消息并返回AI回复
    支持处理两种类型的AI响应：普通文本回复和车辆推荐回复
    """
    import json
    import logging
    
    # 设置日志记录器
    logger = logging.getLogger(__name__)
    
    try:
        # 解析请求数据
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        # 验证输入
        if not message:
            return JsonResponse({
                'status': 'error',
                'type': 'text',
                'content': '消息不能为空',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        
        if not session_id:
            return JsonResponse({
                'status': 'error',
                'type': 'text',
                'content': '会话ID不能为空',
                'timestamp': timezone.now().isoformat()
            }, status=400)
        
        # 获取当前用户
        user = request.user
        
        # 获取或创建聊天会话
        try:
            session = ChatSession.objects.get(session_id=session_id)
            
            # 更新会话最后活动时间
            session.updated_at = timezone.now()
            session.save()
            
        except ChatSession.DoesNotExist:
            # 如果会话不存在，为用户创建新会话
            if user.is_authenticated:
                session_id = str(uuid.uuid4())
                session = ChatSession.objects.create(
                    user=user,
                    session_id=session_id,
                    is_active=True
                )
            else:
                return JsonResponse({
                    'status': 'error',
                    'type': 'text',
                    'content': '无效的会话ID',
                    'timestamp': timezone.now().isoformat()
                }, status=400)
        
        # 记录用户消息
        user_message = ChatMessage.objects.create(
            session=session,
            message_type='user',
            content=message
        )
        
        logger.info(f"用户[{user.username if user.is_authenticated else '游客'}]发送消息: {message[:50]}...")
        
        # 获取AI回复
        try:
            ai_response = get_ai_response(message, user, session)
            current_time = timezone.now().isoformat()
            
            # 根据响应类型构造不同的返回数据
            if ai_response.get('type') == 'car_recommendation':
                # 车辆推荐类型的响应
                return JsonResponse({
                    'status': 'success',
                    'type': 'car_recommendation',
                    'content': ai_response.get('content', ''),
                    'cars': ai_response.get('cars', []),
                    'timestamp': current_time,
                    'session_id': str(session.session_id)
                })
            else:
                # 普通文本类型的响应
                return JsonResponse({
                    'status': 'success',
                    'type': 'text',
                    'content': ai_response.get('content', ''),
                    'timestamp': current_time,
                    'session_id': str(session.session_id)
                })
                
        except Exception as e:
            logger.exception(f"获取AI回复时出错: {str(e)}")
            
            # 创建一个错误消息回复
            error_content = "很抱歉，我在处理您的请求时遇到了问题。请稍后再试或联系客服400-123-4567获取帮助。"
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=error_content
            )
            
            return JsonResponse({
                'status': 'error',
                'type': 'text',
                'content': error_content,
                'timestamp': timezone.now().isoformat(),
                'session_id': str(session.session_id)
            })
            
    except json.JSONDecodeError:
        logger.error("JSON解析错误")
        return JsonResponse({
            'status': 'error',
            'type': 'text',
            'content': '无效的请求格式',
            'timestamp': timezone.now().isoformat()
        }, status=400)
        
    except Exception as e:
        logger.exception(f"处理消息时发生未预期的错误: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'type': 'text',
            'content': '服务器内部错误',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@login_required
def get_chat_history(request, session_id):
    """获取聊天历史记录的API视图"""
    session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
    messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    message_list = []
    for message in messages:
        message_data = {
            'id': message.id,
            'type': message.message_type,
            'content': message.content,
            'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        message_list.append(message_data)
    
    return JsonResponse({'messages': message_list})

@login_required
def start_chat_session(request):
    """开始新的聊天会话的API视图"""
    if request.method == 'POST':
        # 将用户现有的活跃会话设为非活跃
        ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        # 创建新的会话
        session_id = str(uuid.uuid4())
        session = ChatSession.objects.create(
            user=request.user,
            session_id=session_id,
            is_active=True
        )
        
        # 创建一个欢迎消息
        ChatMessage.objects.create(
            session=session,
            message_type='system',
            content='新的对话已开始'
        )
        
        # 是AJAX请求时返回JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'session_id': session.session_id
            })
        
        # 非AJAX请求时重定向回聊天页面
        return redirect('ai_customer_service:chat_interface')
    
    return JsonResponse({'error': '请求方法不支持'}, status=405)

@login_required
def rent_recommended_car(request, car_id):
    """处理AI推荐的租车操作"""
    car = get_object_or_404(Car, id=car_id)
    
    # 重定向到租车表单页面，并标记为AI推荐
    return redirect('car_rental:rent_car', car_id=car.id)

@login_required
def ai_recommend_cars(request):
    """显示AI推荐的车辆列表"""
    # 获取基础车辆集合
    cars = Car.objects.filter(status='available')
    
    # 获取筛选参数
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    car_type = request.GET.get('car_type')
    sort_by = request.GET.get('sort_by', 'recommended')  # 默认按推荐度排序
    
    # 应用筛选条件
    if price_min:
        cars = cars.filter(daily_rate__gte=float(price_min))
    if price_max:
        cars = cars.filter(daily_rate__lte=float(price_max))
    if car_type:
        cars = cars.filter(category__name=car_type)
    
    # 获取浏览历史数据（如有）
    source_car_id = request.GET.get('source_car_id')
    source_car = None
    if source_car_id:
        try:
            source_car = Car.objects.get(id=source_car_id)
        except Car.DoesNotExist:
            pass
    
    # 应用排序
    if sort_by == 'price_asc':
        cars = cars.order_by('daily_rate')
    elif sort_by == 'price_desc':
        cars = cars.order_by('-daily_rate')
    elif sort_by == 'newest':
        cars = cars.order_by('-year')
    else:  # 默认推荐排序，基于一些智能条件
        # 如果有源车辆，优先推荐同类车辆
        if source_car:
            # 首先获取同品牌同类型的车辆
            same_brand_category = cars.filter(brand=source_car.brand, category=source_car.category)
            # 然后获取同类型不同品牌的车辆
            same_category = cars.filter(category=source_car.category).exclude(brand=source_car.brand)
            # 然后获取价格相近的车辆（±20%）
            price_range_min = source_car.daily_rate * 0.8
            price_range_max = source_car.daily_rate * 1.2
            similar_price = cars.filter(daily_rate__gte=price_range_min, daily_rate__lte=price_range_max)
            # 最后获取其他推荐车辆
            other_cars = cars.exclude(id__in=same_brand_category.values_list('id', flat=True))\
                             .exclude(id__in=same_category.values_list('id', flat=True))\
                             .exclude(id__in=similar_price.values_list('id', flat=True))
            
            # 合并结果
            cars = list(same_brand_category) + list(same_category) + list(similar_price) + list(other_cars)
            # 去重
            seen = set()
            unique_cars = []
            for car in cars:
                if car.id not in seen:
                    seen.add(car.id)
                    unique_cars.append(car)
            cars = unique_cars[:12]  # 限制推荐数量
        else:
            # 如果没有源车辆，使用基本排序规则
            cars = cars.order_by('?')[:12]  # 随机排序并限制数量
    
    # 构建上下文
    categories = set(car.category for car in Car.objects.all())
    
    context = {
        'recommended_cars': cars,
        'categories': categories,
        'source_car': source_car,
        'price_min': price_min,
        'price_max': price_max,
        'car_type': car_type,
        'sort_by': sort_by,
        'is_filtered': any([price_min, price_max, car_type, sort_by != 'recommended']),
    }
    
    # 如果是从特定车辆推荐的，记录推荐
    if source_car and request.user.is_authenticated:
        try:
            # 获取或创建用户的聊天会话
            session = ChatSession.objects.filter(user=request.user, is_active=True).latest('created_at')
        except ChatSession.DoesNotExist:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(
                user=request.user,
                session_id=session_id,
                is_active=True
            )
        
        # 创建系统消息记录这次推荐
        system_message = ChatMessage.objects.create(
            session=session,
            message_type='system',
            content=f"系统基于您浏览的{source_car.brand} {source_car.model}，为您推荐了类似车型"
        )
        
        # 创建推荐记录
        recommendation = AIRecommendation.objects.create(
            chat_message=system_message,
            recommendation_text=f"基于{source_car.brand} {source_car.model}的推荐"
        )
        for car in cars[:5]:  # 只记录前5个推荐
            recommendation.cars.add(car)
    
    return render(request, 'ai_customer_service/ai_recommend.html', context)

# 辅助函数
def get_ai_response(user_message, user, session):
    """生成AI回复的函数，使用DeepSeek API处理用户输入，带有重试机制和更稳定的本地回复"""
    import requests
    from django.conf import settings
    import re
    import time
    
    # 设置日志记录
    logger = logging.getLogger(__name__)
    
    # 使用settings中的API密钥
    api_key = settings.DEEPSEEK_API_KEY
    
    # 检测是否包含车辆查询关键词
    car_query_patterns = [
        r'推荐.*车',
        r'有什么.*车',
        r'需要.*车',
        r'查.*车',
        r'租.*车',
        r'想.*租',
        r'suv|轿车|跑车|商务车',
        r'品牌|丰田|本田|大众|宝马|奔驰|奥迪',
        r'预算.*元',
        r'\d+天.*\d+',
        r'\d+.{0,5}预算'
    ]
    
    is_car_query = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in car_query_patterns)
    
    # 本地回复函数，用于API失败时提供回复
    def get_local_response(query, query_type='general', cars=None):
        """根据查询类型和内容生成本地回复"""
        if query_type == 'car':
            if cars and cars.exists():
                car_names = ", ".join([f"{car.brand} {car.model}" for car in cars])
                return f"根据您的需求，我为您推荐以下几款车型: {car_names}。这些车型各有特点，可以满足您不同的用车需求。您可以点击查看详情了解更多信息。"
            else:
                return "很抱歉，目前没有找到符合您需求的车辆。您可以尝试调整需求或浏览我们的全部车型。"
        
        # 一般性查询的本地回复
        if '预算' in query or '价格' in query or '多少钱' in query:
            return "我们的租车价格取决于车型、租期和季节因素。经济型轿车通常在200-400元/天，SUV在300-600元/天，豪华车型则在600元以上/天。长租会有额外优惠。您可以在车辆详情页查看准确价格，也可以告诉我您的预算范围，我可以为您推荐合适的车型。"
        elif '取车' in query or '证件' in query or '需要带' in query:
            return "取车时需要携带：1. 本人身份证原件；2. 本人驾驶证原件；3. 用于支付押金的信用卡。外籍人士还需要提供护照和国际驾照。所有证件必须在有效期内。如有疑问，可以致电客服400-123-4567咨询。"
        elif '订单' in query or '查询' in query or '我的' in query:
            return "您可以在'我的订单'页面查看所有租车记录，包括当前订单和历史订单。每个订单都有详细的租车信息和状态。您也可以通过订单编号或手机号在线查询订单状态。需要我帮您查询具体订单吗？"
        elif '押金' in query or '保证金' in query or '退款' in query:
            return "车辆归还并完成检查后，系统会自动发起押金退还流程。信用卡预授权通常3-15个工作日内解除，具体取决于发卡行。如果超过时间未收到退款，请联系客服400-123-4567处理。"
        elif '保险' in query or '责任' in query or '理赔' in query:
            return "我们提供基础保险（车辆损失险和第三者责任险）和可选的附加保险（全车盗抢险、玻璃单独破碎险、自燃损失险等）。建议根据您的需求选择合适的保险组合，以获得更全面的保障。详细保险条款可在租车时查看。"
        else:
            return f"感谢您的咨询。您询问的是关于'{query}'的问题，我会尽力为您提供帮助。请问您能提供更多具体细节吗？这样我可以更准确地回答您的问题或提供相关建议。您也可以直接浏览我们的车辆列表，或者拨打客服热线400-123-4567获取更多帮助。"
    
    # 调用API的函数，带有重试机制
    def call_api_with_retry(endpoint, headers, json_data, max_retries=2, timeout=15):
        """带有重试机制的API调用函数"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=json_data,
                    timeout=timeout  # 增加超时时间
                )
                return response
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                logger.warning(f"API调用超时或连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    # 指数退避策略 (1秒, 2秒, ...)
                    time.sleep(attempt + 1)
                    continue
                else:
                    logger.error(f"API调用重试  次数已用完: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"API调用时发生未预期错误: {str(e)}")
                raise
    
    # 车辆查询处理
    if is_car_query:
        # 解析用户消息中的关键信息
        location_query = None
        price_min = None
        price_max = None
        car_type = None
        days = None
        
        # 复合匹配模式 - 同时包含城市、天数和预算
        compound_pattern = r'(北京|上海|广州|深圳|成都|重庆|杭州|南京|武汉|西安|天津|苏州|郑州|长沙|沈阳|青岛|宁波|厦门|福州|无锡|济南|合肥|哈尔滨)[^\d]*(\d+)天[^\d]*(\d+)'
        compound_match = re.search(compound_pattern, user_message)
        if compound_match:
            location_query = compound_match.group(1)
            days = int(compound_match.group(2))
            price_val = int(compound_match.group(3))
            
            # 假设价格是总预算或每日预算的判断
            if price_val > 1000:  # 如果价格大于1000，可能是总预算
                total_budget = price_val
                if days > 0:
                    price_max = total_budget / days  # 计算每日最大预算
                else:
                    price_max = total_budget
            else:  # 否则可能是每日预算
                price_max = price_val
        else:
            # 如果没有找到复合匹配，再尝试单独的匹配
            # 城市和地点匹配
            location_patterns = [
                r'(北京|上海|广州|深圳|成都|重庆|杭州|南京|武汉|西安|天津|苏州|郑州|长沙|沈阳|青岛|宁波|厦门|福州|无锡|济南|合肥|哈尔滨)',
                r'在(\w+)租车',
                r'(\w+)地区',
                r'(\w+)取车'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, user_message)
                if match:
                    location_query = match.group(1)
                    break
            
            # 价格范围匹配
            price_patterns = [
                r'预算(\d+)元',
                r'(\d+)元预算',
                r'(\d+)预算',
                r'预算(\d+)',
                r'(\d+)元左右',
                r'(\d+)元以内',
                r'不超过(\d+)元',
                r'(\d+)-(\d+)元'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, user_message)
                if match:
                    if len(match.groups()) == 1:
                        price_max = int(match.group(1))
                    elif len(match.groups()) == 2:
                        price_min = int(match.group(1))
                        price_max = int(match.group(2))
                    break
                    
            # 租期匹配（天数）
            days_patterns = [
                r'(\d+)天',
                r'(\d+)日',
                r'租(\d+)[天日]'
            ]
            
            # 尝试匹配日期，用于构建更个性化的回复
            for pattern in days_patterns:
                match = re.search(pattern, user_message)
                if match:
                    days = int(match.group(1))
                    break
        
        # 车型类型匹配
        car_type_patterns = {
            'SUV': r'suv|越野车|休旅车',
            '轿车': r'轿车|三厢车|家用车',
            '跑车': r'跑车|豪华|超跑',
            '商务车': r'商务车|mpv|商务|面包车',
            '经济型': r'经济型|省油|实惠'
        }
        
        for car_category, pattern in car_type_patterns.items():
            if re.search(pattern, user_message.lower()):
                car_type = car_category
                break
        
        # 构建查询条件
        filter_conditions = Q(status='available')
        
        if location_query:
            # 查询匹配地点的车辆
            location_filter = Q(location__city__icontains=location_query) | Q(location__name__icontains=location_query)
            filter_conditions &= location_filter
        
        if price_min is not None:
            filter_conditions &= Q(daily_rate__gte=price_min)
        
        if price_max is not None:
            filter_conditions &= Q(daily_rate__lte=price_max)
        
        if car_type:
            filter_conditions &= Q(category__name__icontains=car_type)
        
        # 查询符合条件的车辆
        available_cars = Car.objects.filter(filter_conditions).order_by('?')[:3]
        
        # 如果没有找到车辆，放宽条件再试一次
        if not available_cars.exists() and (location_query or price_min or price_max or car_type):
            less_strict_conditions = Q(status='available')
            
            # 如果指定了城市但没有找到车，尝试只根据价格或车型查询
            if location_query and (price_min or price_max or car_type):
                if price_min is not None:
                    less_strict_conditions &= Q(daily_rate__gte=price_min)
                
                if price_max is not None:
                    less_strict_conditions &= Q(daily_rate__lte=price_max)
                
                if car_type:
                    less_strict_conditions &= Q(category__name__icontains=car_type)
                
                available_cars = Car.objects.filter(less_strict_conditions).order_by('?')[:3]
        
        if available_cars.exists():
            # 构建车辆推荐信息
            car_infos = []
            for car in available_cars:
                car_infos.append({
                    'id': car.id,
                    'brand': car.brand,
                    'model': car.model,
                    'category': car.category.name if car.category else '未分类',
                    'price': float(car.daily_rate),
                    'seats': car.seats,
                    'transmission': car.get_transmission_display(),
                    'image_url': car.image.url if car.image and hasattr(car.image, 'url') else None,
                })
            
            # 尝试使用DeepSeek API生成推荐文本
            try:
                # 准备提示词
                system_prompt = "你是一个专业的汽车租赁顾问，负责根据客户需求推荐合适的车型。请提供专业、友好且有针对性的建议。"
                
                # 构建用户查询的详细描述，包括地点、价格、天数
                query_description = []
                if location_query:
                    query_description.append(f"地点：{location_query}")
                if price_min:
                    query_description.append(f"最低价格：{price_min}元/天")
                if price_max:
                    query_description.append(f"最高价格：{price_max}元/天")
                if days:
                    query_description.append(f"租期：{days}天")
                if car_type:
                    query_description.append(f"车型：{car_type}")
                
                query_details = "，".join(query_description) if query_description else "无特定要求"
                
                user_prompt = f"""客户询问: "{user_message}"
                
                客户需求: {query_details}
                
                可供推荐的车辆:
                {', '.join([f"{car['brand']} {car['model']} ({car['category']}, {car['seats']}座, {car['price']}元/天)" for car in car_infos])}
                
                请根据客户询问推荐最合适的车型，简要说明推荐理由。如果客户指定了天数，请计算总费用并说明。回复应该友好专业，不超过120字。"""
                
                logger.info(f"发送DeepSeek API请求: {user_prompt[:100]}...")
                
                # 调用DeepSeek API (带重试)
                response = call_api_with_retry(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json_data={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 200
                    }
                )
                
                # 解析API响应
                if response.status_code == 200:
                    api_response = response.json()
                    ai_content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"DeepSeek API响应成功: {ai_content[:50]}...")
                else:
                    # API调用失败，使用本地回复
                    logger.error(f"DeepSeek API响应错误: {response.status_code}, {response.text[:200]}")
                    ai_content = get_local_response(user_message, 'car', available_cars)
            except Exception as e:
                logger.exception(f"DeepSeek API调用异常: {str(e)}")
                ai_content = get_local_response(user_message, 'car', available_cars)
                
            # 保存AI回复到数据库
            ai_chat_message = ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=ai_content
            )
            
            # 创建推荐记录
            recommendation = AIRecommendation.objects.create(
                chat_message=ai_chat_message,
                recommendation_text=f"为{user.username}推荐车辆"
            )
            
            # 添加推荐的车辆
            for car in available_cars:
                recommendation.cars.add(car)
            
            # 返回带有车辆卡片的回复
            return {
                'type': 'car_recommendation',
                'content': ai_content,
                'cars': [
                    {
                        'id': car.id,
                        'brand': car.brand,
                        'model': car.model,
                        'image_url': car.image.url if car.image and hasattr(car.image, 'url') else None,
                        'daily_rate': float(car.daily_rate),
                        'category': car.category.name if car.category else '未分类',
                        'seats': car.seats,
                        'transmission': car.get_transmission_display(),
                        'location_name': f"{car.location.city} {car.location.name}" if car.location else None,
                        'location_id': car.location.id if car.location else None
                    } 
                    for car in available_cars
                ],
            }
        else:
            # 如果没有可用车辆，返回普通文本响应
            content = "很抱歉，目前没有可用的车辆符合您的要求。请您调整筛选条件或稍后再试。您也可以联系我们的客服400-123-4567获取更多帮助。"
            ChatMessage.objects.create(
                session=session,
                message_type='ai',
                content=content
            )
            return {
                'type': 'text',
                'content': content
            }
    
    # 对于非车辆查询或无车可推荐的情况，尝试使用DeepSeek API生成普通回复
    try:
        # 获取最近的几条对话历史，帮助AI理解上下文
        recent_messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:6]
        chat_history = []
        
        # 反转消息列表，使其按时间顺序排列
        for msg in reversed(list(recent_messages)):
            if msg.message_type == 'system':
                continue  # 忽略系统消息，减少token使用
            role = "user" if msg.message_type == "user" else "assistant"
            chat_history.append({"role": role, "content": msg.content})
        
        # 添加当前用户消息
        chat_history.append({"role": "user", "content": user_message})
        
        # 系统提示词
        system_prompt = """你是智能租车系统的AI客服助手，名为"租车智能助手"。你的主要工作是帮助用户解决租车过程中的各种问题。
        
        你可以:
        1. 根据用户需求推荐合适的车型
        2. 解答租车流程、费用、政策相关问题
        3. 提供个性化的用车建议
        4. 协助处理订单和查询
        
        请使用友好、专业的语气，回答简洁明了。如果无法确定用户的具体需求，请礼貌地询问更多细节。"""
        
        logger.info(f"发送普通查询给DeepSeek API: {user_message[:100]}...")
        
        # 调用DeepSeek API (带重试)
        try:
            response = call_api_with_retry(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json_data={
                    "model": "deepseek-chat",
                    "messages": [{"role": "system", "content": system_prompt}] + chat_history,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=20  # 普通查询给更长的超时时间
            )
            
            # 解析API响应
            if response.status_code == 200:
                api_response = response.json()
                content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.info(f"DeepSeek API普通回复成功: {content[:50]}...")
            else:
                # API调用失败，使用本地回复
                logger.error(f"DeepSeek API普通回复错误: {response.status_code}, {response.text[:200]}")
                content = get_local_response(user_message)
        except Exception as e:
            logger.exception(f"调用DeepSeek API出错: {str(e)}")
            content = get_local_response(user_message)
    except Exception as e:
        logger.exception(f"处理普通回复时出错: {str(e)}")
        content = get_local_response(user_message)
    
    # 创建AI回复
    ChatMessage.objects.create(
        session=session,
        message_type='ai',
        content=content
    )
    
    return {
        'type': 'text',
        'content': content
    }

@login_required
def clear_chat_history(request):
    """清除当前会话的聊天记录"""
    if request.method == 'POST':
        try:
            session_id = request.POST.get('session_id')
            # 验证会话是否属于当前用户
            session = get_object_or_404(ChatSession, session_id=session_id, user=request.user)
            
            # 删除会话的所有消息
            ChatMessage.objects.filter(session=session).delete()
            
            # 创建一个系统消息表示已清除历史
            ChatMessage.objects.create(
                session=session,
                message_type='system',
                content='聊天记录已清除'
            )
            
            # 不使用Django消息框架
            # messages.success(request, '聊天记录已成功清除')
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f'清除聊天记录时出错: {str(e)}')
            # 不使用Django消息框架
            # messages.error(request, f'清除聊天记录时出错: {str(e)}')
        
        return redirect('ai_customer_service:chat_interface')
    
    # 如果不是POST请求，重定向到聊天界面
    return redirect('ai_customer_service:chat_interface')
