import os
import sys
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'car_rental_system.settings')
import django
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from car_rental.models import Location, CarCategory, Car, Rental
from ai_customer_service.models import ChatSession, ChatMessage

def clear_existing_data():
    """清除现有数据"""
    print("清除现有数据...")
    Rental.objects.all().delete()
    Car.objects.all().delete()
    CarCategory.objects.all().delete()
    Location.objects.all().delete()
    ChatMessage.objects.all().delete()
    ChatSession.objects.all().delete()
    UserProfile.objects.filter(user_type='customer').delete()
    User.objects.filter(username__startswith='user').delete()

def create_locations():
    """创建租车网点数据"""
    print("创建租车网点...")
    locations = [
        {
            'name': '市中心店',
            'address': '北京市东城区朝阳门内大街8号',
            'city': '北京',
            'latitude': 39.9145,
            'longitude': 116.4346,
            'phone': '010-66668888',
            'business_hours': '8:00-20:00'
        },
        {
            'name': '西单商圈店',
            'address': '北京市西城区西单北大街120号',
            'city': '北京',
            'latitude': 39.9132,
            'longitude': 116.3737,
            'phone': '010-66669999',
            'business_hours': '9:00-21:00'
        },
        {
            'name': '三里屯店',
            'address': '北京市朝阳区三里屯太古里北区12号',
            'city': '北京',
            'latitude': 39.9344,
            'longitude': 116.4535,
            'phone': '010-66660000',
            'business_hours': '10:00-22:00'
        },
        {
            'name': '浦东机场店',
            'address': '上海市浦东新区浦东国际机场T2航站楼出口处',
            'city': '上海',
            'latitude': 31.1443,
            'longitude': 121.8081,
            'phone': '021-55558888',
            'business_hours': '7:00-23:00'
        },
        {
            'name': '人民广场店',
            'address': '上海市黄浦区人民广场南京路120号',
            'city': '上海',
            'latitude': 31.2304,
            'longitude': 121.4737,
            'phone': '021-55559999',
            'business_hours': '9:00-21:00'
        },
    ]
    
    created_locations = []
    for loc_data in locations:
        location = Location.objects.create(**loc_data)
        created_locations.append(location)
        print(f"- 已创建网点: {location.city} {location.name}")
    
    return created_locations

def create_car_categories():
    """创建车辆类别数据"""
    print("创建车辆类别...")
    categories = [
        {
            'name': '经济型轿车',
            'description': '经济实惠，适合城市通勤和短途旅行的小型轿车，油耗低，操控灵活。'
        },
        {
            'name': '舒适型轿车',
            'description': '中型轿车，提供更为舒适的乘坐体验，适合商务出行和家庭旅行。'
        },
        {
            'name': '豪华型轿车',
            'description': '高端豪华轿车，提供顶级的舒适性和科技配置，适合商务接待和重要场合。'
        },
        {
            'name': '紧凑型SUV',
            'description': '城市SUV，结合了轿车的操控性和SUV的空间，适合城市及周边地区使用。'
        },
        {
            'name': '中大型SUV',
            'description': '强大的动力和宽敞的空间，适合家庭旅行和越野探险。'
        },
        {
            'name': '商务MPV',
            'description': '多功能商务车，拥有灵活的座椅布局和宽敞的内部空间，适合商务接待和家庭出游。'
        },
        {
            'name': '新能源车',
            'description': '包括纯电动、混合动力等环保节能型车辆，适合城市通勤和环保出行。'
        }
    ]
    
    created_categories = []
    for cat_data in categories:
        category = CarCategory.objects.create(**cat_data)
        created_categories.append(category)
        print(f"- 已创建类别: {category.name}")
    
    return created_categories

