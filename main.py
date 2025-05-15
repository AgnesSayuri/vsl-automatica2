from flask import Flask, request, jsonify
import openai
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image
import requests
from io import BytesIO
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# === FUNÇÃO MODULAR: pode ser trocada pela API da Shopee futuramente ===
def obter_produtos():
    return [
        {
            "nome": "Relógio Smart Fitness Pro",
            "link": "https://shope.ee/abc123"
        },
        {
            "nome": "Fone Bluetooth X7",
            "link": "https://shope.ee/xyz456"
        }
    ]

# === GERADOR DE ÁUDIO COM ELEVENLABS ===
def gerar_audio_elevenlabs(texto):
    api_key = os.getenv("ELEVEN_API_KEY)"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": texto,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        with open("audio.mp3", "wb") as f:
            f.write(response.content)
        return True
    else:
        print("Erro ao gerar áudio:", response.text)
        return False

# === GERADOR DE IMAGEM COM TEXTO DO PRODUTO ===
def buscar_imagem(produto):
    query = produto.replace(" ", "+")
    url = f"https://via.placeholder.com/1280x720.png?text={query}"
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        img.save("fundo.jpg")
        return "fundo.jpg"
    else:
        return None

# === ENDPOINT: gera 1 VSL de produto enviado via POST ===
@app.route("/gerar", methods=["POST"])
def gerar_video():
    data = request.json
    produto = data.get("produto")
    link = data.get("link")

    prompt = f"Crie um roteiro persuasivo de 30 segundos para vender o produto '{produto}', focando em dor, desejo e urgência. Finalize com: 'Link na descrição.'"
    resposta = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=200
    )
    texto = resposta.choices[0].text.strip()
    print("Roteiro gerado:", texto)

    if not gerar_audio_elevenlabs(texto):
        return jsonify({"erro": "Erro ao gerar áudio com ElevenLabs"}), 500

    imagem_path = buscar_imagem(produto)
    if not imagem_path:
        return jsonify({"erro": "Erro ao baixar imagem"}), 500

    audio = AudioFileClip("audio.mp3")
    imagem = ImageClip(imagem_path).set_duration(audio.duration).set_audio(audio).resize(height=720)
    video_filename = f"video_{produto.replace(' ', '_')}.mp4"
    imagem.write_videofile(video_filename, fps=24)

    return jsonify({"mensagem": "Vídeo gerado com sucesso!", "roteiro": texto, "arquivo": video_filename})

# === ENDPOINT EXTRA: gera todos os produtos automaticamente ===
@app.route("/gerar-todos", methods=["GET"])
def gerar_videos_em_lote():
    produtos = obter_produtos()
    resultados = []
    for item in produtos:
        response = requests.post("http://localhost:8080/gerar", json=item)
        resultados.append(response.json())
    return jsonify(resultados)

app.run(host="0.0.0.0", port=8080)
