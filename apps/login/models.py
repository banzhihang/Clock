import json

from django.db import models


class User(models.Model):
    """用户信息表"""
    username = models.CharField(max_length=10,verbose_name='用户姓名',default='')
    student_number = models.CharField(max_length=50,verbose_name='用户学工号',default='',db_index=True)
    password = models.CharField(max_length=50,verbose_name='用户学工号密码',default='',db_index=True)
    expires = models.DateTimeField(verbose_name='用户过期时间')
    school = models.ForeignKey('School',on_delete=models.CASCADE,verbose_name='用户所属学校')
    email = models.CharField(max_length=30,verbose_name='用户邮箱')
    status = models.IntegerField(choices=((0,'暂停打卡'),(1,'正常打卡')),verbose_name='状态',default=1,db_index=True)
    photo = models.CharField(verbose_name='图片名字',blank=True,max_length=500,default=json.dumps([]))
    attendance_time = models.IntegerField(choices=((7,'7点查寝'),(8,'8点查寝'),(9,'9点查寝'),(930,'9点30查寝'),(10,'10点查寝'),(1030,'10点30查寝')),
                                          verbose_name='查寝时间',default=7,db_index=True)
    morning_time = models.IntegerField(choices=((7,'7点早签'),(8,'8点早签'),(9,'9点早签')),
                                       verbose_name='早签时间',default=7,db_index=True)
    night_time = models.IntegerField(choices=((7,'7点晚签'),(8,'8点晚签'),(9,'9点晚签')),
                                     verbose_name='晚签时间',default=7,db_index=True)
    location = models.IntegerField(choices=((0,"在学校"),(1,"自定义")),verbose_name="打卡地点",default=0)
    longitude = models.CharField(max_length=25,verbose_name='地点经度',default='无')
    latitude = models.CharField(max_length=25,verbose_name='地点纬度',default='无')
    address = models.CharField(max_length=100,verbose_name='打卡地址',default='无')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name


class School(models.Model):
    """学校信息表"""
    name = models.CharField(max_length=30,verbose_name='学校名',db_index=True)
    address = models.CharField(max_length=100,verbose_name='学校地址')
    longitude = models.CharField(max_length=25,verbose_name='学校经度')
    latitude = models.CharField(max_length=25,verbose_name='学校纬度')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '学校信息'
        verbose_name_plural = verbose_name