def create_cars(locations, categories):
    """创建车辆数据"""
    print("创建车辆数据...")
    cars_data = [
        # 经济型轿车
        {
            'name': '大众朗逸',
            'brand': '大众',
            'model': '朗逸',
            'year': 2022,
            'license_plate': '京A12345',
            'category': categories[0],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('249.00'),
            'description': '大众朗逸是一款经济实惠的紧凑型轿车，提供舒适的驾乘体验和出色的燃油经济性。',
            'status': 'available',
            'location': locations[0],
            'mileage': 15000,
            'features': '倒车雷达、蓝牙音响、电动窗、中控锁、ABS防抱死系统'
        },
        {
            'name': '丰田卡罗拉',
            'brand': '丰田',
            'model': '卡罗拉',
            'year': 2021,
            'license_plate': '京B23456',
            'category': categories[0],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('239.00'),
            'description': '丰田卡罗拉以其可靠性和耐用性著称，是一款经济型家用轿车，具有出色的燃油效率。',
            'status': 'available',
            'location': locations[1],
            'mileage': 18000,
            'features': '倒车影像、天窗、自动空调、巡航控制、车身稳定控制系统'
        },
        
        # 舒适型轿车
        {
            'name': '本田雅阁',
            'brand': '本田',
            'model': '雅阁',
            'year': 2023,
            'license_plate': '沪C34567',
            'category': categories[1],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'hybrid',
            'daily_rate': Decimal('399.00'),
            'description': '本田雅阁混合动力版提供卓越的燃油经济性和舒适的驾乘体验，适合长途旅行和商务用途。',
            'status': 'available',
            'location': locations[3],
            'mileage': 8000,
            'features': '全景天窗、真皮座椅、导航系统、无钥匙进入、自适应巡航控制'
        },
        {
            'name': '日产天籁',
            'brand': '日产',
            'model': '天籁',
            'year': 2022,
            'license_plate': '沪D45678',
            'category': categories[1],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('359.00'),
            'description': '日产天籁以其宁静舒适的驾乘环境和高品质的内饰而闻名，是商务出行的理想选择。',
            'status': 'available',
            'location': locations[4],
            'mileage': 12000,
            'features': '零重力座椅、BOSE音响系统、双区自动空调、主动降噪系统、车道偏离警告'
        },
        
        # 豪华型轿车
        {
            'name': '奔驰E级',
            'brand': '奔驰',
            'model': 'E300L',
            'year': 2023,
            'license_plate': '京E56789',
            'category': categories[2],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('899.00'),
            'description': '奔驰E级是豪华行政轿车的典范，提供卓越的舒适性、先进的技术和精致的内饰，适合商务接待和高端场合。',
            'status': 'available',
            'location': locations[2],
            'mileage': 5000,
            'features': '64色氛围灯、COMAND系统、Burmester环绕音响、头部显示、驾驶辅助套装'
        },
        {
            'name': '宝马5系',
            'brand': '宝马',
            'model': '530Li',
            'year': 2022,
            'license_plate': '京F67890',
            'category': categories[2],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('859.00'),
            'description': '宝马5系以其卓越的驾驶动态和豪华内饰著称，是一款兼具运动性能和奢华体验的行政轿车。',
            'status': 'available',
            'location': locations[0],
            'mileage': 7000,
            'features': 'iDrive 7.0系统、哈曼卡顿音响、全液晶仪表盘、手势控制、自动泊车'
        },
        
        # 紧凑型SUV
        {
            'name': '本田CR-V',
            'brand': '本田',
            'model': 'CR-V',
            'year': 2022,
            'license_plate': '沪G78901',
            'category': categories[3],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('359.00'),
            'description': '本田CR-V是一款实用且高效的紧凑型SUV，提供宽敞的内部空间和出色的燃油经济性。',
            'status': 'available',
            'location': locations[3],
            'mileage': 14000,
            'features': '全景天窗、电动尾门、苹果CarPlay、Android Auto、车道保持辅助'
        },
        {
            'name': '丰田RAV4',
            'brand': '丰田',
            'model': 'RAV4',
            'year': 2022,
            'license_plate': '京H89012',
            'category': categories[3],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'hybrid',
            'daily_rate': Decimal('379.00'),
            'description': '丰田RAV4混合动力版提供出色的燃油经济性和灵活性，是城市SUV的理想选择。',
            'status': 'available',
            'location': locations[1],
            'mileage': 11000,
            'features': '全景摄像头、智能驾驶系统、无线充电、JBL音响系统、四驱系统'
        },
        
        # 中大型SUV
        {
            'name': '奥迪Q7',
            'brand': '奥迪',
            'model': 'Q7',
            'year': 2023,
            'license_plate': '京J90123',
            'category': categories[4],
            'seats': 7,
            'transmission': 'auto',
            'fuel_type': 'diesel',
            'daily_rate': Decimal('799.00'),
            'description': '奥迪Q7是一款豪华中大型SUV，提供宽敞的七座布局和高级内饰，适合家庭旅行和商务用途。',
            'status': 'available',
            'location': locations[2],
            'mileage': 9000,
            'features': '四区自动空调、全景天窗、Bang & Olufsen音响、空气悬架、虚拟驾驶舱'
        },
        {
            'name': '宝马X5',
            'brand': '宝马',
            'model': 'X5',
            'year': 2022,
            'license_plate': '沪K01234',
            'category': categories[4],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('859.00'),
            'description': '宝马X5是一款豪华中型SUV，以其动态驾驶体验和高级内饰而著称，适合长途旅行和日常使用。',
            'status': 'available',
            'location': locations[4],
            'mileage': 10000,
            'features': '全液晶仪表盘、智能语音助手、全LED大灯、空气悬架、四驱系统'
        },
        
        # 商务MPV
        {
            'name': '别克GL8',
            'brand': '别克',
            'model': 'GL8',
            'year': 2022,
            'license_plate': '京L12345',
            'category': categories[5],
            'seats': 7,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('599.00'),
            'description': '别克GL8是国内最受欢迎的商务MPV之一，提供宽敞舒适的内部空间和豪华配置，适合商务接待和家庭旅行。',
            'status': 'available',
            'location': locations[0],
            'mileage': 12000,
            'features': '真皮电动座椅、车载冰箱、车载WiFi、环绕音响、自动空调'
        },
        {
            'name': '丰田埃尔法',
            'brand': '丰田',
            'model': '埃尔法',
            'year': 2023,
            'license_plate': '沪M23456',
            'category': categories[5],
            'seats': 7,
            'transmission': 'auto',
            'fuel_type': 'gasoline',
            'daily_rate': Decimal('999.00'),
            'description': '丰田埃尔法是豪华MPV的顶级代表，以其卓越的乘坐舒适性和豪华配置而闻名，是高端商务接待的首选。',
            'status': 'available',
            'location': locations[3],
            'mileage': 6000,
            'features': 'VIP独立座椅、车载电视、四区自动空调、智能语音控制、JBL高级音响'
        },
        
        # 新能源车
        {
            'name': '特斯拉Model 3',
            'brand': '特斯拉',
            'model': 'Model 3',
            'year': 2023,
            'license_plate': '京N34567',
            'category': categories[6],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'electric',
            'daily_rate': Decimal('599.00'),
            'description': '特斯拉Model 3是目前最受欢迎的纯电动车型之一，提供卓越的性能和先进的自动驾驶辅助功能。',
            'status': 'available',
            'location': locations[1],
            'mileage': 5000,
            'features': '15英寸中控屏、自动驾驶辅助、全景玻璃车顶、无钥匙进入、超充网络'
        },
        {
            'name': '比亚迪汉EV',
            'brand': '比亚迪',
            'model': '汉EV',
            'year': 2022,
            'license_plate': '京P45678',
            'category': categories[6],
            'seats': 5,
            'transmission': 'auto',
            'fuel_type': 'electric',
            'daily_rate': Decimal('499.00'),
            'description': '比亚迪汉EV是国产高端纯电动轿车的代表，提供卓越的性能和先进的智能科技配置。',
            'status': 'available',
            'location': locations[2],
            'mileage': 7000,
            'features': '旋转中控屏、DiPilot智能驾驶系统、悬浮式换挡、刀片电池、NFC手机钥匙'
        }
    ]
    
    created_cars = []
    for car_data in cars_data:
        # 创建初始图片路径（在实际项目中需要真实图片）
        # 在这里，我们假设有一个默认的车辆图片
        car = Car(**car_data)
        car.save()  # 先保存以获取ID
        
        # 在此处可以添加真实图片，这里略过
        created_cars.append(car)
        print(f"- 已创建车辆: {car.brand} {car.model}")
    
    return created_cars

