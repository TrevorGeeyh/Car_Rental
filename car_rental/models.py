from django.db import models
from django.contrib.auth.models import User
import uuid

class Location(models.Model):
    """车辆网点位置模型"""
    name = models.CharField(max_length=100, verbose_name='网点名称')
    address = models.TextField(verbose_name='详细地址')
    city = models.CharField(max_length=50, verbose_name='城市')
    latitude = models.FloatField(verbose_name='纬度', null=True, blank=True)
    longitude = models.FloatField(verbose_name='经度', null=True, blank=True)
    phone = models.CharField(max_length=15, verbose_name='联系电话')
    business_hours = models.CharField(max_length=100, verbose_name='营业时间', default='8:00-20:00')
    
    def __str__(self):
        return f"{self.city} - {self.name}"
    
    class Meta:
        verbose_name = '租车网点'
        verbose_name_plural = '租车网点'

class CarCategory(models.Model):
    """车辆类别模型"""
    name = models.CharField(max_length=50, verbose_name='类别名称')
    description = models.TextField(verbose_name='类别描述')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '车辆类别'
        verbose_name_plural = '车辆类别'

class Car(models.Model):
    """车辆模型"""
    CAR_STATUS_CHOICES = (
        ('available', '可用'),
        ('rented', '已租出'),
        ('maintenance', '维护中'),
        ('unavailable', '不可用'),
    )
    
    TRANSMISSION_CHOICES = (
        ('auto', '自动'),
        ('manual', '手动'),
    )
    
    FUEL_TYPE_CHOICES = (
        ('gasoline', '汽油'),
        ('diesel', '柴油'),
        ('electric', '电动'),
        ('hybrid', '混合动力'),
    )
    
    name = models.CharField(max_length=100, verbose_name='车辆名称')
    brand = models.CharField(max_length=50, verbose_name='品牌')
    model = models.CharField(max_length=50, verbose_name='型号')
    year = models.IntegerField(verbose_name='年份')
    license_plate = models.CharField(max_length=20, verbose_name='车牌号')
    category = models.ForeignKey(CarCategory, on_delete=models.SET_NULL, null=True, related_name='cars', verbose_name='类别')
    seats = models.IntegerField(verbose_name='座位数')
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES, verbose_name='变速箱')
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES, verbose_name='燃料类型')
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='日租金')
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='押金')
    discount_rate = models.IntegerField(null=True, blank=True, verbose_name='折扣率')
    image = models.ImageField(upload_to='car_images/', verbose_name='车辆图片')
    description = models.TextField(verbose_name='车辆描述')
    status = models.CharField(max_length=15, choices=CAR_STATUS_CHOICES, default='available', verbose_name='状态')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='cars', verbose_name='所在网点')
    mileage = models.IntegerField(verbose_name='里程数', default=0)
    features = models.TextField(verbose_name='特性和配置', blank=True, null=True)
    
    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"
    
    @property
    def is_available(self):
        """判断车辆是否可租赁"""
        return self.status == 'available'
    
    @property
    def availability_count(self):
        """返回该类型车辆的可用数量
        
        注意：此方法是一个简化实现，实际项目中可能需要更复杂的库存管理
        """
        # 获取同品牌同型号的可用车辆数量
        return Car.objects.filter(
            brand=self.brand,
            model=self.model,
            status='available'
        ).count()
    
    class Meta:
        verbose_name = '车辆'
        verbose_name_plural = '车辆'

class Rental(models.Model):
    """租车订单模型"""
    RENTAL_STATUS_CHOICES = (
        ('pending', '待处理'),
        ('confirmed', '已确认'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('refunded', '已退款'),
    )
    
    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='订单编号')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals', verbose_name='用户')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals', verbose_name='车辆')
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='pickup_rentals', verbose_name='取车网点')
    return_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='return_rentals', verbose_name='还车网点')
    start_date = models.DateTimeField(verbose_name='开始日期')
    end_date = models.DateTimeField(verbose_name='结束日期')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总价')
    status = models.CharField(max_length=15, choices=RENTAL_STATUS_CHOICES, default='pending', verbose_name='订单状态')
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='支付状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    is_ai_assisted = models.BooleanField(default=False, verbose_name='AI助手推荐')
    
    def __str__(self):
        return f"订单 {self.order_id} - {self.user.username}"
    
    @property
    def get_status_display_color(self):
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'ongoing': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
        }
        return status_colors.get(self.status, 'secondary')
    
    class Meta:
        verbose_name = '租车订单'
        verbose_name_plural = '租车订单'

class CarReview(models.Model):
    """车辆评价模型"""
    RATING_CHOICES = (
        (1, '1星'),
        (2, '2星'),
        (3, '3星'),
        (4, '4星'),
        (5, '5星'),
    )
    
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='review', verbose_name='关联订单')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='car_reviews', verbose_name='用户')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='reviews', verbose_name='车辆')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name='评分')
    comment = models.TextField(verbose_name='评价内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    def __str__(self):
        return f"{self.user.username}对{self.car.name}的评价"
    
    class Meta:
        verbose_name = '车辆评价'
        verbose_name_plural = '车辆评价'
        ordering = ['-created_at']
