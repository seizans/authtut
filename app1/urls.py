# coding=utf-8
from django.conf.urls import patterns, url

import app1.views as v


urlpatterns = patterns(
    '',
    url(r'^hello$', v.HelloView.as_view()),
    url(r'^facebook/login$', v.loginview),
    url(r'^facebook/callback$', v.callbackview),
    url(r'^twitter/login$', v.twitter_login),
    url(r'^twitter/callback$', v.twitter_callback),

    url(r'^signup$', v.SignupView.as_view()),
    # TODO: reverse()を使わないようにしてこのnameも消す
    url(r'^confirmation/(?P<key>\w+)/$', v.ConfirmationView.as_view(),
        name=u'confirmation'),
)
