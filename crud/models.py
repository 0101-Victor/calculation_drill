from django.db import models
from django.contrib.auth.models import User

class DrillType(models.TextChoices):
    ADD = 'ADD', 'たし算'
    SUB = 'SUB', 'ひき算'
    MUL = 'MUL', 'かけ算'
    DIV = 'DIV', 'わり算'

class ProblemMistake(models.Model):
    """ユーザーが間違えた問題を保存（苦手問題の出題に使う）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mistakes')
    drill = models.CharField(max_length=3, choices=DrillType.choices)
    a = models.IntegerField()
    b = models.IntegerField()
    correct_answer = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'drill']),
        ]

class ScoreHistory(models.Model):
    """1ラウンド（10問）ごとのスコアを保存（任意活用）"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores', null=True, blank=True)
    drill = models.CharField(max_length=3, choices=DrillType.choices)
    round_index = models.IntegerField()  # 1..3
    score = models.IntegerField()        # 0..10
    total_after_round = models.IntegerField()  # その時点の累計
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'drill']),
        ]

class Feedback(models.Model):
    """ご意見・ご感想の保存用（メール送信はしない仕様）"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(blank=True, null=True, help_text="返信が必要な場合のみ任意で入力")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.user.username if self.user else (self.email or "anonymous")
        return f"{who}: {self.created_at:%Y-%m-%d %H:%M}"
