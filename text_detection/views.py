from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import cv2
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
import base64
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from deep_translator import GoogleTranslator
import urllib.parse
import pandas as pd
from .models import DetectionResult, CombinedTranslation, UserProfile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm, UserUpdateForm
from django.contrib.auth.models import User
import datetime

# Initialize EasyOCR
reader = easyocr.Reader(['en', 'vi'], gpu=False)

# Initialize translators
translator_vi_to_en = GoogleTranslator(source='vi', target='en')
translator_en_to_vi = GoogleTranslator(source='en', target='vi')

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    sharpened = cv2.addWeighted(enhanced, 1.5, blurred, -0.5, 0)
    return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)

def download_images(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        images = []
        for img_tag in soup.find_all('img'):
            img_url = img_tag.get('src')
            if img_url:
                img_url = urllib.parse.urljoin(url, img_url)
                try:
                    img_response = requests.get(img_url, headers=headers)
                    img_array = np.frombuffer(img_response.content, np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        images.append(img)
                except:
                    continue
        if images:
            return images
    except Exception as e:
        print(f"Error downloading images: {e}")
    return capture_screenshot(url)

def capture_screenshot(url):
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Edge(options=edge_options)
    try:
        driver.get(url)
        driver.implicitly_wait(5)
        height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight);")
        driver.set_window_size(1920, height)
        screenshot = driver.get_screenshot_as_png()
        img_array = np.frombuffer(screenshot, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        driver.quit()
        return [img] if img is not None else []
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        driver.quit()
        return []

def decode_base64_image(base64_string):
    base64_string = base64_string.split(',')[1] if ',' in base64_string else base64_string
    img_data = base64.b64decode(base64_string)
    img_array = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

def extend_image(image, min_width=800, min_height=600, border=100):
    height, width = image.shape[:2]
    new_width = max(width, min_width) + 2 * border
    new_height = max(height, min_height) + 2 * border
    extended_image = np.ones((new_height, new_width, 3), dtype=np.uint8) * 255
    top = (new_height - height) // 2
    left = (new_width - width) // 2
    extended_image[top:top + height, left:left + width] = image
    return extended_image, top, left

def detect_and_translate(image, translate_direction=None):
    processed_image = preprocess_image(image)
    results = reader.readtext(processed_image, detail=1, contrast_ths=0.1, adjust_contrast=0.5)
    threshold = 0.25

    extended_image, offset_y, offset_x = extend_image(image)
    img_rgb = cv2.cvtColor(extended_image, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)

    base_font_size = min(image.shape[0], image.shape[1]) // 20
    font_size = max(14, base_font_size)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    detected_texts = []
    all_lines = []

    for (bbox, text, score) in results:
        if score >= threshold:
            all_lines.append(text)
            top_left = (int(bbox[0][0]) + offset_x, int(bbox[0][1]) + offset_y)
            bottom_right = (int(bbox[2][0]) + offset_x, int(bbox[2][1]) + offset_y)

            text_bbox = draw.textbbox((top_left[0], top_left[1] - font_size - 5), text, font=font)
            text_top_left = (text_bbox[0], text_bbox[1])
            text_bottom_right = (text_bbox[2], text_bbox[3])

            new_top_left = (min(top_left[0], text_top_left[0]), min(top_left[1], text_top_left[1]))
            new_bottom_right = (max(bottom_right[0], text_bottom_right[0]), max(bottom_right[1], text_bottom_right[1]))

            draw.rectangle([new_top_left, new_bottom_right], outline=(0, 255, 0), width=3)
            draw.text((top_left[0], top_left[1] - font_size - 5), text, font=font, fill=(4, 35, 134))

            translated_text = text
            if translate_direction == 'vi_to_en':
                translated_text = translator_vi_to_en.translate(text)
            elif translate_direction == 'en_to_vi':
                translated_text = translator_en_to_vi.translate(text)

            if translated_text and translated_text != text:
                translate_x = new_bottom_right[0] + 10
                translate_y = top_left[1] - font_size - 5
                draw.text((translate_x, translate_y), translated_text, font=font, fill=(255, 0, 0))
                arrow_end = (new_bottom_right[0], top_left[1] - font_size // 2)
                arrow_start = (translate_x, translate_y + font_size // 2)
                draw.line([arrow_start, arrow_end], fill=(255, 0, 0), width=2)

            detected_texts.append({
                'original': text,
                'translated': translated_text if translated_text != text else None,
                'confidence': score
            })

    full_paragraph = " ".join(all_lines)
    translated_paragraph = None

    if translate_direction == 'vi_to_en':
        translated_paragraph = translator_vi_to_en.translate(full_paragraph)
    elif translate_direction == 'en_to_vi':
        translated_paragraph = translator_en_to_vi.translate(full_paragraph)

    if translated_paragraph:
        width, height = img_pil.size
        new_height = height + 60
        extended_img = Image.new("RGB", (width, new_height), (255, 255, 255))
        extended_img.paste(img_pil, (0, 0))
        draw = ImageDraw.Draw(extended_img)
        draw.text((10, height + 10), f"Combined translation: {translated_paragraph}", font=font, fill=(0, 0, 0))
        img_pil = extended_img

    result_image = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return result_image, detected_texts, full_paragraph, translated_paragraph

def index(request):
    if request.method == "POST":
        url = request.POST.get("url")
        translate_direction = request.POST.get("translate_direction")
        input_type = request.POST.get("input_type")
        paste_image = request.POST.get("paste_image")
        image_file = request.FILES.get("image_file")

        images = []

        if input_type == "url" and url:
            images = download_images(url)
            if not images:
                return render(request, "text_detection/index.html", {"error": "Could not download images or capture screenshot"})

        elif input_type == "paste" and paste_image:
            try:
                img = decode_base64_image(paste_image)
                if img is not None:
                    images.append(img)
                else:
                    return render(request, "text_detection/index.html", {"error": "Invalid pasted image"})
            except:
                return render(request, "text_detection/index.html", {"error": "Error decoding pasted image"})

        elif input_type == "upload" and image_file:
            try:
                img_array = np.frombuffer(image_file.read(), np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    images.append(img)
                else:
                    return render(request, "text_detection/index.html", {"error": "Invalid uploaded image"})
            except:
                return render(request, "text_detection/index.html", {"error": "Error processing uploaded image"})

        if not images:
            return render(request, "text_detection/index.html", {"error": "No valid images provided"})

        result_images = []
        all_detected_texts = []
        all_full_paragraphs = []
        all_translated_paragraphs = []

        for idx, img in enumerate(images):
            result_image, detected_texts, full_paragraph, translated_paragraph = detect_and_translate(img, translate_direction)
            
            # Convert OpenCV image to PIL Image
            result_image_rgb = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(result_image_rgb)
            
            # Save to BytesIO
            img_io = BytesIO()
            pil_image.save(img_io, format='PNG')
            img_io.seek(0)
            
            # Tạo tên file và lưu vào media/detection_results/
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            image_name = f"detection_{idx}_{timestamp}.png"
            relative_path = f"detection_results/{image_name}"
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(img_io.getvalue())

            # Lưu vào DB
            for text in detected_texts:
                detection_result = DetectionResult(
                    original_text=text['original'],
                    translated_text=text['translated'],
                    confidence_score=text['confidence'],
                    translation_direction=translate_direction,
                    image_path=relative_path
                )
                if request.user.is_authenticated:
                    detection_result.user = request.user
                detection_result.save()

            if full_paragraph and translated_paragraph:
                translation = CombinedTranslation.objects.create(
                    original_paragraph=full_paragraph,
                    translated_paragraph=translated_paragraph,
                    translation_direction=translate_direction
                )
                if request.user.is_authenticated:
                    translation.user = request.user
                    translation.save()

            # Convert to base64 for immediate display
            _, buffer = cv2.imencode(".png", result_image)
            img_str = base64.b64encode(buffer).decode("utf-8")
            result_images.append(img_str)
            all_detected_texts.extend(detected_texts)
            all_full_paragraphs.append(full_paragraph)
            if translated_paragraph:
                all_translated_paragraphs.append(translated_paragraph)

        table_data = []
        for idx, text in enumerate(all_detected_texts, 1):
            table_data.append({
                'stt': idx,
                'original': text['original'],
                'translated': text['translated'] if text['translated'] else '-'
            })

        combined_paragraph = " ".join(all_full_paragraphs)
        combined_translated = " ".join(all_translated_paragraphs) if all_translated_paragraphs else None

        if combined_paragraph:
            table_data.append({
                'stt': 'Combined',
                'original': combined_paragraph,
                'translated': combined_translated if combined_translated else '-'
            })

        return render(request, "text_detection/index.html", {
            'images': result_images,
            'table_data': table_data,
            'url': url,
            'translate_direction': translate_direction,
            'input_type': input_type,
            'combined_paragraph': combined_paragraph,
            'combined_translated': combined_translated
        })

    return render(request, "text_detection/index.html")

def download_excel(request):
    detection_results = DetectionResult.objects.all().order_by('-created_at')
    
    df_data = []
    for idx, result in enumerate(detection_results, 1):
        df_data.append({
            'STT': idx,
            'Original Text': result.original_text,
            'Translated Text': result.translated_text or '-',
            'Confidence': f"{result.confidence_score:.2f}",
            'Created At': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(df_data)
    excel_path = os.path.join(settings.MEDIA_ROOT, "translated_texts.xlsx")
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    return FileResponse(open(excel_path, 'rb'), as_attachment=True, filename="translated_texts.xlsx")

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Đăng ký thành công!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'text_detection/register.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'text_detection/profile.html', context)

@login_required
def my_detections(request):
    detections = DetectionResult.objects.filter(user=request.user).order_by('-created_at')
    translations = CombinedTranslation.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'detections': detections,
        'translations': translations,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'text_detection/my_detections.html', context)

def home(request):
    if request.user.is_authenticated:
        recent_detections = DetectionResult.objects.filter(user=request.user).order_by('-created_at')[:5]
        recent_translations = CombinedTranslation.objects.filter(user=request.user).order_by('-created_at')[:5]
        context = {
            'recent_detections': recent_detections,
            'recent_translations': recent_translations
        }
    else:
        context = {}
    return render(request, 'text_detection/index.html', context)
