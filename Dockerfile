FROM python:3.10-slim

# تثبيت ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المشروع إلى الحاوية
COPY . .

# تثبيت المكتبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# تشغيل البوت
CMD ["python", "main.py"]
