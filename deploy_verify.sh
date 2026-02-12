#!/bin/bash
# سكربت التحقق من جاهزية النشر
echo "=== التحقق من جاهزية دوّرها للنشر ==="
python manage.py check --deploy --settings=dawerha.production_settings && \
python manage.py migrate --check --settings=dawerha.production_settings && \
echo "✅ المشروع جاهز للنشر"
exit $?
