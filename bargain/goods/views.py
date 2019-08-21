import base64
import datetime
import hashlib
import os
import random
import string
from hashlib import md5

import emoji
from django.db.models import Sum, Count
import time

from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status, filters, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from bargain import settings
from bargain.settings import MEDIA_URL, APPSECRET, APPID
from goods.models import Goods, GoodImage, OrderGoods, User, BargainRecord, Activity
from goods.serializers import GoodsSerialize, GoodsDetailSerialize, CreateUserSerializer, \
    OrderSerializer, RecordSerializer, ShareSerialize, ExchangeListSerializer, GoodsAdminSerializer, \
    GoodImageAdminSerializer, BargainRecordSerializer, OrderGoodsSerializer, UserSerializer, OrderGoods1Serializer, \
    UploadImageSerializer, GargainImageSerialize, ActivitySerializer, Goods1AdminSerializer
from utils.pay import Alipay_Access
from utils.wx import get_jsapi_ticket, get_accesstoken


class GoodsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_size_query_description = '每页返回条目数, 不传默认返回10条, 最大返回数50'
    page_query_param = 'page'
    page_query_description = '页码'
    max_page_size = 50


class RegisterView(mixins.CreateModelMixin,viewsets.GenericViewSet):
    '''注册'''
    serializer_class = CreateUserSerializer


