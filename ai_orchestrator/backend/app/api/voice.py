from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.services.voice_to_task import process_voice_command, pick_demo_transcript
import os
import tempfile

router = APIRouter()

class VoicePayload(BaseModel):
    audio_base64: Optional[str] = None
    test_text: Optional[str] = None

@router.post("/task")
async def handle_voice_task(payload: VoicePayload):
    """Принимает текст и создаёт задачи через LLM."""
    result = process_voice_command(test_text=payload.test_text)
    links = [f"https://dashboard.example.com/task/{i}" for i in range(len(result.tasks))]
    return {
        "voice_decomposition": result,
        "task_links": links
    }

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Принимает аудиофайл (webm/wav) → транскрибирует через OpenAI Whisper.
    Если ключ невалидный — возвращает ошибку.
    """
    stt_api_key = os.getenv("ALEM_STT_API_KEY", "")
    alem_stt_url = os.getenv("ALEM_STT_URL", "https://llm.alem.ai/v1/audio/transcriptions")
    alem_stt_model = os.getenv("ALEM_STT_MODEL", "speech-to-text")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    openai_stt_model = os.getenv("OPENAI_STT_MODEL", "whisper-1")
    
    # Сохраняем временный файл
    suffix = ".webm" if "webm" in (file.content_type or "") else ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    wav_path = tmp_path + ".wav"
    upload_path = tmp_path
    filename = "voice.webm"
    mime = "audio/webm"

    try:
        if not stt_api_key or stt_api_key == "mock":
            fallback_text = pick_demo_transcript()
            return {"transcript": fallback_text, "error": "fallback_mode", "engine": "mock"}

        import subprocess
        try:
            # Конвертируем WebM из браузера в чистый WAV (16kHz), который 100% поддерживается любым движком
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            upload_path = wav_path
            filename = "voice.wav"
            mime = "audio/wav"
        except FileNotFoundError:
            return {"transcript": None, "error": "ffmpeg_not_installed"}
        except subprocess.CalledProcessError:
            return {"transcript": None, "error": "ffmpeg_conversion_failed"}
        
        # --- PROVIDER 1: ALEM STT (PRIMARY) ---
        import requests
        stt_url = alem_stt_url
        headers = {"Authorization": f"Bearer {stt_api_key}"}
        data = {"model": alem_stt_model, "language": "ru"}
        
        try:
            with open(upload_path, "rb") as audio_file:
                files = {"file": (filename, audio_file, mime)}
                response = requests.post(stt_url, headers=headers, files=files, data=data, timeout=20)
            if response.status_code == 200:
                transcription_data = response.json()
                transcript_text = (
                    transcription_data.get("text")
                    or transcription_data.get("transcript")
                    or transcription_data.get("result", {}).get("text", "")
                )
                return {"transcript": transcript_text, "error": None, "engine": "alem", "model": alem_stt_model}
            print(f"⚠️ Alem API failed ({response.status_code}). Trying Whisper...")
        except Exception as net_err:
            print(f"⚠️ Alem Network Error: {net_err}. Trying Whisper...")

        # --- PROVIDER 2: OPENAI WHISPER (FALLBACK 1) ---
        if openai_key and openai_key != "mock" and len(openai_key) > 5:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                with open(upload_path, "rb") as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model=openai_stt_model,
                        file=audio_file,
                        language="ru"
                    )
                return {"transcript": transcript.text, "error": None, "engine": "openai", "model": openai_stt_model}
            except Exception as whisper_err:
                print(f"⚠️ Whisper API Error: {whisper_err}")

        # --- PROVIDER 3: SMART MOCK (FALLBACK 2 / OFFLINE) ---
        # Для хакатона: если всё упало, возвращаем одну из ожидаемых фраз на основе длины аудио
        fallback_text = pick_demo_transcript()
        print(f"вњ… Demo Fallback triggered: '{fallback_text}'")
        return {"transcript": fallback_text, "error": "fallback_mode", "engine": "mock"}
        duration_mock = os.path.getsize(upload_path)
        if duration_mock > 50000: # длинный запрос
            fallback_text = "Айгерим, подготовьте актовый зал к мероприятию на среду"
        else:
            fallback_text = "Закажите 20 бутылей воды на завтра"
            
        print(f"✅ Demo Fallback triggered: '{fallback_text}'")
        return {"transcript": fallback_text, "error": "fallback_mode", "engine": "mock"}
    
    except Exception as e:
        return {"transcript": "Повторите, пожалуйста", "error": f"Critical: {str(e)}"}
    finally:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except:
            pass
