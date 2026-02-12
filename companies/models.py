"""
Company models for Dawerha platform
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import json
import random
import string


class Company(models.Model):
    """
    Company model for storing business information
    """
    
    TYPE_CHOICES = [
        ('restaurant', 'مطعم'),
        ('resort', 'منتجع'),
        ('hotel', 'فندق'),
        ('coffee', 'كوفي'),
        ('cafe', 'مقهى'),
        ('event', 'فعالية'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('approved', 'مُوافق عليه'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('scheduled', 'مجدول'),
        ('inactive', 'غير نشط'),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200, 
        verbose_name="اسم الجهة",
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name="الرابط الفريد",
        help_text="سيتم إنشاؤه تلقائياً من اسم الجهة"
    )
    type = models.CharField(
        max_length=50, 
        choices=TYPE_CHOICES,
        verbose_name="نوع الجهة"
    )
    custom_type = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="نوع مخصص"
    )
    
    # Contact Information
    email = models.EmailField(
        verbose_name="البريد الإلكتروني"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="رقم التواصل"
    )
    
    # Game Configuration
    prizes = models.JSONField(
        default=list,
        verbose_name="الجوائز"
    )
    colors = models.JSONField(
        default=list,
        verbose_name="الألوان"
    )
    
    # Status and Management
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="الحالة"
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="نشط"
    )
    active_hours = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        verbose_name="عدد ساعات التفعيل",
        help_text="من 1 إلى 168 ساعة (أسبوع كامل)"
    )
    activation_start_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="وقت بداية التفعيل"
    )
    activation_end_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="وقت نهاية التفعيل"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ الإنشاء"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    approved_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="تاريخ الموافقة"
    )
    
    # Additional Information
    logo_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name="رابط الشعار"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="ملاحظات"
    )
    
    class Meta:
        verbose_name = "شركة"
        verbose_name_plural = "الشركات"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to generate unique slug"""
        if not self.slug:
            # Use allow_unicode=False to ensure slug contains only Latin characters
            base_slug = slugify(self.name, allow_unicode=False)
            
            # If slug is empty (name was all non-Latin characters), generate a random one
            if not base_slug:
                base_slug = ''.join(random.choices(string.ascii_lowercase, k=8))
            
            unique_slug = base_slug
            counter = 1
            
            # Ensure slug is unique
            while Company.objects.filter(slug=unique_slug).exists():
                # Add random suffix to make it unique
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                unique_slug = f"{base_slug}-{random_suffix}"
                counter += 1
                if counter > 10:  # Safety check
                    break
            
            self.slug = unique_slug
        
        super().save(*args, **kwargs)
    
    @property
    def final_type(self):
        """Return the final type (custom or selected)"""
        return self.custom_type if self.type == 'other' else self.get_type_display()
    
    @property
    def company_url(self):
        """Generate company game URL with encrypted token"""
        from django.urls import reverse
        from .utils import encrypt_slug
        token = encrypt_slug(self.slug)
        if token:
            return reverse('game:play', kwargs={'token': token})
        # Fallback to slug if encryption fails
        return reverse('game:play', kwargs={'token': self.slug})
    
    @property
    def calculated_active_hours(self):
        """Calculate active hours based on activation type"""
        if not self.is_active:
            return 0
        
        # If permanently active (no start/end time)
        if not self.activation_start_time and not self.activation_end_time:
            return 24  # Show as 24 hours for permanent activation
        
        # If has end time, calculate duration
        if self.activation_end_time and self.activation_start_time:
            duration = self.activation_end_time - self.activation_start_time
            return int(duration.total_seconds() / 3600)  # Convert to hours
        
        # If only has start time, use active_hours
        if self.activation_start_time:
            return self.active_hours
        
        return self.active_hours
    
    @property
    def dynamic_status(self):
        """Get dynamic status based on actual state"""
        # If company is currently active, show as active
        if self.is_currently_active:
            return 'active'
        
        # If company has schedules but not currently active, show as scheduled
        if self.schedules.filter(is_active=True).exists():
            return 'scheduled'
        
        # If company is not active, show as inactive
        if not self.is_active:
            return 'inactive'
        
        # Default to pending
        return 'pending'
    
    @property
    def dynamic_status_display(self):
        """Get human-readable dynamic status"""
        status = self.dynamic_status
        
        if status == 'active':
            return "نشط الآن"
        elif status == 'scheduled':
            return "مجدول"
        elif status == 'inactive':
            return "غير نشط"
        elif status == 'pending':
            return "قيد المراجعة"
        elif status == 'approved':
            return "موافق عليه"
        elif status == 'rejected':
            return "مرفوض"
        else:
            return "غير محدد"
    
    @property
    def is_currently_active(self):
        """Check if company is currently active based on time window and schedules"""
        # First, check schedules and auto-activate if needed
        self._check_and_activate_from_schedule()
        
        # If company is not active, return False
        if not self.is_active:
            return False
        
        # If no activation times are set, it's permanently active
        if not self.activation_start_time and not self.activation_end_time:
            return True
        
        # If activation_start_time is not set, it's permanently active
        if not self.activation_start_time:
            return True
        
        now = timezone.now()
        
        # If activation_end_time is set, check if we're within the window
        if self.activation_end_time:
            return self.activation_start_time <= now <= self.activation_end_time
        
        # Otherwise, calculate based on active_hours
        end_time = self.activation_start_time + timezone.timedelta(hours=self.active_hours)
        return self.activation_start_time <= now <= end_time
    
    @property
    def activation_status_display(self):
        """Get human-readable activation status"""
        if not self.is_active:
            return "غير مفعل"
        
        if not self.activation_start_time and not self.activation_end_time:
            return "مفعل دائم"
        
        if not self.activation_start_time:
            return "مفعل دائم"
        
        now = timezone.now()
        
        if self.activation_end_time:
            if self.activation_start_time <= now <= self.activation_end_time:
                # Convert to Saudi time for display
                saudi_end_time = self.activation_end_time.astimezone(timezone.get_current_timezone())
                return f"مفعل (حتى {saudi_end_time.strftime('%Y-%m-%d %H:%M')})"
            else:
                return "غير مفعل"
        
        end_time = self.activation_start_time + timezone.timedelta(hours=self.active_hours)
        if self.activation_start_time <= now <= end_time:
            # Convert to Saudi time for display
            saudi_end_time = end_time.astimezone(timezone.get_current_timezone())
            return f"مفعل (حتى {saudi_end_time.strftime('%Y-%m-%d %H:%M')})"
        else:
            return "غير مفعل"
    
    def _check_and_activate_from_schedule(self):
        """Check schedules and auto-activate if needed"""
        # Get active schedules for this company
        active_schedules = self.schedules.filter(is_active=True)
        
        for schedule in active_schedules:
            if schedule.should_activate_now():
                # Check if already activated recently
                if schedule.last_activation:
                    time_since_last = timezone.now() - schedule.last_activation
                    if time_since_last.total_seconds() < (schedule.duration_hours * 3600):
                        continue  # Still within activation period
                
                # Activate company with scheduled hour
                self.activate_now(hours=schedule.duration_hours, scheduled_hour=schedule.start_hour, scheduled_end_hour=schedule.end_hour)
                schedule.last_activation = timezone.now()
                schedule.save()
                break  # Only activate from one schedule at a time
    
    def approve(self):
        """Approve the company"""
        self.status = 'approved'
        self.is_active = True
        self.approved_at = timezone.now()
        self.save()
    
    def activate_now(self, hours=None, scheduled_hour=None, scheduled_end_hour=None):
        """
        Activate the company for specified hours
        Args:
            hours: Number of hours to activate
            scheduled_hour: If provided, set start time to the beginning of that hour
            scheduled_end_hour: If provided, set end time to the end of that hour
        """
        if hours is None:
            hours = self.active_hours
        
        self.is_active = True
        
        # If scheduled_hour is provided, set start/end times based on schedule
        if scheduled_hour is not None:
            now = timezone.now()
            saudi_time = now.astimezone(timezone.get_current_timezone())
            
            # Set start time to the beginning of the scheduled hour
            saudi_start = saudi_time.replace(hour=scheduled_hour, minute=0, second=0, microsecond=0)
            
            # If the scheduled time is in the past, use current time instead
            if saudi_start <= saudi_time:
                # Use current time as start (immediate activation)
                self.activation_start_time = now
            else:
                # Use the scheduled hour start time
                self.activation_start_time = saudi_start
            
            # Set end time based on scheduled_end_hour if provided
            if scheduled_end_hour is not None:
                # Calculate end time at the end of the scheduled hour
                if saudi_start <= saudi_time:
                    # If we started now, calculate end based on current time
                    saudi_end = saudi_time.replace(hour=scheduled_end_hour, minute=0, second=0, microsecond=0)
                    # If end hour has passed today, schedule for tomorrow
                    if saudi_end <= saudi_time:
                        saudi_end = saudi_end + timezone.timedelta(days=1)
                    self.activation_end_time = saudi_end
                else:
                    # Started at scheduled time, calculate end normally
                    saudi_end = saudi_start.replace(hour=scheduled_end_hour, minute=0, second=0, microsecond=0)
                    # Handle cross-midnight
                    if scheduled_end_hour < scheduled_hour:
                        saudi_end = saudi_end + timezone.timedelta(days=1)
                    self.activation_end_time = saudi_end
            else:
                # Use duration if no end_hour specified
                self.activation_end_time = self.activation_start_time + timezone.timedelta(hours=hours)
        else:
            # Normal activation - start from now
            self.activation_start_time = timezone.now()
            self.activation_end_time = timezone.now() + timezone.timedelta(hours=hours)
        
        self.save()
    
    def reject(self):
        """Reject the company"""
        self.status = 'rejected'
        self.is_active = False
        self.save()
    
    def get_prizes_list(self):
        """Get prizes as a list"""
        if isinstance(self.prizes, str):
            try:
                return json.loads(self.prizes)
            except json.JSONDecodeError:
                return self.prizes.split(',')
        return self.prizes if self.prizes else []
    
    def get_colors_list(self):
        """Get colors as a list"""
        if isinstance(self.colors, str):
            try:
                return json.loads(self.colors)
            except json.JSONDecodeError:
                return self.colors.split(',')
        return self.colors if self.colors else []


