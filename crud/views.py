import random
from typing import List, Dict, Tuple
from django.views.generic import TemplateView, View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.utils import timezone
from .models import DrillType, ProblemMistake, ScoreHistory, Feedback
from .forms import RegisterForm, FeedbackForm
from crud.forms import CustomUserCreationForm

# ====== ヘルパ ======

OP_MAP = {
    'addition':  DrillType.ADD,
    'subtraction': DrillType.SUB,
    'multiplication': DrillType.MUL,
    'division':  DrillType.DIV,
}

LABEL_MAP = {
    DrillType.ADD: 'たし算',
    DrillType.SUB: 'ひき算',
    DrillType.MUL: 'かけ算',
    DrillType.DIV: 'わり算',
}

def generate_problems(drill: str, n: int = 10) -> List[Dict]:
    """四則別に10問生成。divisionは割り切れる整数問題のみ。subtractionは非負。"""
    problems = []
    for _ in range(n):
        if drill == DrillType.ADD:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            ans = a + b
            sym = "＋"
        elif drill == DrillType.SUB:
            a = random.randint(1, 9)
            b = random.randint(1, a)  # マイナス回避
            ans = a - b
            sym = "－"
        elif drill == DrillType.MUL:
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            ans = a * b
            sym = "×"
        elif drill == DrillType.DIV:
            b = random.randint(1, 9)
            ans = random.randint(1, 9)
            a = b * ans  # 割り切れるように作る
            sym = "÷"
        else:
            raise ValueError("unknown drill")
        problems.append({"a": a, "b": b, "ans": ans, "sym": sym})
    return problems


def grade_post(post_data, n: int = 10) -> Tuple[List[Dict], int]:
    """POSTデータから10問採点して、結果配列とスコアを返す"""
    results = []
    score = 0
    for i in range(n):
        a = int(post_data.get(f"a{i}"))
        b = int(post_data.get(f"b{i}"))
        ans = int(post_data.get(f"ans{i}"))  # 正解（hidden）
        user_raw = post_data.get(f"answer{i}")
        try:
            user_answer = int(user_raw)
        except (TypeError, ValueError):
            if user_raw is None or user_raw == "":
                user_answer = "未入力"
            else:
                user_answer = str(user_raw)

        is_correct = (isinstance(user_answer, int) and user_answer == ans)

        if is_correct:
            score += 1
        results.append({
            "a": a, "b": b, "correct_answer": ans,
            "user_answer": user_answer, "is_correct": is_correct,
        })
    return results, score


# ====== 画面 ======

class TopView(TemplateView):
    template_name = "top.html"


class DrillView(View):
    """
    /drill/<op>/ で四則共通に出題＆採点。
    3回実施したら、その3回分の合計を結果画面に表示して「トップに戻る」リンク。
    戻った後は再び3回実施可能（セッションリセット）。
    """
    template_name = "drill.html"

    def get(self, request, op: str, *args, **kwargs):
        drill = OP_MAP.get(op)
        if not drill:
            messages.error(request, "不正なドリルです。")
            return redirect('top')

        # セッションキー（四則別に独立）
        round_key = f"{drill}_round"
        total_key = f"{drill}_total"

        round_num = request.session.get(round_key, 0)
        if round_num >= 3:
            # 3回終わってる → リセットしてトップへ（ユーザーが戻ってきたケース）
            request.session[round_key] = 0
            request.session[total_key] = 0
            return redirect('top')

        # 新しい問題生成
        problems = generate_problems(drill)
        # hidden で正解も渡す（改ざんしても採点側で整合性取る必要があればDB化だが今回は簡易）
        context = {
            "label": LABEL_MAP[drill],
            "op": op,
            "round_display": round_num + 1,  # 1..3
            "problems": problems,
        }
        return render(request, self.template_name, context)

    def post(self, request, op: str, *args, **kwargs):
        drill = OP_MAP.get(op)
        if not drill:
            messages.error(request, "不正なドリルです。")
            return redirect('top')

        round_key = f"{drill}_round"
        total_key = f"{drill}_total"

        # 採点
        results, score = grade_post(request.POST)
        round_num = request.session.get(round_key, 0) + 1
        total_score = request.session.get(total_key, 0) + score

        # ユーザー保存（ログイン時のみ）
        if request.user.is_authenticated:
            # スコア履歴
            ScoreHistory.objects.create(
                user=request.user, drill=drill,
                round_index=round_num, score=score, total_after_round=total_score
            )
            # 間違え問題を保存
            wrongs = [r for r in results if not r["is_correct"]]
            bulk = []
            for r in wrongs:
                bulk.append(ProblemMistake(
                    user=request.user, drill=drill,
                    a=r["a"], b=r["b"], correct_answer=r["correct"]
                ))
            if bulk:
                ProblemMistake.objects.bulk_create(bulk, ignore_conflicts=True)

        # セッション更新
        request.session[round_key] = round_num
        request.session[total_key] = total_score

        # 3回目なら合計を出してセッション即リセット→トップに戻れる
        from django.template.loader import render_to_string
        context = {
            "label": LABEL_MAP[drill],
            "op": op,
            "round_display": round_num,
            "results": results,
            "score": score,
            "total_3runs": total_score if round_num == 3 else None,
        }

        if round_num == 3:
            # 次回に備えてリセット
            request.session[round_key] = 0
            request.session[total_key] = 0

        return render(request, "results.html", context)


