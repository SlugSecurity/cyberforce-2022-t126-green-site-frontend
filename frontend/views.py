from django.shortcuts import render, redirect

import requests


def getStatusText(request):
    if request.COOKIES.get('token') == None:
        return 'Login'
    else:
        return 'Admin'


def index(request):
    r = requests.get('http://127.0.0.1:8080/api/solar')
    solar_arrays = []

    if r.status_code == 200:
        solar_arrays = r.json()

    return render(request, 'home.html', context={
        'userStateHref': getStatusText(request).lower(),
        'userStateText': getStatusText(request),
        'solarArrays': solar_arrays})


def admin(request):
    return render(request, 'admin.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def contact(request):
    if request.method == 'POST':
        # TODO: Need validators for max size to ensure we're not receiving/sending too much data.
        headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR']}
        r_email = requests.post('http://127.0.0.1:8080/api/emails', headers=headers, json={
            'subject': 'Contact Us Submission - ' + request.POST['name'],
            'from': request.POST['name'] + ' <' + request.POST['email'] + '>',
            'body': 'Name: ' + request.POST['name'] + '\nEmail: ' + request.POST['email'] + '\nPhone Number: ' + request.POST['phone number']})

        r_file = requests.post(
            'http://127.0.0.1:8080/api/files', headers=headers, files={'file': request.FILES['file']})

        if r_email.status_code == 200 and r_file.status_code == 200:
            return render(request, 'contact-us.html', context=({'resp': 'Thank you for contacting us. We will get back to you shortly.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

        return render(request, 'contact-us.html', context=({'resp': 'Form submission error, check form contents and file name length.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

    return render(request, 'contact-us.html', context=({'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))


def solar(request):
    return render(request, 'solar-generation.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def manufacturing(request):
    return render(request, 'manufacturing.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def login(request):
    if request.method == 'POST':
        # TODO: Need validators for max size to ensure we're not receiving/sending too much data.
        headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR']}
        r = requests.post('http://127.0.0.1:8080/api/login', headers=headers, json={
            'username': request.POST['username'],
            'password': request.POST['password']})

        if r.status_code == 200:
            response = redirect('/')
            token = r.json().get('token')

            if token is not None:
                response.set_cookie('token', token)

            return response

        return render(request, 'login.html', context=({'resp': 'Login Failed. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

    return render(request, 'login.html', context=({'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))
