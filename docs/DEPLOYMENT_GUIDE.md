# دوّرها - دليل النشر على Hostinger

## متطلبات النشر

### 1. قاعدة البيانات PostgreSQL
- تأكد من أن Hostinger يدعم PostgreSQL
- أنشئ قاعدة بيانات جديدة
- احصل على بيانات الاتصال (اسم قاعدة البيانات، المستخدم، كلمة المرور، المضيف، المنفذ)

### 2. إعداد المتغيرات البيئية
انسخ ملف `env.example` إلى `.env` واملأ القيم الصحيحة:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,www.yourdomain.com

# Database Settings (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dwrha_db
DB_USER=postgres
DB_PASSWORD=your-db-password-here
DB_HOST=localhost
DB_PORT=5432
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. إعداد قاعدة البيانات
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

### 5. تشغيل الخادم
```bash
# للتطوير
python manage.py runserver

# للإنتاج
bash start_production.sh
```

## خطوات النشر على Hostinger

### 1. رفع الملفات
- ارفع جميع ملفات المشروع إلى مجلد `public_html`
- تأكد من رفع ملف `.env` مع البيانات الصحيحة

### 2. إعداد قاعدة البيانات
- أنشئ قاعدة بيانات PostgreSQL في لوحة تحكم Hostinger
- اربط قاعدة البيانات بالمشروع

### 3. تشغيل الأوامر
```bash
cd public_html
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

### 4. إعداد الخادم
- استخدم Gunicorn أو أي خادم WSGI آخر
- تأكد من أن المنفذ 8000 متاح أو غيّر المنفذ حسب إعدادات Hostinger

## ملاحظات مهمة

1. **الأمان**: تأكد من تغيير `SECRET_KEY` في الإنتاج
2. **DEBUG**: تأكد من تعيين `DEBUG=False` في الإنتاج
3. **ALLOWED_HOSTS**: أضف نطاقك إلى `ALLOWED_HOSTS`
4. **الملفات الثابتة**: تأكد من رفع مجلد `staticfiles` بعد تشغيل `collectstatic`
5. **الجدولة**: تأكد من تشغيل الجدولة التلقائية في الإنتاج

## استكشاف الأخطاء

### مشاكل قاعدة البيانات
- تأكد من صحة بيانات الاتصال
- تأكد من أن PostgreSQL يعمل
- تحقق من الأذونات

### مشاكل الملفات الثابتة
- تأكد من تشغيل `collectstatic`
- تحقق من إعدادات `STATIC_ROOT`
- تأكد من إعدادات WhiteNoise

### مشاكل الجدولة
- تأكد من أن Middleware يعمل
- تحقق من إعدادات الوقت
- تأكد من صحة الجداول في قاعدة البيانات




