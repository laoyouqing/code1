import base64
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import time
from urllib.parse import urlencode

import django
import emoji
import requests
from PIL import Image
from django.core.cache import cache
from django.http import HttpResponse

from bargain import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bargain.settings')
django.setup()


# 手机号码正则表达式
REGEX_MOBILE = r'^1[3589]\d{9}$|^147\d{8}$|^176\d{8}$'

# 邮箱正则表达式
REGEX_MAIL = r'^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$'



def getRandomList(size=40, total=200, big_num=5, random_range=20):
    """
    获取一个随机的数组
    :param size: 数组大小
    :param total: 数据总和
    :param big_num: 大数数量
    :param random_range: 随机范围
    :return: list
    """
    import random
    # 随机数数组
    r_list = []
    # 返回数组
    ret_list = []
    # 获取size个随机数
    for i in range(big_num):
        num = random.randint(random_range*3, random_range*4)
        r_list.append(num)
    for i in range(size - big_num):
        num = random.randint(1, random_range)
        r_list.append(num)
    # 求和
    num_sum = sum(r_list)
    # 生成要返回的列表
    for index,num in enumerate(r_list[:]):
        if len(ret_list) < size - 1:
            ret_list.append(round(round(num / num_sum, 4) * 100 * total, 2))
        # 最后一个数单独计算
        else:
            ret_list.append(total*100 - sum(ret_list))
    ret_list = [int(i)/100 for i in ret_list]
    # 调试
    print(ret_list, sum(ret_list), len(ret_list))
    cache.set('order', ret_list)
    print(cache.get('order'))
    a=cache.get('order')
    return ret_list


def get_accesstoken(appid,secret):
    '''获取微信分享access_token'''
    if cache.get(appid):
        return cache.get(appid)
    else:
        req = requests.get('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'%(appid,secret))
        print(req.text)
        token = json.loads(req.text)['access_token']
        cache.set(appid,token,7000)
        return token

def get_jsapi_ticket(access_token):
    '''获取微信ticket'''
    if cache.get(access_token):
        return cache.get(access_token)
    else:
        req = requests.get('https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi'%(access_token))
        ticket = json.loads(req.text)['ticket']
        cache.set(access_token,ticket,7000)
        return ticket



def compress_img(path,high_path='',width=1376):
    '''图片压缩'''

    img=Image.open(path)
    w,h=img.size
    if not os.path.exists(high_path):
        shutil.copy(path,high_path)
    if w>width:
        new_img = img.resize((width, math.floor(h * width / w)), Image.ANTIALIAS)
        new_img.save(path,quality=95)



def del_file(path, file_name, roll=True):
    """
    删除指定路径下的所有该名称的文件
    :param path: 文件夹路径
    :param file_name: 要删除的文件名称
    :return:
    """
    try:
        file_path = os.path.join(path, file_name)
        os.remove(file_path)
    except Exception as e:
        print('-' * 5, '删除文件出错：', e)
    if roll:
        for file in os.listdir(path):
            try:
                file_path = os.path.join(path, file)
                if os.path.isdir(file_path):
                    del_file(file_path, file_name)
            except Exception as e:
                print('-' * 5, '删除文件出错：', e)



def validate_mobile(self, mobile):
    """自定义验证手机号码"""

    # 是否合法
    if not re.match(REGEX_MOBILE, mobile):
        # raise serializers.ValidationError("手机号码非法")
        return False
    return True


def validate_email(email):
    """
    验证邮箱的合法性
    """
    if not re.match(REGEX_MAIL, email): ret = False
    return True

def getWeekDate(type='day', default_date=None):
    """
    获取指定日期
    :param type: 类别
    :return:
    """
    if not default_date:
        now = datetime.datetime.now()
    else:
        now = default_date
    _year = now.year
    if type == 'mouth':
        start_mouth_list = ['%d-%d-1' % (_year, i) for i in range(1, 13)]
        end_mouth_list = ['%d-%d-1' % (_year, i) for i in range(2, 13)] + ['%d-1-1' % (_year+1)]
        mouth_list = zip(start_mouth_list, end_mouth_list)
        return mouth_list

    # 周
    # w_start = now - timedelta(days=now.weekday())  # 本周第一天
    # w_end = now + timedelta(days=6 - now.weekday())  # 本周最后一天

    day_list = []
    start_day_list = []
    end_day_list = []

    for i in range(now.weekday(), -1, -1):
        star_time = now - datetime.timedelta(days=i)
        end_time = now - datetime.timedelta(days=i-1)
        start_day_list.append(star_time.strftime('%Y-%m-%d'))  # 追加日期
        end_day_list.append(end_time.strftime('%Y-%m-%d'))  # 追加日期

    return zip(start_day_list, end_day_list)



def upload_image(request,image):
    '''图片上传'''
    #base64解密
    image = image.split('base64,')[1]
    imagefile=base64.b64decode(image)
    now=time.time()
    fname = '%s/goods/%s.jpg' % (settings.MEDIA_ROOT, now)
    with open(fname, 'wb') as pic:
        pic.write(imagefile)
    url = 'http://' + request.META['HTTP_HOST']+  settings.MEDIA_URL + 'goods/' + str(now)+'.jpg'
    return url



