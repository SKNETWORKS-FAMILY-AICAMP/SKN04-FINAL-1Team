from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('nickname',)

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.nickname:
            # username을 기본 nickname으로 사용
            user.nickname = user.username
        if commit:
            user.save()
        return user 