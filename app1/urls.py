from django.conf.urls import patterns, url

import app1.views as v


urlpatterns = patterns(
    '',
    url(r'^hello$', v.HelloView.as_view()),
)