def create_users():
    """创建测试用户数据"""
    print("创建测试用户...")
    created_users = []
    
    # 创建5个测试用户
    for i in range(1, 6):
        username = f"user{i}"
        email = f"user{i}@example.com"
        password = "testpassword"
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=f"用户{i}",
                last_name="测试"
            )
            
            # 创建用户资料
            profile = UserProfile.objects.create(
                user=user,
                phone_number=f"1381234{i:04d}",
                address=f"北京市朝阳区测试地址{i}号",
                user_type='customer',
                id_card=f"11010119900101{i:04d}",
                driver_license=f"11010119900101{i:04d}"
            )
            
            created_users.append(user)
            print(f"- 已创建用户: {username}")
        except Exception as e:
            print(f"创建用户 {username} 失败: {e}")
    
    return created_users

def create_rentals(users, cars):
    """创建租车订单数据"""
    print("创建租车订单...")
    
    # 确保有用户和车辆数据
    if not users or not cars:
        print("没有足够的用户或车辆数据来创建订单")
        return []
    
    # 随机选择一些车辆来创建订单（保持一些车辆可用）
    selected_cars = random.sample(cars, min(5, len(cars)))
    
    # 为每个用户创建一些租车记录
    created_rentals = []
    for user in users:
        # 每个用户创建1-2个订单
        num_rentals = random.randint(1, 2)
        for _ in range(num_rentals):
            # 随机选择一辆车
            car = random.choice(cars)
            
            # 随机生成租期（3-7天）
            rental_days = random.randint(3, 7)
            
            # 随机生成开始日期（过去30天内）
            start_date = datetime.now() - timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=rental_days)
            
            # 随机选择取车和还车地点
            pickup_location = car.location
            return_location = pickup_location  # 大多数情况下，取还车地点相同
            
            # 随机分配状态（进行中、已完成、已取消）
            statuses = ['pending', 'confirmed', 'ongoing', 'completed', 'cancelled']
            status_weights = [0.1, 0.2, 0.3, 0.3, 0.1]  # 权重
            status = random.choices(statuses, weights=status_weights, k=1)[0]
            
            # 根据状态设置支付状态
            if status in ['pending']:
                payment_status = 'pending'
            elif status in ['confirmed', 'ongoing', 'completed']:
                payment_status = 'paid'
            else:  # cancelled
                payment_status = random.choice(['pending', 'refunded'])
            
            # 计算总价
            daily_rate = car.daily_rate
            total_price = daily_rate * Decimal(rental_days)
            
            # 创建订单
            try:
                rental = Rental(
                    user=user,
                    car=car,
                    pickup_location=pickup_location,
                    return_location=return_location,
                    start_date=start_date,
                    end_date=end_date,
                    total_price=total_price,
                    status=status,
                    payment_status=payment_status,
                    notes=f"测试订单 - {user.username} 租用 {car.brand} {car.model}",
                    is_ai_assisted=random.choice([True, False])
                )
                rental.save()
                created_rentals.append(rental)
                print(f"- 已创建订单: {rental.order_id} - {user.username} - {car.brand} {car.model}")
            except Exception as e:
                print(f"创建订单失败: {e}")
    
    return created_rentals

