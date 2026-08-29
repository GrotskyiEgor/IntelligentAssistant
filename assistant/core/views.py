from django.shortcuts import render
from django.views import View

# def render_home(request):
#     return render(request, 'core/core.html')

class Core(View):
    template_name = "core/core.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name) 
    
    def post(self, request, *args, **kwargs):

        command = request.POST.get('command')
        print("command", command)

        return render(request, 'core/core.html', {"success": True}) 