class ActivationSchedule(models.Model):
    """
    Model for scheduling automatic activation
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="الشركة"
    )
    
    # Days of week (ordered for Arabic calendar: Saturday to Friday)
    saturday = models.BooleanField(default=False, verbose_name="السبت")
    sunday = models.BooleanField(default=False, verbose_name="الأحد")
    monday = models.BooleanField(default=False, verbose_name="الاثنين")
    tuesday = models.BooleanField(default=False, verbose_name="الثلاثاء")
    wednesday = models.BooleanField(default=False, verbose_name="الأربعاء")
    thursday = models.BooleanField(default=False, verbose_name="الخميس")
    friday = models.BooleanField(default=False, verbose_name="الجمعة")
    
    # Time settings (12-hour format with AM/PM)
    HOUR_CHOICES = [
        (0, '12:00 منتصف الليل'),
        (1, '01:00 صباحاً'),
        (2, '02:00 صباحاً'),
        (3, '03:00 صباحاً'),
        (4, '04:00 صباحاً'),
        (5, '05:00 صباحاً'),
        (6, '06:00 صباحاً'),
        (7, '07:00 صباحاً'),
        (8, '08:00 صباحاً'),
        (9, '09:00 صباحاً'),
        (10, '10:00 صباحاً'),
        (11, '11:00 صباحاً'),
        (12, '12:00 ظهراً'),
        (13, '01:00 مساءً'),
        (14, '02:00 مساءً'),
        (15, '03:00 مساءً'),
        (16, '04:00 مساءً'),
        (17, '05:00 مساءً'),
        (18, '06:00 مساءً'),
        (19, '07:00 مساءً'),
        (20, '08:00 مساءً'),
        (21, '09:00 مساءً'),
        (22, '10:00 مساءً'),
        (23, '11:00 مساءً'),
    ]
    
    start_hour = models.IntegerField(
        choices=HOUR_CHOICES,
        default=9,
        verbose_name="ساعة البداية",
        help_text="اختر وقت البداية"
    )
    end_hour = models.IntegerField(
        choices=HOUR_CHOICES,
        default=17,
        verbose_name="ساعة النهاية",
        help_text="اختر وقت النهاية"
    )
    
    duration_hours = models.IntegerField(
        default=24,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        verbose_name="عدد ساعات التفعيل",
        help_text="عدد الساعات التي يبقى فيها الحساب مفعلاً (من 1 إلى 168 ساعة)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="الجدولة مفعلة",
        help_text="تفعيل أو إيقاف الجدولة التلقائية"
    )
    
    # Tracking
    last_activation = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="آخر تفعيل"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ الإنشاء"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        verbose_name = "جدولة التفعيل"
        verbose_name_plural = "جداول التفعيل"
        ordering = ['-created_at']
    
    def __str__(self):
        days = self.get_active_days_display()
        return f"{self.company.name} - {days}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate duration before saving and auto-activate if schedule conditions are met"""
        # Calculate duration automatically based on start and end hours
        if self.start_hour <= self.end_hour:
            # Normal case: start=9, end=17 → duration=8 hours
            self.duration_hours = self.end_hour - self.start_hour
            if self.duration_hours == 0:
                self.duration_hours = 1  # Minimum 1 hour
        else:
            # Crosses midnight: start=22, end=2 → duration=4 hours (22,23,0,1,2)
            self.duration_hours = (24 - self.start_hour) + self.end_hour
        
        # Save the schedule (no auto-activation - only via "activate_by_schedule" action)
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate schedule"""
        # Check if at least one day is selected
        if not any([self.saturday, self.sunday, self.monday, self.tuesday, 
                   self.wednesday, self.thursday, self.friday]):
            raise ValidationError('يجب اختيار يوم واحد على الأقل')
        
        # Validate hours
        if self.start_hour < 0 or self.start_hour > 23:
            raise ValidationError('ساعة البداية يجب أن تكون بين 0 و 23')
        if self.end_hour < 0 or self.end_hour > 23:
            raise ValidationError('ساعة النهاية يجب أن تكون بين 0 و 23')
    
    def get_active_days_display(self):
        """Get display of active days (in Arabic week order)"""
        days = []
        if self.saturday: days.append('السبت')
        if self.sunday: days.append('الأحد')
        if self.monday: days.append('الاثنين')
        if self.tuesday: days.append('الثلاثاء')
        if self.wednesday: days.append('الأربعاء')
        if self.thursday: days.append('الخميس')
        if self.friday: days.append('الجمعة')
        return ', '.join(days) if days else 'لا يوجد'
    
    def get_active_days_list(self):
        """Get list of active day numbers (0=Monday, 6=Sunday)"""
        days = []
        if self.saturday: days.append(5)
        if self.sunday: days.append(6)
        if self.monday: days.append(0)
        if self.tuesday: days.append(1)
        if self.wednesday: days.append(2)
        if self.thursday: days.append(3)
        if self.friday: days.append(4)
        return days
    
    def should_activate_now(self):
        """Check if should activate based on current time - only at the exact scheduled hour"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        # Convert to Saudi time for accurate hour and weekday
        saudi_time = now.astimezone(timezone.get_current_timezone())
        current_weekday = saudi_time.weekday()  # 0=Monday, 6=Sunday
        current_hour = saudi_time.hour
        current_minute = saudi_time.minute
        
        # Check if today is an active day
        active_days = self.get_active_days_list()
        if current_weekday not in active_days:
            return False
        
        # Only activate at the exact scheduled start hour (minute 0)
        # This ensures activation happens at the exact time, not just within the time window
        if current_hour != self.start_hour:
            return False
        
        # Only activate during the first minute (00:00) of the scheduled hour
        # This prevents multiple activations during the same hour
        if current_minute != 0:
            return False
        
        # Check if already activated in this hour window
        if self.last_activation:
            saudi_last_activation = self.last_activation.astimezone(timezone.get_current_timezone())
            time_since_last = now - self.last_activation
            
            # Only allow activation if last activation was in a different hour
            # This prevents re-activation in the same hour window
            if saudi_last_activation.hour == current_hour:
                return False
        
        return True
    
    def get_time_display(self):
        """Get human-readable time display"""
        def hour_display(hour):
            if hour == 0:
                return "12:00 منتصف الليل"
            elif hour < 12:
                return f"{hour:02d}:00 صباحاً"
            elif hour == 12:
                return "12:00 ظهراً"
            else:
                return f"{hour-12:02d}:00 مساءً"
        
        start = hour_display(self.start_hour)
        end = hour_display(self.end_hour)
        return f"من {start} إلى {end}"
    
    def is_today_active_day(self):
        """Check if today is one of the scheduled days"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        saudi_time = now.astimezone(timezone.get_current_timezone())
        current_weekday = saudi_time.weekday()  # 0=Monday, 6=Sunday
        active_days = self.get_active_days_list()
        return current_weekday in active_days
    
    def should_activate_soon(self):
        """Check if should activate soon based on current time - check if within scheduled window"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        saudi_time = now.astimezone(timezone.get_current_timezone())
        current_weekday = saudi_time.weekday()  # 0=Monday, 6=Sunday
        current_hour = saudi_time.hour
        current_minute = saudi_time.minute
        
        # Check if today is an active day
        active_days = self.get_active_days_list()
        if current_weekday not in active_days:
            return False
        
        # Check if current hour is within activation window
        if self.start_hour <= self.end_hour:
            # Normal case: start=9, end=17 (9 AM to 5 PM)
            # Include end_hour to allow activation during the entire end hour
            return self.start_hour <= current_hour <= self.end_hour
        else:
            # Crosses midnight: start=22, end=2 (10 PM to 2 AM)
            return current_hour >= self.start_hour or current_hour <= self.end_hour
    
    def can_activate_manually(self):
        """
        Check if schedule can be activated manually from admin action.
        Returns: (can_activate, is_exact_hour, message)
        - can_activate: True if should activate immediately
        - is_exact_hour: True if current time is exactly at start_hour (minute 0)
        - message: message to display if cannot activate
        """
        if not self.is_active:
            return (False, False, "الجدولة غير مفعلة")
        
        now = timezone.now()
        saudi_time = now.astimezone(timezone.get_current_timezone())
        current_weekday = saudi_time.weekday()  # 0=Monday, 6=Sunday
        current_hour = saudi_time.hour
        current_minute = saudi_time.minute
        
        # Check if today is an active day
        active_days = self.get_active_days_list()
        if current_weekday not in active_days:
            return (False, False, "اليوم ليس ضمن أيام التفعيل المحددة")
        
        # Check if exactly at start_hour (minute 0)
        if current_hour == self.start_hour and current_minute == 0:
            return (False, True, f"الوقت الحالي هو نفس وقت بداية الجدولة ({self.start_hour}:00)")
        
        # Check if within activation window (before start_hour by 1 minute or after start_hour)
        if self.start_hour <= self.end_hour:
            # Normal case: start=10, end=11
            # If before start_hour by 1 minute, can activate
            if current_hour < self.start_hour:
                return (True, False, None)
            # If at or after start_hour and within end_hour, can activate
            if self.start_hour <= current_hour <= self.end_hour:
                return (True, False, None)
        else:
            # Crosses midnight: start=22, end=2
            if current_hour < self.start_hour and current_hour > self.end_hour:
                return (False, False, "خارج نطاق وقت التفعيل")
            return (True, False, None)
        
        return (False, False, "خارج نطاق وقت التفعيل")
    
    def activate_company(self):
        """Activate the company based on schedule"""
        if not self.should_activate_now():
            return False
        
        # Activate company with scheduled hour
        self.company.activate_now(hours=self.duration_hours, scheduled_hour=self.start_hour, scheduled_end_hour=self.end_hour)
        self.last_activation = timezone.now()
        self.save()
        
        return True
    
    def get_company_activation_status(self):
        """Get real-time company activation status"""
        # Refresh company from database
        self.company.refresh_from_db()
        
        if not self.company.is_active:
            return {
                'status': 'inactive',
                'display': 'غير نشط',
                'color': '#dc3545',
                'is_active': False
            }
        
        now = timezone.now()
        
        # Check if currently active based on time window
        if self.company.activation_end_time:
            if self.company.activation_start_time and self.company.activation_start_time <= now <= self.company.activation_end_time:
                # Calculate remaining time
                remaining = self.company.activation_end_time - now
                hours_left = int(remaining.total_seconds() / 3600)
                minutes_left = int((remaining.total_seconds() % 3600) / 60)
                
                return {
                    'status': 'active',
                    'display': f'نشط الآن ({hours_left}س {minutes_left}د)',
                    'color': '#28a745',
                    'is_active': True,
                    'end_time': self.company.activation_end_time.strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return {
            'status': 'inactive',
            'display': 'غير نشط',
            'color': '#dc3545',
            'is_active': False
        }
