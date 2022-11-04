from django.shortcuts import render


def getStatusText(request):
    return "Login"


def index(request):
    solar_arrays = []
    power_generation = []

    return render(request, 'home.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def admin(request):
    return render(request, 'admin.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def contact(request):
    if request.method == 'POST':
        print(request.POST['name'])
        print(request.POST['email'])
        print(request.POST['phone number'])
        # bytes of files do what u want with it, prob should also do like checks if these actually exist etc
        print(request.FILES['file'].read())
        # do all ur checks here and stuff

        return render(request, 'contact-us.html', context=({'resp': 'Thank you for contacting us. We will get back to you shortly.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))

    return render(request, 'contact-us.html', context=({'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))


def solar(request):
    return render(request, 'solar-generation.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def manufacturing(request):
    return render(request, 'manufacturing.html', context={'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)})


def login(request):
    if request.method == 'POST':
        return render(request, 'login.html', context=({'resp': 'Login Failed. Please try again.', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))
        # do all ur checks here and stuff

    return render(request, 'login.html', context=({'resp': '', 'userStateHref': getStatusText(request).lower(), 'userStateText': getStatusText(request)}))
