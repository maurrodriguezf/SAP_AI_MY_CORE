import speech_recognition as sr
import requests
import pyttsx3
import time

# Configuración de la API de LM Studio
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

# Inicializar el reconocedor de voz
recognizer = sr.Recognizer()

# Configurar el motor de texto a voz
tts_engine = pyttsx3.init()

# Configurar propiedades de la voz
voices = tts_engine.getProperty('voices')
# Para voz en español, si está disponible (depende de tu sistema)
for index, voice in enumerate(voices):
    if "spanish" in voice.name.lower() or "español" in voice.name.lower():
        tts_engine.setProperty('voice', voice.id)
        break
else:
    print("Voz en español no encontrada. Usando voz predeterminada.")

tts_engine.setProperty('rate', 150)  # Velocidad de habla
tts_engine.setProperty('volume', 0.9)  # Volumen (0.0 a 1.0)

def listen_and_transcribe():
    """Escucha del micrófono y transcribe el audio a texto"""
    with sr.Microphone() as source:
        print("Ajustando para ruido ambiente... por favor espera.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Di algo...")
        
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Procesando audio...")
            
            # Usar Google Speech Recognition
            text = recognizer.recognize_google(audio, language='es-ES')
            print(f"Tú: {text}")
            return text
            
        except sr.WaitTimeoutError:
            print("Tiempo de espera agotado. No se detectó voz.")
            return None
        except sr.UnknownValueError:
            print("No se pudo entender el audio")
            return None
        except sr.RequestError as e:
            print(f"Error en el servicio de reconocimiento: {e}")
            return None

def send_to_lm_studio(message, conversation_history=[]):
    """Envía el mensaje a LM Studio y devuelve la respuesta"""
    # Agregar el nuevo mensaje al historial de conversación
    conversation_history.append({"role": "user", "content": message})
    
    payload = {
        "model": "openai/gpt-oss-20b",  # Reemplaza con el nombre de tu modelo cargado en LM Studio
        "messages": conversation_history,
        "temperature": 0.7,
        "max_tokens": -1,
        "stream": False
    }
    
    try:
        response = requests.post(LM_STUDIO_API_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()  # Lanza excepción para códigos de error HTTP
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        # Agregar la respuesta al historial
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message, conversation_history
        
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con LM Studio: {e}")
        return None, conversation_history

def speak(text):
    """Reproduce el texto usando el motor de texto a voz"""
    if text:
        print(f"Asistente: {text}")
        tts_engine.say(text)
        tts_engine.runAndWait()
    else:
        print("No hay texto para reproducir")

def main():
    print("Iniciando asistente de voz con LM Studio...")
    print("Presiona Ctrl+C para salir")
    
    conversation_history = []
    
    try:
        while True:
            # Escuchar y transcribir
            user_text = listen_and_transcribe()
            
            if user_text:
                # Enviar a LM Studio
                response, conversation_history = send_to_lm_studio(user_text, conversation_history)
                
                if response:
                    # Reproducir la respuesta
                    speak(response)
                else:
                    speak("Lo siento, hubo un error al procesar tu solicitud.")
            
            # Pequeña pausa antes de escuchar de nuevo
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nSaliendo del asistente de voz...")

if __name__ == "__main__":
    main()