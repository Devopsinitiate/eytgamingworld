
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Avg, Count
from datetime import datetime, timedelta
from .models import (CoachProfile, CoachGameExpertise, CoachAvailability,
                     CoachingSession, SessionReview, CoachingPackage)
from .forms import (CoachProfileForm, AvailabilityFormSet, BookingForm,
                   SessionReviewForm, PackageForm)
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class CoachListView(ListView):
    """List all active coaches"""
    model = CoachProfile
    template_name = 'coaching/coach_list.html'
    context_object_name = 'coaches'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = CoachProfile.objects.filter(
            is_verified=True,
            status='active'
        ).select_related('user').prefetch_related('game_expertise__game')
        
        # Filter by game
        game = self.request.GET.get('game')
        if game:
            queryset = queryset.filter(game_expertise__game__slug=game)
        
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(hourly_rate__gte=min_price)
        if max_price:
            queryset = queryset.filter(hourly_rate__lte=max_price)
        
        # Filter by experience
        experience = self.request.GET.get('experience')
        if experience:
            queryset = queryset.filter(experience_level=experience)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(bio__icontains=search) |
                Q(achievements__icontains=search)
            )
        
        # Sort
        sort = self.request.GET.get('sort', '-average_rating')
        valid_sorts = ['-average_rating', 'hourly_rate', '-hourly_rate',
                       '-total_sessions', '-created_at']
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)
        
        return queryset.distinct()


class CoachDetailView(DetailView):
    """Coach profile detail page"""
    model = CoachProfile
    template_name = 'coaching/coach_detail.html'
    context_object_name = 'coach'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        coach = self.object
        
        # Get games taught
        context['games'] = coach.game_expertise.select_related('game').all()
        
        # Get availability
        context['availability'] = coach.availability.filter(is_active=True).order_by('weekday')
        
        # Get reviews
        context['reviews'] = coach.reviews.filter(
            is_approved=True
        ).select_related('student', 'session').order_by('-created_at')[:10]
        
        # Get packages
        context['packages'] = coach.packages.filter(is_active=True)
        
        # Statistics
        context['stats'] = {
            'total_sessions': coach.total_sessions,
            'total_students': coach.total_students,
            'average_rating': coach.average_rating,
            'total_reviews': coach.total_reviews,
        }
        
        return context


class CoachProfileCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create coach profile"""
    model = CoachProfile
    form_class = CoachProfileForm
    template_name = 'coaching/coach_form.html'
    
    def test_func(self):
        return self.request.user.can_coach() and not hasattr(self.request.user, 'coach_profile')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Coach profile created! Add your availability and games.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('coaching:coach_edit', kwargs={'pk': self.object.pk})


class CoachProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit coach profile"""
    model = CoachProfile
    form_class = CoachProfileForm
    template_name = 'coaching/coach_form.html'
    
    def test_func(self):
        return self.get_object().user == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['availability_formset'] = AvailabilityFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['availability_formset'] = AvailabilityFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        availability_formset = context['availability_formset']
        
        if availability_formset.is_valid():
            self.object = form.save()
            availability_formset.instance = self.object
            availability_formset.save()
            messages.success(self.request, 'Profile updated successfully!')
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        return reverse('coaching:coach_detail', kwargs={'pk': self.object.pk})


@login_required
def book_session(request, coach_pk):
    """Book a coaching session"""
    coach = get_object_or_404(CoachProfile, pk=coach_pk)
    
    if not coach.is_available:
        messages.error(request, 'This coach is not currently accepting bookings.')
        return redirect('coaching:coach_detail', pk=coach_pk)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, coach=coach)
        if form.is_valid():
            # Create Stripe payment intent
            try:
                session_obj = form.save(commit=False)
                session_obj.coach = coach
                session_obj.student = request.user
                session_obj.status = 'pending'
                
                # Calculate price
                duration_hours = session_obj.duration_minutes / 60
                game_expertise = coach.game_expertise.filter(
                    game=session_obj.game
                ).first()
                
                rate = game_expertise.effective_rate if game_expertise else coach.hourly_rate
                session_obj.price = rate * duration_hours
                
                # Create Stripe payment intent
                intent = stripe.PaymentIntent.create(
                    amount=int(session_obj.price * 100),  # Convert to cents
                    currency='usd',
                    metadata={
                        'coach_id': str(coach.id),
                        'student_id': str(request.user.id),
                        'game_id': str(session_obj.game.id),
                    }
                )
                
                session_obj.payment_intent_id = intent.id
                session_obj.save()
                
                # Redirect to payment
                return redirect('coaching:session_payment', pk=session_obj.pk)
                
            except stripe.error.StripeError as e:
                messages.error(request, f'Payment error: {str(e)}')
                return redirect('coaching:book_session', coach_pk=coach_pk)
    else:
        form = BookingForm(coach=coach)
    
    return render(request, 'coaching/book_session.html', {
        'form': form,
        'coach': coach
    })


