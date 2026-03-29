from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def become_organizer(request):
    """
    Public landing page explaining the organizer program.
    Authenticated users who are already organizers are redirected to dashboard.
    """
    if request.user.is_authenticated and request.user.can_organize_tournaments():
        messages.info(request, 'You are already an organizer.')
        return redirect('dashboard:home')

    if request.method == 'POST' and request.user.is_authenticated:
        # Upgrade the user's role to organizer
        user = request.user
        user.role = 'organizer'
        user.save(update_fields=['role'])
        messages.success(request, 'Congratulations! Your account has been upgraded to Organizer. You can now create tournaments and list venues.')
        return redirect('tournaments:create')

    return render(request, 'accounts/become_organizer.html')
