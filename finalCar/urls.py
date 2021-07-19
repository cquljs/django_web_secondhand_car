"""finalCar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf.urls import url
from django.contrib import admin
from django.urls import path

from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.gotoindex),
    path('app/index/',views.index),
    path('app/draw/', views.draw),
    path('app/details/',views.draw_all),
    path('app/detailsUpdate/<str:resultType>/', views.update_draw),
    path('app/login/',views.login),
    path('app/register/',views.register),
    url(r'^app/login_action/',views.login_action),
    url(r'^app/login_wrong/',views.login_wrong),
    url(r'^app/reg_action/',views.reg_action),
    url(r'^app/reg_success/',views.reg_success),
    url(r'^app/loginindex/',views.loginindex),
]
