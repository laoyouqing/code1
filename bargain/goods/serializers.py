import datetime
import random
import time
import emoji
from rest_framework import serializers

from bargain import settings
from goods.models import Goods, GoodImage, User, OrderGoods, BargainRecord, Activity


class CreateUserSerializer(serializers.ModelSerializer):
    '''注册'''
    class Meta:
        model = User
        fields = ('id','name', 'photo','openid')

    def create(self, validated_data):

        validated_data['name']=emoji.demojize(validated_data['name'])

        validated_data['username']=str(time.time())+str(random.random())

        user = super(CreateUserSerializer, self).create(validated_data)
        return user


class GoodsSerialize(serializers.ModelSerializer):
    '''商品砍价活动'''
    deadline=serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Goods
        fields = ('id', 'name', 'stock','sales','price','lowest_price','image','part_num','deadline','activity_rules')
        depth=1


    def to_representation(self, instance):
        instance = super(GoodsSerialize, self).to_representation(instance)
        curr_time = datetime.datetime.now()
        otherStyleTime = curr_time.strftime("%Y-%m-%d %H:%M:%S")
        deadline=instance['deadline']
        id=instance['id']
        if otherStyleTime > deadline:
            goods=Goods.objects.get(id=id)
            orders=goods.ordergoods_set.all()
            for order in orders:
                order.status=2
                order.save()
            goods.status = 1
            goods.save()
        return instance


class GoodsDetailSerialize(serializers.ModelSerializer):
    '''详情页商品信息'''

    deadline = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = Goods
        fields = ( 'id', 'name', 'price','lowest_price','sales','deadline','detail','activity','activity_rules','image')
        depth=1

    def to_representation(self, instance):
        instance = super(GoodsDetailSerialize, self).to_representation(instance)
        curr_time = datetime.datetime.now()
        otherStyleTime = curr_time.strftime("%Y-%m-%d %H:%M:%S")
        deadline = instance['deadline']
        id = instance['id']
        if otherStyleTime > deadline:
            goods = Goods.objects.get(id=id)
            goods.status = 1
            goods.save()
        return instance





class GargainImageSerialize(serializers.ModelSerializer):
    '''轮播图图片'''
    class Meta:
        model = GoodImage
        fields = ('image','id')


class OrderSerializer(serializers.ModelSerializer):
    '''订单'''
    order=serializers.CharField(read_only=True)
    goods_id=serializers.CharField(allow_blank=False,error_messages={'blank': "商品id不能为空"})
    user_id=serializers.CharField(allow_blank=False,error_messages={'blank': "用户id不能为空"})

    class Meta:
        model = OrderGoods
        fields=('id','order','goods_id','user_id')

    def create(self, validated_data):
        # 订单id
        gid=validated_data['goods_id']
        uid=validated_data['user_id']
        order_id = datetime.datetime.today().strftime('%Y%m%d%H%M%S') + str(uid)
        try:
            order=OrderGoods.objects.get(goods_id=gid, user_id=uid)
        except:
            #创建订单
            order=OrderGoods.objects.create(order=order_id, goods_id=gid, user_id=uid)
            goods=Goods.objects.get(id=gid)
            #参与人数
            goods.part_num+=1
            goods.save()
        return order


class RecordSerializer(serializers.ModelSerializer):
    '''纪录详情'''
    create_time=serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")
    username=serializers.CharField(source='user.name')
    photo=serializers.CharField(source='user.photo')
    class Meta:
        model = BargainRecord
        fields='__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        username = emoji.emojize(data['username'])
        data['username'] = username
        return data



class ShareSerialize(serializers.ModelSerializer):
    '''分享海报'''
    deadline = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Goods
        fields = ( 'id', 'name', 'desc','image','sales','price','lowest_price','deadline','goods_code')


class ExchangeListSerializer(serializers.ModelSerializer):
    '''卡券核销列表'''
    name=serializers.CharField(source='goods.name')
    price=serializers.DecimalField(source='goods.price',max_digits=10, decimal_places=2)
    lowest_price=serializers.DecimalField(source='goods.lowest_price',max_digits=10, decimal_places=2)
    image=serializers.CharField(source='goods.image')

    class Meta:
        model = OrderGoods
        fields=('id','name','price','lowest_price','image')



class ActivitySerializer(serializers.ModelSerializer):
    '''活动'''

    class Meta:
        model = Activity
        fields = '__all__'

# 管理界面接口
class GoodsAdminSerializer(serializers.ModelSerializer):
    '''商品'''
    detail=serializers.CharField(required=False,allow_blank=True)
    deadline = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = Goods
        fields = '__all__'


class Goods1AdminSerializer(serializers.ModelSerializer):
    '''商品'''
    detail=serializers.CharField(required=False,allow_blank=True)
    deadline = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = Goods
        fields = '__all__'
        depth=1


class GoodImageAdminSerializer(serializers.ModelSerializer):
    '''商品图片'''
    name = serializers.CharField(source='goods.name',read_only=True)
    class Meta:
        model = GoodImage
        fields = ('id','name','goods','image')





class BargainRecordSerializer(serializers.ModelSerializer):
    '''砍价纪录'''

    class Meta:
        model = BargainRecord
        fields = '__all__'



class OrderGoodsSerializer(serializers.ModelSerializer):
    '''订单'''

    class Meta:
        model = OrderGoods
        fields = '__all__'


class GoodsAdminSerializer2(serializers.ModelSerializer):
    '''商品'''
    # detail=serializers.CharField(required=False,allow_blank=True)
    # deadline = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model = Goods
        # fields = '__all__'
        fields=('id','name','price','lowest_price')


class OrderGoods1Serializer(serializers.ModelSerializer):
    '''订单'''
    goods=GoodsAdminSerializer2()
    user=serializers.CharField(source='user.name')
    user_id=serializers.CharField(source='user.id')

    class Meta:
        model = OrderGoods
        fields = ('id','order','status','goods','user','user_id')


class UserSerializer(serializers.ModelSerializer):
    '''用户'''

    class Meta:
        model = User
        fields = '__all__'




class UploadImageSerializer(serializers.Serializer):

    image=serializers.ImageField()


