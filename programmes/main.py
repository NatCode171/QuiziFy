import random, time, cv2, os, requests, tempfile, base64, string, re, json, math
import numpy as np
from collections import deque
from openai import OpenAI, OpenAIError, RateLimitError
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
import google_auth_oauthlib.flow, googleapiclient.discovery, googleapiclient.errors, googleapiclient.http, google.auth.transport.requests, pickle

# CONSTANTES
with open("../outis/constantes.json", "r", encoding="utf-8") as f:
    constantes = json.load(f)

    API_KEY = constantes["API_KEY"]
    BG_VIDEO = constantes["BG_VIDEO"]
    BACKGROUND_MUSIC_COURT = constantes["BACKGROUND_MUSIC_COURT"]
    BACKGROUND_MUSIC_LONG = constantes["BACKGROUND_MUSIC_LONG"]
    YT_NAME_FILE = constantes["YT_NAME_FILE"]
    GAMEPLAY_CLIP = constantes["GAMEPLAY_CLIP"]
    SCOPES = constantes["SCOPES"]
    CONTENT_FILE_DEFAULT = constantes["CONTENT_FILE_DEFAULT"]
    FONT_PATH = constantes["FONT_PATH"]
    NOBEEP_PATH = constantes["NOBEEP_PATH"]
    BEEP_PATH = constantes["BEEP_PATH"]
    CONFIG_FILE = constantes["CONFIG_FILE"]
    THEMES_FILE = constantes["THEMES_FILE"]
    MODEL = constantes["MODEL"]
    QUESTION_INTERVAL = constantes["QUESTION_INTERVAL"]
    SILENCE_DURATION = constantes["SILENCE_DURATION"]
    SECS_ENT = constantes["SECS_ENT"]
    SECS = constantes["SECS"]
    CERCLE_COLOR = [tuple(color) for color in constantes["CERCLE_COLOR"]]
    PROMPT = constantes["PROMPT"]

def init():
    # On change de répertoire, on va dans le dossier d'avant (../)
    os.chdir(os.path.abspath(os.path.join(os.getcwd(), "..")))

    # On vérifie si les dossiers existent
    os.makedirs("outis", exist_ok=True)
    os.makedirs("outis/audio", exist_ok=True)
    os.makedirs("outis/background_video", exist_ok=True)
    os.makedirs("outis/font", exist_ok=True)
    os.makedirs("outis/gameplay", exist_ok=True)
    os.makedirs("outis/youtubeAPI", exist_ok=True)
    os.makedirs("shorts", exist_ok=True)

    # On vérifie si le fichier de config existe
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write(CONTENT_FILE_DEFAULT)

    # On vérifie si le fichier de themes existe
    if not os.path.exists(THEMES_FILE):
        with open(THEMES_FILE, "w") as f:
            f.write("viral")

    with open(THEMES_FILE, "r", encoding="utf-8") as f:
        lignes = f.readlines()
        themes = [ligne.strip() for ligne in lignes if ligne.strip()]

    return themes

def setup():
    # On récup le fichier de config
    with open(CONFIG_FILE, "r") as f:
        contenu = f.read()

    # Puis on regarde le nom de la prochaine vidéo
    try:
        variables = eval(contenu, {}, {})
    except Exception:
        variables = {"vid_name": 1}

    # On choisit le nombre de questions
    quest_nb = random.choice([2, 3, 5, 6, 8, 10])
    print(f"Nombre de questions : {quest_nb}")

    return variables.get("vid_name", 1), quest_nb

def generate_voice(text):
    headers = {
        "User-Agent": "Mozilla/5.0 Google Chrome (Win11; x64); KHTML (like Gecko)"
    }
    data = {
        "text": text,
        "voice": "fr_001"
    }
    resp = requests.post("https://tiktok-tts.weilnet.workers.dev/api/generation", headers=headers, json=data)
    filename = tempfile.mktemp(suffix=".mp3")
    with open(filename, "wb") as tmp_file:
        tmp_file.write(base64.b64decode(resp.json()["data"].encode()))
    return filename

def addata(nb):
    content = f'{{"vid_name": {nb}}}'
    with open(CONFIG_FILE, "w") as f:
        f.write(content)