def upload_video(request,video):
    '''上传视频'''
    fname = '%s/video/%s' % (settings.MEDIA_ROOT, video.name)
    with open(fname, 'wb') as pic:
        for c in video.chunks():
            pic.write(c)

    url = 'http://' + request.get_host() + settings.MEDIA_URL + 'video/' + video.name
    return url



# 授权
class WxOAuth(object):
    '''微信认证辅助工具类'''

    def __init__(self):
        self.appid = ''
        self.secret = ''

    def get_access_token(self,code):
        '''获取授权access_token'''
        req=requests.get('https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code' % (self.appid, self.secret,code))
        access_token = json.loads(req.text)['access_token']
        openid = json.loads(req.text)['openid']
        if not (access_token or openid):
            raise Exception
        return (access_token,openid)

    def flush_access_token(self,refresh_token):
        '''刷新access_token'''
        req = requests.get('https://api.weixin.qq.com/sns/oauth2/refresh_token?appid=%s&grant_type=refresh_token&refresh_token=%s' % (self.appid, refresh_token))
        access_token = json.loads(req.text)['access_token']
        openid = json.loads(req.text)['openid']
        if not (access_token or openid):
            raise Exception
        return (access_token, openid)


    def get_user_info(self,access_token,openid):
        '''获取用户信息'''
        req = requests.get('https://api.weixin.qq.com/sns/userinfo?access_token=%s&openid=%s&lang=zh_CN ' % (access_token, openid))
        req=json.loads(req.content.decode('utf8'))

        openid = req.get('openid')
        nickname = req.get('nickname')
        headimgurl = req.get('headimgurl')
        sex = req.get('sex')
        if not (nickname or openid or headimgurl):
            raise Exception
        return (openid, nickname, headimgurl, sex)


class YunPian(object):
    '''发送短信'''
    def __init__(self):
        self.secret_key = 'a6d6e990-273b-5fad-a0c1-7845ef1cde5b'
        self.single_send_url = "http://47.112.126.133:8004/push/"
        self.template_code= 'SMS_125020249'

    def send_sms(self, code, mobile):
        # 需要传递的参数
        params = {
            "secret_key": self.secret_key,
            "mobile": mobile,
            "msg": code,
            'template_code':self.template_code
        }
        response = requests.post(self.single_send_url, data=params)
        re_dict = json.loads(response.text)
        return re_dict



def md5s(str_param):
    m=hashlib.md5()
    m.update(str_param.encode('utf8'))
    return m.hexdigest()

def shas(str_param):
    m=hashlib.sha1()
    m.update(str_param.encode('utf8'))
    return m.hexdigest()


def Alipay_Access(order_id,openid,price,return_url,quit_url):
    '''支付接口'''
    params={
        'paymentType':'rz_wx_wap',
        'signType':'MD5',
        'timeStamp':str(int(time.time())),
        'nonce_str':'1',
        'rzAppId':'',      #appid
        'subject':'test1',
        'body':order_id,
        'out_trade_no':order_id,
        'total_amount':str(int(float(price)*100)),
        'notify_url':'',     #支付成功通知地址
        'return_url':return_url,    #支付成功回调地址
        'quit_url':quit_url,        #支付中断退出地址
        'openid':openid,    #openid
        'client_ip':'',
        'currency':'CNY',
        'secret':''       #秘钥
    }
    str_param=urlencode(params).lower()

    sign=md5s(str_param)
    str_param+='sign='+sign

    URLstr = 'http://pay.ie1e.com/api/RzExternalApiCenter/callPayApi'
    r = requests.post(URLstr, data=str_param,headers={'Content-Type':'application/x-www-form-urlencoded'})
    rep=json.loads(r.content.decode(encoding='utf-8'))

    if rep.get('code')==10000:
        coenter_back_msg=rep.get('message')
        center_back_url=rep.get('data')
    elif rep.get('code')==-1:
        coenter_back_msg = rep.get('message')
        center_back_url = rep.get('data')
    else:
        coenter_back_msg = None
        center_back_url = None

    return center_back_url,coenter_back_msg


class PaymentCenterRuiZ(object):
    """支付中心支付成功后的中台访问接口"""

    def __init__(self):
        self.secret=''     #秘钥

    def post(self,request):
        #copy数据，对除了签名sign以外的方法进行签名验证
        data=request.data.copy()
        del data['sign']
        str_data = urlencode(data).lower()
        #验签数据
        presign=self.secret+str_data
        #订单id
        order_id=request.POST.get('OrderId')
        if data.get('signType')=='MD5':
            sign=md5s(presign)
            sign=sign.upper()
            if sign==data.get('sign'):
                #校验成功
                # 对订单进行逻辑操作
                return HttpResponse('SUCCESS')
            else:
                return HttpResponse('Fail\n' + order_id + '支付校验失败')
        else:
            return HttpResponse('Fail\n' + order_id + '不支持MD5校验')



name=':candy:m'
name_emoji=emoji.emojize(name)  #转成emoji表情
name=emoji.demojize(name_emoji)    #转成字符串


if __name__ == '__main__':
    getRandomList()
    # print(__name__)