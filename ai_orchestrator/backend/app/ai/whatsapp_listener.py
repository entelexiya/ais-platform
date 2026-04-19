import asyncio
import subprocess
import os
import logging
from app.ai.whatsapp_voice_handler import handle_incoming_wa_audio

logging.basicConfig(level=logging.INFO)

async def listen_whatsapp():
    """
    Полноценный слушатель: Запускает Node.js процесс c whatsapp-web.js 
    и читает его логи, интегрируя его в единый бэкенд.
    """
    logging.info("Инициализация WhatsApp Слушателя (Hybrid Mode)...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    wa_dir = os.path.join(base_dir, "..", "whatsapp_bot")
    
    # Пытаемся запустить Node.js процесс
    if not os.path.exists(os.path.join(wa_dir, "package.json")):
        logging.error(f"Директория whatsapp_bot не найдена или пуста: {wa_dir}")
        return

    logging.info(f"Запуск Node.js процесса из {wa_dir}...")
    try:
        # Устанавливаем зависимости перед запуском
        # subprocess.run(["npm", "install"], cwd=wa_dir)
        
        process = subprocess.Popen(
            ["npm", "start"], 
            cwd=wa_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Читаем вывод Node.js скрипта в реальном времени
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[WA Listener] {output.strip()}")
                
    except Exception as e:
        logging.error(f"Сбой при запуске WhatsApp Listener: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_whatsapp())
    except KeyboardInterrupt:
        print("WhatsApp Слушатель остановлен.")