def ask_chatGPT(prompt, openai_key, i):
    try:
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.2,
            top_p=0.8
        )
        # Vérifie que le contenu existe bien
        if response and response.choices and response.choices[0].message:
            return response.choices[0].message.content.strip()
        else:
            print(f"Réponse vide ou invalide avec {openai_key[:15]}...")
            return None
    except RateLimitError as e:
        print(f"Quota dépassé pour la clé {i} : {openai_key[:15]}...")
    except OpenAIError as e:
        print(f"Erreur API pour la clé {i} avec {openai_key[:15]}...")
    except Exception as e:
        print(f"Erreur inattendue pour la clé {i} avec {openai_key[:15]}...")
    return None

def get_chatGPT_rep(prompt):
    for i, key in enumerate(API_KEY):
        try:
            rep = ask_chatGPT(prompt, key, i + 1)
            if rep:
                return rep, True
        except Exception as e:
            print(f"Exception inattendue avec la clé {i + 1} : {e}")

    print("Toutes les clés ont échoué. Attente de 5 mins avant de réessayer...")
    time.sleep(60 * 5)
    return "", False

def wrap_text_pil(text, font, max_width):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if font.getlength(test_line) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines

def draw_text_pil(draw, lines, x_center, y_start, line_height, font, fill):
    for i, line in enumerate(lines):
        text_width = font.getlength(line)
        x = x_center - text_width / 2
        y = y_start + i * line_height
        draw.text((x, y), line, font=font, fill=fill)

def clean_string(text):
    allowed_chars = string.ascii_letters + string.digits + string.punctuation + ' '
    pattern = f"[^{re.escape(allowed_chars)}]"
    return re.sub(pattern, "", text)

