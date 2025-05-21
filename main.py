from flask import Flask, request, jsonify
from moviepy.editor import *
import openai
import os
import requests
from PIL import Image
from io import BytesIO

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")


def gerar_audio_elevenlabs(texto):
    api_key = os.environ.get("ELEVEN_API_KEY")
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # voz americana padrão da Eleven

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": texto,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8
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


def buscar_imagem(produto):
    url = "https://source.unsplash.com/1280x720/?" + produto
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        img.save("fundo.jpg")
        return "fundo.jpg"
    return None

@app.route("/gerar", methods=["POST"])
def gerar_video():
    print("🔥 Entrou na função gerar_video")

    return jsonify({"mensagem": "Servidor recebeu o POST com sucesso!"}), 200

        print("🔥 Requisição recebida no /gerar")

        print("RAW BODY:", request.data)
        print("HEADERS:", dict(request.headers))

        data = request.get_json(force=True)
        produto = data.get("produto")
        link = data.get("link")

        print("Produto:", produto)
        print("Link:", link)

        prompt = f"Write a 30-second persuasive script to sell the product '{produto}', focusing on pain, desire, and urgency. End with: 'Link in description: {link}'"
        print("Prompt criado:", prompt)

        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.1
        )
        texto = resposta.choices[0].message.content
        print("Texto gerado:", texto)

        if not gerar_audio_elevenlabs(texto):
            return jsonify({"erro": "Erro ao gerar áudio"}), 500

        fundo = buscar_imagem(produto)
        if not fundo:
            return jsonify({"erro": "Imagem não encontrada"}), 500

        imagem = ImageClip(fundo).set_duration(30)
        audio = AudioFileClip("audio.mp3")
        video = imagem.set_audio(audio)
        video.write_videofile("vsl_final.mp4", fps=24)

        return jsonify({"mensagem": "VSL criada com sucesso!"})
    
    except Exception as e:
        print("Erro final:", str(e))
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500

    # Imagem
    fundo = buscar_imagem(produto)
    if not fundo:
        return jsonify({"erro": "Imagem não encontrada"}), 500

    # Vídeo
    imagem = ImageClip(fundo).set_duration(30)
    audio = AudioFileClip("audio.mp3")
    video = imagem.set_audio(audio)
    video.write_videofile("vsl_final.mp4", fps=24)

    return jsonify({"mensagem": "VSL criada com sucesso!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
