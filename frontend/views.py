from django import forms
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from ratelimit.decorators import ratelimit
from queue import Queue

import ftplib
import re
import requests
import threading

token = "3910caf078b1f37d4a611d0b1f25d92bc729d61fb97e4935960b2c50216e7c2e"


class FTP_TLS_FIXED(ftplib.FTP_TLS):
    """Explicit FTPS, with shared TLS session"""

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(conn,
                                            server_hostname=self.host,
                                            session=self.sock.session)

        return conn, size


def ftp_chunk_iterator(FTP, command):
    queue = Queue(maxsize=4096)

    def ftp_thread_target():
        FTP.retrbinary(command, callback=queue.put)
        queue.put(None)

    ftp_thread = threading.Thread(target=ftp_thread_target)
    ftp_thread.start()

    while True:
        chunk = queue.get()
        if chunk is not None:
            yield chunk
        else:
            return


class ContactForm(forms.Form):
    name = forms.CharField(label='Name', max_length=100, required=True,
                           widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    email = forms.EmailField(label='Email', max_length=100, required=True,
                             widget=forms.TextInput(attrs={'placeholder': 'Email'}))
    phone_number = forms.CharField(label='Phone Number', max_length=100, required=True,
                                   widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))
    file = forms.FileField(label='File', required=True)


def getStatusText(request):
    if request.COOKIES.get('user') == None:
        return 'Login'
    
    if request.COOKIES.get('token') == None:
        return 'Logout'
    else:
        return 'Admin'


@ratelimit(key='ip', rate='3/s', block=True)
def index(request):
    solar_arrays = None
    headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR']}

    try:
        r = requests.get('http://127.0.0.1:8080/api/solar', headers=headers)
    except:
        return render(request, 'home.html', context={
            'userStateHref': getStatusText(request).lower(),
            'userStateText': getStatusText(request)})

    if r.status_code == 200:
        solar_arrays = r.json()

    return render(request, 'home.html', context={
        'userStateHref': getStatusText(request).lower(),
        'userStateText': getStatusText(request),
        'solarArrays': solar_arrays
    })


@ratelimit(key='ip', rate='3/s', block=True)
def admin(request):
    # No token. Redirect to login page.
    if request.COOKIES.get('token') != token:
        return redirect('/login')

    emails = None
    headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR'],
               'Authorization': 'Bearer ' + request.COOKIES.get('token')}

    try:
        ftps = FTP_TLS_FIXED()
        ftps.connect('10.0.126.73')
        ftps.login()
        ftps.prot_p()
        ftps.set_pasv(True)
        file_names = ftps.nlst()
        files = []

        for file_name_orig in file_names:
            try:
                # Take the 128-bit file ID away from the file name.
                file_name = file_name_orig[32:]
                file_id = file_name_orig[:32]
            except:
                continue

            files.append({'name': file_name, 'id': file_id})
    except:
        ftps.close()
        return render(request, 'admin.html', context={'userStateHref': 'logout', 'userStateText': 'Logout'})

    if request.method == 'POST':
        file_id = request.POST.get('file')

        if file_id is not None:
            for file in files:
                if file['id'] == file_id:
                    try:
                        return StreamingHttpResponse(streaming_content=ftp_chunk_iterator(
                            ftps, 'RETR ' + file['id'] + file['name']), headers={
                            'Content-Disposition': 'attachment; filename="' + file['name'] + '"'})
                    except:
                        pass

                    break

    ftps.close()

    try:
        r = requests.get('http://127.0.0.1:8080/api/emails', headers=headers)
    except:
        return render(request, 'admin.html', context={'userStateHref': 'logout', 'userStateText': 'Logout'})

    if r.status_code == 200:
        emails = r.json()

    return render(request, 'admin.html', context={
        'userStateHref': 'logout', 
        'userStateText': 'Logout',
        'files': files,
        'emails': emails
    })


@ratelimit(key='ip', rate='3/s', block=True)
def contact(request):
    form = ContactForm()

    if request.method == 'POST':
        try:
            contact_name = request.POST.get('name')
            contact_email = request.POST.get('email')
            contact_phone = request.POST.get('phone_number')
            contact_file = request.FILES.get('file')

            if contact_name is None or contact_email is None or contact_phone is None or contact_file is None:
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'Missing required field.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            if 0 > len(contact_name) > 100:
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'Name must be between 1 and 100 characters.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            if 0 > len(contact_email) > 100:
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'Email must be between 1 and 100 characters.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            if not re.match('([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+', contact_email):
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'Email is not valid.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            if 0 > len(contact_phone) > 20:
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'Phone number must be between 1 and 20 characters.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            if contact_file.size > 10485760:
                return render(request, 'contact-us.html', context={'form': form, 'resp': 'File is larger than 10MB', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})

            try:
                headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR']}
                r_email = requests.post('http://127.0.0.1:8080/api/emails', headers=headers, json={
                    'subject': 'Contact Us Submission - ' + contact_name,
                    'from_name': contact_name,
                    'from_email': contact_email,
                    'body': 'Name: ' + contact_name + '\nEmail: ' + contact_email + '\nPhone Number: ' + contact_phone})

                r_file = requests.post(
                    'http://127.0.0.1:8080/api/files', headers=headers, files={'file': contact_file})

                if r_email.status_code == 200 and r_file.status_code == 200:
                    return render(request, 'contact-us.html', context=({'hide_submit': True, 'resp': 'Thank you for contacting us. We will get back to you shortly.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

                return render(request, 'contact-us.html', context=({'hide_submit': True, 'resp': 'An internal server error occured. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))
            except:
                return render(request, 'contact-us.html', context=({'hide_submit': True, 'resp': 'Failed to connect to the server. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))
        except Exception as e:
            return render(request, 'contact-us.html', context=({'hide_submit': True, 'resp': 'An error occurred. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

    return render(request, 'contact-us.html', context=({'form': form, 'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))


@ratelimit(key='ip', rate='3/s', block=True)
def solar(request):
    return render(request, 'solar-generation.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


@ratelimit(key='ip', rate='3/s', block=True)
def manufacturing(request):
    return render(request, 'manufacturing.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


@ratelimit(key='ip', rate='3/s', block=True)
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username is None or password is None:
            return render(request, 'login.html', context=({'resp': 'Missing required field.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

        if 0 > len(username) > 100 or 0 > len(password) > 100:
            return render(request, 'login.html', context=({'resp': 'Login Failed. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

        try:
            headers = {'Forwarded': 'for=' + request.META['REMOTE_ADDR']}
            r = requests.post('http://127.0.0.1:8080/api/login', headers=headers, json={
                'username': username,
                'password': password})
        except:
            return render(request, 'login.html', context=({'resp': 'Failed to connect to the server. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

        if r.status_code == 200:
            response = redirect('/')
            response.set_cookie('user', username)
            token = r.json().get('token')

            if token is not None:
                response.set_cookie('token', token)

            return response

        return render(request, 'login.html', context=({'resp': 'Login Failed. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

    return render(request, 'login.html', context=({'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

@ratelimit(key='ip', rate='3/s', block=True)
def logout(request):
	response = redirect('/')
	response.delete_cookie('user')
	response.delete_cookie('token')
	return response