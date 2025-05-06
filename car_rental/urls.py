from django.urls import path
from . import views
from ai_customer_service.views import ai_recommend_cars
from . import admin_views

app_name = 'car_rental'

urlpatterns = [
    # 首页
    path('', views.home, name='home'),
    
    # 车辆相关
    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/search/', views.car_search, name='car_search'),
    path('cars/filter/', views.car_filter, name='car_filter'),
    
    # 位置相关
    path('locations/', views.location_list, name='location_list'),
    path('locations/<int:location_id>/', views.location_detail, name='location_detail'),
    path('locations/search/', views.location_search, name='location_search'),
    
    # 租车相关
    path('rent/<int:car_id>/', views.rent_car, name='rent_car'),
    path('rental/confirm/<int:rental_id>/', views.confirm_rental, name='confirm_rental'),
    path('rental/payment/<int:rental_id>/', views.payment, name='payment'),
    path('rental/success/<uuid:order_id>/', views.rental_success, name='rental_success'),
    
    # 用户订单
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    path('my-rentals/<uuid:order_id>/', views.rental_detail, name='rental_detail'),
    path('rental/cancel/<int:rental_id>/', views.cancel_rental, name='cancel_rental'),
    path('rental/review/<int:rental_id>/', views.review_rental, name='review_rental'),
    
    # 用户评价
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    
    # 取车还车操作
    path('rental/pickup/<int:rental_id>/', views.pickup_car, name='pickup_car'),
    path('rental/return/<int:rental_id>/', views.return_car, name='return_car'),
    
    # AI推荐
    path('ai-recommend/', ai_recommend_cars, name='ai_recommend'),
    
    # 管理员相关
    path('my-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('my-admin/cars/', views.admin_cars, name='admin_cars'),
    path('my-admin/cars/add/', views.admin_add_car, name='admin_add_car'),
    path('my-admin/cars/edit/<int:car_id>/', views.admin_edit_car, name='admin_edit_car'),
    path('my-admin/cars/toggle-status/<int:car_id>/', views.toggle_car_status, name='toggle_car_status'),
    path('my-admin/rentals/', views.admin_rentals, name='admin_rentals'),
    path('my-admin/stats/', views.admin_stats, name='admin_stats'),
    
    # 用户管理
    path('my-admin/users/', admin_views.admin_users, name='admin_users'),
    path('my-admin/users/add/', admin_views.admin_add_user, name='admin_add_user'),
    path('my-admin/users/<int:user_id>/edit/', admin_views.admin_edit_user, name='admin_edit_user'),
    path('my-admin/users/<int:user_id>/toggle_status/', admin_views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('my-admin/users/<int:user_id>/reset_password/', admin_views.admin_reset_user_password, name='admin_reset_user_password'),
] 