class Login(APIView):
    def post(self,request):
        openid=request.data.get('openid')
        if not openid:
            return Response({'msg': '缺少openid'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(openid=openid)
        except:
            return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        ser=CreateUserSerializer(instance=user,many=False)
        return Response(ser.data)


class GargainActivity(mixins.ListModelMixin,viewsets.GenericViewSet):
    '''砍价活动'''
    queryset = Goods.objects.filter(status=0)
    serializer_class = GoodsSerialize
    pagination_class = GoodsPagination


class GargainImage(APIView):
    '''详情页图片'''

    def get(self, request, id):
        images = GoodImage.objects.filter(goods_id=id)
        ser=GargainImageSerialize(images,many=True)

        return Response(ser.data)


class GargainDetail(mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    '''详情页信息'''

    queryset = Goods.objects.all()
    serializer_class = GoodsDetailSerialize


    def retrieve(self, request, pk):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        dict = {}
        oid = request._request.GET.get('order_id')
        if not oid:
            return Response({'msg': '缺少order_id'}, status=status.HTTP_400_BAD_REQUEST)


        order = OrderGoods.objects.filter(id=oid,goods_id = pk).first()
        if order:
            user = order.user
            name = user.name
            #转换成emoji表情
            username = emoji.emojize(name)
            #砍价总人数
            total = order.bargainrecord_set.aggregate(Count('user'))
            #已砍价格
            price = order.bargainrecord_set.aggregate(Sum('price'))
            #亲友团砍价纪录
            records = order.bargainrecord_set.all()
            records=RecordSerializer(instance=records,many=True)
            dict['username'] = username
            dict['photo'] = user.photo
            dict['total'] = total
            dict['price'] = price
            dict['status']=order.status
            dict['goodinfo']=serializer.data
            dict['records'] = records.data
        else:
            return Response({'msg':'参数错误订单不存在'},status=status.HTTP_400_BAD_REQUEST)

        return Response(dict, status=status.HTTP_200_OK)


class OrderViewSet(mixins.CreateModelMixin,viewsets.GenericViewSet):
    '''生成订单'''
    serializer_class = OrderSerializer


class SharePoster(mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    '''分享海报'''
    serializer_class = ShareSerialize
    queryset = Goods.objects.all()

    def retrieve(self, request, *args, **kwargs):
        dict={}
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        uid = request._request.GET.get('user_id')
        if not uid:
            return Response({'msg': '缺少user_id'}, status=status.HTTP_400_BAD_REQUEST)

        user=User.objects.get(id=uid)
        name = user.name
        username = emoji.emojize(name)
        dict['goodinfo']=serializer.data
        dict['username']=username
        dict['photo']=user.photo
        return Response(dict)


class FriendsBargain(GenericViewSet):
    '''好友砍价'''
    serializer_class = ShareSerialize
    def retrieve(self,request):
        dict={}
        oid = request._request.GET.get('order_id')
        uid = request._request.GET.get('user_id')
        if not (uid or oid):
            return Response({'msg': '缺少user_id or order_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = OrderGoods.objects.get(id=oid)
        except Exception as msg:
            dict['msg']='参数错误'
            return Response(dict,status=status.HTTP_400_BAD_REQUEST)
        else:
            # 对正在砍价中的订单判断剩余时间，更新订单状态
            if order.status==0:
                deadline = order.goods.deadline
                deadline = deadline.strftime("%Y-%m-%d %H:%M:%S")
                curr_time = datetime.datetime.now()
                otherStyleTime = curr_time.strftime("%Y-%m-%d %H:%M:%S")
                if otherStyleTime > deadline:
                    order.status = 2
                    order.save()
            #是否使用户自己
            dict['isself'] = False
            old_id=order.user_id
            if int(old_id)==int(uid):
                dict['isself']=True
            is_user=BargainRecord.objects.filter(order=order,user_id=uid)
            if len(is_user)==0:
                #是否已砍过
                dict['is_cut']=False
            else:
                dict['is_cut']=True
            goods = order.goods
            ser = self.get_serializer(goods)
            user = order.user
            name=user.name
            username=emoji.emojize(name)
            # 已砍
            has_price = order.bargainrecord_set.aggregate(Sum('price'))
            print(has_price)

            # 剩余
            if has_price['price__sum']==None:
                residue_price = goods.price - goods.lowest_price
            else:
                residue_price = goods.price - goods.lowest_price - has_price['price__sum']

            # if residue_price < 0:
            #     residue_price=0
            #     has_price['price__sum']=goods.price - goods.lowest_price
            #     print(has_price)
            dict['goodinfo'] = ser.data
            dict['username'] = username
            dict['status']=order.status
            dict['has_price'] = has_price
            dict['residue_price'] = residue_price
            return Response(dict, status=status.HTTP_200_OK)



class HelpBargain(GenericViewSet):
    '''砍价策略'''
    serializer_class = ShareSerialize
    def retrieve(self,request):
        dict = {}
        oid = request._request.GET.get('order_id')
        uid = request._request.GET.get('user_id')

        if not (uid or oid):
            return Response({'msg': '缺少user_id or order_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order = OrderGoods.objects.get(id=oid)
        except Exception as msg:
            dict['msg'] = '参数错误'
            return Response(dict, status=status.HTTP_400_BAD_REQUEST)
        goods = order.goods
        price = goods.price
        lowest_price = goods.lowest_price
        #已砍价格
        has_cut=BargainRecord.objects.filter(order_id=oid).aggregate(Sum('price'))
        if has_cut['price__sum'] == None:
            residue_price =  price - lowest_price
        else:
            residue_price = price - lowest_price - has_cut['price__sum']

        total_cut=price - lowest_price
        after_percent=residue_price/total_cut

        if after_percent>0.4:
            max = float((price * 13) / 100)
            min = float(price / 13)
            kprice = ('%.2f' % (random.uniform(min, max)))
            BargainRecord.objects.create(user_id=uid, price=kprice, order_id=order.id)
        elif after_percent>0.1 and after_percent<0.4:
            max = float((price * 7) / 100)
            min = float((price * 5) / 100)
            kprice = ('%.2f' % (random.uniform(min, max)))
            BargainRecord.objects.create(user_id=uid, price=kprice, order_id=order.id)
        elif after_percent>0 and after_percent<0.1:
            max = float((price * 5) / 100)
            min = float((price * 3) / 100)
            # kprice = ('%.2f' % random.uniform(0.1,0.2))
            kprice = float('%.2f' % (random.uniform(min, max)))
            #判断砍得价格是不是大于剩余可砍价
            if kprice>residue_price:
                kprice=residue_price
            BargainRecord.objects.create(user_id=uid, price=kprice, order_id=order.id)
        else:
            ser = self.get_serializer(goods)
            return Response(ser.data,status=status.HTTP_200_OK)

        has_price = order.bargainrecord_set.aggregate(Sum('price'))
        # 剩余
        residue_price = price - lowest_price - has_price['price__sum']
        #如果剩余可砍价格为0，更新订单，库存状态
        if residue_price==0:
            if lowest_price == 0:
                order.status = 3
            else:
                order.status = 1
            order.save()
            goods = order.goods
            goods.sales -= 1
            goods.save()

        ser=self.get_serializer(goods)
        dict['goodinfo'] = ser.data
        dict['has_price'] = has_price
        dict['residue_price'] = residue_price
        return Response(dict, status=status.HTTP_200_OK)



class MyBargain(GenericViewSet):
    '''我的砍价'''
    serializer_class = GoodsSerialize
    pagination_class = GoodsPagination

    def retrieve(self,request):
        list=[]
        uid = request._request.GET.get('user_id')
        if not uid:
            return Response({'msg': '缺少user_id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user=User.objects.get(id=uid)
            pg=GoodsPagination()
            orders=user.ordergoods_set.all()
            orders=pg.paginate_queryset(queryset=orders,request=request,view=self)
            for order in orders:
                dict = {}
                goods=order.goods
                has_price = order.bargainrecord_set.aggregate(Sum('price'))
                residue_price = goods.price - has_price['price__sum']
                ser=self.get_serializer(goods)
                dict['order_id']=order.id
                dict['status']=order.status
                dict['goodinfo']=ser.data
                dict['residue_price']=residue_price
                list.append(dict)
            return pg.get_paginated_response(list)
        except:
            return Response({'msg':'用户不存在'},status=status.HTTP_400_BAD_REQUEST)



class ExchangeView(GenericViewSet):
    '''卡券核销'''
    serializer_class = ShareSerialize

    def retrieve(self,request):
        dict = {}
        oid = request._request.GET.get('order_id')
        if not oid:
            return Response({'msg': '缺少order_id'}, status=status.HTTP_400_BAD_REQUEST)
        order = OrderGoods.objects.filter(id=oid,status=3)
        if order:
            goods=order[0].goods
            serializer = self.get_serializer(goods)

            dict['goodsinfo']=serializer.data
            dict['residue_price']=goods.lowest_price
            dict['order_id']=oid
        else:
            dict['msg'] = '该订单未完成'
            return Response(dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(dict)



class ExchangeDetail(GenericViewSet):
    '''核销跳转'''
    serializer_class = ShareSerialize

    def retrieve(self, request):
        dict = {}
        oid = request._request.GET.get('order_id')
        if not oid:
            return Response({'msg': '缺少order_id'}, status=status.HTTP_400_BAD_REQUEST)
        str='asvghyk'
        order = OrderGoods.objects.filter(id=oid, status=3)
        if order:
            goods = order[0].goods
            serializer = self.get_serializer(goods)
            dict['goodsinfo'] = serializer.data
            dict['order_id'] = oid
            dict['str']=str
        else:
            dict['msg'] = '该订单未完成'
            return Response(dict, status=status.HTTP_400_BAD_REQUEST)
        return Response(dict)




class ShowShareView(GenericViewSet):
    '''分享'''
    serializer_class = ShareSerialize

    def retrieve(self, request):
        oid = request.query_params.get('order_id')
        if not oid:
            return Response({'msg': '缺少order_id'}, status=status.HTTP_400_BAD_REQUEST)
        order=OrderGoods.objects.get(id=oid)
        goods=order.goods
        serializer = self.get_serializer(goods)
        nonceStr = ''.join(random.sample(string.ascii_letters, 32))
        url = 'http://' + request.get_host() + request.get_full_path()
        timestrip = int(time.time())
        ticket = get_jsapi_ticket(get_accesstoken(APPID, APPSECRET))
        strs = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (ticket, nonceStr, timestrip, url)
        shaa1 = hashlib.sha1()
        shaa1.update(strs.encode('utf-8'))
        signature = shaa1.hexdigest()
        dict={}
        dict['appid'] = APPID
        dict['signature'] = signature
        dict['timestrip'] = timestrip
        dict['nonceStr'] = nonceStr
        dict['goodsinfo'] = serializer.data

        return Response(dict)



class HasExchange(APIView):
    '''已核销'''

    def put(self, request, id):
        str=request.data.get('str')
        order=OrderGoods.objects.get(id=id)
        print(str)
        if str==order.goods.command_str:
            order.status=4
            order.save()
            return Response({'msg':'兑换成功'})
        else:
            return Response({'msg':'兑换失败'})


class ExchangeList(mixins.ListModelMixin,viewsets.GenericViewSet):
    '''卡券核销列表'''

    serializer_class = ExchangeListSerializer

    def get_queryset(self):
        uid=self.request.query_params.get('user_id')
        return OrderGoods.objects.filter(user_id=uid,status=3)




class GoodsAdminView(viewsets.ModelViewSet):
    '''商品后台'''
    serializer_class = GoodsAdminSerializer
    queryset = Goods.objects.all()
    filter_backends = (filters.SearchFilter,)
    search_fields=('name',)
    pagination_class = GoodsPagination  # 指定自定义分页类

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return Goods1AdminSerializer
        else:
            return GoodsAdminSerializer



class GoodImageAdminView(viewsets.ModelViewSet):
    '''商品图片后台'''
    serializer_class = GoodImageAdminSerializer
    queryset = GoodImage.objects.all()
    pagination_class = GoodsPagination  # 指定自定义分页类
    filter_backends = (filters.SearchFilter,)
    search_fields = ('goods__name',)

    def create(self, request, *args, **kwargs):
        image=request._request.POST.get('image')
        id=request._request.POST.get('goods')
        images=image.split(',')
        if not (image or id):
            return Response({'msg': '缺少image or id'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            good=Goods.objects.get(id=id)
        except:
            return Response({'msg':'商品不存在'},status=status.HTTP_400_BAD_REQUEST)
        else:
            for image in images:
                GoodImage.objects.create(goods=good,image=image)
        return Response({'msg':'添加成功'},status=status.HTTP_201_CREATED)




class BargainRecordAdminView(viewsets.ModelViewSet):
    '''砍价纪录后台'''

    serializer_class = BargainRecordSerializer
    queryset = BargainRecord.objects.all()
    pagination_class = GoodsPagination  # 指定自定义分页类



class OrderGoodsAdminView(viewsets.ModelViewSet):
    '''订单后台'''

    queryset = OrderGoods.objects.all()
    pagination_class = GoodsPagination  # 指定自定义分页类
    filter_backends = (filters.SearchFilter,DjangoFilterBackend)
    search_fields = ('goods__name',)
    filter_fields = ('status',)

    def get_serializer_class(self):
        if self.action=='create':
            return OrderGoodsSerializer
        else:
            return OrderGoods1Serializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        has_price=instance.bargainrecord_set.aggregate(Sum('price'))
        dict=serializer.data
        dict.update({'has_price':has_price})
        return Response(dict)

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)
    #     li=[]
    #     if page is not None:
    #         for quer in page:
    #             has_price = quer.bargainrecord_set.aggregate(Sum('price'))
    #             serializer = self.get_serializer(quer, many=False)
    #             dict = serializer.data
    #             dict.update({'has_price': has_price})
    #             li.append(dict)
    #         return self.get_paginated_response(li)
    #     for quer in queryset:
    #         has_price = quer.bargainrecord_set.aggregate(Sum('price'))
    #         serializer = self.get_serializer(quer, many=False)
    #         dict = serializer.data
    #         dict.update({'has_price': has_price})
    #         li.append(dict)
    #     return Response(li)



class UserAdminView(viewsets.ModelViewSet):
    '''用户后台'''
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = GoodsPagination  # 指定自定义分页类



class ActivityAdminView(viewsets.ModelViewSet):
    '''活动'''
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()
    pagination_class = GoodsPagination  # 指定自定义分页类



class UploadImage(generics.GenericAPIView):
    '''图片上传'''
    serializer_class = UploadImageSerializer

    def post(self,request):
        image = request._request.POST.get('image')
        #base64分割
        image = image.split('base64,')[1]
        #base64解码
        imagefile=base64.b64decode(image)
        now=time.time()
        fname = '%s/goods/%s.jpg' % (settings.MEDIA_ROOT, now)
        with open(fname, 'wb') as pic:
            pic.write(imagefile)
        url = 'http://' + self.request.get_host()+  MEDIA_URL + 'goods/' + str(now)+'.jpg'
        return Response(url)




class Pay(APIView):
    '''支付'''

    def get(self,request):
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response({'msg':'请输入订单号 order_id'},status=status.HTTP_400_BAD_REQUEST)
        return_url = request.query_params.get('return_url')
        if not return_url:
            return Response({'msg':'请输入支付成功回调地址 return_url'},status=status.HTTP_400_BAD_REQUEST)
        quit_url = request.query_params.get('quit_url')
        if not quit_url:
            return Response({'msg':'请输入支付中断回调地址 quit_url'},status=status.HTTP_400_BAD_REQUEST)

        instance = OrderGoods.objects.filter(id=order_id).first()

        if not instance:
            return Response({'msg':'没有此订单号'},status=status.HTTP_400_BAD_REQUEST)

        price = instance.goods.lowest_price
        user = instance.user
        if not user:
            return Response({'msg':'没有此用户'},status=status.HTTP_400_BAD_REQUEST)
        center_back_url = ''
        center_back_msg = ''
        expir_time = int(time.time()) + 5
        while not center_back_url and not center_back_msg and expir_time > int(time.time()):
            center_back_url, center_back_msg = Alipay_Access(order_id, user.openid, price, return_url, quit_url)

        if center_back_url:

            return Response(center_back_url,status=status.HTTP_200_OK)
        else:
            return Response(center_back_msg,status=status.HTTP_200_OK)



