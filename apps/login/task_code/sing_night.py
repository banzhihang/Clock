import redis
import requests
import json
import uuid
import base64
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from retry import retry
from pyDes import des, CBC, PAD_PKCS5

from Clock.settings import POOL
from login.public import log, getYmlConfig, getCpdailyApis, post_server, SignEmail

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# 登陆并获取session
def getSession(user, apis,type):
    """
    :param user: User实例
    :param apis: api字典
    :param type: 执行类型
    :return:
    """
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
            email = SignEmail(name=user.username,type="晚上签到",address=user.email,status="失败")
            email.build('学校服务器内部错误')
        else:
            # 将该用户添加到重试集和
            coon.sadd('retry', user.pk)
            log('------'+user.username+':'+'fail,已加入重试列表')
            exit(-1)

    log(user.username + ':获得session')
    # 将该用户从重试集和删除
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
def getUnSignedTasks(session, apis,user):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8'
    }

    res = session.post(
        url='https://{host}/wec-counselor-sign-apps/stu/sign/queryDailySginTasks'.format(host=apis['host']),
        headers=headers, data=json.dumps({}),verify=False)
    res = res.json()

    if len(res['datas']['unSignedTasks']) < 1:
        coon = redis.Redis(connection_pool=POOL)
        log('--------'+user.username + ':当前没有未签到任务')
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
    res = session.post(
        url='https://{host}/wec-counselor-sign-apps/stu/sign/detailSignTaskInst'.format(host=apis['host']),
        headers=headers, data=json.dumps(params),verify=False)
    data = res.json()['datas']
    return data


# 填充表单
def fillForm(task, user):
    coon = redis.Redis(connection_pool=POOL)
    config = getYmlConfig(yaml_file='night_config.yml')
    form = {}
    if task['isPhoto'] == 1:
        form['signPhotoUrl'] = ''
    else:
        form['signPhotoUrl'] = ''
    if task['isNeedExtra'] == 1:
        extraFields = task['extraField']
        defaults = config['cpdaily']['defaults']
        extraFieldItemValues = []
        for i in range(0, len(extraFields)):
            default = defaults[i]['default']
            extraField = extraFields[i]
            if default['title'] != extraField['title']:
                log('-------------'+user.username +':第%d个默认配置项错误，请检查' % (i + 1))
                # 增加成功人数
                coon.incr('success', 1)
                exit(-1)
            extraFieldItems = extraField['extraFieldItems']
            for extraFieldItem in extraFieldItems:
                if extraFieldItem['content'] == default['value']:
                    extraFieldItemValue = {'extraFieldItemValue': default['value'],
                                           'extraFieldItemWid': extraFieldItem['wid']}
                    extraFieldItemValues.append(extraFieldItemValue)
        # log(extraFieldItemValues)
        # 处理带附加选项的签到
        form['extraFieldItems'] = extraFieldItemValues
    # form['signInstanceWid'] = params['signInstanceWid']
    form['signInstanceWid'] = task['signInstanceWid']
    form['longitude'] = user.school.longitude if user.location == 0 else user.longitude
    form['latitude'] = user.school.latitude if user.location == 0 else user.latitude
    form['isMalposition'] = task['isMalposition']
    form['abnormalReason'] = ''
    form['position'] = user.school.address if user.location == 0 else user.address
    return form

# DES加密
def DESEncrypt(s, key='XCE927=='):
    key = key
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    encrypt_str = k.encrypt(s)
    return base64.b64encode(encrypt_str).decode()


# 提交签到任务
def submitForm(session, user, form, apis):
    # Cpdaily-Extension
    extension = {
        "lon": user.school.longitude if user.location == 0 else user.longitude,
        "model": "OPPO R11 Plus",
        "appVersion": "8.2.6",
        "systemVersion": "4.4.4",
        "userId": user.student_number,
        "systemName": "android",
        "lat": user.school.latitude if user.location == 0 else user.latitude,
        "deviceId": str(uuid.uuid1())
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 okhttp/3.12.4',
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': DESEncrypt(json.dumps(extension)),
        'Content-Type': 'application/json; charset=utf-8',
        'Accept-Encoding': 'gzip',
        'Connection': 'Keep-Alive'
    }
    res = session.post(url='https://{host}/wec-counselor-sign-apps/stu/sign/completeSignIn'.format(host=apis['host']),
                       headers=headers, data=json.dumps(form),verify=False)
    res = res.json()
    message = res['message']
    if message == 'SUCCESS':
        log('----'+user.username + ':' + message)
    else:
        log('----'+user.username + ':' + message)
        email = SignEmail(name=user.username,type="晚上签到",address=user.email,status="失败")
        email.build(message)
    coon = redis.Redis(connection_pool=POOL)
    coon.incr('success', 1)


# 执行函数
def night_execute(user,type):

    @retry(tries=3, delay=1)
    def start():
        apis = getCpdailyApis()
        session = getSession(user, apis, type)
        params = getUnSignedTasks(session, apis,user)
        task = getDetailTask(session, params, apis)
        form = fillForm(task,user)
        submitForm(session, user, form, apis)

    try:
        start()
    except Exception as e:
        coon = redis.Redis(connection_pool=POOL)
        print(repr(e))
        log('------' + user.username + ':' + 'fail,已加入重试列表')
        # 将该用户添加到重试集和
        coon.sadd('retry', user.pk)



