from django.shortcuts import render

def myapp_view(request):
    return render(request, 'subplayer.html')
