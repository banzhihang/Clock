import base64
import json
import os
from datetime import datetime, timedelta
import redis
import requests
import imghdr

from django.db.models import F
from rest_framework.response import Response
from Clock.settings import POOL, SESSION_API_URL1, LOGIN_URL, IMAGE_ROOT
from rest_framework.views import APIView

from login.models import User, School
from login.public import recover_code, uuid4_string, remove_old
from login.serializers import RegisterSerializer, AlterSerializer
from login.tasks import register_and_try_email


class RegisterView(APIView):
    """注册用户视图"""

    def post(self, request):
        school = request.data.get('school', '西南大学')
        code = request.data.get('code')
        coon = redis.Redis(connection_pool=POOL)
        # 检查激活码是否存在
        if not code:
            return Response({'code': 1, 'msg': '没有激活码', 'data': {}})

        is_exits_10 = coon.sismember('code:nonactivated:10', code)
        is_exits_30 = coon.sismember('code:nonactivated:30', code)
        coon.srem('code:nonactivated:10', code)
        coon.srem('code:nonactivated:30', code)
        if is_exits_10 or is_exits_30:
            # 校验数据
            ser = RegisterSerializer(data=request.data)
            if ser.is_valid():
                try:
                    school = School.objects.get(name=school)
                except School.DoesNotExist:
                    recover_code(code, is_exits_10, is_exits_30)
                    return Response({'code': 1, 'msg': '未查询到该学校', 'data': {}})

                params = {
                    'login_url': LOGIN_URL,
                    'needcaptcha_url': '',
                    'captcha_url': '',
                    'username': ser.validated_data['student_number'],
                    'password': ser.validated_data['password']
                }
                # 判断用户账号密码是否正确
                try:
                    res_json = requests.post(url=SESSION_API_URL1, data=params)
                except:
                    recover_code(code, is_exits_10, is_exits_30)
                    return Response({'code': 1, 'msg': '发生错误', 'data': {}})
                res = res_json.json()
                if res['code'] != 0:
                    # 若登录失败恢复激活码
                    recover_code(code, is_exits_10, is_exits_30)
                    return Response({'code': 1, 'msg': res['msg'], 'data': {}})
                # 尝试查找是否存在该用户,若存在就更新该用户的时间 不存在就创建用户
                try:
                    user = User.objects.get(student_number=ser.validated_data['student_number'],
                                            password=ser.validated_data['password'])
                except User.DoesNotExist:
                    if is_exits_10:
                        expires = datetime.now() + timedelta(days=30)
                    else:
                        expires = datetime.now() + timedelta(days=1000)
                    data = {
                        'username': ser.validated_data['username'],
                        'student_number': ser.validated_data['student_number'],
                        'password': ser.validated_data['password'],
                        'school': school,
                        'email': ser.validated_data['email'],
                        'attendance_time': ser.validated_data['time'],
                        'expires': expires,
                        'photo': ser.validated_data['photo'],
                    }
                    user = User.objects.create(**data)
                else:
                    if is_exits_10:
                        user.expires = F('expires') + timedelta(days=30)
                    else:
                        user.expires = F('expires') + timedelta(days=1000)
                    # 删除旧照片
                    remove_old(user.photo)
                    user.attendance_time = ser.validated_data['time']
                    user.photo = ser.validated_data['photo']
                    user.save()
                register_and_try_email.delay(user.username,"激活",user.email,"成功",user.attendance_time)
                return Response({'code': 0, 'msg': '激活成功！重要邮件已发送,请查收(有可能在垃圾邮箱)', 'data': {}})
            else:
                recover_code(code, is_exits_10, is_exits_30)
                return Response({'code': 2, 'msg': '激活失败', 'data': ser.errors})
        else:
            return Response({'code': 1, 'msg': '激活码失效', 'data': {}})


class GetExpireview(APIView):
    """查询用户的过期时间视图"""

    def get(self, request):
        student_number = request.GET.get('student_number')
        password = request.GET.get('password')

        # 账号或密码为空
        if not student_number or not password:
            return Response({'code': 1, 'msg': '账号或密码必须填写完整', 'data': {}})
        try:
            # 数据库无此人
            user = User.objects.get(student_number=student_number, password=password)
        except User.DoesNotExist:
            return Response({'code': 2, 'msg': '账号或密码错误', 'data': {}})
        else:
            # 查询成功,返回过期时间
            time = user.expires.strftime('%Y-%m-%d %H:%M')
            return Response({'code': 0, 'msg': '查询成功', 'data': {'expire': time}})


class GetActionCodeView(APIView):
    """生成激活码"""

    def get(self, request):
        type = request.GET.get('type', 10)

        try:
            type = int(type)
        except:
            return Response({'code': 1, 'msg': '激活码生成失败', 'data': {}})
        else:
            coon = redis.Redis(connection_pool=POOL)
            code = uuid4_string()
            if type == 10:
                coon.sadd('code:nonactivated:10', code)
            elif type == 30:
                coon.sadd('code:nonactivated:30', code)
            else:
                return Response({'code': 1, 'msg': '激活码生成失败', 'data': {}})

            return Response({'code': 0,
                             'msg': '10元激活码生成成功' if type == 10 else '30元激活码生成成功',
                             'data': {'code': code}
                             })


