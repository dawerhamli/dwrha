"""
Game models for storing spin data
"""
from django.db import models
from django.utils import timezone
from companies.models import Company


# الجوائز الثابتة على عجلة LEAP (7 شرائح)
DEFAULT_LEAP_PRIZES = [
    {'order': 0, 'name': 'LORIVA'},
    {'order': 1, 'name': 'مسقيفة'},
    {'order': 2, 'name': 'سين جيم'},
    {'order': 3, 'name': 'Nutters'},
    {'order': 4, 'name': 'DUNNAH'},
    {'order': 5, 'name': 'RE9LOV'},
    {'order': 6, 'name': 'TRUNK coffee'},
]


class GameSpin(models.Model):
    """
    Model for storing game spin results
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='spins',
        verbose_name="الشركة"
    )
    visitor_name = models.CharField(
        max_length=100,
        verbose_name="اسم الزائر"
    )
    visitor_phone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="رقم الجوال",
        help_text="رقم الجوال السعودي (مثال: 0501234567) - اختياري"
    )
    prize = models.CharField(
        max_length=200,
        verbose_name="الجائزة"
    )
    won = models.BooleanField(
        default=True,
        verbose_name="فاز"
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="معرف الجلسة"
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="عنوان IP"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name="معلومات المتصفح"
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاريخ الدورة"
    )

    class Meta:
        verbose_name = "دورة لعبة"
        verbose_name_plural = "دورات الألعاب"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.visitor_name} - {self.prize} ({self.company.name})"


class LeapWheel(models.Model):
    """إعدادات عجلة LEAP — تُدار من لوحة الإدارة فقط."""

    is_enabled = models.BooleanField(
        default=False,
        verbose_name="تفعيل العجلة",
        help_text="عند التفعيل تظهر صفحة العجلة للعملاء على الرابط العام"
    )
    title = models.CharField(
        max_length=200,
        default='العجلة المشتركة',
        verbose_name="عنوان العجلة"
    )
    center_label = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="نص مركز العجلة"
    )
    center_logo = models.ImageField(
        upload_to='leap_wheel/center/',
        blank=True,
        null=True,
        verbose_name="شعار مركز العجلة"
    )
    sponsor_1_name = models.CharField(
        max_length=120,
        blank=True,
        default='Badie',
        verbose_name="الراعي الاستراتيجي 1"
    )
    sponsor_1_logo = models.ImageField(
        upload_to='leap_wheel/sponsors/',
        blank=True,
        null=True,
        verbose_name="شعار الراعي 1"
    )
    sponsor_2_name = models.CharField(
        max_length=120,
        blank=True,
        default='Poco Dor CHOCOLATIER',
        verbose_name="الراعي الاستراتيجي 2"
    )
    sponsor_2_logo = models.ImageField(
        upload_to='leap_wheel/sponsors/',
        blank=True,
        null=True,
        verbose_name="شعار الراعي 2"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "عجلة LEAP"
        verbose_name_plural = "عجلة LEAP"

    def __str__(self):
        status = "مفعّلة" if self.is_enabled else "متوقفة"
        return f"{self.title} ({status})"

    @classmethod
    def get_instance(cls):
        obj, _created = cls.objects.get_or_create(
            pk=1,
            defaults={'title': 'العجلة المشتركة', 'is_enabled': False}
        )
        obj.ensure_default_prizes()
        return obj

    def ensure_default_prizes(self):
        """إنشاء الجوائز الثابتة — يُكمّل الناقص فقط."""
        valid_names = {item['name'] for item in DEFAULT_LEAP_PRIZES}
        self.prizes.exclude(name__in=valid_names).delete()

        existing = {p.name: p for p in self.prizes.all()}
        for item in DEFAULT_LEAP_PRIZES:
            if item['name'] not in existing:
                LeapWheelPrize.objects.create(
                    leap_wheel=self,
                    name=item['name'],
                    order=item['order'],
                    total_quantity=0,
                    remaining_quantity=0,
                    is_active=True,
                )

    def get_wheel_segments(self):
        """كل شرائح العجلة (ثابتة — 7)."""
        return self.prizes.order_by('order', 'id')[:7]

    def get_available_prizes(self):
        return self.prizes.filter(is_active=True, remaining_quantity__gt=0).order_by('order', 'id')

    def has_stock(self):
        return self.get_available_prizes().exists()


class LeapWheelPrize(models.Model):
    """جائزة في مخزون عجلة LEAP."""

    leap_wheel = models.ForeignKey(
        LeapWheel,
        on_delete=models.CASCADE,
        related_name='prizes',
        verbose_name="عجلة LEAP"
    )
    name = models.CharField(max_length=200, verbose_name="اسم الجائزة / الشريك")
    logo = models.ImageField(
        upload_to='leap_wheel/prizes/',
        blank=True,
        null=True,
        verbose_name="شعار الشريك",
        help_text="يظهر على شريحة العجلة — ارفع شعار الشريك من التصميم"
    )
    total_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="الكمية الإجمالية",
        help_text="عدد مرات ظهور هذه الجائزة في المخزون"
    )
    remaining_quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="الكمية المتبقية"
    )
    is_active = models.BooleanField(default=True, verbose_name="نشطة")
    order = models.PositiveIntegerField(default=0, verbose_name="الترتيب")

    class Meta:
        verbose_name = "جائزة LEAP"
        verbose_name_plural = "جوائز LEAP"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.name} ({self.remaining_quantity}/{self.total_quantity})"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.remaining_quantity = self.total_quantity
        if self.remaining_quantity > self.total_quantity:
            self.remaining_quantity = self.total_quantity
        super().save(*args, **kwargs)


class LeapWheelSpin(models.Model):
    """سجل دورات عجلة LEAP."""

    leap_wheel = models.ForeignKey(
        LeapWheel,
        on_delete=models.CASCADE,
        related_name='spins',
        verbose_name="عجلة LEAP"
    )
    prize = models.ForeignKey(
        LeapWheelPrize,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='spins',
        verbose_name="الجائزة"
    )
    visitor_name = models.CharField(max_length=100, verbose_name="اسم العميل")
    visitor_phone = models.CharField(max_length=15, verbose_name="رقم الجوال")
    prize_name = models.CharField(max_length=200, verbose_name="اسم الجائزة")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="المتصفح")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ الدورة")

    class Meta:
        verbose_name = "دورة LEAP"
        verbose_name_plural = "دورات LEAP"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.visitor_name} — {self.prize_name}"
