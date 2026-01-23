# tasks_api/views_account.py
"""Account API endpoints for registration, login, and profile management."""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Account
from .serializers import (
    AccountSerializer, AccountRegisterSerializer, AccountLoginSerializer,
    AccountUpdateSerializer, ChangePasswordSerializer
)


@api_view(['POST'])
def register(request):
    """Register a new account."""
    serializer = AccountRegisterSerializer(data=request.data)
    if serializer.is_valid():
        account = serializer.save()
        return Response({
            'message': 'Account created successfully',
            'account': AccountSerializer(account).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    """Authenticate an account and return account details."""
    serializer = AccountLoginSerializer(data=request.data)
    if serializer.is_valid():
        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']

        # Try to authenticate
        account = Account.authenticate(username_or_email, password)
        if account:
            # Update last login
            from django.utils import timezone
            account.last_login = timezone.now()
            account.save(update_fields=['last_login'])

            return Response({
                'message': 'Login successful',
                'account': AccountSerializer(account).data
            })
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def profile(request):
    """Get account profile by user_id."""
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({'error': 'user_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id=user_id)
        return Response(AccountSerializer(account).data)
    except Account.DoesNotExist:
        return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def update_profile(request):
    """Update account profile."""
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id=user_id)
        serializer = AccountUpdateSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'account': AccountSerializer(account).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Account.DoesNotExist:
        return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def change_password(request):
    """Change account password."""
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id=user_id)
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']

            # Verify current password
            if not account.check_password(current_password):
                return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

            # Set new password
            account.set_password(new_password)
            account.save()

            return Response({'message': 'Password changed successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Account.DoesNotExist:
        return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def list_accounts(request):
    """List all accounts (for admin/development purposes)."""
    accounts = Account.objects.filter(is_active=True)
    serializer = AccountSerializer(accounts, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_account(request):
    """Delete an account (soft delete by setting is_active=False)."""
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account = Account.objects.get(id=user_id)
        account.is_active = False
        account.save()
        return Response({'message': 'Account deleted successfully'})
    except Account.DoesNotExist:
        return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
