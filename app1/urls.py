# coding=utf-8
from django.conf.urls import patterns, url

import app1.views as v


urlpatterns = patterns(
    '',
    url(r'^hello$', v.hello),
    url(r'^facebook/login$', v.loginview),
    url(r'^facebook/callback$', v.callbackview),
    url(r'^twitter/login$', v.twitter_login),
    url(r'^twitter/callback$', v.twitter_callback),

    url(r'^signup$', v.SignupView.as_view()),
    url(r'^confirmation/(?P<key>\w+)$', v.confirmation),
    url(r'^login$', v.LoginView.as_view()),
    url(r'^logout$', v.logout),
)
