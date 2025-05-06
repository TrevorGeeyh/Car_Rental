from django.contrib import admin
from .models import Car, Location, CarCategory, Rental, CarReview

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'model', 'license_plate', 'category', 'daily_rate', 'status', 'location')
    list_filter = ('status', 'category', 'location', 'transmission', 'fuel_type')
    search_fields = ('name', 'brand', 'model', 'license_plate')
    list_per_page = 20

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address', 'phone', 'business_hours')
    list_filter = ('city',)
    search_fields = ('name', 'city', 'address')

@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'car', 'start_date', 'end_date', 'total_price', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'is_ai_assisted')
    search_fields = ('order_id', 'user__username', 'car__name', 'car__license_plate')
    date_hierarchy = 'created_at'
    list_per_page = 20

@admin.register(CarReview)
class CarReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'car__name', 'car__brand', 'comment')
    date_hierarchy = 'created_at'
    list_per_page = 20
