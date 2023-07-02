from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from accounts.forms import UserRegistrationForm

User = get_user_model()

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration or redirect to a login page
            # You can customize this based on your requirements
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})
