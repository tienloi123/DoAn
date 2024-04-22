from django.shortcuts import render, redirect
from userauths.forms import UserRegisterForm, ProfileForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

from django.conf import settings

from userauths.models import Profile

User = settings.AUTH_USER_MODEL


# Create your views here.
def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST or None)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, f"Hello {username}, You account was create successfully.")
            # new_user = authenticate(username=form.cleaned_data['email'],
            #                         password=form.cleaned_data['password1'])
            # login(request, new_user)
            return redirect("userauths:sign-in")

    else:
        form = UserRegisterForm()

    context = {
        'form': form,
    }

    return render(request, "userauths/sign-up.html", context)


def login_view(request):
    if request.user.is_authenticated:
        messages.warning(request, f"You are already logged in")
        return redirect("core:index")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        print("Email:", email)
        print("Password:", password)

        try:
            user = authenticate(request, email=email, password=password)
            print("User:", user)
            if user is not None:
                login(request, user)
                messages.success(request, "You are logged in.")
                return redirect("core:index")
            else:
                messages.warning(request, "Invalid credentials. Please register account.")
        except Exception:
            print(Exception)
            messages.warning(request, f"User with {email} does not exist")
    return render(request, "userauths/sign-in.html")


def logout_view(request):
    logout(request)
    messages.success(request, "you logged out")
    return redirect("userauths:sign-in")
def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            return redirect("core:dashboard")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }
    return render(request, "userauths/profile-edit.html", context)
