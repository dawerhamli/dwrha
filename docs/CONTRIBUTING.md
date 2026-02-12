# دليل المساهمة

## إعداد المشروع

1. **استنساخ المشروع**
```bash
git clone <repository-url>
cd dwrha_1s
```

2. **إنشاء بيئة افتراضية**
```bash
python -m venv venv
source venv/bin/activate  # على Linux/Mac
# أو
venv\Scripts\activate  # على Windows
```

3. **تثبيت المتطلبات**
```bash
pip install -r requirements.txt
```

4. **إعداد متغيرات البيئة**
```bash
cp .env.example .env
# عدل ملف .env وأضف المعلومات المطلوبة
```

5. **تشغيل Migrations**
```bash
python manage.py migrate
```

6. **إنشاء مستخدم إداري**
```bash
python manage.py createsuperuser
```

7. **تشغيل الخادم**
```bash
python manage.py runserver
```

## معايير الكود

- استخدم أسماء متغيرات واضحة ووصفية
- أضف تعليقات بالعربية للمنطق المعقد
- اتبع نمط PEP 8 لـ Python
- تأكد من أن الكود يعمل قبل الرفع

## الالتزامات (Commits)

- استخدم رسائل واضحة ووصفية
- اذكر التغييرات الرئيسية في الرسالة

## Pull Requests

- تأكد من أن الكود يعمل بدون أخطاء
- تأكد من أن جميع الاختبارات تمر
- لا ترفع ملفات `.env` أو معلومات حساسة