class WeakDrillView(LoginRequiredMixin, View):
    """
    /drill/<op>/weak/ で苦手問題（間違い保存）から最大10問出題。
    保存済みが10未満なら新規問題で補充。
    正解できた苦手問題は解消＝記録削除（復習で克服する仕組み）
    """
    template_name = "drill.html"

    def get(self, request, op: str, *args, **kwargs):
        drill = OP_MAP.get(op)
        if not drill:
            messages.error(request, "不正なドリルです。")
            return redirect('top')

        mistakes = list(
            ProblemMistake.objects.filter(user=request.user, drill=drill)
            .order_by('created_at')[:10]
        )
        problems = [{"a": m.a, "b": m.b, "ans": m.correct_answer,
                     "sym": {"ADD":"＋","SUB":"－","MUL":"×","DIV":"÷"}[drill]} for m in mistakes]

        if len(problems) < 10:
            # 補充
            problems += generate_problems(drill, n=10-len(problems))

        context = {
            "label": f"{LABEL_MAP[drill]}（苦手）",
            "op": op,
            "round_display": None,  # 表示しない
            "problems": problems,
            "weak_mode": True,
        }
        return render(request, self.template_name, context)

    def post(self, request, op: str, *args, **kwargs):
        drill = OP_MAP.get(op)
        if not drill:
            messages.error(request, "不正なドリルです。")
            return redirect('top')

        results, score = grade_post(request.POST)

        # 苦手だった問題で今回正答できたものは削除（克服）
        if request.user.is_authenticated:
            for r in results:
                # その問題が苦手帳に存在するなら消す
                ProblemMistake.objects.filter(
                    user=request.user, drill=drill,
                    a=r["a"], b=r["b"], correct_answer=r["correct"]
                ).delete()

        context = {
            "label": f"{LABEL_MAP[drill]}（苦手）",
            "op": op,
            "round_display": None,
            "results": results,
            "score": score,
            "total_3runs": None,
            "weak_mode": True,
        }
        return render(request, "results.html", context)


class RegisterView(View):
    def get(self, request):
        return render(request, "register.html", {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "登録が完了しました。ログインしてください。")
            return redirect("login")
        return render(request, "register.html", {"form": form})
    
class RegisterView(CreateView):
    template_name = "register.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    
# --- 静的ページ ---
class DisclaimerView(TemplateView):
    template_name = "legal_disclaimer.html"

class CopyrightView(TemplateView):
    template_name = "legal_copyright.html"

class PrivacyView(TemplateView):
    template_name = "legal_privacy.html"

# --- ご意見 ---
class FeedbackView(View):
    def get(self, request):
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
        return render(request, "feedback.html", {"form": FeedbackForm(initial=initial)})

    def post(self, request):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            if request.user.is_authenticated:
                fb.user = request.user
            fb.save()
            messages.success(request, "お送りいただきありがとうございました。")
            return redirect("feedback_thanks")
        return render(request, "feedback.html", {"form": form})

class FeedbackThanksView(TemplateView):
    template_name = "feedback_thanks.html"