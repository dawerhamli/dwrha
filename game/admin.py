"""
Admin configuration for game app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from datetime import datetime
from .models import GameSpin


@admin.register(GameSpin)
class GameSpinAdmin(admin.ModelAdmin):
    list_display = [
        'visitor_name', 
        'visitor_phone',
        'company', 
        'prize', 
        'won', 
        'created_at',
        'ip_address'
    ]
    list_filter = ['won', 'company', 'created_at']
    search_fields = ['visitor_name', 'visitor_phone', 'prize', 'company__name']
    readonly_fields = ['created_at', 'session_id', 'ip_address', 'user_agent']
    actions = ['export_to_excel']

    fieldsets = (
        ('معلومات الدورة', {
            'fields': ('company', 'visitor_name', 'visitor_phone', 'prize', 'won')
        }),
        ('معلومات تقنية', {
            'fields': ('session_id', 'ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')

    def changelist_view(self, request, extra_context=None):
        """
        نفس سلوك التصدير في باقي الخانات:
        - إذا اختار عناصر → يصدّر المحدد
        - إذا لم يختَر شيء → يصدّر الكل
        """
        if 'action' in request.POST and request.POST['action'] == 'export_to_excel':
            selected_ids = request.POST.getlist('_selected_action')
            if selected_ids:
                queryset = self.get_queryset(request).filter(pk__in=selected_ids)
            else:
                queryset = self.get_queryset(request)
            return self.export_to_excel(request, queryset)

        extra_context = extra_context or {}
        extra_context['show_export_button'] = True
        extra_context['export_action_name'] = 'export_to_excel'
        return super().changelist_view(request, extra_context)

    def export_to_excel(self, request, queryset):
        """تصدير دورات الألعاب إلى ملف Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "دورات الألعاب"

        headers = [
            'ID',
            'الشركة',
            'اسم الزائر',
            'رقم الجوال',
            'الجائزة',
            'فاز',
            'تاريخ الدورة',
            'عنوان IP',
            'المتصفح',
        ]

        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="6A3FA0", end_color="6A3FA0", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        row_num = 2
        for spin in queryset:
            ws.cell(row=row_num, column=1, value=spin.id)
            ws.cell(row=row_num, column=2, value=getattr(spin.company, 'name', '-'))
            ws.cell(row=row_num, column=3, value=spin.visitor_name)
            ws.cell(row=row_num, column=4, value=spin.visitor_phone or '-')
            ws.cell(row=row_num, column=5, value=spin.prize)
            ws.cell(row=row_num, column=6, value='نعم' if spin.won else 'لا')

            created_val = spin.created_at
            if created_val and hasattr(created_val, 'strftime'):
                ws.cell(row=row_num, column=7, value=created_val.strftime('%Y-%m-%d %H:%M'))
            else:
                ws.cell(row=row_num, column=7, value=str(created_val) if created_val else '-')

            ws.cell(row=row_num, column=8, value=spin.ip_address or '-')
            ws.cell(row=row_num, column=9, value=spin.user_agent or '-')

            row_num += 1

        for col_num in range(1, len(headers) + 1):
            column_letter = get_column_letter(col_num)
            max_length = 0
            for row in ws[column_letter]:
                try:
                    if row.value:
                        max_length = max(max_length, len(str(row.value)))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 60)
            ws.column_dimensions[column_letter].width = adjusted_width

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'دورات_الألعاب_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'
        wb.save(response)
        return response

    export_to_excel.short_description = "📊 تصدير دورات الألعاب إلى Excel"
