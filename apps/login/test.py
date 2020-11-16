import base64
import json
import sys
from datetime import datetime,timezone,timedelta

# def getTimeStr():
#     utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
#     bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
#     return bj_dt.strftime("%Y-%m-%d %H:%M:%S")
#
#
#
#
#
# def log(content):
#     if type(content) == str:
#         print(getTimeStr() + ' ' + str(content))
#     else:
#         print(getTimeStr() + ' ' + json.dumps(content))
#     sys.stdout.flush()
#
# log({'a':'gaga','b':2})
# import requests
# paras = {
#     "name":"班治行",
#     "types":"早上",
#     "message":"签到成功",
#     "email":"2581123805@qq.com"
# }
# proxies ={
#     "http":"106.88.128.144:19981"
# }
# a = requests.post("http://106.13.118.89:9090/send",data=paras,proxies=proxies)
# print('hahha')

# def random_email():
#     """
#     随机选择一个邮箱发送邮件,避免邮箱失效
#     参数:无
#     返回值:包含邮箱信息的字典
#     """
#     email_list = [
#         {
#             'email_name': 'ccczz1516@sina.com',
#             'password': '987db958e71bc63d',
#             'email_user': '杨迪',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'jokelike@sina.com',
#             'password': '37d915ea58d3c63d',
#             'email_user': '班治杭',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'nazu_ki@sina.com',
#             'password': '037aa701fb65943f',
#             'email_user': '刘煜鑫',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'jacklike_na@sina.com',
#             'password': '947bcea13733be23',
#             'email_user': '班治杭',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': '123456likemomo@sina.com',
#             'password': '22ef268f46236864',
#             'email_user': '杨康',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'boyzzli@sina.com',
#             'password': '67c8b4131c9f648c',
#             'email_user': '刘丽琴',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'girlzzli@sina.com',
#             'password': 'a01a063cdc9e7525',
#             'email_user': '刘丽琴',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'bobfluent@sina.com',
#             'password': '1100416db48520b6',
#             'email_user': '杨迪',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'jobfluent@sina.com',
#             'password': '3f77aaeb80a48fa7',
#             'email_user': '班治杭',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'mikejustyou@sina.com',
#             'password': 'c51f8e6d381dce2f',
#             'email_user': '何倩',
#             'smtp_address': 'smtp.sina.com'
#         },
#         {
#             'email_name': 'mikejustme@sina.com',
#             'password': 'eef42553e07c6c76',
#             'email_user': '谭煜',
#             'smtp_address': 'smtp.sina.com'
#         },
#     ]
#
#     result = random.choice(email_list)
#     return result


# def email(message: str, user, type: str):
#     """
#     :param message: 签到信息
#     :param user: User实例
#     :param type:早上还是晚上,还是查寝
#     :return:None
#     """
#
#     if type == "早上":
#         content = '-早上签到'
#     elif type == '晚上':
#         content = '-晚上签到'
#     elif type == '过期':
#         content = '-自动签到过期'
#     elif type == '管理员':
#         content = '-结果'
#     else:
#         content = '-查寝'
#
#     if '成功' in message:
#         status = '-成功'
#     elif '失败' in message:
#         status = '-失败'
#     elif '人数' in message:
#         status = ''
#     else:
#         status = ''
#
#     to_user = user.email
#     subject = user.username + content + status
#     name = user.username
#     body = name + message
#     msg = MIMEText(body, 'plain', 'utf-8')
#     msg['TO'] = "{}<{}>".format(name[0], to_user)
#     msg['SUBJECT'] = subject
#
#     def random_email_send():
#         """随机选择邮箱并填充信息以及发送"""
#         email_info = random_email()
#         smtpsever = email_info['smtp_address']
#         sender = email_info['email_name']
#         psw = email_info['password']
#         msg['FROM'] = 'DK<{}>'.format(email_info['email_name'])
#
#         smtp = smtplib.SMTP()
#         smtp.connect(smtpsever)
#         smtp.login(sender, psw)
#         smtp.sendmail(sender, to_user, msg.as_string())
#
#     # 邮件发送失败时重试5次
#     @retry(tries=5)
#     def send_mail():
#         # 正太分布休眠,避免同时发送太多邮件
#         random_sleep()
#         random_email_send()
#
#     try:
#         send_mail()
#         log(name + ":" + "邮件发送成功")
#     except smtplib.SMTPException as e:
#         print(e)
#         log(name + ":" + "无法发送邮件")

