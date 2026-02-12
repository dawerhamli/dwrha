"""
Influencer models for Dawerha platform
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.utils.text import slugify
import json
import random
import string


class Influencer(models.Model):
    """
    Influencer model for storing influencer information
    """
    
    PLATFORM_CHOICES = [
        ('instagram', 'إنستغرام'),
        ('tiktok', 'تيك توك'),
        ('youtube', 'يوتيوب'),
        ('snapchat', 'سناب شات'),
        ('twitter', 'تويتر'),
        ('other', 'أخرى'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('approved', 'مُوافق عليه'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('inactive', 'غير نشط'),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200, 
        verbose_name="اسم المؤثر",
        validators=[MinLengthValidator(2)]
    )
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,
        verbose_name="الرابط الفريد",
        help_text="سيتم إنشاؤه تلقائياً من اسم المؤثر"
    )
    
    # Platform Information
    platform = models.CharField(
        max_length=50, 
        choices=PLATFORM_CHOICES,
        verbose_name="المنصة الرئيسية"
    )
    custom_platform = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="منصة مخصصة"
    )
    username = models.CharField(
        max_length=200,
        verbose_name="اسم المستخدم",
        help_text="اسم المستخدم في المنصة (مثال: @username)"
    )
    profile_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="رابط الملف الشخصي"
    )
    followers_count = models.IntegerField(
        default=0,
        verbose_name="عدد المتابعين"
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
    profile_image_url = models.URLField(
        blank=True, 
        null=True,
        verbose_name="رابط صورة الملف الشخصي"
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name="نبذة تعريفية"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="ملاحظات"
    )
    
    class Meta:
        verbose_name = "مؤثر"
        verbose_name_plural = "المؤثرون"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to generate unique slug"""
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=False)
            
            if not base_slug:
                base_slug = ''.join(random.choices(string.ascii_lowercase, k=8))
            
            unique_slug = base_slug
            counter = 1
            
            while Influencer.objects.filter(slug=unique_slug).exists():
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                unique_slug = f"{base_slug}-{random_suffix}"
                counter += 1
                if counter > 10:
                    break
            
            self.slug = unique_slug
        
        super().save(*args, **kwargs)
    
    @property
    def final_platform(self):
        """Return the final platform (custom or selected)"""
        return self.custom_platform if self.platform == 'other' else self.get_platform_display()
    
    @property
    def influencer_url(self):
        """Generate influencer game URL"""
        from django.urls import reverse
        from .utils import encrypt_slug

        # Use the same encrypted token mechanism as companies
        token = encrypt_slug(self.slug)
        if token:
            return reverse('game:play', kwargs={'token': token})
        # Fallback to plain slug if encryption ever fails
        return reverse('game:play', kwargs={'token': self.slug})
    
    def approve(self):
        """Approve the influencer"""
        self.status = 'approved'
        self.is_active = True
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self):
        """Reject the influencer"""
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
    
    @property
    def registration_url(self):
        """Generate registration page URL for participants with encrypted token"""
        from django.urls import reverse
        from .utils import encrypt_slug
        token = encrypt_slug(self.slug)
        if token:
            return reverse('influencers:register_participant', kwargs={'token': token})
        # Fallback to slug if encryption fails
        return reverse('influencers:register_participant', kwargs={'token': self.slug})
    
    @property
    def wheel_url(self):
        """Generate wheel game URL with encrypted token"""
        from django.urls import reverse
        from .utils import encrypt_slug
        token = encrypt_slug(self.slug)
        if token:
            return reverse('influencers:play_wheel', kwargs={'token': token})
        # Fallback to slug if encryption fails
        return reverse('influencers:play_wheel', kwargs={'token': self.slug})


class Participant(models.Model):
    """
    Model for storing participants who registered for influencer's wheel game
    """
    influencer = models.ForeignKey(
        Influencer,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name="المؤثر"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="الاسم"
    )
    phone = models.CharField(
        max_length=15,
        verbose_name="رقم الجوال",
        db_index=True  # لتحسين البحث ومنع التكرار بسرعة
    )
    social_media_account = models.CharField(
        max_length=200,
        verbose_name="حساب التواصل الاجتماعي",
        help_text="مثال: @username"
    )
    city = models.CharField(
        max_length=100,
        verbose_name="المدينة"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ التسجيل"
    )
    
    class Meta:
        verbose_name = "مشارك"
        verbose_name_plural = "المشاركون"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['influencer', 'phone'],
                name='unique_influencer_phone'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.influencer.name}"


class InfluencerWinner(models.Model):
    """
    Stores winners for an influencer's wheel game.

    Each record represents one prize that has been won and must not be repeated.
    """
    influencer = models.ForeignKey(
        Influencer,
        on_delete=models.CASCADE,
        related_name='winners',
        verbose_name="المؤثر"
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wins',
        verbose_name="الفائز"
    )
    prize = models.CharField(
        max_length=255,
        verbose_name="الجائزة"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ الفوز"
    )

    class Meta:
        verbose_name = "فائز (مؤثر)"
        verbose_name_plural = "الفائزون (مؤثرين)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.prize} - {self.influencer.name}"
