"""Browser and API request handlers, grouped by feature."""
from contextlib import redirect_stdout
from io import StringIO

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, ProgrammingError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .forms import ProfileUpdateForm
from .models import CustomUser, Role, ensure_default_roles
from .serializers import RoleSerializer, SignupSerializer

# Authentication

def host_url(request):
    return request.build_absolute_uri('/')[:-1]


def register_view(request):
    roles = []
    api_url = f'{host_url(request)}{reverse("signup_api")}'

    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            roles = response.json().get('data', [])
    except requests.RequestException:
        ensure_default_roles()
        roles = RoleSerializer(Role.objects.all(), many=True).data

    if request.method == 'POST':
        payload = {
            'email': request.POST.get('email'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'role_id': request.POST.get('role_id'),
            'phone_number': request.POST.get('phone_number'),
            'password': request.POST.get('password'),
        }

        try:
            response = requests.post(api_url, json=payload, timeout=10)
            data = response.json()
        except requests.RequestException as exc:
            messages.error(request, f'API connection error: {exc}')
            return render(request, 'authentication/register.html', {'roles': roles})

        if response.status_code == 201:
            messages.success(request, data.get('message', 'Account created successfully.'))
            return redirect('login')

        messages.error(request, data.get('message', 'Registration failed.'))
        return render(request, 'authentication/register.html', {
            'roles': roles,
            'errors': data.get('errors', {}),
            'form_data': request.POST,
        })

    return render(request, 'authentication/register.html', {'roles': roles})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')
        api_url = f'{host_url(request)}{reverse("obtain_token")}'

        try:
            response = requests.post(api_url, json={
                'username': username,
                'password': password,
            }, timeout=10)
            data = response.json()
        except requests.RequestException as exc:
            messages.error(request, f'API connection error: {exc}')
            return render(request, 'authentication/login.html')

        if response.status_code == 200:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
            request.session['auth_token'] = data['token']
            request.session['user_role'] = data['user_role']
            messages.success(request, data.get('message', 'Logged in successfully.'))
            return redirect('dashboard')

        messages.error(request, data.get('error', 'Invalid credentials.'))

    return render(request, 'authentication/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    form = ProfileUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'authentication/profile.html', {'form': form})


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def obtain_token(request):
    username = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return JsonResponse({'error': 'Email and password are required.'}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        if not user.is_superuser and not getattr(user, 'is_approved', False):
            return JsonResponse({
                'error': 'Your account is awaiting admin approval.'
            }, status=403)

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)

        user_role = CustomUser.objects.filter(id=user.id).values(
            'email',
            'id',
            'first_name',
            'last_name',
            'phone_number',
            'role_id',
            'role_id__role',
        ).first()

        return JsonResponse({
            'user_id': user.id,
            'token': token.key,
            'status': 'success',
            'user_role': user_role,
            'message': 'Logged in successfully',
        }, status=200)

    return JsonResponse({'error': 'Invalid credentials.'}, status=400)


@csrf_exempt
@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def signup_api(request):
    ensure_default_roles()

    if request.method == 'POST':
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'status': 'success',
                'message': 'User created successfully. Your account is awaiting admin approval.',
                'data': SignupSerializer(user).data,
                'token': token.key,
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Validation failed',
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    roles = Role.objects.all()
    serializer = RoleSerializer(roles, many=True)
    return Response({
        'status': 'success',
        'message': 'Roles fetched successfully',
        'data': serializer.data,
    }, status=status.HTTP_200_OK)


