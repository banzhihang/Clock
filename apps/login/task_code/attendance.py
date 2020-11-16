import os
import random
from json.decoder import JSONDecodeError

import redis
import requests
import json
import base64
from pyDes import des, CBC, PAD_PKCS5
import oss2
import uuid
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from retry import retry

from Clock.settings import IMAGE_ROOT, POOL, DEFLAUT_PHOTO_NAME
from login.public import log, getCpdailyApis, post_server, SignEmail

# 忽略证书异常
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def getSession(user, apis, type):
    params = {
        'login_url': apis['login-url'],
        'needcaptcha_url': '',
        'captcha_url': '',
        'username': user.student_number,
        'password': user.password
    }

    cookies = {}
    # 借助上一个项目开放出来的登陆API，模拟登陆
    res = post_server(params)
    coon = redis.Redis(connection_pool=POOL)

    if res == "失败":
        # 将该用户添加到重试集和
        coon.sadd('retry', user.pk)
        log('------' + user.username + ':' + 'fail,已加入重试列表')
        exit(-1)

    if res['code'] != 0:
        # type为1为重试,0 为正常,重试就说明第二次错误,直接发送错误邮件,并从重试集和删除
        if type == '重试':
            coon.srem('retry', user.id)
            log('------' + user.username + ':' + 'fail,学校服务器错误')
            email = SignEmail(name=user.username, type="查寝", address=user.email, status="失败")
            email.build('学校服务器内部错误')
            exit(-1)
        else:
            # 将该用户添加到重试集和
            coon.sadd('retry', user.pk)
            log('------' + user.username + ':' + 'fail,已加入重试列表')
            exit(-1)

    # 将该用户从重试集和删除
    log(user.username+':获得session')
    coon.srem('retry', user.id)
    cookieStr = str(res['cookies'])
    if cookieStr == 'None':
        log(res.json())
        exit(-1)

    # 解析cookie
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    session = requests.session()
    session.cookies = requests.utils.cookiejar_from_dict(cookies, cookiejar=None, overwrite=True)
    return session


# 获取最新未签到任务
def getUnSignedTasks(session, apis, user):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }

    res = session.post(
        url='https://{host}/wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay'.format(
            host=apis['host']),headers=headers, data=json.dumps({}),verify=False)
    res = res.json()

    if len(res['datas']['unSignedTasks']) < 1:
        log('--------'+user.username + ':当前没有未签到任务')
        coon = redis.Redis(connection_pool=POOL)
        coon.incr('success', 1)
        exit(-1)

    latestTask = res['datas']['unSignedTasks'][0]
    return {
        'signInstanceWid': latestTask['signInstanceWid'],
        'signWid': latestTask['signWid']
    }


# 获取签到任务详情
def getDetailTask(session, params, apis):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }
    res = session.post(url='https://{host}/wec-counselor-attendance-apps/student/attendance/detailSignInstance'.format(
        host=apis['host']), headers=headers, data=json.dumps(params),verify=False)
    data = res.json()['datas']
    return data


# 填充表单
def fillForm(task, session, user, apis):
    form = {}
    form['signInstanceWid'] = task['signInstanceWid']
    form['longitude'] = user.school.longitude if user.location == 0 else user.longitude
    form['latitude'] = user.school.latitude if user.location == 0 else user.latitude
    form['isMalposition'] = task['isMalposition']
    form['abnormalReason'] = ''
    if task['isPhoto'] == 1:
        fileName = uploadPicture(session, apis, user)
        form['signPhotoUrl'] = getPictureUrl(session, fileName, apis)
        log(user.username+':'+form['signPhotoUrl'])
    else:
        form['signPhotoUrl'] = ''
    form['position'] = user.school.address if user.location == 0 else user.address
    form['qrUuid'] = ''
    return form


