from django.shortcuts import render
from flask import request

def index(request):
	return render(request, 'home.html')

def admin(request):
	return render(request, 'admin.html')

def contact(request):
	return render(request, 'contact-us.html')

def solar(request):
	return render(request, 'solar-generation.html')

def manufacturing(request):
	return render(request, 'manufacturing.html')

def login(request):
	if request.method == 'POST':
		return render(request, 'login.html', context={'resp': 'EATED??'})
	
	return render(request, 'login.html', context={'resp': 'bruh'})