class TryOutView(APIView):
    """试用视图"""

    def post(self, request):
        school = request.data.get('school', '西南大学')
        coon = redis.Redis(connection_pool=POOL)
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            # 查询该用户在不在试用集和
            data = ser.validated_data['student_number']
            is_exist = coon.sismember('tryout', data)
            if not is_exist:
                coon.sadd('tryout', data)
                try:
                    User.objects.get(student_number=ser.validated_data['student_number'],
                                     password=ser.validated_data['password'])
                except User.DoesNotExist:
                    try:
                        school = School.objects.get(name=school)
                    except School.DoesNotExist:
                        coon.srem('tryout', data)
                        return Response({'code': 1, 'msg': '未查询到该学校', 'data': {}})
                    else:
                        params = {
                            'login_url': LOGIN_URL,
                            'needcaptcha_url': '',
                            'captcha_url': '',
                            'username': ser.validated_data['student_number'],
                            'password': ser.validated_data['password']
                        }
                        try:
                            res_json = requests.post(url=SESSION_API_URL1, data=params)
                        except:
                            coon.srem('tryout', data)
                            return Response({'code': 1, 'msg': '发生错误', 'data': {}})
                        res = res_json.json()
                        if res['code'] != 0:
                            coon.srem('tryout', data)
                            return Response({'code': 1, 'msg': res['msg'], 'data': {}})
                        # 试用期为2天
                        expires = datetime.now() + timedelta(days=2)

                        user_data = {
                            'username': ser.validated_data['username'],
                            'student_number': ser.validated_data['student_number'],
                            'password': ser.validated_data['password'],
                            'school': school,
                            'email': ser.validated_data['email'],
                            'expires': expires,
                            'attendance_time': ser.validated_data['time'],
                            'photo': ser.validated_data['photo'],
                        }
                        user = User.objects.create(**user_data)
                        register_and_try_email.delay(user.username,"激活",user.email,"成功",user.attendance_time)
                        return Response({'code': 0, 'msg': '试用成功！重要邮件已发送,请查收(有可能在垃圾邮箱)', 'data': {}})
                else:
                    return Response({'code': 1, 'msg': '该账户已激活', 'data': {}})
            else:
                return Response({'code': 1, 'msg': '该账户已试用', 'data': {}})
        else:
            return Response({'code': 2, 'msg': '发生错误', 'data': ser.errors})


class UploadView(APIView):
    """图片上传视图"""

    def post(self, request):
        # 图片为一个json数组
        image_base64_list_json = request.data.get('image')
        if not image_base64_list_json or image_base64_list_json == '[]':
            return Response({'code': 1, 'msg': '图片不允许为空', 'data': {}})
        try:
            image_name_list = []
            # 反序列化json数组
            image_base64_list = json.loads(image_base64_list_json)
            # 若图片数大于5张则返回错误
            if len(image_base64_list) > 5:
                return Response({'code': 1, 'msg': '照片数量过多', 'data': {}})
            for image_base64 in image_base64_list:
                # base64解码
                image = base64.b64decode(image_base64)
                # 获得图片后缀(imghdr.what函数第一个参数的疑问参见网页https://www.jb51.net/article/132671.htm)
                image_sufixx = imghdr.what(None, h=image)
                # 给图片规范命名
                image_name = uuid4_string() + '.' + image_sufixx
                # 指定图片存储路径
                image_path = os.path.join(IMAGE_ROOT, image_name)
                with open(image_path, 'wb') as f:
                    f.write(image)
                image_name_list.append(image_name)
        except:
            return Response({'code': 1, 'msg': '发生错误', 'data': {}})
        else:
            return Response({'code': 0, 'msg': '图片上传成功,接下来请点击提交', 'data': {'image_name': image_name_list}})


class AlterView(APIView):
    """修改用户信息视图"""

    def post(self, request):
        ser = AlterSerializer(data=request.data)
        if ser.is_valid():
            try:
                user = User.objects.get(student_number=ser.validated_data['student_number'],
                                        password=ser.validated_data['password'])
            except User.DoesNotExist:
                return Response({'code': 1, 'msg': '账号或密码错误(或者已过期)', 'data': {}})
            else:
                # 若photo不为[]
                if ser.validated_data['photo']:
                    remove_old(user.photo)
                    user.photo = ser.validated_data['photo']
                user.status = ser.validated_data['status']
                user.location = ser.validated_data['location']
                # 若address不为None,更新打卡地址
                if ser.validated_data['address']:
                    user.longitude,user.latitude,user.address = ser.validated_data['address']
                user.save()
                return Response({'code': 0, 'msg': '修改成功', 'data': {}})
        else:
            return Response({'code': 2, 'msg': '发生错误', 'data': ser.errors})
