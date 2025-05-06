from django import forms
from django.utils import timezone
from .models import Rental, Car, Location, CarCategory, CarReview

class CarSearchForm(forms.Form):
    """车辆搜索表单"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜索车辆（品牌、型号、特性等）',
        })
    )

class CarFilterForm(forms.Form):
    """车辆过滤表单"""
    category = forms.ModelChoiceField(
        queryset=CarCategory.objects.all(),
        required=False,
        empty_label="所有类别",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label="所有位置",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '最低价格',
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '最高价格',
        })
    )
    
    seats = forms.ChoiceField(
        choices=[('', '所有座位数')] + [(i, f"{i}座") for i in range(2, 9)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    transmission = forms.ChoiceField(
        choices=[('', '所有变速箱类型')] + list(Car.TRANSMISSION_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fuel_type = forms.ChoiceField(
        choices=[('', '所有燃料类型')] + list(Car.FUEL_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super(CarFilterForm, self).__init__(*args, **kwargs)
        self.fields['category'].label = "车辆类别"
        self.fields['location'].label = "取车位置"
        self.fields['min_price'].label = "最低价格"
        self.fields['max_price'].label = "最高价格"
        self.fields['seats'].label = "座位数"
        self.fields['transmission'].label = "变速箱"
        self.fields['fuel_type'].label = "燃料类型"

class RentalForm(forms.ModelForm):
    """租车表单"""
    class Meta:
        model = Rental
        fields = ['pickup_location', 'return_location', 'start_date', 'end_date', 'notes']
        widgets = {
            'pickup_location': forms.Select(attrs={'class': 'form-select'}),
            'return_location': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '如有特殊要求，请在此备注'
            }),
        }
        labels = {
            'pickup_location': '取车网点',
            'return_location': '还车网点',
            'start_date': '取车时间',
            'end_date': '还车时间',
            'notes': '备注',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # 打印调试信息
        print(f"后端接收到的取车时间: {start_date}")
        print(f"后端接收到的还车时间: {end_date}")
        
        # 验证日期
        if start_date and end_date:
            # 结束日期不能早于开始日期
            if end_date < start_date:
                self.add_error('end_date', '还车时间不能早于取车时间')
            
            # 租期不能超过30天
            if (end_date - start_date).days > 30:
                self.add_error('end_date', '租车时间不能超过30天')
        
        return cleaned_data

class AdminCarForm(forms.ModelForm):
    """管理员车辆表单"""
    class Meta:
        model = Car
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control'}),
            'transmission': forms.Select(attrs={'class': 'form-select'}),
            'fuel_type': forms.Select(attrs={'class': 'form-select'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CarReviewForm(forms.ModelForm):
    """车辆评价表单"""
    class Meta:
        model = CarReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '请分享您的用车体验...'
            }),
        }
        labels = {
            'rating': '评分',
            'comment': '评价内容',
        }
        help_texts = {
            'rating': '请为本次租车体验打分',
            'comment': '请详细描述您的用车体验，包括车况、服务等方面',
        } 