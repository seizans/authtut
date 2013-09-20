# coding=utf-8
import datetime

from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
import django.db.models as m


class MyUser(AbstractBaseUser):
    username = m.CharField(max_length=40, unique=True, db_index=True)
    email = m.EmailField(max_length=255, unique=True, db_index=True)
    is_adult = m.BooleanField(default=True)
    is_active = m.BooleanField(default=True)
    is_admin = m.BooleanField(default=False)
    USERNAME_FIELD = 'username'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

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
        expiration_date = self.sent + datetime.timedelta(days=1)
        return expiration_date <= timezone.now()