@login_required
def session_payment(request, pk):
    """Handle session payment"""
    session = get_object_or_404(CoachingSession, pk=pk)
    
    if session.student != request.user:
        return HttpResponseForbidden()
    
    if session.is_paid:
        messages.info(request, 'This session is already paid for.')
        return redirect('coaching:session_detail', pk=pk)
    
    # Get Stripe publishable key
    context = {
        'session': session,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'payment_intent_client_secret': session.payment_intent_id,
    }
    
    return render(request, 'coaching/session_payment.html', context)


@login_required
def confirm_payment(request, pk):
    """Confirm payment and update session"""
    session = get_object_or_404(CoachingSession, pk=pk)
    
    if session.student != request.user:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        # Verify payment with Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(session.payment_intent_id)
            
            if intent.status == 'succeeded':
                session.is_paid = True
                session.status = 'confirmed'
                session.save()
                
                messages.success(request, 'Payment successful! Your session is confirmed.')
                
                # Send confirmation email (via Celery task)
                from .tasks import send_session_confirmation
                send_session_confirmation.delay(session.id)
                
                return redirect('coaching:session_detail', pk=pk)
            else:
                messages.error(request, 'Payment not completed. Please try again.')
                
        except stripe.error.StripeError as e:
            messages.error(request, f'Error verifying payment: {str(e)}')
    
    return redirect('coaching:session_payment', pk=pk)


class SessionListView(LoginRequiredMixin, ListView):
    """List user's coaching sessions"""
    model = CoachingSession
    template_name = 'coaching/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # Show sessions where user is coach or student
        queryset = CoachingSession.objects.filter(
            Q(coach__user=user) | Q(student=user)
        ).select_related('coach__user', 'student', 'game').order_by('-scheduled_start')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type (as coach or student)
        view_type = self.request.GET.get('type')
        if view_type == 'coaching':
            queryset = queryset.filter(coach__user=user)
        elif view_type == 'learning':
            queryset = queryset.filter(student=user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Upcoming sessions
        context['upcoming_sessions'] = CoachingSession.objects.filter(
            Q(coach__user=user) | Q(student=user),
            status__in=['pending', 'confirmed'],
            scheduled_start__gte=timezone.now()
        ).order_by('scheduled_start')[:5]
        
        return context


class SessionDetailView(LoginRequiredMixin, DetailView):
    """Session detail page"""
    model = CoachingSession
    template_name = 'coaching/session_detail.html'
    context_object_name = 'session'
    
    def get_queryset(self):
        # Only show sessions where user is involved
        return CoachingSession.objects.filter(
            Q(coach__user=self.request.user) | Q(student=self.request.user)
        ).select_related('coach__user', 'student', 'game')


@login_required
def cancel_session(request, pk):
    """Cancel a coaching session"""
    session = get_object_or_404(CoachingSession, pk=pk)
    
    # Check if user is involved in session
    if session.coach.user != request.user and session.student != request.user:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        if session.cancel_session(request.user, reason):
            # Process refund if paid
            if session.is_paid:
                try:
                    stripe.Refund.create(
                        payment_intent=session.payment_intent_id,
                        reason='requested_by_customer'
                    )
                    messages.success(request, 'Session cancelled and refund initiated.')
                except stripe.error.StripeError as e:
                    messages.warning(request, f'Session cancelled but refund failed: {str(e)}')
            else:
                messages.success(request, 'Session cancelled successfully.')
            
            # Send cancellation notification
            from .tasks import send_cancellation_notification
            send_cancellation_notification.delay(session.id)
            
        else:
            messages.error(request, 'Cannot cancel session (must be 24h before start).')
        
        return redirect('coaching:session_detail', pk=pk)
    
    return render(request, 'coaching/cancel_session.html', {'session': session})


@login_required
def start_session(request, pk):
    """Start a coaching session"""
    session = get_object_or_404(CoachingSession, pk=pk)
    
    if session.coach.user != request.user:
        return HttpResponseForbidden()
    
    if session.start_session():
        messages.success(request, 'Session started!')
        
        # Generate video call link if not exists
        if not session.video_link:
            # Here you would integrate with Daily.co, Whereby, etc.
            # For now, just use coach's platform
            session.video_link = f"https://discord.gg/{session.coach.platform_username}"
            session.save()
    else:
        messages.error(request, 'Cannot start session.')
    
    return redirect('coaching:session_detail', pk=pk)


@login_required
def complete_session(request, pk):
    """Complete a coaching session"""
    session = get_object_or_404(CoachingSession, pk=pk)
    
    if session.coach.user != request.user:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        notes = request.POST.get('coach_notes', '')
        session.coach_notes = notes
        
        if session.complete_session():
            messages.success(request, 'Session completed! Student can now leave a review.')
        else:
            messages.error(request, 'Cannot complete session.')
        
        return redirect('coaching:session_detail', pk=pk)
    
    return render(request, 'coaching/complete_session.html', {'session': session})


@login_required
def review_session(request, pk):
    """Leave a review for completed session"""
    session = get_object_or_404(CoachingSession, pk=pk, student=request.user,
                                status='completed')
    
    # Check if review already exists
    if hasattr(session, 'review'):
        messages.info(request, 'You already reviewed this session.')
        return redirect('coaching:session_detail', pk=pk)
    
    if request.method == 'POST':
        form = SessionReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.session = session
            review.coach = session.coach
            review.student = request.user
            review.save()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('coaching:coach_detail', pk=session.coach.pk)
    else:
        form = SessionReviewForm()
    
    return render(request, 'coaching/review_session.html', {
        'session': session,
        'form': form
    })


class PackageListView(ListView):
    """List coaching packages"""
    model = CoachingPackage
    template_name = 'coaching/package_list.html'
    context_object_name = 'packages'
    paginate_by = 12
    
    def get_queryset(self):
        return CoachingPackage.objects.filter(
            is_active=True,
            coach__is_verified=True,
            coach__status='active'
        ).select_related('coach__user', 'game')


@login_required
def purchase_package(request, pk):
    """Purchase a coaching package"""
    package = get_object_or_404(CoachingPackage, pk=pk, is_active=True)
    
    if request.method == 'POST':
        try:
            # Create Stripe payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(package.total_price * 100),
                currency='usd',
                metadata={
                    'package_id': str(package.id),
                    'student_id': str(request.user.id),
                }
            )
            
            # Create package purchase
            from .models import PackagePurchase
            purchase = PackagePurchase.objects.create(
                package=package,
                student=request.user,
                sessions_remaining=package.number_of_sessions,
                amount_paid=package.total_price,
                payment_intent_id=intent.id,
                expires_at=timezone.now() + timedelta(days=package.valid_for_days),
                status='active'
            )
            
            return redirect('coaching:package_payment', pk=purchase.pk)
            
        except stripe.error.StripeError as e:
            messages.error(request, f'Payment error: {str(e)}')
    
    return render(request, 'coaching/purchase_package.html', {'package': package})


