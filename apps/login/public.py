import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from json.decoder import JSONDecodeError
from urllib.parse import urlparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import redis
import requests
import yaml
from retry import retry

from Clock.settings import POOL, IMAGE_ROOT, SESSION_API_URL2, EMAIL_URL
from login.models import User

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getTimeStr():
    """获取当前时间"""
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")


def log(content):
    print(getTimeStr() + ' ' + str(content))
    sys.stdout.flush()


# 读取yml配置
def getYmlConfig(yaml_file='morning_config.yml'):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


def uuid4_string():
    """生成激活码"""
    return str(uuid.uuid4()).replace('-', '')  # 去掉破折号


def remove_old(image_name_list_json):
    """ 删除旧的自拍照片"""
    if not image_name_list_json:
        return
    try:
        image_name_list = json.loads(image_name_list_json)
    except JSONDecodeError:
        image_name_list = [image_name_list_json]
    for image_name in image_name_list:
        if not image_name:
            continue
        image_path = os.path.join(IMAGE_ROOT, image_name)
        is_exists = os.path.exists(image_path)
        if is_exists:
            os.remove(image_path)
            continue
        else:
            continue


# 获取今日校园api
def getCpdailyApis():
    apis = {'login-url': LOGIN_URL, 'host': HOST}
    return apis


def recover_code(code, is_exits_10=None, is_exits_30=None):
    """
    恢复激活码
    :param code: 激活码
    :param is_exits_10: 是不是10元激活码
    :param is_exits_30: 是不是30元激活码
    :return:
    """
    coon = redis.Redis(connection_pool=POOL)
    if is_exits_10:
        coon.sadd('code:nonactivated:10', code)
    elif is_exits_30:
        coon.sadd('code:nonactivated:30', code)


# 主函数
def all_main(execute, type, **kwargs):
    """
    主函数
    :param execute: 执行函数
    :param type:正常为正常打卡,重试为重试
    :return:无
    """
    coon = redis.Redis(connection_pool=POOL)
    user_set = get_user_info(type, **kwargs)
    # 获得执行人数
    user_length = len(user_set)
    if user_set:
        # 获得学校接口
        setCpdailyApis()
        log('开始人数: ' + str(user_length))
        worker_num = min(user_length, 150)
        threadPool = ThreadPoolExecutor(max_workers=worker_num)
        # 构造参数,使用生成器提高性能
        param_list = ((i, type) for i in user_set)
        index = 0
        for i in param_list:
            index += 1
            if index >= 150:
                time.sleep(120)
                index = 0
            threadPool.submit(execute, *i)
        threadPool.shutdown(wait=True)
        success_number = coon.get('success')
        coon.delete('success')
        log('成功人数: ' + str(success_number))
        email = NoticEmail("管理员", "打卡结果", "2581123805@qq.com", "")
        # 重试情况下, 无论是否所有人都成功,都发送邮件.正常情况下,只有开始人数和成功人数不同时才发送邮件
        if type == '重试':
            email.build('开始人数：' + str(user_length) + ',成功人数：' + str(success_number))
        else:
            if str(success_number) != str(user_length):
                email.build('开始人数：' + str(user_length) + ',成功人数：' + str(success_number))
        return 0
    else:
        log('没有需要打卡的用户')
        return 0


def random_sleep(mu=1, sigma=0.4, extra=0):
    '''正态分布随机睡眠
    :param mu: 平均值
    :param sigma: 标准差，决定波动范围
    :param extra:额外的休眠时间
    '''
    secs = random.normalvariate(mu, sigma)
    if secs <= 0:
        secs = mu  # 太小则重置为平均值
    time.sleep(secs + extra)


def post_server(params):
    """重复请求学校接口,避免意外失效"""

    @retry(tries=5, delay=1)
    def retry_send():
        index = 0
        session_api_url = SESSION_API_URL2
        while index < 5:
            random_sleep()
            index += 1
            res_json = requests.post(url=session_api_url, data=params)
            res = res_json.json()
            code = res['code']
            if code == 0:
                break
        return res

    try:
        r = retry_send()
    except JSONDecodeError:
        return "失败"
    else:
        return r


