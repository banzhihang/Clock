from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse

import redis
import requests

from Clock.celery import app
from Clock.settings import POOL

from login.models import User
from login.public import all_main, log, remove_old, PastEmail, RegisterAndTryEmail
from login.task_code.attendance import attendance_execute
from login.task_code.sing_morning import morning_execute
from login.task_code.sing_night import night_execute

from requests.packages.urllib3.exceptions import InsecureRequestWarning


@app.task(acks_late=True)
def auto_sign_morning():
    """
    早签函数
    参数:无
    执行时间:每日早晨7.15
    """
    all_main(morning_execute,'正常',morning_time=7)


@app.task(acks_late=True)
def auto_sign_morning_retry():
    """
    早签函数(重试)
    参数:无
    执行时间:每日早晨7.20
    """
    all_main(morning_execute,'重试',morning_time=7)


@app.task(acks_late=True)
def auto_sign_night():
    """
    晚签函数
    参数:无
    执行时间:每日晚上7.15
    """
    all_main(night_execute,'正常',night_time=7)


@app.task(acks_late=True)
def auto_sign_night_retry():
    """
    晚签函数(重试)
    参数:无
    执行时间:每日晚上7.18
    """
    all_main(night_execute,'重试',night_time=7)


@app.task(acks_late=True)
def auto_attendance_7():
    """
    查寝函数
    参数:无
    执行时间:每日晚上7.20
    """
    all_main(attendance_execute,'正常',attendance_time=7)


@app.task(acks_late=True)
def auto_attendance_7_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上7.25
    """
    all_main(attendance_execute,'重试',attendance_time=7)


@app.task(acks_late=True)
def auto_attendance_8():
    """
    查寝函数
    参数:无
    执行时间:每日晚上8.15
    """
    all_main(attendance_execute,'正常',attendance_time=8)


@app.task(acks_late=True)
def auto_attendance_8_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上8.20
    """
    all_main(attendance_execute,'重试',attendance_time=8)


@app.task(acks_late=True)
def auto_attendance_9():
    """
    查寝函数
    参数:无
    执行时间:每日晚上9.15
    """
    all_main(attendance_execute,'正常',attendance_time=9)


@app.task(acks_late=True)
def auto_attendance_9_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上9.20
    """
    all_main(attendance_execute,'重试',attendance_time=9)


@app.task(acks_late=True)
def auto_attendance_930():
    """
    查寝函数
    参数:无
    执行时间:每日晚上9.45
    """
    all_main(attendance_execute,'正常',attendance_time=930)


@app.task(acks_late=True)
def auto_attendance_930_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上9.50
    """
    all_main(attendance_execute,'重试',attendance_time=930)

@app.task(acks_late=True)
def auto_attendance_10():
    """
    查寝函数
    参数:无
    执行时间:每日晚上10.15
    """
    all_main(attendance_execute,'正常',attendance_time=10)


@app.task(acks_late=True)
def auto_attendance_10_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上10.20
    """
    all_main(attendance_execute,'重试',attendance_time=10)

@app.task(acks_late=True)
def auto_attendance_1030():
    """
    查寝函数
    参数:无
    执行时间:每日晚上10.45
    """
    all_main(attendance_execute,'正常',attendance_time=1030)


@app.task(acks_late=True)
def auto_attendance_1030_retry():
    """
    查寝函数(重试)
    参数:无
    执行时间:每日晚上10.50
    """
    all_main(attendance_execute,'重试',attendance_time=1030)


@app.task(acks_late=True)
def clear_user():
    """
    清除过期用户
    参数:无
    执行时间:每3小时执行一次
    """

    def delete_user(user):
        # 删除照片
        remove_old(user.photo)
        email = PastEmail(name=user.username,type="自动签到过期",address=user.email,status="")
        email.build()
        log(user.username+':过期清除完成')
        user.delete()

    delete_set = User.objects.filter(expires__lt=datetime.now())
    if delete_set.exists():
        user_length = delete_set.count()
        threadPool = ThreadPoolExecutor(max_workers=min(user_length, 40))
        threadPool.map(delete_user,delete_set)
        threadPool.shutdown(wait=True)
        log('过期用户邮件发送成功')
    else:
        log('没有过期用户')


@app.task(acks_late=True)
def update_login_url():
    """更新学校相关url 3小时执行一次"""
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
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
                res = requests.get(parse.scheme + '://' + host,verify=False)
                parse = urlparse(res.url)
                LOGIN_URL = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                HOST = host

            ampUrl2 = data['ampUrl2']
            if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                parse = urlparse(ampUrl2)
                host = parse.netloc
                res = requests.get(parse.scheme + '://' + host,verify=False)
                parse = urlparse(res.url)
                LOGIN_URL = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                HOST = host
            break
    if flag:
        exit(-1)
    coon = redis.Redis(connection_pool=POOL)
    data = {
        'LOGIN_URL':LOGIN_URL,
        'HOST':HOST
    }
    coon.hmset(name='login',mapping=data)
    log('学校信息更新成功')


@app.task(acks_late=True)
def register_and_try_email(username,type,address,status,user_attendance_time):
    """激活或试用异步发送邮件"""
    email = RegisterAndTryEmail(name=username, type=type, address=address, status=status)
    email.build(user_attendance_time)


