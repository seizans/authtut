from django.views.generic import TemplateView


class HelloView(TemplateView):
    template_name = 'app1/hello.html'