def create_chat_data(users):
    """创建AI聊天数据"""
    print("创建AI聊天数据...")
    
    # 确保有用户数据
    if not users:
        print("没有用户数据来创建聊天记录")
        return
    
    for user in users:
        # 为每个用户创建一个聊天会话
        session = ChatSession.objects.create(
            user=user,
            session_id=str(uuid.uuid4()),
            is_active=True
        )
        
        # 创建一些基本的聊天记录
        messages = [
            {'message_type': 'system', 'content': '欢迎使用AI租车助手，请问有什么可以帮助您的？'},
            {'message_type': 'user', 'content': '你好，我需要租一辆车'},
            {'message_type': 'ai', 'content': '您好！很高兴为您服务。请问您需要什么类型的车辆，用于什么场景呢？'},
            {'message_type': 'user', 'content': '我需要一辆SUV，周末带家人出游'},
            {'message_type': 'ai', 'content': '好的，根据您的需求，我推荐您考虑本田CR-V或丰田RAV4，这两款都是非常适合家庭出游的紧凑型SUV，空间宽敞，燃油经济性好。您更倾向于哪种品牌呢？'},
            {'message_type': 'user', 'content': '我更喜欢本田'},
            {'message_type': 'ai', 'content': '本田CR-V是一个很好的选择！它提供宽敞的内部空间、出色的燃油经济性和可靠的性能。我们目前有2022款本田CR-V可供租赁，每天租金为359元。您想了解更多关于这款车的信息，还是希望我帮您安排租车事宜？'},
        ]
        
        # 添加消息到数据库
        for msg_data in messages:
            ChatMessage.objects.create(
                session=session,
                **msg_data
            )
        
        print(f"- 已为用户 {user.username} 创建聊天会话和消息")

def main():
    """主函数"""
    print("开始生成示例数据...")
    
    # 清除现有数据（注意：使用前请确认）
    clear_existing_data()
    
    # 创建位置数据
    locations = create_locations()
    
    # 创建车辆类别
    categories = create_car_categories()
    
    # 创建车辆数据
    cars = create_cars(locations, categories)
    
    # 创建用户数据
    users = create_users()
    
    # 创建租车订单
    rentals = create_rentals(users, cars)
    
    # 创建聊天数据
    create_chat_data(users)
    
    print("\n数据生成完成!")
    print(f"- 创建了 {len(locations)} 个网点")
    print(f"- 创建了 {len(categories)} 个车辆类别")
    print(f"- 创建了 {len(cars)} 辆车")
    print(f"- 创建了 {len(users)} 个用户")
    print(f"- 创建了 {len(rentals)} 个租车订单")

if __name__ == "__main__":
    main() 