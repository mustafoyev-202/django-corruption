import json
import logging
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .utils import uzbek_speech_to_text, generate_gemini_content
from django.views.decorators.csrf import csrf_exempt
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os, json
from django.conf import settings
from datetime import datetime

load_dotenv()
GROQ_API_KEY = "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"


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def home(request):
    """Render the homepage."""
    return render(request, "index.html")


def user_login(request):
    """Handle user login."""
    error_message = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            error_message = "Username and password are required."
            logger.error("Username or password missing.")
            return render(request, "login.html", {"error_message": error_message})

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully.")
            return redirect("home")
        else:
            error_message = "Invalid username or password."
            logger.warning(f"Failed login attempt for {username}.")
    return render(request, "login.html", {"error_message": error_message})


def user_signup(request):
    """Handle user signup."""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        repeat_password = request.POST.get("repeatPassword", "").strip()

        if not all([username, email, password, repeat_password]):
            error_message = "All fields are required."
            logger.error("All fields are required for signup.")
            return render(request, "signup.html", {"error_message": error_message})

        if len(password) < 8:
            error_message = "Password must be at least 8 characters long."
            logger.error("Password too short.")
            return render(request, "signup.html", {"error_message": error_message})

        if password != repeat_password:
            error_message = "Passwords do not match."
            logger.error("Passwords do not match.")
            return render(request, "signup.html", {"error_message": error_message})

        try:
            if User.objects.filter(username=username).exists():
                error_message = "Username already exists."
                logger.warning(f"Username {username} already exists.")
                return render(request, "signup.html", {"error_message": error_message})

            if User.objects.filter(email=email).exists():
                error_message = "Email already in use."
                logger.warning(f"Email {email} already in use.")
                return render(request, "signup.html", {"error_message": error_message})

            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            login(request, user)
            logger.info(f"User {username} signed up and logged in.")
            return redirect("home")

        except Exception as e:
            error_message = f"Registration failed: {str(e)}"
            logger.exception("Error during user signup.")
            return render(request, "signup.html", {"error_message": error_message})

    return render(request, "signup.html")


def user_logout(request):
    """Handle user logout."""
    logout(request)
    logger.info("User logged out successfully.")
    return redirect("login")


@login_required
def submit_text_complaint(request):
    """Handle text complaint submission."""
    if request.method == "POST":
        try:
            text_complaint = request.POST.get("complaint")
            prompt = "Siz O'zbekiston qonunlari va huquqiy me'yorlar bo'yicha yetuk advokatsiz. Quyidagi shikoyatni ko'rib chiqing, undagi huquqiy muammolarni aniqlang, ularning qonunchilikka muvofiqligini tahlil qiling, eng muhim jihatlarni ustuvorlik bilan ajratib ko'rsating va qonuniy asoslangan amaliy yechimlar taklif qiling. Javobda faqat professional huquqiy tahlil va aniq yechimlarni ko'rsating."
            summary = generate_gemini_content(text_complaint, prompt)
            return JsonResponse({"success": True, "summary": summary})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return render(request, "submit_text_complaint.html")


@login_required
@csrf_exempt
def submit_audio_complaint(request):
    """
    Handle audio complaint submission via file upload or recorded audio.
    """
    if request.method == "POST" and request.FILES.get("audio"):
        audio_file = request.FILES["audio"]
        try:
            logger.info("Received audio file for complaint submission.")

            # Process transcription
            transcription = uzbek_speech_to_text(audio_file)
            if "Error" in transcription:
                logger.error("Transcription failed.")
                return JsonResponse(
                    {"success": False, "error": "Transcription failed."}
                )

            # Generate summary
            prompt = "Siz O'zbekiston qonunlari va huquqiy me'yorlar bo'yicha yetuk advokatsiz. Quyidagi shikoyatni ko'rib chiqing, undagi huquqiy muammolarni aniqlang, ularning qonunchilikka muvofiqligini tahlil qiling, eng muhim jihatlarni ustuvorlik bilan ajratib ko'rsating va qonuniy asoslangan amaliy yechimlar taklif qiling. Javobda faqat professional huquqiy tahlil va aniq yechimlarni ko'rsating."
            summary = generate_gemini_content(transcription, prompt)
            if "Error" in summary:
                logger.error("Content generation failed.")
                return JsonResponse(
                    {"success": False, "error": "Content generation failed."}
                )

            logger.info("Successfully processed audio complaint.")
            return JsonResponse(
                {
                    "success": True,
                    "summary": {
                        "transcription": transcription,
                        "summary": summary,
                    },
                }
            )
        except Exception as e:
            logger.exception("Error processing audio complaint.")
            return JsonResponse({"success": False, "error": str(e)})

    logger.warning("No audio file received in request.")
    return render(request, "submit_audio_complaint.html")


@csrf_exempt
@login_required
def chatbot_api(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Method not allowed"}, status=405
        )

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse(
                {"status": "error", "message": "Message cannot be empty"}, status=400
            )

        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=1)

        # Correct message format for Groq
        messages = [
            {
                "role": "system",
                "content": "Siz O'zbekiston qonunlari, huquqiy me'yorlari, va ularning amaliy qo'llanilishi bo'yicha chuqur bilim va tajribaga ega bo'lgan yetuk huquqiy mutaxassissiz. Sizga huquqiy masalalarni tahlil qilish, aniq va asosli huquqiy maslahatlar berish, shuningdek, O'zbekiston qonunchiligiga oid masalalarda dolzarb va samarali yechimlar taklif qilish vazifasi yuklatilgan. Berilgan savollarga ideal ravishda javob bering.",
            },
            {"role": "user", "content": message},
        ]

        response = llm.invoke(messages)

        return JsonResponse(
            {
                "status": "success",
                "response": response.content,  # Access the content property
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@login_required
def about(request):
    return render(request, "about.html")