def get_user_info(type, **kwargs):
    """
    获得用户信息
    :param type: 获取类型,type 0为正常,1为重试
    :param kwargs:
    :return:
    """
    if type == '正常':
        user_set = User.objects.select_related('school').filter(**kwargs, status=1)
    elif type == '重试':
        coon = redis.Redis(connection_pool=POOL)
        # 获取重试用户id
        user_list = coon.smembers('retry')
        if user_list:
            user_set = User.objects.select_related('school').filter(id__in=user_list)
        else:
            user_set = []
    else:
        user_set = []

    return user_set


def setCpdailyApis():
    """获得学校api"""
    global LOGIN_URL, HOST
    schools = requests.get(url='https://www.cpdaily.com/v6/config/guest/tenant/list', verify=False).json()['data']
    flag = True
    for one in schools:
        if one['name'] == '西南大学':
            if one['joinType'] == 'NONE':
                exit(-1)
            flag = False
            params = {
                'ids': one['id']
            }
            res = requests.get(url='https://www.cpdaily.com/v6/config/guest/tenant/info', params=params,
                               verify=False)
            data = res.json()['data'][0]
            idsUrl = data['idsUrl']
            ampUrl = data['ampUrl']
            if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                parse = urlparse(ampUrl)
                host = parse.netloc
                res = requests.get(parse.scheme + '://' + host, verify=False)
                parse = urlparse(res.url)
                LOGIN_URL = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                HOST = host

            ampUrl2 = data['ampUrl2']
            if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                parse = urlparse(ampUrl2)
                host = parse.netloc
                res = requests.get(parse.scheme + '://' + host, verify=False)
                parse = urlparse(res.url)
                LOGIN_URL = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                HOST = host
            break
    if flag:
        exit(-1)
    return


class Email:
    """邮件发送类"""

    def __init__(self, name, type, address, status):
        self.name = name
        self.type = type  # "早上"  "晚上"  "查寝"  "试用" "激活" "过期" "结果"
        self.address = address
        self.status = status  # "成功" 失败" ""

    def build_content(self, *args):
        pass

    def build(self, *args):
        data = {
            'name': self.name,
            'type': self.type,
            'address': self.address,
            'content': self.build_content(*args),
            'status': self.status
        }
        return self.send(data)

    def send(self, data):
        @retry(tries=5, delay=1)
        def retry_send():
            _ = requests.post(EMAIL_URL, data=data)

        try:
            retry_send()
            log(self.name + ":" + "邮件发送成功")
        except Exception as e:
            print(repr(e))
            log(self.name + ":" + "无法发送邮件")


class RegisterAndTryEmail(Email):
    """激活试用发送邮件类"""

    def build_content(self, time):
        time = int(time)
        if time == 7:
            check_time = "19:26"
        elif time == 8:
            check_time = "20:15"
        elif time == 9:
            check_time = "21:15"
        elif time == 930:
            check_time = "21:45"
        elif time == 10:
            check_time = "22:13"
        elif time == 1030:
            check_time = "22:45"
        else:
            check_time = ""

        content = """你好,{name}。你的自动打卡{type}成功！早上签到时间为7:15，晚上签到时间为19:14，查寝时间为{check_time}。
                    修改信息(修改打卡状态,修改查寝照片,修改定位地点)请点击该链接https://hotschool.ltd/%E9%A6%96%E9%A1%B5-9.html
                    。若打卡失败将通过该邮箱通知你,请将该邮箱标记为不是垃圾邮件!否则可能会错失重要邮件!""".format(name=self.name,
                                                                           check_time=check_time, type=self.type)
        return content


class SignEmail(Email):
    """打卡查寝发送邮件类"""

    def build_content(self, content):
        type = "签到" if "签到" in self.type else "查寝"
        content = """{type}{status},原因是：{content}。""".format(status=self.status, content=content, type=type)
        return content


class PastEmail(Email):
    """过期邮件类"""

    def build_content(self):
        content = """你好,{name}。你的自动打卡已经过期了！若还想继续获得自动打卡服务,请QQ联系997948107购买激活码。
                        激活码价格：10元每月，20元打到打卡结束。""".format(name=self.name)
        return content


class NoticEmail(Email):
    """管理员邮件通知"""

    def build_content(self, content):
        return content
