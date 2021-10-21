
from django.contrib import admin
from django.urls import path
from app.botreport import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('event/', views.event, name='event')
]
