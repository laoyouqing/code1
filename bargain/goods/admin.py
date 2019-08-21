from django.contrib import admin

# Register your models here.
from goods.models import User, Goods, GoodImage, BargainRecord, OrderGoods, Activity

admin.site.register(User)
admin.site.register(Goods)
admin.site.register(GoodImage)
admin.site.register(BargainRecord)
admin.site.register(OrderGoods)
admin.site.register(Activity)
