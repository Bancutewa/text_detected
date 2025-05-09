# Text Detection Web Application

A modern web application for text detection and translation from images, built with Django, EasyOCR, MySQL, and a user-friendly interface.

---

## 🚀 Main Features

- **Text detection** from images using EasyOCR.
- **Text translation** between Vietnamese and English (Google Translate API).
- **User authentication**: Register, login, profile management.
- **History**: Save and view detection and translation history per user.
- **Export results** to Excel files.
- **Modern UI** with Bootstrap 5.

---

## 🛠️ Technology Stack & Libraries

- Python 3.8+
- Django 4.2.0
- MySQL
- EasyOCR
- OpenCV
- Pillow
- Selenium
- BeautifulSoup4
- Deep Translator
- Pandas, Openpyxl

See [`requirements.txt`](requirements.txt) for full details.

---

## 📁 Project Structure

```
text_detection_project/
├── manage.py
├── requirements.txt
├── huong_dan.txt
├── text_detection/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   ├── migrations/
│   └── ...
├── text_detection_project/
│   ├── settings.py
│   ├── urls.py
│   └── ...
└── media/
```

---

## ⚙️ Installation & Usage

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd text_detection_project
python -m venv venv
# Activate:
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Database setup

- Create a MySQL database (e.g. `text_detection_db`)
- Update connection info in `text_detection_project/settings.py`:
  ```python
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.mysql',
          'NAME': 'text_detection_db',
          'USER': 'root',
          'PASSWORD': 'your_password',
          'HOST': 'localhost',
          'PORT': '3306',
      }
  }
  ```

### 4. Initialize the database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run the server

```bash
python manage.py runserver
```

- Open your browser and go to: [http://localhost:8000](http://localhost:8000)

---

## 🖼️ Media & Static Files

- Result images are saved in `media/detection_results/`
- Make sure your `settings.py` includes:
  ```python
  MEDIA_URL = '/media/'
  MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
  ```
- And your project `urls.py` includes:
  ```python
  from django.conf import settings
  from django.conf.urls.static import static

  urlpatterns = [
      # ... your urls ...
  ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
  ```

---

## 🗄️ Main Data Models

- **UserProfile**: Extended user information
- **DetectionResult**: Detection results (image, original/translated text, confidence, timestamp, user)
- **CombinedTranslation**: Paragraph-level translation history

---

## 🔗 Main Endpoints

- `/` : Home page, text detection
- `/register/` : Register
- `/login/` : Login
- `/logout/` : Logout
- `/profile/` : User profile
- `/my-detections/` : Detection & translation history
- `/download-excel/` : Export results to Excel

---

## 💡 Notes

- Ensure all dependencies in `requirements.txt` are installed
- Check your database connection before running
- You may need to install additional drivers for OpenCV, EasyOCR, Selenium (Edge/Chrome driver)
- Python 3.8+ is recommended for best compatibility

---

## 🆘 Support

If you encounter issues:
- Check error logs in the console
- Ensure all libraries are installed with correct versions
- Check your database connection
- Make sure environment variables are set correctly

---

**Happy coding!** 