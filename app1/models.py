# coding=utf-8
import datetime

from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, UserManager
import django.db.models as m


class MyUser(AbstractBaseUser):
    username = m.CharField(max_length=40, unique=True, db_index=True)
    email = m.EmailField(max_length=255, unique=True, db_index=True)
    fb_token = m.TextField(null=True)
    fb_username = m.CharField(max_length=100, unique=True, null=True)
    fb_name = m.CharField(max_length=100, null=True)
    fb_updated = m.DateTimeField(null=True)
    tw_token = m.TextField(null=True)
    tw_secret = m.TextField(null=True)
    tw_name = m.TextField(null=True)
    tw_screen_name = m.TextField(null=True)
    tw_updated = m.DateTimeField(null=True)
    tw_profile_image_url = m.TextField(null=True)
    is_adult = m.BooleanField(default=True)
    is_active = m.BooleanField(default=True)
    is_admin = m.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = 'username'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def get_avatar_url(self):
        if not self.fb_updated:
            return self.tw__profile_image_url
        elif not self.tw_updated:
            return self.get_fb_avatar_url()
        if self.fb_updated < self.tw_updated:
            return self.tw_profile_image_url
        else:
            return self.get_fb_avatar_url()

    def get_fb_avatar_url(self):
        fb_avatar_url = 'http://graph.facebook.com/{0}/picture?type=large'
        return fb_avatar_url.format(self.fb_username)

    @property
    def is_staff(self):
        return self.is_admin


class EmailConfirmation(m.Model):
    user = m.ForeignKey(MyUser)
    email = m.EmailField(max_length=255, unique=True, db_index=True)
    verified = m.BooleanField(default=False)
    key = m.CharField(max_length=64, unique=True)
    created = m.DateTimeField(default=timezone.now)
    sent = m.DateTimeField(null=True)

    def key_expired(self):
        # TODO: 有効期限1日というハードコーディングをやめる
        expiration_date = self.sent + datetime.timedelta(days=1)
        return expiration_date <= timezone.now()
