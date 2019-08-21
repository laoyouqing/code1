import time
import hashlib
import json

import requests
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from goods.models import OrderGoods


def Alipay_Access(GoodsNo,openid,GoodsFreight,return_url,quit_url):
    """ 支付接口 """

    # print(quit_url)
    param = {}
    param['paymentType'] = 'rz_wx_wap'
    param['signType'] = 'MD5'
    # param['timeStamp'] = '11231321321' # str(time.time())
    param['timeStamp'] = str(int(time.time()))
    param['nonce_str'] = '1'
    param['rzAppId'] = '20190710144426414598'
    # param['rzAppId'] = 'wxc49613664351bece'
    param['subject'] = 'test1'
    param['body'] = GoodsNo
    param['out_trade_no'] = GoodsNo
    param['total_amount'] = str(int(float(GoodsFreight)*100))
    from bargain.settings import server_ip, server_port
    # param['notify_url'] = server_ip + server_port +'/goods/pay_suc/'     # 支付成功通知地址
    param['notify_url'] = 'http://47.112.126.133:8003/pay_suc/'     # 支付成功通知地址
    print(param['notify_url'])
    param['return_url'] = return_url     # 支付成功回调地址
    param['quit_url'] = quit_url     # 支付中断退出URL
    # param['openid'] = 'oCOvf5zSNd7cOiz6_u4O-oA6ZEDs'
    param['openid'] = openid
    # param['product_id'] = None
    param['client_ip'] = '47.112.126.133'
    param['currency'] = 'CNY'

    # print(param)
    param = sorted(param.items(), key=lambda d: d[0].lower(), reverse=False )
    # print(param)
    # 拼接为字符串 = &
    str_param = ''
    for item in param:
        str_param += item[0]+'='+item[1] + '&'
    str_param=str_param[:-1]
    # print(str_param)
    # 拼接字符串添加secret
    presign=str_param+'&secret=842f9243a8714de8be33f049a5fddc63'
    # print('拼接字符串',presign)

    # 拼接字符串添加签名 sign
    # print(str(param))
    print('-'*10, presign, type(presign))
    m = hashlib.md5()
    m.update(presign.encode("utf8"))

    sign = m.hexdigest()
    # print(sign,len(sign))
    #param.append(('sign',sign))
    str_param+='&sign='+sign
    import os
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'test.log')
    with open(LOG_DIR, 'a',newline='\n') as f:
        f.write('\n\n{} 支付接口 发送字符串: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),str_param))
    print('支付接口 发送字符串: ',str_param)
    # print(type(param),param)
    URLstr = 'http://pay.ie1e.com/api/RzExternalApiCenter/callPayApi'
    r = requests.post(URLstr, data=str_param,headers={'Content-Type':'application/x-www-form-urlencoded'})
    # print(r)
    rep = json.loads(r.content.decode(encoding='utf-8'))
    while(not rep):
        pass
    with open(LOG_DIR, 'a',newline='\n') as f:
        f.write('\n\n{} 返回数据: {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),str(rep)))
    print('返回数据: ',str(rep))
    # print('index')
    if rep.get('code')==10000 :
        center_back_msg = rep.get('message')
        center_back_url = rep.get('data')
    elif rep.get('code')==-1:
        center_back_url = rep.get('data')
        center_back_msg = rep.get('message')
    else:
        center_back_url = None
        center_back_msg = None
    return center_back_url,center_back_msg
    # from django.shortcuts import redirect
    # return redirect('http://www.baidu.com')

@csrf_exempt
def PaymentCenterRuiZ(request):
    """支付中心支付成功后的中台访问接口"""
    from django.http import HttpResponse

    try:
        if request.method == 'GET':
            return HttpResponse('不支持GET方法')
        # copy数据，对除了签名sign以外的方法进行签名验证
        data = request.POST.copy()
        del data['sign']
        # 不区分大小写排序
        data = sorted(data.items(), key=lambda d: d[0].lower(), reverse=False)
        str_data = ''
        str_data = "&".join("{0}={1}".format(k, v) for k, v in data)
        # 加secret密钥
        stt_secret = '&secret=842f9243a8714de8be33f049a5fddc63'
        # 验签数据 presign
        presign = str_data + stt_secret
        # print(presign)
        order_id = request.POST.get('OrderId')

        # MD5验签
        if request.POST.get('signType') == 'MD5':
            m = hashlib.md5()
            m.update(presign.encode("utf8"))
            sign = m.hexdigest()
            sign=sign.upper()

            # print('sign',sign)
            if sign == request.POST.get('sign'):
                # print('MD5校验成功')
                ###### 订单操作
                order = OrderGoods.objects.get(id=order_id)
                order.status=3
                order.save()
                return HttpResponse('SUCCESS')
            else:
                print('订单号', order_id, '支付校验失败')
                return HttpResponse('Fail\n' + order_id + '支付校验失败')
        else:
            print('不支持MD5校验，订单号：', order_id)
            return HttpResponse('Fail\n' + order_id + '不支持MD5校验')
    except Exception as msg:
        print('信息错误')
        print(msg)
        return HttpResponse('信息错误')
    # print('PaymentCenterRuiZ#########################')





