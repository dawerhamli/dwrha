"""
Views for game app
"""
import json
import logging
import random
import re
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from companies.models import Company
from companies.utils import decrypt_slug
from .models import GameSpin

# Set up logger
logger = logging.getLogger(__name__)


def select_weighted_prize(company, prizes):
    """
    Select a prize using weighted random algorithm based on percentages.
    
    Algorithm:
    1. Get prize percentages from company notes (if available)
    2. Use percentages directly as weights (higher percentage = higher chance)
    3. Normalize weights to ensure they sum to 1
    4. Select prize based on weighted random
    
    The percentages represent the probability of winning each prize:
    - Higher percentage = higher chance to win
    - Lower percentage = lower chance to win
    
    Returns:
        str: The selected prize name
    """
    # Ensure prizes list is not empty
    if not prizes:
        logger.error(f"Company {company.name} has no prizes")
        return None
    
    # Try to get prize percentages from notes
    prize_percentages = None
    
    if company.notes:
        try:
            notes_data = json.loads(company.notes)
            if 'prize_percentages' in notes_data:
                prize_percentages = notes_data['prize_percentages']
                logger.info(f"Company {company.name}: Using custom percentages: {prize_percentages}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Company {company.name}: Could not parse prize percentages from notes: {e}")
    
    # If no percentages stored or length mismatch, use equal distribution
    if not prize_percentages or len(prize_percentages) != len(prizes):
        equal_percentage = 100 / len(prizes)
        prize_percentages = [equal_percentage] * len(prizes)
        logger.info(f"Company {company.name}: Using equal distribution ({equal_percentage}% each)")
    
    # Convert percentages to weights (0-1 range)
    # Higher percentage = higher weight = higher probability
    # The percentages are already normalized to sum to 100, but we normalize again
    # to ensure accuracy even if there are slight rounding errors
    weights = [float(p) / 100.0 for p in prize_percentages]
    
    # Normalize weights to sum to 1 (probability distribution)
    # This ensures that if percentages don't sum to exactly 100, they're still valid
    # This also handles cases where percentages sum to 300% or any other value
    total_weight = sum(weights)
    if total_weight > 0:
        # Normalize: divide each weight by total to get probabilities that sum to 1
        normalized_weights = [w / total_weight for w in weights]
    else:
        # Fallback: equal weights if all are zero
        logger.warning(f"Company {company.name}: All weights are zero, using equal distribution")
        normalized_weights = [1.0 / len(prizes)] * len(prizes)
    
    # Log the weights and prizes for debugging
    if settings.DEBUG:
        logger.debug(f"Company {company.name} - Prize selection weights:")
        for prize, weight, percentage in zip(prizes, normalized_weights, prize_percentages):
            logger.debug(f"  {prize}: {percentage}% (weight: {weight:.4f})")
    
    # Select prize based on weighted random
    # random.choices uses weights directly - higher weight = higher probability
    selected_prize = random.choices(prizes, weights=normalized_weights, k=1)[0]
    
    # Find the index of selected prize for logging
    selected_index = prizes.index(selected_prize) if selected_prize in prizes else -1
    
    logger.info(
        f"Company {company.name}: Selected prize '{selected_prize}' "
        f"(index: {selected_index}, percentage: {prize_percentages[selected_index] if selected_index >= 0 else 'N/A'}%, "
        f"weight: {normalized_weights[selected_index] if selected_index >= 0 else 'N/A':.4f})"
    )
    
    return selected_prize


