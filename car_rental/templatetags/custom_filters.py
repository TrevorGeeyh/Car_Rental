from django import template

register = template.Library()

@register.filter
def get_item(obj, key):
    """
    获取对象中的项目，支持字典和列表
    用法：{{ mydict|get_item:key }} 或 {{ mylist|get_item:index }}
    """
    if isinstance(obj, dict):
        return obj.get(key, 0)  # 字典获取
    elif isinstance(obj, (list, tuple)) and isinstance(key, int):
        try:
            return obj[key]  # 列表获取
        except IndexError:
            return None
    return None

@register.filter
def split(value, arg):
    """
    将字符串按指定分隔符分割成列表
    用法：{{ value|split:'分隔符' }}
    """
    return value.split(arg) 

@register.filter
def subtract(value, arg):
    """
    减法运算
    用法：{{ value|subtract:arg }}
    """
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, arg):
    """
    计算百分比
    用法：{{ value|percentage:arg }}
    """
    try:
        if float(arg) == 0:
            return 0
        return round((float(value) / float(arg)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def absolute(value):
    """
    取绝对值
    用法：{{ value|absolute }}
    """
    try:
        return abs(value)
    except (ValueError, TypeError):
        return 0 