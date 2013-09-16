from django.conf.urls import patterns, url

import app1.views as v


urlpatterns = patterns(
    '',
    url(r'^hello$', v.HelloView.as_view()),
    url(r'^facebook/login$', v.loginview),
    url(r'^facebook/callback$', v.callbackview),
)