def play_game(request, token):
    """Game page view"""
    # Decrypt the token to get the slug
    slug = decrypt_slug(token)
    if not slug:
        from django.http import Http404
        raise Http404("Invalid or expired link")
    
    company = get_object_or_404(Company, slug=slug)
    
    # Get and normalize prizes (remove extra spaces) to ensure consistency
    prizes = company.get_prizes_list()
    prizes = [str(p).strip() for p in prizes if p]  # Normalize and filter empty
    
    # Get colors
    colors = company.get_colors_list()
    
    # Log prizes for debugging
    if settings.DEBUG:
        logger.debug(f"Company {company.slug} - Play page loaded:")
        logger.debug(f"  Prizes: {prizes}")
        logger.debug(f"  Colors: {colors}")
        logger.debug(f"  Is active: {company.is_currently_active}")
    
    # Get encrypted token for API calls
    from companies.utils import encrypt_slug
    encrypted_token = encrypt_slug(slug) or token
    
    # Always show the play page, but pass activation status
    context = {
        'company': company,
        'prizes': prizes,  # Already normalized
        'colors': colors,
        'status': company.status,
        'is_active': company.is_currently_active,
        'activation_end_time': company.activation_end_time,
        'encrypted_token': encrypted_token,
    }
    
    return render(request, 'game/play.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def spin_wheel(request, token):
    """Handle wheel spin"""
    try:
        # Decrypt the token to get the slug
        slug = decrypt_slug(token)
        if not slug:
            return JsonResponse({
                'success': False,
                'message': 'رابط غير صحيح أو منتهي الصلاحية'
            }, status=404)
        
        company = get_object_or_404(Company, slug=slug)
        
        # Check if company is currently active (allow pending companies if they are active)
        if not company.is_currently_active:
            return JsonResponse({
                'success': False,
                'message': 'الشركة غير مفعلة حالياً'
            }, status=403)
        
        data = json.loads(request.body)
        visitor_name = data.get('visitor_name', '').strip()
        visitor_phone = data.get('visitor_phone', '').strip()
        
        if not visitor_name:
            return JsonResponse({
                'success': False,
                'message': 'اسم الزائر مطلوب'
            }, status=400)
        
        # Validate phone number format (optional)
        phone_pattern = r'^05[0-9]{8}$'
        if visitor_phone and not re.match(phone_pattern, visitor_phone):
            return JsonResponse({
                'success': False,
                'message': 'رقم الجوال غير صحيح. يجب أن يبدأ بـ 05 ويحتوي على 10 أرقام أو تركه فارغاً'
            }, status=400)
        
        # Get prizes and normalize them (remove extra spaces)
        prizes = company.get_prizes_list()
        if not prizes:
            logger.error(f"Company {company.slug}: No prizes available")
            return JsonResponse({
                'success': False,
                'message': 'لا توجد جوائز متاحة'
            }, status=400)
        
        # Normalize prizes (trim whitespace) to ensure matching with frontend
        prizes = [str(p).strip() for p in prizes if p]
        
        if not prizes:
            logger.error(f"Company {company.slug}: All prizes are empty after normalization")
            return JsonResponse({
                'success': False,
                'message': 'لا توجد جوائز صالحة'
            }, status=400)
        
        # Select random prize using weighted algorithm based on percentages
        selected_prize = select_weighted_prize(company, prizes)
        
        if not selected_prize:
            logger.error(f"Company {company.slug}: Failed to select prize")
            return JsonResponse({
                'success': False,
                'message': 'فشل في اختيار الجائزة'
            }, status=500)
        
        # Ensure selected prize is in the prizes list
        if selected_prize not in prizes:
            logger.warning(
                f"Company {company.slug}: Selected prize '{selected_prize}' not in prizes list {prizes}. "
                f"Using first prize as fallback."
            )
            selected_prize = prizes[0]
        
        # Get client info
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create spin record
        spin = GameSpin.objects.create(
            company=company,
            visitor_name=visitor_name,
            visitor_phone=visitor_phone if visitor_phone else None,
            prize=selected_prize,
            won=True,
            session_id=request.session.session_key or f'session_{timezone.now().timestamp()}',
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return JsonResponse({
            'success': True,
            'prize': selected_prize,
            'spin_id': spin.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'خطأ في البيانات المرسلة'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'حدث خطأ: {str(e)}'
        }, status=500)


def game_dashboard(request, token):
    """Game dashboard for company"""
    # Decrypt the token to get the slug
    slug = decrypt_slug(token)
    if not slug:
        from django.http import Http404
        raise Http404("Invalid or expired link")
    
    company = get_object_or_404(Company, slug=slug)
    
    # Get statistics
    spins = company.spins.all()
    total_spins = spins.count()
    unique_visitors = spins.values('visitor_name').distinct().count()
    
    # Today's spins
    today = timezone.now().date()
    today_spins = spins.filter(created_at__date=today).count()
    
    # This week's spins
    week_ago = today - timedelta(days=7)
    week_spins = spins.filter(created_at__date__gte=week_ago).count()
    
    # Prize distribution
    prize_distribution = spins.values('prize').annotate(count=Count('prize')).order_by('-count')
    
    # Recent spins
    recent_spins = spins[:10]
    
    context = {
        'company': company,
        'total_spins': total_spins,
        'unique_visitors': unique_visitors,
        'today_spins': today_spins,
        'week_spins': week_spins,
        'prize_distribution': prize_distribution,
        'recent_spins': recent_spins,
    }
    
    return render(request, 'game/dashboard.html', context)
