from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Feedback

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,  # 任意入力
        label="メールアドレス（任意）",
        widget=forms.EmailInput(attrs={'placeholder': 'example@example.com'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "なまえ（ユーザー名）",
            "password1": "パスワード",
            "password2": "もう一度パスワード",
        }

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="任意（通知など使いません）")
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("email", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6, "placeholder": "ご意見・ご感想をお書きください"}),
        }
        labels = {
            "email": "メールアドレス（任意）",
            "message": "メッセージ",
        }
        help_texts = {
            "email": "返信が必要な場合のみご入力ください。メール送信は行いません。",
        }