# DES加密
# from pyDes import des, CBC, PAD_PKCS5
#
#
# def DESEncrypt(s, key='XCE927=='):
#     key = key
#     iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
#     # iv = bytes([1,2,3,4,5,6,7,8]) 作用同上
#     k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
#     encrypt_str = k.encrypt(s)
#     return base64.b64encode(encrypt_str).decode()
#
# a = DESEncrypt("123456")
# print(a)

# a = {'a':1,"b":'2'}
# print(a=="b")
# import requests
#
# MAP_URL = "https://apis.map.qq.com/jsapi?qt=geoc&key=UGMBZ-CINWR-DDRW5-W52AK-D3ENK-ZEBRC&output=jsonp&pf=jsapi&ref=jsapi&cb=qq.maps._svcb3.geocoder0"
# addr_url = MAP_URL+"&addr="+"重庆市"
# addr_info = requests.get(addr_url,verify=True)
# json1 = addr_info.text.replace("qq.maps._svcb3.geocoder0&&qq.maps._svcb3.geocoder0","")
# json2 = eval(json1)
# x,y = json2["detail"]["pointx"],json2["detail"]["pointy"]
#
# print(x,type(x),y,type(y))
# import requests
# from retry import retry
#
# EMAIL_URL = "http://localhost:9090/send"
#
#
# class Email:
#     """邮件发送类"""
#     def __init__(self,name,type,address,status):
#         self.name = name
#         self.type = type
#         self.address = address
#         self.status = status
#
#     def build_content(self,*kargs):
#         return kargs
#
#     def build(self,**kwargs):
#         data = {
#             'name': self.name,
#             'type': self.type,
#             'address': self.address,
#             'content': self.build_content(**kwargs),
#             'status': self.status
#         }
#         return self.send(data)
#
#     def send(self,data):
#         @retry(tries=5, delay=1)
#         def retry_send():
#             _ = requests.post(EMAIL_URL, data=data)
#         try:
#             retry_send()
#             print(self.name + ":" + "邮件发送成功")
#         except Exception as e:
#             print(repr(e))
#             print(self.name + ":" + "无法发送邮件")
#
#
# class RegisterAndTryEmail(Email):
#     """激活试用发送邮件类"""
#     def build_content(self,time,type):
#         time = int(time)
#         if time == 7:
#             check_time = "19:26"
#         elif time == 8:
#             check_time = "20:15"
#         elif time == 9:
#             check_time = "21:15"
#         elif time == 930:
#             check_time = "21:45"
#         elif time == 10:
#             check_time = "22.13"
#         elif time == 1030:
#             check_time = "22.45"
#
#         content = """你好,{name}。你的自动打卡{type}成功！早上签到时间为7:15，晚上签到为19:14，查寝时间为{check_time}。
#                     修改信息(修改打卡状态,修改查寝照片,修改定位地点)请点击该链接https://hotschool.ltd/%E9%A6%96%E9%A1%B5-9.html
#                     。若打卡失败将通过该邮箱通知你,请将该邮箱标记为不是垃圾邮件!。""".format(name=self.name, check_time=check_time, type=type)
#         return content
#
#
# class SignEmail(Email):
#     """打卡查寝发送邮件类"""
#     def build_content(self,content):
#         content = """打卡{status},原因是：{content}。""".format(status=self.status,content=content)
#         return content
#
#
#
# class PastEmail(Email):
#     """过期邮件类"""
#     def build_content(self):
#         content = """你好,{name}。你的自动打卡已经过期了！若还想继续获得自动打卡服务,请QQ联系997948107购买激活码。
#                         激活码价格：10元每月，20打到打卡结束。""".format(name=self.name)
#         return content
#
#
# a = SignEmail("班治杭","晚上签到","2581123805@qq.com","失败")
# a.build(content="学校服务器异常")