import json
import os

import requests
from rest_framework import serializers

from Clock.settings import IMAGE_ROOT, MAP_URL
from login.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """注册序列化器"""
    username = serializers.CharField(max_length=10,min_length=2,required=True,allow_blank=False,error_messages={
                                                        "required":'名字不允许为空',
                                                        "max_length":"名字最长为10个字",
                                                        "min_length":"名字最短为2个字",
                                                        "allow_blank":"名字不允许为空白"})
    student_number = serializers.CharField(min_length=10,max_length=50,required=True,allow_blank=False,error_messages={
                                                        "required":'学工号不允许为空',
                                                        "max_length":"学工最长为50个数字",
                                                        "min_length":"学工号最短为10个数字",
                                                        "allow_blank":"学工号不允许为空白"})
    password = serializers.CharField(min_length=1,max_length=30,required=True,allow_blank=False,error_messages={
                                                        "required":'密码不允许为空',
                                                        "max_length":"密码为30个数字",
                                                        "min_length":"密码最短为1位",
                                                        "allow_blank":"密码不允许为空白"})
    email = serializers.EmailField(required=True,allow_blank=False,
                                   error_messages={'required':'邮箱不允许为空',"allow_blank":"邮箱不允许为空白"})
    time = serializers.IntegerField(required=True)
    photo = serializers.ListField(required=False,default=[])

    def validate_time(self,value):
        if value not in (7,8,9,930,10,1030):
            raise serializers.ValidationError('时间选择不符合')
        else:
            return value

    def validate_photo(self,values):
        # 先检查图片是否存在
        if values:
            if len(values)>5:
                raise serializers.ValidationError('图片数量过多')
            for value in values:
                image_path = os.path.join(IMAGE_ROOT,value)
                is_exists =  os.path.exists(image_path)
                if is_exists:
                    continue
                else:
                    raise serializers.ValidationError('不存在该图片')
            return json.dumps(values)
        else:
            return json.dumps([])

    class Meta:
        model = User
        fields = ['username','student_number','password','email','time','photo']


class AlterSerializer(serializers.ModelSerializer):
    """修改用户信息照片"""
    status = serializers.IntegerField(required=True,error_messages={
        'required':'该字段不允许为空'
    })

    student_number = serializers.CharField(required=True,allow_blank=False,error_messages={
        "required":'学工号不允许为空',
        "max_length":"学工最长为50个数字",
        "min_length":"学工号最短为1个数字",
        "allow_blank":"学工号不允许为空白"
    })
    password = serializers.CharField(min_length=1, max_length=30, required=True, allow_blank=False, error_messages={
        "required": '密码不允许为空',
        "max_length": "密码最长为30个字符",
        "min_length": "密码最短为1个字符",
        "allow_blank": "密码不允许为空白"
    })
    photo = serializers.ListField(required=False, default=[])
    location = serializers.IntegerField(required=True)
    address = serializers.CharField(required=True,min_length=4,max_length=30,allow_blank=True,error_messages={
        "max_length": "地址最长为30个字符",
        "min_length": "地址最短为4个字符",
        "required":"地址不允许为空"
    })

    def validate_photo(self,values):
        # 先检查图片是否存在
        if values:
            if len(values)>5:
                raise serializers.ValidationError('图片数量过多')
            for value in values:
                image_path = os.path.join(IMAGE_ROOT,value)
                is_exists =  os.path.exists(image_path)
                if is_exists:
                    continue
                else:
                    raise serializers.ValidationError('不存在该图片')
            return json.dumps(values)
        else:
            # 未上传图片则返回空数组
            return []

    def validate_status(self,value):
        if value not in (0,1):
            raise serializers.ValidationError('打卡状态选择不符合')
        else:
            return value

    def validate_location(self,value):
        if value not in (0, 1):
            raise serializers.ValidationError('定位地点选择不符合')
        else:
            return value

    # 校验地点是否符合要求
    def validate_address(self,value):
        # 请求经纬度api
        value = value.strip()
        if value:
            addr_url = MAP_URL+"&addr="+value
            try:
                addr_info = requests.get(addr_url,verify=True)
                # 获得的返回数据为str,且开头包含如下字符串,需要去掉
                addr_info_str = addr_info.text.replace("qq.maps._svcb3.geocoder0&&qq.maps._svcb3.geocoder0","")
                # 使用eval函数将字符串转换成字典
                addr_info_dict = eval(addr_info_str)
                # 获得经纬度
                longitude,latitude = addr_info_dict["detail"]["pointx"],addr_info_dict["detail"]["pointy"]
            except Exception as e:
                print(repr(e))
                raise serializers.ValidationError('获取经纬度时发生异常')
            # 返回经纬度
            return longitude,latitude,value
        else:
            return None

    class Meta:
        model = User
        fields = ['student_number','password','status','photo','location','address']


