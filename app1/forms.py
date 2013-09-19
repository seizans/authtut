# coding=utf-8
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import (
    MAXIMUM_PASSWORD_LENGTH
)


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput,
        max_length=MAXIMUM_PASSWORD_LENGTH,
    )
    password2 = forms.CharField(
        label='パスワード確認',
        widget=forms.PasswordInput,
        max_length=MAXIMUM_PASSWORD_LENGTH,
        help_text='確認のため同じパスワードを入力ください'
    )

    class Meta:
        model = get_user_model()
        fields = ('username', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                'パスワードが同じになっていません'
            )
        return password2

    def save(self, commit=True):
        user = super(SignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
