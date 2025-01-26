import os
import torch
import librosa
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from moviepy import VideoFileClip
from io import BytesIO
import tempfile
from langchain_groq import ChatGroq


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = "AIzaSyBFvUh4MGR9astxpNsmYtSrYihFS63-iVE"
if not GOOGLE_API_KEY:
    logger.error("Google API key not found in environment variables.")
else:
    genai.configure(api_key=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)


GROQ_API_KEY = "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"

# Load STT model
try:
    logger.info("Loading Uzbek Speech-to-Text model...")
    processor = Wav2Vec2Processor.from_pretrained("oyqiz/uzbek_stt")
    model = Wav2Vec2ForCTC.from_pretrained("oyqiz/uzbek_stt")
    logger.info("Uzbek Speech-to-Text model loaded successfully.")
except Exception as e:
    logger.exception("Failed to load Uzbek Speech-to-Text model.")


def uzbek_speech_to_text(audio_file):
    """
    Convert Uzbek speech to text using a Wav2Vec2 model and correct its grammar using a Groq model.
    Args:
        audio_file (str or file-like): Path to the audio file or file object.

    Returns:
        str: Corrected transcription.
    """
    try:
        # Step 1: Transcribe speech to text
        logger.info("Processing audio file for speech-to-text...")
        audio, _ = librosa.load(audio_file, sr=16000)
        input_values = processor(
            audio, return_tensors="pt", padding="longest"
        ).input_values
        with torch.no_grad():
            logits = model(input_values).logits
            predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
        logger.info("Speech-to-text transcription completed successfully.")

        # Step 2: Correct grammar using Groq model
        logger.info("Correcting grammar using Groq model...")
        llm = ChatGroq(
            model="llama-3.3-70b-versatile", temperature=1  # Specify the model
        )
        messages = [
            (
                "system",
                "Siz o'zbek tilida mutaxassissiz. Sizning vazifangiz berilgan o'zbek matnining grammatikasini to'g'rilash. Hech qanday izoh, tarjima yoki qo'shimcha ma'lumot bermang. Faqat to'g'rilangan o'zbek matnini qaytaring.",
            ),
            ("human", transcription),
        ]

        response = llm.invoke(messages)
        if hasattr(response, "content"):
            transcription = response.content.split("content")[0].strip()
        else:
            transcription = str(response).split("content")[0].strip()
        return transcription

    except Exception as e:
        logger.exception("Error during speech-to-text or grammar correction.")
        return "Error in speech-to-text or grammar correction."


def generate_gemini_content(text, prompt):
    """
    Generate content using the Google Gemini generative model.
    Args:
        text (str): Input text for processing.
        prompt (str): Prompt to guide content generation.

    Returns:
        str: Generated content from the model.
    """
    if not GOOGLE_API_KEY:
        logger.error("Google API key not configured. Cannot generate content.")
        return "Error: Google API key not configured."

    try:
        logger.info("Generating content using Google Gemini model...")
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        response = model.generate_content(f"{prompt} {text}")
        logger.info("Content generation completed successfully.")
        return response.text
    except Exception as e:
        logger.exception("Error during content generation.")
        return "Error in content generation."
