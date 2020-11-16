"""Clock URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve

from Clock.settings import STATIC_ROOT
from apps.login.views import RegisterView, GetExpireview, GetActionCodeView, TryOutView, UploadView, AlterView

urlpatterns = [
    path('bzhhahahaadmin/', admin.site.urls),
    re_path('static/(?P<path>.*)', serve, {'document_root':STATIC_ROOT}),
    # 注册
    path('register',RegisterView.as_view()),
    # 查询
    path('query',GetExpireview.as_view()),
    # 生成激活码
    path('zxcvbnm131955',GetActionCodeView.as_view()),
    # 试用
    path('try',TryOutView.as_view()),
    # 图片上传请求接口
    path('upload',UploadView.as_view()),
    # 修改信息接口
    path('alter',AlterView.as_view()),
    # path('a',TestView.as_view())

]
