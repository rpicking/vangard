from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'main/home.html')

def request(request):
    return render(request, 'main/request.html')
