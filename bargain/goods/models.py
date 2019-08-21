from django.contrib.auth.models import AbstractUser
from django.db import models
from tinymce.models import HTMLField
# Create your models here.

class User(AbstractUser):
    '''
    用户模型类
    '''
    name = models.CharField(max_length=1000,verbose_name='用户名')
    photo=models.CharField(max_length=1000,verbose_name='头像')
    openid=models.CharField(max_length=100,verbose_name='微信openid')
    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name



class Goods(models.Model):
    '''商品模型类'''

    status_choices = (
        (0, '去砍价'),
        (1, '已结束'),
        (2, '下架')
    )
    name = models.CharField(max_length=50, verbose_name='商品名称')
    desc = models.CharField(max_length=256, verbose_name='商品简介')
    # 富文本类型：
    detail = HTMLField()
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    lowest_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品最低砍至价格')
    image = models.CharField(max_length=1000, verbose_name='商品图片')
    stock = models.IntegerField(default=1, verbose_name='商品总量')
    sales = models.IntegerField(default=0, verbose_name='商品销量')
    status = models.SmallIntegerField(default=0, choices=status_choices, verbose_name='商品状态')
    part_num = models.IntegerField(default=1, verbose_name='参与人数')
    deadline=models.DateTimeField(verbose_name='截止时间')
    activity=HTMLField()
    activity_rules=models.ForeignKey('Activity',on_delete=models.SET_NULL,verbose_name='活动',null=True,blank=True)
    goods_code=models.CharField(max_length=1000,verbose_name='商品二维码',null=True,blank=True)
    command_str=models.CharField(max_length=32,verbose_name='核销口令',help_text='核销口令',null=True,blank=True)
    # total_num=models.IntegerField(default=30,verbose_name='可砍刀数',help_text='可砍刀数')



    class Meta:
        db_table = 'df_goods'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodImage(models.Model):
    '''商品图片模型类'''
    goods = models.ForeignKey('Goods', verbose_name='商品',on_delete=models.CASCADE)
    image = models.CharField(max_length=1000,verbose_name='图片路径')

    class Meta:
        db_table = 'df_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class BargainRecord(models.Model):
    '''纪录'''

    user = models.ForeignKey('User', verbose_name='砍价好友', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='砍价价格')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='砍价时间')
    order = models.ForeignKey('OrderGoods', verbose_name='订单',on_delete=models.CASCADE)


    class Meta:
        db_table = 'df_bargain_record'
        verbose_name = '纪录'
        verbose_name_plural = verbose_name



class OrderGoods(models.Model):
    '''订单商品模型类'''

    status_choices = (
        (0, '砍价中'),
        (1, '已完成'),
        (2, '已结束'),
        (3, '已支付'),
        (4, '已核销')
    )
    order = models.CharField(max_length=100,verbose_name='订单')
    status = models.SmallIntegerField(default=0, choices=status_choices, verbose_name='状态')
    goods = models.ForeignKey('Goods', verbose_name='商品',on_delete=models.CASCADE)
    user = models.ForeignKey('User', verbose_name='用户', on_delete=models.CASCADE)
    # total_num = models.IntegerField(default=30,verbose_name='可砍刀数', help_text='可砍刀数')

    class Meta:
        db_table = 'df_order_goods'
        verbose_name = '订单商品'
        verbose_name_plural = verbose_name


class Activity(models.Model):
    activity_id = models.CharField(max_length=64,verbose_name="活动商品id")
    activity_desc=models.CharField(max_length=300,verbose_name='活动规则')


    def __str__(self):
        return self.activity_desc