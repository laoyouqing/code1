#!coding=utf-8
import os,sys,json,re,random,requests,bisect
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wechat_share.settings')
import django
django.setup()
from django.core.cache import cache


import requests,json,time
from django.core.cache import cache

def get_accesstoken(appid,secret):
    if cache.get(appid):
        return cache.get(appid)
    else:
        req = requests.get('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'%(appid,secret))
        print(req.text)
        token = json.loads(req.text)['access_token']
        cache.set(appid,token,7000)
        return token
def get_jsapi_ticket(access_token):
    if cache.get(access_token):
        return cache.get(access_token)
    else:
        req = requests.get('https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi'%(access_token))
        ticket = json.loads(req.text)['ticket']
        cache.set(access_token,ticket,7000)
        return ticket
def get_qy_accesstoken(corpid,corpsecret):
    req = requests.get('https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s'%(corpid,corpsecret))
    access_token = json.loads(req.text)['access_token']
    return access_token
def get_qy_ticket(access_token):
    if cache.get(access_token):
        return cache.get(access_token)
    else:
        req = requests.get('https://qyapi.weixin.qq.com/cgi-bin/get_jsapi_ticket?access_token=%s'%(access_token))
        ticket = json.loads(req.text)['ticket']
        cache.set(access_token,ticket,7000)
        return ticket

def getaccesstoken():
    req = requests.get('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wxd4aee23fe285cf1b&secret=815eb0602260acb19e2b5b9164f9988d')
    accesstoken = json.loads(req.text)['access_token']
    cache.set('accesstoken',accesstoken,7200)
    return True

def getshoturl(url):
    accesstoken = cache.get('access_token')
    if accesstoken == None:
        getaccesstoken()
        accesstoken = cache.get('accesstoken')
    datas = {
        'action':'long2short',
        'long_url':url
    }
    req = requests.post('https://api.weixin.qq.com/cgi-bin/shorturl?access_token='+accesstoken,data=json.dumps(datas))
    # print req.text
    shorturl =  json.loads(req.text)['short_url']
    return shorturl

def checkw(url):
    wurl = getshoturl(url)
    req = requests.get(wurl)
    print(req.url)
    locationurl = req.url
    if 'weixin110.qq.com' in locationurl:
        return False
    else:
        return True


def check(url):
    f = requests.get("http://vip.xxweixin.com/weixin/2764009661.php?domain=%s"%(url))
    print(f.text)
    req = json.loads(f.text)
    if req['status'] == "2":
        return False
    elif req['status'] == "3":
        return 3
    else:
        return True
def checkn(url):
    f = requests.get("http://wz5.tkc8.com/manage/api/check?token=81b5d6225dec44943f641305d711d052&url=%s"%(url))
    print(f.text)
    req = json.loads(f.text)
    if req['code'] == 9900:
        return True
    elif req['code'] == 9904:
        return False
    elif req['code'] == 402:
        return 3