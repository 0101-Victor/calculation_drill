from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from crud import views
from .views import (
    TopView, DrillView, RegisterView, WeakDrillView,
    DisclaimerView, CopyrightView, PrivacyView,
    FeedbackView, FeedbackThanksView,
)

urlpatterns = [
    path('', TopView.as_view(), name='top'),

    # 四則演算（/drill/addition/ 等）
    path('drill/<str:op>/', DrillView.as_view(), name='drill'),
    path('drill/<str:op>/weak/', WeakDrillView.as_view(), name='drill_weak'),

    # 認証
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='top'), name='logout'),
    path('', views.TopView.as_view(), name='top'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # ★ 法務系ページ
    path('legal/disclaimer/', DisclaimerView.as_view(), name='disclaimer'),
    path('legal/copyright/', CopyrightView.as_view(), name='copyright'),
    path('legal/privacy/', PrivacyView.as_view(), name='privacy'),

    # ★ ご意見・ご感想
    path('contact/', FeedbackView.as_view(), name='feedback'),
    path('contact/thanks/', FeedbackThanksView.as_view(), name='feedback_thanks'),
]