def create_vertical_countdown_video(quest_nb, vid_name, output_file, fps, resolution, questions, answers):
    video = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, resolution)

    bg_video = VideoFileClip(random.choice(BG_VIDEO)).resized(resolution)
    bg_duration = bg_video.duration
    gameplay_clip = VideoFileClip(random.choice(GAMEPLAY_CLIP)).without_audio()
    gameplay_height = int(resolution[1] * 0.35)
    gameplay_width = int(gameplay_clip.w * (gameplay_height / gameplay_clip.h))
    gameplay_clip = gameplay_clip.resized((gameplay_width, gameplay_height))
    gameplay_duration = gameplay_clip.duration
    frame_gameplay = 0

    font_question = ImageFont.truetype(FONT_PATH, 36)
    font_count = ImageFont.truetype(FONT_PATH, 140)
    font_answer = ImageFont.truetype(FONT_PATH, 70)
    cercle_color = random.choice(CERCLE_COLOR)
    center = (resolution[0] // 2, resolution[1] // 2)

    fail_answer_nb = random.randint(math.ceil(quest_nb / 2), quest_nb)
    pause = random.randint(math.floor(quest_nb / 2), quest_nb - 1)
    tts_questions, tts_answers = [], []
    teaser_audio_path, is_audio = False, False

    teaser_text = f"😱 Tu n'arriveras jamais à répondre à la {fail_answer_nb}ème question !!! ❌"
    teaser_audio_path = generate_voice(teaser_text)
    teaser_lines = wrap_text_pil(teaser_text, font_question, resolution[0] - 100)

    intro_lines = wrap_text_pil(f"🔥 {random.randint(50, 99)}% des gens échouent à ce quiz ✅ Seulement les vrais savent ! 🔥", font_question, resolution[0] - 100)

    for i in range(SECS_ENT * fps):
        current_time = min((i / fps) % bg_duration, bg_duration - 0.01)
        img = Image.fromarray(bg_video.get_frame(current_time)).convert("RGB")

        frame_gameplay += 1
        current_gameplay_time = min((frame_gameplay / fps) % gameplay_duration, gameplay_duration - 0.01)
        gameplay_img = Image.fromarray(gameplay_clip.get_frame(current_gameplay_time)).convert("RGB")
        img.paste(gameplay_img, ((resolution[0] - gameplay_width) // 2, resolution[1] - gameplay_height))

        draw = ImageDraw.Draw(img)
        draw_text_pil(draw, intro_lines, center[0], center[1] - 500, 50, font_question, (255, 255, 255))
        draw_text_pil(draw, teaser_lines, center[0], center[1] - 50, 50, font_question, (255, 255, 255))

        video.write(np.array(img))

    nq = -1
    for nbq in range(quest_nb + 1):
        nq += 1
        if (nbq) == pause:
            nq -= 1
            pause_1_txt = "Avant de continuer, abonne toi si tu aimes ce genre de quiz !"
            pause_2_txt = "Et dis en commentaire à quelle heure tu as vu ce short 😉"
            pause_1_audio, pause_2_audio = generate_voice(pause_1_txt), generate_voice(pause_2_txt)
            is_audio, nb_question_pause_last = True, nbq

            pause_txt_1_lines = wrap_text_pil(pause_1_txt, font_question, resolution[0] - 100)
            pause_txt_2_lines = wrap_text_pil(pause_2_txt, font_answer, resolution[0] - 100)

            for frame_idx in range(6 * fps):
                current_time = min((frame_idx / fps) % bg_duration, bg_duration - 0.01)
                img = Image.fromarray(bg_video.get_frame(current_time)).convert("RGB")
                frame_gameplay += 1
                current_gameplay_time = min((frame_gameplay / fps) % gameplay_duration, gameplay_duration - 0.01)
                gameplay_img = Image.fromarray(gameplay_clip.get_frame(current_gameplay_time)).convert("RGB")
                img.paste(gameplay_img, ((resolution[0] - gameplay_width) // 2, resolution[1] - gameplay_height))
                draw = ImageDraw.Draw(img)
                alpha = min(1.0, frame_idx / (2 * fps))
                draw_text_pil(draw, pause_txt_1_lines, center[0], center[1] - 300, 50, font_question, (255, 255, 255, int(255 * alpha)))
                draw_text_pil(draw, pause_txt_2_lines, center[0], center[1] - 150, 65, font_answer, (255, 255, 255, int(255 * alpha)))
                video.write(np.array(img))
        else:
            question, answer = questions[nq], answers[nq]
            tts_questions.append(generate_voice(clean_string(question)))
            tts_answers.append(generate_voice(clean_string(answer)))
            question_lines = wrap_text_pil(question, font_question, resolution[0] - 100)
            answer_lines = wrap_text_pil(answer, font_answer, resolution[0] - 100)

            for frame_idx in range((SECS + 1 + 5) * fps):
                current_time = min((frame_idx / fps) % bg_duration, bg_duration - 0.01)
                img = Image.fromarray(bg_video.get_frame(current_time)).convert("RGB")
                img.paste(gameplay_img, ((resolution[0] - gameplay_width) // 2, resolution[1] - gameplay_height))
                draw = ImageDraw.Draw(img)
                draw.text((20, 20), f"Question {nq + 1}/{quest_nb}", font=font_question, fill=(255, 255, 255))
                draw_text_pil(draw, question_lines, center[0], 130, 45, font_question, (200, 200, 200))

                if frame_idx < (SECS + 1) * fps:
                    sec = SECS - (frame_idx // fps)
                    frame_in_sec = frame_idx % fps
                    pulse_scale = 1 + 0.1 * np.sin(2 * np.pi * frame_in_sec / fps)
                    font_dynamic = ImageFont.truetype(font_count.path, int(font_count.size * pulse_scale))
                    text_width = font_dynamic.getlength(str(sec))
                    text_height = font_dynamic.getbbox(str(sec))[3] - font_dynamic.getbbox(str(sec))[1]
                    draw.text((center[0] - text_width / 2, center[1] - text_height / 2), str(sec), font=font_dynamic, fill=(255, 255, 255))
                    frame_cv = np.array(img)
                    cv2.ellipse(frame_cv, center, (200, 200), 0, -90, int(360 * ((frame_in_sec + 1) / fps)) - 90, cercle_color, 20)
                    img = Image.fromarray(frame_cv)
                    img.paste(gameplay_img, ((resolution[0] - gameplay_width) // 2, resolution[1] - gameplay_height))
                else:
                    alpha = min(1.0, (frame_idx - (SECS + 1) * fps) / (1.5 * fps))
                    temp_img = Image.new("RGBA", resolution, (0, 0, 0, 0))
                    draw_text_pil(ImageDraw.Draw(temp_img), answer_lines, center[0], center[1] - 40, 80, font_answer, (255, 255, 255, int(255 * alpha)))
                    img = Image.alpha_composite(img.convert("RGBA"), temp_img).convert("RGB")

                frame_gameplay += 1
                current_gameplay_time = min((frame_gameplay / fps) % gameplay_duration, gameplay_duration - 0.01)
                gameplay_img = Image.fromarray(gameplay_clip.get_frame(current_gameplay_time)).convert("RGB")
                video.write(np.array(img))

    font_final = ImageFont.truetype(FONT_PATH, 60)
    lines = "🔥 Abonne-toi !!! 🔥\n\n👇 et 👇\n\ndis ton score\n🧠 en commentaire ! 💬".split("\n")
    line_spacing = 10
    line_heights = [(font_final.getbbox(line)[3] - font_final.getbbox(line)[1]) if line.strip() else font_final.size for line in lines]
    total_text_height = sum(line_heights) + (len(lines) - 1) * line_spacing
    line_positions = []
    current_y = (resolution[1] - total_text_height) / 2 - 100
    for i, line in enumerate(lines):
        line_positions.append((line, current_y))
        current_y += line_heights[i] + line_spacing

    for i in range(3 * fps):
        current_time = min((i / fps) % bg_duration, bg_duration - 0.01)
        img = Image.fromarray(bg_video.get_frame(current_time)).convert("RGB")
        frame_gameplay += 1
        current_gameplay_time = min((frame_gameplay / fps) % gameplay_duration, gameplay_duration - 0.01)
        gameplay_img = Image.fromarray(gameplay_clip.get_frame(current_gameplay_time)).convert("RGB")
        img.paste(gameplay_img, ((resolution[0] - gameplay_width) // 2, resolution[1] - gameplay_height))
        draw = ImageDraw.Draw(img)
        for line, y in line_positions:
            if line.strip():
                draw.text(((resolution[0] - font_final.getlength(line)) / 2, y), line, font=font_final, fill=(255, 255, 0))
        video.write(np.array(img))

    video.release()
    print(f"Vidéo créée : {output_file}")

    video = VideoFileClip(output_file)
    beep, nobeep = AudioFileClip(BEEP_PATH), AudioFileClip(NOBEEP_PATH)
    music_file = random.choice(BACKGROUND_MUSIC_COURT if video.duration <= 59 else BACKGROUND_MUSIC_LONG)
    background_music = AudioFileClip(music_file).with_duration(video.duration)

    spaced_beeps, tts_clips = [], []
    total_questions = quest_nb + 1 if is_audio else quest_nb
    s = 3
    nbq = 0
    timings = {
        "teaser": 0,
        "questions": [],
        "answers": [],
        "pauses": 3 + nb_question_pause_last * QUESTION_INTERVAL
    }

    for q in range(total_questions):
        if q == nb_question_pause_last:
            s += 6
            continue
        nbq += 1
        timings["questions"].append((nbq, s))
        timings["answers"].append((nbq, s))
        s += QUESTION_INTERVAL

    if teaser_audio_path:
        tts_clips.append(AudioFileClip(teaser_audio_path).with_start(timings["teaser"]))

    nbq, q_audio = 0, 0
    for q in range(total_questions):
        if is_audio and q == nb_question_pause_last:
            tts_clips.append(AudioFileClip(pause_1_audio).with_start(timings["pauses"]))
            tts_clips.append(AudioFileClip(pause_2_audio).with_start(timings["pauses"] + AudioFileClip(pause_1_audio).duration + 0.3))
            continue
        nbq += 1
        try:
            _, base_time = timings["questions"][q_audio]
        except IndexError:
            continue
        if q_audio < len(tts_questions):
            tts_clips.append(AudioFileClip(tts_questions[q_audio]).with_start(base_time))
        for i in range(SECS + 1):
            spaced_beeps.append(beep.with_start(base_time + i))
        spaced_beeps.append(nobeep.with_start(base_time + 12).with_duration(SILENCE_DURATION))
        if q_audio < len(tts_answers):
            tts_clips.append(AudioFileClip(tts_answers[q_audio]).with_start(base_time + SECS + 1))
        q_audio += 1

    final_audio = CompositeAudioClip(tts_clips + spaced_beeps + [background_music]).with_duration(video.duration)
    final_video = video.with_audio(final_audio)

    output_path = f"shorts/{vid_name}.mp4"
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video.close(), final_video.close(), beep.close(), nobeep.close(), background_music.close()
    for clip in tts_clips:
        try: clip.close()
        except: pass

    files_to_remove = tts_questions + tts_answers
    if teaser_audio_path: files_to_remove.append(teaser_audio_path)
    if is_audio: files_to_remove += [pause_1_audio, pause_2_audio]
    for file in files_to_remove:
        try: os.remove(file)
        except Exception as e: print(f"Erreur suppression {file} : {e}")

    return output_path

def get_authenticated_service(file_client_sercret, file_token):
    creds = None

    if os.path.exists(file_token):
        with open(file_token, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                file_client_sercret, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(file_token, "wb") as token:
            pickle.dump(creds, token)

    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_video(file_path, title, description, tags):
    for i, file in enumerate(YT_NAME_FILE):
        try:
            youtube = get_authenticated_service(f"outis/youtubeAPI/{file}.json", f"outis/youtubeAPI/{file}.pickle")

            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "tags": tags,
                        "categoryId": "22"
                    },
                    "status": {
                        "privacyStatus": "public",
                        "madeForKids": False
                    }
                },
                media_body=googleapiclient.http.MediaFileUpload(file_path)
            )

            response = request.execute()
            return response["id"], True
        except googleapiclient.errors.HttpError as e:
            print(f"Erreur lors de l'envoi de la vidéo avec le fichier : {file}")
    
    print("Toutes les fichiers ont échoué. Attente de 1 heure avant de réessayer...")
    time.sleep(3600)
    return "", False

def get_chatGPT_all(quest_nb):
    theme = random.choice(THEMES)
    print(f"Thème: {theme}")

    prompt = f"Donne moi {quest_nb} questions et réponses (factuelle, non subjective) assez simple sur le thème '{theme}' pour un short youtube. Trouve également un titre et des hashtag. Les réponses aux questions doivent être le plus court possible. REPONDS EN FORMAT JSON COMME CECI, NE MET PAS D'AUTRES COMMENTAIRES : '{PROMPT}'"
    while True:
        rep, status = get_chatGPT_rep(prompt)
        if status:
            break

    print(rep)

    # Nettoyage au cas où la réponse aurait du texte parasite
    try:
        data = json.loads(rep)
    except json.JSONDecodeError as e:
        print(f"Erreur lors de nétoyage : {e}")

    # Extraction
    questions = data.get("questions", [])
    answers = data.get("reponses", [])
    title = data.get("title", "")
    hashtags = data.get("hashtag", [])

    description = f"Bonjour à tous !\nAujourd'hui {len(questions)} questions dans un nouveau quiz !!!\n\n"
    for q in questions:
        description += f"- {q}\n"
    description += "\nAbonnez-vous !!!\n\n#{theme.replace(' ', '_')}"
    for q in hashtags:
        description += f"#{q}"
    
    return questions, answers, title, description, hashtags

def countdown(seconds):
    spinner = ['|', '\\', '-', '/']
    for remaining in range(seconds, -1, -1):
        print(f"Prochaine vidéo dans {remaining // 60}mins et {remaining % 60}s {spinner[remaining % len(spinner)]}".ljust(30), end="\r")
        time.sleep(1)

def main():
    while True:
        print("****************************************")

        vid_name, quest_nb = setup()

        # Récup les infos pour la vid
        questions, answers, title, description, hashtags = get_chatGPT_all(quest_nb)

        # Générer la vidéo
        temp_file = f"shorts/temp_file_{vid_name}.mp4"
        file_name = create_vertical_countdown_video(quest_nb, vid_name, temp_file, 60, (720, 1280), questions, answers)

        os.remove(temp_file)

        # Sauvegarder des infos liées à la vidéo
        addata(vid_name + 1)

        while True:
            try:
                # Uploader la vidéo sur YouTube
                video_id, status = upload_video(
                    file_path=file_name,
                    title=title,
                    description=description,
                    tags=[hashtags]
                )
            except Exception as e:
                print(f"Erreur dans l'upload de la vidéo : {e}")
                print("Réessaye dans 1min")
                time.sleep(60)
                continue

            if status:
                print("Vidéo publiée avec succès !")
                print("Lien : https://youtu.be/" + video_id)
                break

        os.remove(file_name)
        
        countdown(3600)

if __name__ == "__main__":
    THEMES = init()
    main()