# 上传图片到阿里云oss
def uploadPicture(session, apis, user):
    url = 'https://{host}/wec-counselor-attendance-apps/stu/collector/getStsAccess'.format(host=apis['host'])
    res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps({}),verify=False)
    datas = res.json().get('datas')
    fileName = datas.get('fileName')
    accessKeyId = datas.get('accessKeyId')
    accessSecret = datas.get('accessKeySecret')
    securityToken = datas.get('securityToken')
    endPoint = datas.get('endPoint')
    bucket = datas.get('bucket')
    bucket = oss2.Bucket(oss2.Auth(access_key_id=accessKeyId, access_key_secret=accessSecret), endPoint, bucket)
    # 从数据库获得用户图片名列表,随机选择一张打卡
    try:
        photo_list = json.loads(user.photo)
    except JSONDecodeError:
        # 若用户图片为空字符串
        if not user.photo:
            photo_list = user.photo
        else:
            photo_list = [user.photo]
    if not photo_list:
        log(user.username+':没有找到照片')
        coon = redis.Redis(connection_pool=POOL)
        coon.incr('success', 1)
        email = SignEmail(name=user.username, type="查寝", address=user.email, status="失败")
        email.build('你没有上传照片,请点击该链接的修改信息选项上传照片https://hotschool.ltd/%E9%A6%96%E9%A1%B5-9.html')
        exit(-1)
    image_name = random.choice(photo_list)
    # 用户图片路径
    image_path = os.path.join(IMAGE_ROOT, image_name)
    try:
        with open(image_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        image_name = DEFLAUT_PHOTO_NAME
        image_path = os.path.join(IMAGE_ROOT, image_name)
        with open(image_path,'rb') as f:
            data = f.read()

    bucket.put_object(key=fileName, headers={'x-oss-security-token': securityToken}, data=data)
    return fileName


# 获取图片上传位置
def getPictureUrl(session, fileName, apis):
    url = 'https://{host}/wec-counselor-attendance-apps/student/attendance/previewAttachment'.format(host=apis['host'])
    data = {
        'ossKey': fileName
    }
    res = session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(data), verify=False)
    photoUrl = res.json().get('datas')
    return photoUrl


# DES加密
def DESEncrypt(s, key='XCE927=='):
    key = key
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    encrypt_str = k.encrypt(s)
    return base64.b64encode(encrypt_str).decode()


# DES解密
def DESDecrypt(s, key='XCE927=='):
    s = base64.b64decode(s)
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    return k.decrypt(s)


# 提交签到任务
def submitForm(session, user, form, apis):
    # Cpdaily-Extension
    extension = {
        "lon": user.school.longitude if user.location == 0 else user.longitude,
        "model": "PCRT00",
        "appVersion": "8.0.8",
        "systemVersion": "4.4.4",
        "userId": user.student_number,
        "systemName": "android",
        "lat": user.school.latitude if user.location == 0 else user.latitude,
        "deviceId": str(uuid.uuid1())
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36 okhttp/3.8.1',
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': DESEncrypt(json.dumps(extension)),
        'Content-Type': 'application/json; charset=utf-8',
        'Host': apis['host'],
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }
    res = session.post(
        url='https://{host}/wec-counselor-attendance-apps/student/attendance/submitSign'.format(host=apis['host']),
        headers=headers, data=json.dumps(form),verify=False)

    message = res.json()['message']
    if message == 'SUCCESS':
        log('----' + user.username + ':' + message)
    else:
        log('----' + user.username + ':' + message)
        email = SignEmail(name=user.username, type="查寝", address=user.email, status="失败")
        email.build(message)
    coon = redis.Redis(connection_pool=POOL)
    coon.incr('success', 1)


# 执行函数
def attendance_execute(user, type):

    @retry(tries=3, delay=1)
    def start():
        apis = getCpdailyApis()
        session = getSession(user, apis, type)
        params = getUnSignedTasks(session, apis, user)
        task = getDetailTask(session, params, apis)
        form = fillForm(task, session, user, apis)
        submitForm(session, user, form, apis)

    try:
        start()
    except Exception as e:
        coon = redis.Redis(connection_pool=POOL)
        print(repr(e))
        log('------' + user.username + ':' + 'fail,已加入重试列表')
        # 将该用户添加到重试集和
        coon.sadd('retry', user.pk)