def get_available_slots(request, coach_pk):
    """API endpoint to get available time slots"""
    try:
        coach = get_object_or_404(CoachProfile, pk=coach_pk)
        date_str = request.GET.get('date')
        
        if not date_str:
            return JsonResponse({'error': 'Date required'}, status=400)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Ensure date is not in the past
        if date < timezone.now().date():
            return JsonResponse({'slots': []})  # No slots for past dates
        
        # Get coach's availability for this weekday
        weekday = date.weekday()
        availability = coach.availability.filter(weekday=weekday, is_active=True)
        
        if not availability.exists():
            return JsonResponse({'slots': []})  # No availability for this day
        
        # Get session increment with fallback
        session_increment = getattr(coach, 'session_increment', 30)
        if not session_increment or session_increment <= 0:
            session_increment = 30
        
        # Get existing bookings
        existing_sessions = CoachingSession.objects.filter(
            coach=coach,
            scheduled_start__date=date,
            status__in=['pending', 'confirmed', 'in_progress']
        ).values_list('scheduled_start', 'scheduled_end')
        
        # Generate available slots
        slots = []
        current_time = timezone.now()
        
        for avail in availability:
            # Create timezone-aware datetimes
            start_datetime = timezone.make_aware(datetime.combine(date, avail.start_time))
            end_datetime = timezone.make_aware(datetime.combine(date, avail.end_time))
            
            # If the date is today, start from current time + buffer
            if date == timezone.now().date():
                buffer_time = current_time + timedelta(hours=1)  # 1 hour buffer
                if start_datetime < buffer_time:
                    start_datetime = buffer_time
            
            current = start_datetime
            while current < end_datetime:
                slot_end = current + timedelta(minutes=session_increment)
                
                # Don't create slots that extend past availability end time
                if slot_end > end_datetime:
                    break
                
                # Check if slot is available
                is_available = True
                for session_start, session_end in existing_sessions:
                    # Ensure session times are timezone-aware
                    if timezone.is_naive(session_start):
                        session_start = timezone.make_aware(session_start)
                    if timezone.is_naive(session_end):
                        session_end = timezone.make_aware(session_end)
                    
                    # Check for overlap
                    if (current < session_end and slot_end > session_start):
                        is_available = False
                        break
                
                if is_available:
                    slots.append({
                        'time': current.strftime('%I:%M %p'),  # 12-hour format
                        'datetime': current.isoformat()
                    })
                
                current = slot_end
        
        return JsonResponse({'slots': slots})
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_available_slots: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'An error occurred loading time slots'}, status=500)