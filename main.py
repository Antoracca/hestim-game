import customtkinter
from PIL import Image, ImageTk
from tkinter import ttk, StringVar
import re
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from google_auth_oauthlib.flow import InstalledAppFlow
import pycountry
import cv2
import json
import pygame
from pygame import mixer
import random
import tkinter as tk
from collections import Counter
import webbrowser  # Nouveau module à importer
import tkinter.messagebox as messagebox




def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        country VARCHAR(100),
        gender VARCHAR(20),
        otp_code VARCHAR(6),
        is_verified BOOLEAN DEFAULT FALSE,
        reset_code VARCHAR(6)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS game_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        name1 VARCHAR(50) NOT NULL,
        name2 VARCHAR(50) NOT NULL,
        result VARCHAR(255) NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    cursor.close()
    conn.close()

# Appeler la fonction init_db pour s'assurer que la table des utilisateurs est créée
init_db()

# Initialiser pygame
pygame.init()
pygame.mixer.init()

# Chemins d'accès aux fichiers audio
main_music_path = "C:/Users/admin/Downloads/videoplayback.mp3"
game_music_path = "C:/Users/admin\Downloads/videoplayback-_1_.mp3"
# Variable pour vérifier si la musique principale est en cours de lecture
main_music_playing = False
game_music_playing = False
# Fonction pour jouer de la musique en boucle
def play_main_music():
    global main_music_playing
    if not main_music_playing:
        mixer.music.load(main_music_path)
        mixer.music.play(-1)  # Lire en boucle
        main_music_playing = True

def play_game_music():
    global game_music_playing
    if not game_music_playing:
        mixer.music.load(game_music_path)
        mixer.music.play(-1)
        game_music_playing= False


def stop_music():
    mixer.music.stop()
    global main_music_playing
    global game_music_playing
    main_music_playing = False
    game_music_playing = False


# Commencer la lecture de la musique principale dès le début
play_main_music()




# Helper functions for storing and retrieving user credentials
def store_credentials(username, password):
    credentials = {"username": username, "password": password}
    with open("credentials.json", "w") as file:
        json.dump(credentials, file)

def retrieve_credentials():
    try:
        with open("credentials.json", "r") as file:
            credentials = json.load(file)
            return credentials["username"], credentials.get("password", "")
    except (FileNotFoundError, json.JSONDecodeError):
        return "", ""

# Function to update the username dropdown
def update_username_dropdown():
    usernames = []
    try:
        with open("credentials.json", "r") as file:
            credentials = json.load(file)
            usernames = credentials.get("usernames", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    entry_username['values'] = usernames






# Création de la fenêtre principale
customtkinter.set_appearance_mode("white")
customtkinter.set_default_color_theme("blue")
root = customtkinter.CTk()
root.geometry("1200x800")
root.iconbitmap("C:/Users/admin/Downloads/Capture d’écran (38).ico")
root.title("Hestim Game")

# Définition des frames
frame_login = customtkinter.CTkFrame(master=root,fg_color="#EE82EE")

frame_signup = customtkinter.CTkFrame(master=root,fg_color="white")

frame_welcome = customtkinter.CTkFrame(master=root,fg_color="#E6E6FA")
frame_signup_success = customtkinter.CTkFrame(master=root,fg_color="#E6E6FA")
frame_game = customtkinter.CTkFrame(master=root, fg_color="#87CEEB")
frame_profile = customtkinter.CTkFrame(master=root)
# Frame pour afficher l'historique des jeux
frame_game_history = customtkinter.CTkFrame(master=root)
frame_otp = customtkinter.CTkFrame(master=root,fg_color="#E6E6FA")
frame_reset_password = customtkinter.CTkFrame(master=root,fg_color="#E6E6FA")
frame_reset_success = customtkinter.CTkFrame(master=root)
frame_intro = customtkinter.CTkFrame(master=root)


current_user = ""
user_data = {
    'username': 'DemoUser',
    'email': 'demo@example.com',
    'country': 'France',
    'gender': 'Homme'
}

def show_other_frames():
    # Vous pouvez créer cette fonction pour afficher toutes les autres frames où vous voulez que la musique principale continue
    stop_music()
    play_main_music()


def process_user_info(user_info):
    global current_user
    email = user_info['email']
    username = user_info['name']
    user_data['username'] = username
    user_data['email'] = email
    user_data['country'] = "Unknown"
    user_data['gender'] = "Unknown"
    show_welcome_frame()

def google_login():
    SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']

    flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
    creds = flow.run_local_server(port=0)

    from googleapiclient.discovery import build
    service = build('people', 'v1', credentials=creds)
    profile = service.people().get(resourceName='people/me', personFields='names,emailAddresses,genders').execute()
    email = profile['emailAddresses'][0]['value']
    first_name = profile['names'][0]['givenName']
    last_name = profile['names'][0]['familyName']
    gender = profile['genders'][0]['value'] if 'genders' in profile else 'Non précisé'

    username = generate_unique_username(first_name, last_name)
    password = generate_temporary_password()  # Générer un mot de passe temporaire

    store_user_info(username, email, gender, password)

    # Assigner l'utilisateur actuel pour l'interface de bienvenue
    global current_user
    current_user = username
    user_data['username'] = username
    user_data['email'] = email
    user_data['country'] = "Unknown"
    user_data['gender'] = gender

    # Afficher la frame de succès d'inscription
    show_signup_success_frame()


def save_game_result(username, name1, name2, result):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO game_history (username, name1, name2, result)
                      VALUES (%s, %s, %s, %s)''',
                   (username, name1, name2, result))
    conn.commit()
    cursor.close()
    conn.close()

def fetch_game_history(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute('''SELECT name1, name2, result, date FROM game_history WHERE username=%s ORDER BY date DESC''', (username,))
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    return history

def generate_history_share_message(history):
    message = "Voici l'historique de mes jeux sur Hestim Game :\n\n"
    for i, (name1, name2, result, date) in enumerate(history, start=1):
        message += f"{i}. {name1} & {name2} : {result} ({date})\n"
    message += "\nJouez aussi à Hestim Game !"
    return message

def open_history_share_dialog():
    history = fetch_game_history(current_user)
    if history:
        share_message = generate_history_share_message(history)

        share_dialog = tk.Toplevel(root)
        customtkinter.set_appearance_mode("white")
        customtkinter.set_default_color_theme("blue")
        share_dialog.title("Partager l'historique")
        share_dialog.geometry("500x400")

        label = customtkinter.CTkLabel(master=share_dialog, text="Partager avec:", font=("Cambria", 25))
        label.pack(pady=20)

        def open_url(url):
            webbrowser.open(url)
            share_dialog.destroy()

        whatsapp_url = f"https://api.whatsapp.com/send?text={share_message}"
        whatsapp_button = customtkinter.CTkButton(master=share_dialog, text="WhatsApp", font=("Cambria", 18), fg_color="green", command=lambda: open_url(whatsapp_url))
        whatsapp_button.pack(pady=5)

        facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={share_message}"
        facebook_button = customtkinter.CTkButton(master=share_dialog, text="Facebook", font=("Cambria", 18), fg_color="#1E90FF", command=lambda: open_url(facebook_url))
        facebook_button.pack(pady=5)

        twitter_url = f"https://twitter.com/intent/tweet?text={share_message}"
        twitter_button = customtkinter.CTkButton(master=share_dialog, text="X", font=("Cambria", 18), fg_color="black", command=lambda: open_url(twitter_url))
        twitter_button.pack(pady=5)

        google_plus_url = f"https://plus.google.com/share?url={share_message}"
        google_plus_button = customtkinter.CTkButton(master=share_dialog, text="Google+", font=("Cambria", 18), fg_color="red", command=lambda: open_url(google_plus_url))
        google_plus_button.pack(pady=5)

        mailto_link = f"mailto:?subject=Hestim Game - Historique de jeux&body={share_message}"
        email_button = customtkinter.CTkButton(master=share_dialog, text="Email", font=("Cambria", 18), command=lambda: open_url(mailto_link))
        email_button.pack(pady=5)
    else:
        tk.messagebox.showerror("Erreur", "Votre historique de jeu est vide.")


def show_game_history():
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_game_history.pack(pady=90, padx=690, fill="both", expand=True)

    for widget in frame_game_history.winfo_children():
        widget.destroy()

    canvas = tk.Canvas(frame_game_history)
    scrollbar = ttk.Scrollbar(frame_game_history, orient="vertical", command=canvas.yview)
    scrollable_frame = customtkinter.CTkFrame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    history = fetch_game_history(current_user)

    if history:
        for i, (name1, name2, result, date) in enumerate(history, start=1):
            record = f"{i}. {name1} & {name2} : {result} ({date})"
            label = customtkinter.CTkLabel(master=scrollable_frame, text=record, font=("Cambria", 14))
            label.pack(pady=5, padx=10)
    else:
        label_no_history = customtkinter.CTkLabel(master=scrollable_frame, text="Votre historique de jeu est vide.",
                                                  font=("Cambria", 14))
        label_no_history.pack(pady=20, padx=10)

    frame_buttons = customtkinter.CTkFrame(master=frame_game_history, fg_color="transparent")
    frame_buttons.pack(side="bottom", pady=10)

    button_delete_history = customtkinter.CTkButton(master=frame_buttons, text="Supprimer l'historique",
                                                    font=("Cambria", 14),
                                                    corner_radius=16, fg_color="#FF0000", hover_color="#FF4444",
                                                    command=delete_game_history)
    button_delete_history.pack(side="left", padx=10)

    button_hide_history = customtkinter.CTkButton(master=frame_buttons, text="Retour au profil",
                                                  font=("Cambria", 14),
                                                  corner_radius=16, fg_color="#2196F3", hover_color="#42A5F5",
                                                  command=show_profile_frame)
    button_hide_history.pack(side="left", padx=10)
    button_share_history = customtkinter.CTkButton(master=frame_buttons, text="Partager mon historique",
                                                   font=("Cambria", 14),
                                                   corner_radius=16, fg_color="#32CD32", hover_color="#66BB6A",
                                                   command=open_history_share_dialog)
    button_share_history.pack(side="left", padx=5)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


# Function to delete game history for the current user
def delete_game_history():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM game_history WHERE username=%s''', (current_user,))
    conn.commit()
    cursor.close()
    conn.close()
    show_game_history()  # Refresh the game history frame after deletion


def generate_unique_username(first_name, last_name):
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    username = base_username
    count = 1
    while username_exists(username):
        username = f"{base_username}{count}"
        count += 1
    return username

def username_exists(username):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def store_user_info(username, email, gender, password):
    country = "Unknown"

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
    result = cursor.fetchone()
    if result:
        cursor.execute(
            "UPDATE users SET username=%s, gender=%s, password=%s, country=%s, is_verified=%s WHERE email=%s",
            (username, gender, password, country, True, email))
    else:
        cursor.execute(
            "INSERT INTO users (username, email, password, country, gender, is_verified) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, email, password, country, gender, True))

    conn.commit()
    cursor.close()
    conn.close()

    # Envoyer l'e-mail avec le mot de passe temporaire
    send_temporary_password(email, username, password)

    global current_user
    current_user = username
    user_data['username'] = username
    user_data['email'] = email
    user_data['country'] = country
    user_data['gender'] = gender

    show_signup_success_frame()

def generate_temporary_password():
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=12))

def toggle_password():
    if show_password_var.get():
        entry_new_password.configure(show="")
        entry_confirm_password.configure(show="")
    else:
        entry_new_password.configure(show="*")
        entry_confirm_password.configure(show="*")

def toggle_password_login():
    if show_password_var_login.get():
        entry_password.configure(show="")
    else:
        entry_password.configure(show="*")

# Fonctions pour afficher les différentes frames
def show_login_form():
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_login.pack(pady=0, padx=0, fill="both", expand=True)



def show_signup_form():
    frame_login.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_signup.pack(pady=0, padx=0, fill="both", expand=True)



def show_welcome_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_welcome.pack(pady=0, padx=0, fill="both", expand=True)
    label_welcome_text = f"Ravi de vous revoir encore une fois, {current_user}!"
    label_welcome.configure(text=label_welcome_text)
    activate_shortcut()

# Variable pour vérifier si la musique est muette ou non
is_muted = False
previous_volume = 1.0
# Ajouter un raccourci clavier pour couper la musique avec F10
def toggle_mute(event=None):
    global is_muted, previous_volume
    if is_muted:
        mixer.music.set_volume(previous_volume)  # Remettre le volume précédent
        is_muted = False
    else:
        previous_volume = mixer.music.get_volume()
        mixer.music.set_volume(0.0)  # Couper le son
        is_muted = True

# Lier le raccourci clavier F10 pour couper la musique
root.bind('<F10>', toggle_mute)




def show_signup_success_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_signup_success.pack(pady=0, padx=0, fill="both", expand=True)
    activate_shortcut()  # Activer le raccourci pour cette frame
    activate_shortcutt()


    label_signup_success_text = (
        f"Félicitations {current_user}, votre inscription à Hestim Game est réussie!\n"
        "Vos identifiants de connexion vous ont été envoyés dans votre boîte mail."
    )
    label_signup_success.configure(text=label_signup_success_text)


def show_game_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game_history.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_game.pack(pady=0, padx=0, fill="both", expand=True)
    stop_music()  # Arrêter la musique principale
    play_game_music()  # Jouer la musique de jeu

def show_profile_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_otp.pack_forget()
    frame_game_history.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_profile.pack(pady=80, padx=100, fill="both", expand=True)
    update_profile_info()



def show_otp_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack_forget()
    frame_otp.pack(pady=0, padx=0, fill="both", expand=True)


def show_reset_password_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_success.pack_forget()
    frame_reset_password.pack(pady=0, padx=0, fill="both", expand=True)


def show_reset_success_frame():
    frame_login.pack_forget()
    frame_signup.pack_forget()
    frame_welcome.pack_forget()
    frame_signup_success.pack_forget()
    frame_game.pack_forget()
    frame_profile.pack_forget()
    frame_otp.pack_forget()
    frame_reset_password.pack_forget()
    frame_reset_success.pack(pady=80, padx=100, fill="both", expand=True)
    label_reset_success_text = f"Votre mot de passe a été réinitialisé avec succès, {current_user}!"
    label_reset_success.configure(text=label_reset_success_text)



def send_otp(receiver_email, otp_code):
    sender_email = "a.koueni@hestim.ma"
    sender_password = "Koueniantoni21@"

    with open("otp_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    html_content = html_template.replace("{{OTP_CODE}}", otp_code)

    message = MIMEMultipart('related')  # Assurez-vous que c'est 'related' pour le message principal
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Confirmation de Code OTP - Hestim Game App'

    # Ajouter le corps HTML
    message.attach(MIMEText(html_content, 'html'))

    # Attacher l'image avec CID
    with open("C:/Users/admin/PycharmProjects/interface 224/Adobe/assets/logo/logo 1 hestim.png", 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<logo>')  # Le CID ici doit correspondre exactement à 'cid:logo' dans le HTML
        mime_image.add_header('Content-Disposition', 'inline', filename="logo.png")  # Assurez-vous que la disposition est 'inline'
        message.attach(mime_image)

    # Connexion au serveur SMTP et envoi de l'e-mail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def generate_otp():
    return ''.join(random.choices('0123456789', k=6))

def get_best_and_worst_friends(history):
    if not history:
        return None, None

    best_friend = max(history, key=lambda x: int(re.search(r'(\d+)%', x[2]).group(1)))
    worst_friend = min(history, key=lambda x: int(re.search(r'(\d+)%', x[2]).group(1)))

    return best_friend, worst_friend




def generate_share_message(name1, name2, relation, percentage):
    message = (
        f"Bonjour,\n\n\n\n\n\n\n\n ✨ J'ai joué à Hestim Game et j'ai calculé la relation qui existe entre {name1.capitalize()} et {name2.capitalize()}.\n"
        f"✨  \"{relation}\" à {percentage}%.\n\n"
        f"🎮 Toi aussi tu veux essayer ? Installe vite le jeu via ce lien : https://antoracca.github.io/hestim-game/  \n\n"
        f"Amuse-toi bien ! 😄"
    )
    return message

def open_share_dialog():
    if entry_name1.get() and entry_name2.get() and result_label.cget("text"):
        name1 = entry_name1.get().strip().lower()
        name2 = entry_name2.get().strip().lower()
        relation_text = result_label.cget("text")
        relation_parts = relation_text.split(" ")
        relation = " ".join(relation_parts[1:-2])  # Obtenir la relation depuis le texte
        percentage = relation_parts[-1].strip("%")  # Obtenir le pourcentage depuis le texte

        share_message = generate_share_message(name1, name2, relation, percentage)

        share_dialog = tk.Toplevel(root)
        customtkinter.set_appearance_mode("white")
        customtkinter.set_default_color_theme("blue")
        share_dialog.title("Partager le résultat")
        share_dialog.iconbitmap("C:/Users/admin\Downloads/52049.ico")
        share_dialog.geometry("500x400")

        label = customtkinter.CTkLabel(master=share_dialog, text="Partager avec:", font=("Cambria", 25))
        label.pack(pady=20)

        def open_url(url):
            webbrowser.open(url)
            share_dialog.destroy()

        whatsapp_url = f"https://api.whatsapp.com/send?text={share_message}"
        whatsapp_button = customtkinter.CTkButton(master=share_dialog, text="WhatsApp", font=("Cambria", 18),fg_color="green", command=lambda: open_url(whatsapp_url))
        whatsapp_button.pack(pady=5)

        facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={share_message}"
        facebook_button = customtkinter.CTkButton(master=share_dialog, text="Facebook", font=("Cambria", 18), fg_color="#1E90FF" ,command=lambda: open_url(facebook_url))
        facebook_button.pack(pady=5)

        twitter_url = f"https://twitter.com/intent/tweet?text={share_message}"
        twitter_button = customtkinter.CTkButton(master=share_dialog, text="X", font=("Cambria", 18), fg_color="black", command=lambda: open_url(twitter_url))
        twitter_button.pack(pady=5)

        google_plus_url = f"https://plus.google.com/share?url={share_message}"
        google_plus_button = customtkinter.CTkButton(master=share_dialog, text="Google+", font=("Cambria", 18),fg_color="red", command=lambda: open_url(google_plus_url))
        google_plus_button.pack(pady=5)

        mailto_link = f"mailto:?subject=Hestim Game - Résultat de relation&body={share_message}"
        email_button = customtkinter.CTkButton(master=share_dialog, text="Email", font=("Cambria", 18), command=lambda: open_url(mailto_link))
        email_button.pack(pady=5)
    else:
        tk.messagebox.showerror("Erreur", "Veuillez calculer une relation avant de partager.")



def send_temporary_password(email, username, password):
    sender_email = "a.koueni@hestim.ma"
    sender_password = "Koueniantoni21@"
    receiver_email = email

    # Lire le template HTML
    with open("temporary_password_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    # Remplacer les placeholders par les valeurs réelles
    html_content = html_template.replace("{{USERNAME}}", username).replace("{{PASSWORD}}", password)

    # Créer le message principal
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Hestim Game - Informations de connexion"

    # Ajouter le corps HTML
    message.attach(MIMEText(html_content, 'html'))

    # Attacher l'image avec CID
    with open("C:/Users/admin/PycharmProjects/interface 224/Adobe/assets/logo/logo 1 hestim.png", 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<logo>')  # Le CID ici doit correspondre exactement à 'cid:logo' dans le HTML
        mime_image.add_header('Content-Disposition', 'inline', filename="logo.png")  # Assurez-vous que la disposition est 'inline'
        message.attach(mime_image)

    # Connexion au serveur SMTP et envoi de l'e-mail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())

def send_confirmation_email(email, username, password, country):
    sender_email = "a.koueni@hestim.ma"
    sender_password = "Koueniantoni21@"
    receiver_email = email

    # Lire le template HTML
    with open("confirmation_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    # Remplacer les placeholders par les valeurs réelles
    html_content = html_template.replace("{{USERNAME}}", username).replace("{{PASSWORD}}", password).replace("{{COUNTRY}}", country)

    # Créer le message principal
    message = MIMEMultipart('related')
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Hestim Game - Confirmation d'inscription"

    # Ajouter le corps HTML
    message.attach(MIMEText(html_content, 'html'))

    # Attacher l'image avec CID
    with open("C:/Users/admin/PycharmProjects/interface 224/Adobe/assets/logo/logo 1 hestim.png", 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<logo>')  # Le CID ici doit correspondre exactement à 'cid:logo' dans le HTML
        mime_image.add_header('Content-Disposition', 'inline', filename="logo.png")  # Assurez-vous que la disposition est 'inline'
        message.attach(mime_image)

    # Connexion au serveur SMTP et envoi de l'e-mail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def send_reset_confirmation_email(email, username, password, country):
    sender_email = "a.koueni@hestim.ma"
    sender_password = "Koueniantoni21@"
    receiver_email = email

    with open("reset_confirmation_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    html_content = html_template.replace("{{USERNAME}}", username).replace("{{COUNTRY}}", country).replace("{{PASSWORD}}", password)

    message = MIMEMultipart('related')
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Hestim Game - Confirmation de réinitialisation de mot de passe"

    message.attach(MIMEText(html_content, "html"))

    with open("C:/Users/admin/PycharmProjects/interface 224/Adobe/assets/logo/logo 1 hestim.png", 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<logo>')
        mime_image.add_header('Content-Disposition', 'inline', filename="logo.png")
        message.attach(mime_image)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())



def validate_signup():
    global current_user
    global otp_user_info
    username = entry_new_username.get()
    email = entry_email.get()
    password = entry_new_password.get()
    confirm_password = entry_confirm_password.get()
    country = country_var.get()
    gender = gender_var.get()
    error_message = ""

    # Reset styles
    entry_new_username.configure(border_color="#CCCCCC")
    entry_email.configure(border_color="#CCCCCC")
    entry_new_password.configure(border_color="#CCCCCC")
    entry_confirm_password.configure(border_color="#CCCCCC")
    signup_error_label_username.configure(text="")
    signup_error_label_email.configure(text="")
    signup_error_label_password.configure(text="")
    signup_error_label_confirm_password.configure(text="")
    signup_error_label_country.configure(text="")
    signup_error_label_gender.configure(text="")

    # Validation du nom d'utilisateur
    if len(username) < 4:
        error_message = "Le nom d'utilisateur doit comporter au moins 4 caractères."
        signup_error_label_username.configure(text=error_message)
        entry_new_username.configure(border_color="red")
    elif not re.search(r'[A-Za-z]', username):
        error_message = "Le nom d'utilisateur doit contenir au moins une lettre."
        signup_error_label_username.configure(text=error_message)
        entry_new_username.configure(border_color="red")
    elif not re.match(r'^[A-Za-z0-9@#$%^&+=_.-]+$', username):
        error_message = "Le nom d'utilisateur contient des caractères non autorisés."
        signup_error_label_username.configure(text=error_message)
        entry_new_username.configure(border_color="red")
    # Validation de l'email
    elif not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
        error_message = "L'email n'est pas valide."
        signup_error_label_email.configure(text=error_message)
        entry_email.configure(border_color="red")
    # Validation du mot de passe
    elif len(password) < 14 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"[0-9]", password) or not re.search(r"[@$!%*?&]", password):
        error_message = "Le mot de passe doit avoir au moins 14 caractères, incluant des lettres majuscules, des lettres minuscules, des chiffres et des caractères spéciaux."
        signup_error_label_password.configure(text=error_message)
        entry_new_password.configure(border_color="red")
    elif password != confirm_password:
        error_message = "Les mots de passe ne correspondent pas."
        signup_error_label_confirm_password.configure(text=error_message)
        entry_confirm_password.configure(border_color="red")
    elif country == "Select your country":
        error_message = "Veuillez sélectionner un pays."
        signup_error_label_country.configure(text=error_message)
    elif gender == "Non précisé":
        error_message = "Veuillez sélectionner un genre."
        signup_error_label_gender.configure(text=error_message)

    if not error_message:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root",
            database="user_management"
        )
        cursor = conn.cursor()

        # Vérifier si le nom d'utilisateur existe déjà
        cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            error_message = "Le nom d'utilisateur existe déjà."
            signup_error_label_username.configure(text=error_message)
            entry_new_username.configure(border_color="red")
            cursor.close()
            conn.close()
            return

        # Vérifier si l'email existe déjà
        cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            error_message = "L'email existe déjà."
            signup_error_label_email.configure(text=error_message)
            entry_email.configure(border_color="red")
            cursor.close()
            conn.close()
            return

        cursor.close()
        conn.close()

        otp_code = generate_otp()
        send_otp(email, otp_code)

        otp_user_info = {
            'username': username,
            'email': email,
            'password': password,
            'country': country,
            'gender': gender,
            'otp_code': otp_code
        }

        current_user = username
        user_data['username'] = username
        user_data['email'] = email
        user_data['country'] = country
        user_data['gender'] = gender

        show_otp_frame()

def validate_otp():
    global otp_user_info
    otp_input = otp_entry.get()

    if otp_user_info['otp_code'] == otp_input:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root",
            database="user_management"
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password, country, gender, is_verified) VALUES (%s, %s, %s, %s, %s, %s)",
            (otp_user_info['username'], otp_user_info['email'], otp_user_info['password'], otp_user_info['country'], otp_user_info['gender'], True)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Envoyer l'e-mail de confirmation avec les informations de connexion
        send_confirmation_email(otp_user_info['email'], otp_user_info['username'], otp_user_info['password'], otp_user_info['country'])

        # Réinitialiser les champs d'inscription et le champ OTP
        reset_signup_form()
        otp_entry.delete(0, customtkinter.END)

        show_signup_success_frame()  # Affiche la frame de succès d'inscription
    else:
        otp_error_label.configure(text="Le code OTP est incorrect. Veuillez réessayer.")


def resend_otp():
    global otp_user_info
    email = otp_user_info['email']
    otp_code = generate_otp()

    # Mettre à jour le code OTP dans otp_user_info
    otp_user_info['otp_code'] = otp_code

    # Envoyer le nouvel OTP par email
    send_otp(email, otp_code)

    otp_error_label.configure(text="Un nouveau code OTP a été envoyé à votre email.", text_color="green")


def validate_login():
    global current_user
    username = entry_username.get()
    password = entry_password.get()
    error_message = ""

    # Reset styles
    entry_username.configure(border_color="#CCCCCC")
    entry_password.configure(border_color="#CCCCCC")
    login_error_label_username.configure(text="")
    login_error_label_password.configure(text="")

    # Validation du nom d'utilisateur (autoriser les espaces et les ponctuations)
    if len(username) == 0:
        error_message = "Le nom d'utilisateur ne peut pas être vide."
        login_error_label_username.configure(text=error_message)
        entry_username.configure(border_color="red")
    elif len(password) < 4:
        error_message = "Le mot de passe doit comporter au moins 4 caractères."
        login_error_label_password.configure(text=error_message)
        entry_password.configure(border_color="red")
    else:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Root",
            database="user_management"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            if user[7]:  # Vérifie si l'utilisateur est vérifié
                current_user = username
                user_data['username'] = user[1]
                user_data['email'] = user[2]
                user_data['country'] = user[4]
                user_data['gender'] = user[5]
                show_welcome_frame()
            else:
                error_message = "Veuillez vérifier votre adresse e-mail."
                login_error_label_password.configure(text=error_message)
                entry_password.configure(border_color="red")
        else:
            error_message = "Nom d'utilisateur ou mot de passe incorrect."
            login_error_label_password.configure(text=error_message)
            entry_password.configure(border_color="red")



# Fonction pour mettre à jour les informations du profil en temps réel
def update_profile_info():
    label_profile_username.configure(text=f"Nom d'utilisateur: {user_data['username']}")
    label_profile_email.configure(text=f"Email: {user_data['email']}")
    label_profile_country.configure(text=f"Pays: {user_data['country']}")
    label_profile_gender.configure(text=f"Genre: {user_data['gender']}")

def send_reset_code(email, reset_code):
    sender_email = "a.koueni@hestim.ma"
    sender_password = "Koueniantoni21@"
    receiver_email = email

    with open("reset_code_template.html", "r", encoding="utf-8") as file:
        html_template = file.read()

    html_content = html_template.replace("{{RESET_CODE}}", reset_code)

    message = MIMEMultipart('related')
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Hestim Game - Code de réinitialisation de mot de passe"

    message.attach(MIMEText(html_content, "html"))

    with open("C:/Users/admin/PycharmProjects/interface 224/Adobe/assets/logo/logo 1 hestim.png", 'rb') as img:
        mime_image = MIMEImage(img.read())
        mime_image.add_header('Content-ID', '<logo>')
        mime_image.add_header('Content-Disposition', 'inline', filename="logo.png")
        message.attach(mime_image)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def reset_password():
    email = entry_reset_email.get()

    # Réinitialiser le message d'erreur
    reset_error_label.configure(text="", text_color="red")

    # Vérifier si l'email est vide
    if not email:
        reset_error_label.configure(text="Veuillez entrer votre adresse e-mail s'il vous plaît.")
        return

    # Vérifier si l'email respecte le format attendu
    if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
        reset_error_label.configure(
            text="L'adresse e-mail n'est pas valide. Veuillez entrer une adresse e-mail correcte.")
        return

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        reset_code = generate_otp()
        cursor.execute("UPDATE users SET reset_code=%s WHERE email=%s", (reset_code, email))
        conn.commit()
        send_reset_code(email, reset_code)
        reset_error_label.configure(text="Un code de réinitialisation a été envoyé à votre email.", text_color="green")
    else:
        reset_error_label.configure(
            text="Oups... Quelque chose s'est mal passé. Il semblerait que cet e-mail n'existe pas dans notre système. Veuillez vérifier et réessayer.")

    cursor.close()
    conn.close()


def validate_reset_code():
    global current_user
    email = entry_reset_email.get()
    reset_code = entry_reset_code.get()
    new_password = entry_new_reset_password.get()
    confirm_password = entry_confirm_reset_password.get()

    # Réinitialiser les messages d'erreur
    reset_error_label_password.configure(text="")

    # Vérifier si les mots de passe correspondent
    if new_password != confirm_password:
        reset_error_label_password.configure(text="Les mots de passe ne correspondent pas.", text_color="red")
        return

    # Vérifier la robustesse du mot de passe
    if len(new_password) < 14 or not re.search(r"[A-Z]", new_password) or not re.search(r"[a-z]", new_password) or not re.search(r"[0-9]", new_password) or not re.search(r"[@$!%*?&]", new_password):
        reset_error_label_password.configure(text="Le mot de passe doit avoir au moins 14 caractères, incluant des lettres majuscules, des lettres minuscules, des chiffres et des caractères spéciaux.", text_color="red")
        return

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root",
        database="user_management"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT reset_code FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user and user[0] == reset_code:
        cursor.execute("UPDATE users SET password=%s, reset_code=NULL WHERE email=%s", (new_password, email))
        conn.commit()

        cursor.execute("SELECT username, country, gender FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        user_data['username'] = user[0]
        user_data['email'] = email
        user_data['country'] = user[1]
        user_data['gender'] = user[2]
        current_user = user[0]

        send_reset_confirmation_email(email, user[0], new_password, user[1])

        show_reset_success_frame()
    else:
        reset_error_label_code.configure(text="Le code de réinitialisation est incorrect.", text_color="red")

    cursor.close()
    conn.close()



# Fonction pour vérifier la robustesse du mot de passe
# Fonction pour vérifier la robustesse du mot de passe
def check_password_strength(event=None):
    password = entry_new_password.get()
    if password:
        if not circle_frame.winfo_ismapped():
            circle_frame.place(x=400, y=390)  # Afficher les cercles de robustesse sous le champ de saisie du mot de passe
        # Réinitialiser les couleurs des cercles
        circle_weak.configure(text_color="gray")
        circle_medium.configure(text_color="gray")
        circle_strong.configure(text_color="gray")
        circle_robust.configure(text_color="gray")

        # Logique pour la couleur des cercles
        if len(password) >= 14 and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[0-9]", password) and re.search(r"[@$!%*?&]", password):
            circle_weak.configure(text_color="green")
            circle_medium.configure(text_color="green")
            circle_strong.configure(text_color="green")
            circle_robust.configure(text_color="green")
        elif len(password) >= 8 and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[0-9]", password):
            circle_weak.configure(text_color="blue")
            circle_medium.configure(text_color="blue")
            circle_strong.configure(text_color="blue")
        elif len(password) >= 6:
            circle_weak.configure(text_color="orange")
            circle_medium.configure(text_color="orange")
        elif len(password) >= 4:
            circle_weak.configure(text_color="red")
    else:
        circle_frame.place_forget()  # Masquer les cercles de robustesse si aucun mot de passe n'est entré


# Fonction pour récupérer la liste des pays depuis pycountry
def fetch_countries():
    countries = [country.name for country in pycountry.countries]
    countries.sort()
    print(f"Nombre de pays récupérés : {len(countries)}")
    return countries


# Fonction pour filtrer les pays en fonction de la recherche
def filter_countries():
    value = entry_country.get().lower()
    if value == '':
        filtered_countries = countries
    else:
        filtered_countries = [country for country in countries if country.lower().startswith(value)]
    entry_country['values'] = filtered_countries
    entry_country.event_generate('<Down>')  # Ouvrir la liste déroulante

# Fonction appelée à chaque touche pressée, démarre un timer pour filtrer après un délai
def on_key_release(event):
    global timer
    if timer:
        root.after_cancel(timer)
    timer = root.after(filter_delay, filter_countries)


# Corriger le comportement de la sélection pour effacer le placeholder au focus
def clear_placeholderr(event):
    if country_var.get() == "Select your country":
        entry_country.set('')
        entry_country.config(foreground='black')

def restore_placeholder(event):
    if country_var.get() == '':
        entry_country.set('Select your country')
        entry_country.config(foreground='grey')


def set_placeholder(entry, placeholder):
    entry.delete(0, customtkinter.END)
    entry.insert(0, placeholder)
    entry.bind("<FocusIn>", lambda event: clear_placeholder(entry, placeholder))
    entry.bind("<FocusOut>", lambda event: add_placeholder(entry, placeholder))

def clear_placeholder(entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, customtkinter.END)

def add_placeholder(entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)

# Lier la fonction de vérification de la robustesse du mot de passe pour le champ de réinitialisation
def check_password_strength_reset(event=None):
    password = entry_new_reset_password.get()
    if password:
        if not circle_frame_reset.winfo_ismapped():
            circle_frame_reset.pack(pady=(5, 10), after=entry_new_reset_password)  # Afficher les cercles de robustesse sous le champ de saisie du mot de passe
        # Réinitialiser les couleurs des cercles
        circle_weak_reset.configure(text_color="gray")
        circle_medium_reset.configure(text_color="gray")
        circle_strong_reset.configure(text_color="gray")
        circle_robust_reset.configure(text_color="gray")

        # Logique pour la couleur des cercles
        if len(password) >= 14 and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[0-9]", password) and re.search(r"[@$!%*?&]", password):
            circle_weak_reset.configure(text_color="green")
            circle_medium_reset.configure(text_color="green")
            circle_strong_reset.configure(text_color="green")
            circle_robust_reset.configure(text_color="green")
        elif len(password) >= 8 and re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"[0-9]", password):
            circle_weak_reset.configure(text_color="blue")
            circle_medium_reset.configure(text_color="blue")
            circle_strong_reset.configure(text_color="blue")
        elif len(password) >= 6:
            circle_weak_reset.configure(text_color="orange")
            circle_medium_reset.configure(text_color="orange")
        elif len(password) >= 4:
            circle_weak_reset.configure(text_color="red")
    else:
        circle_frame_reset.pack_forget()  # Masquer les cercles de robustesse si aucun mot de passe n'est entré

def reset_signup_form():
    # Réinitialiser les champs de saisie en réappliquant les placeholders
    set_placeholder(entry_new_username, "Username")
    set_placeholder(entry_email, "Email")
    set_placeholder(entry_new_password, "Password")
    set_placeholder(entry_confirm_password, "Confirm your password")

    # Réinitialiser les messages d'erreur
    signup_error_label_username.configure(text="")
    signup_error_label_email.configure(text="")
    signup_error_label_password.configure(text="")
    signup_error_label_confirm_password.configure(text="")
    signup_error_label_country.configure(text="")
    signup_error_label_gender.configure(text="")

    # Réinitialiser les cercles de robustesse du mot de passe
    circle_weak.configure(text_color="gray")
    circle_medium.configure(text_color="gray")
    circle_strong.configure(text_color="gray")
    circle_robust.configure(text_color="gray")

    # Réinitialiser les choix de pays et de genre
    country_var.set("Select your country")
    gender_var.set("Non précisé")

    # Revenir à la frame de connexion
    show_login_form()
    root.focus()  # Pour que le curseur ne se place pas automatiquement dans un champ
def reset_reset_password_form():
    # Réinitialiser les champs de saisie en réappliquant les placeholders
    set_placeholder(entry_reset_email, "Email")
    set_placeholder(entry_reset_code, "Code de réinitialisation")
    set_placeholder(entry_new_reset_password, "Nouveau mot de passe")
    set_placeholder(entry_confirm_reset_password, "Confirmer le mot de passe")

    # Réinitialiser les messages d'erreur
    reset_error_label.configure(text="")
    reset_error_label_code.configure(text="")
    reset_error_label_password.configure(text="")

    # Réinitialiser les cercles de robustesse du mot de passe
    circle_weak_reset.configure(text_color="gray")
    circle_medium_reset.configure(text_color="gray")
    circle_strong_reset.configure(text_color="gray")
    circle_robust_reset.configure(text_color="gray")

    # Revenir à la frame de connexion
    show_login_form()
    root.focus()  # Pour que le curseur ne se place pas automatiquement dans un champ


# Images

back_image_path = "C:/Users/admin/Desktop/backfleche.png"
back_image = Image.open(back_image_path)
back_image = back_image.resize((30, 30), Image.Resampling.LANCZOS)
back_photo = ImageTk.PhotoImage(back_image)

user_icon_path_login = "C:/Users/admin/Downloads/user.png"
user_icon_path_signup = "C:/Users/admin/Downloads/icon2.png"

image_pil_login = Image.open(user_icon_path_login)
image_pil_login = image_pil_login.resize((100, 100), Image.Resampling.LANCZOS)
image_photo_login = ImageTk.PhotoImage(image_pil_login)

image_pil_signup = Image.open(user_icon_path_signup)
image_pil_signup = image_pil_signup.resize((100, 100), Image.Resampling.LANCZOS)
image_photo_signup = ImageTk.PhotoImage(image_pil_signup)




# Fonction pour lire la vidéo et afficher les images dans Tkinter
def video_stream(label, cap, delay=20):
    ret, frame = cap.read()
    if ret:
        frame_width = label.winfo_width()
        frame_height = label.winfo_height()
        frame = cv2.resize(frame, (frame_width, frame_height))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        label.imgtk = imgtk
        label.configure(image=imgtk)

    else:
      cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Réinitialiser la vidéo à la première image
    label.after(delay, lambda: video_stream(label, cap, delay))

# Charger la vidéo avec OpenCV pour la frame de connexion
cap_login = cv2.VideoCapture("C:/Users/admin\Downloads\Hestim Game App (5).mp4")
video_label_login = tk.Label(frame_login)
video_label_login.pack(pady=(40, 0), fill="both", expand=True)  # Ajouter de l'espace en haut
video_stream(video_label_login, cap_login, delay=100)

# Charger la vidéo avec OpenCV pour la frame d'inscription
cap_signup = cv2.VideoCapture("C:/Users/admin\Downloads\Bannière YouTube de Jeux vidéo Gaming Jeu de rôle Moderne Jaune et Violet (11).mp4")
video_label_signup = tk.Label(frame_signup)
video_label_signup.pack(fill="both", expand=True)
video_stream(video_label_signup, cap_signup, delay=90)

# Charger la vidéo avec OpenCV pour la frame de jeu
cap_game = cv2.VideoCapture("C:/Users/admin\Downloads\Colorful Futuristic Coming Soon Nightclub Neon Video (3).mp4")
video_label_game = tk.Label(frame_game)
video_label_game.pack(fill="both", expand=True)
video_stream(video_label_game, cap_game, delay=80)



# Ajouter un bouton en haut à droite du frame de connexion
button_signup_form = customtkinter.CTkButton(
    master=frame_login,
    text="S'inscrire",
    font=("Verdana Bold", 21, "bold"),
    fg_color="#EE82EE",
    text_color="white",
    bg_color="#EE82EE",
    hover_color="black",
    corner_radius=25,
    command=show_signup_form,
    width=100,  # Largeur augmentée
    height=25  # Hauteur augmentée

)
button_signup_form.place(relx=1, rely=0, anchor="ne", x=-10, y=10)
button_signup_form.pack_propagate(False)


#frame connexion

entry_username = customtkinter.CTkEntry(master=frame_login, placeholder_text="Nom d'utilisateur", width=600, height=80, corner_radius=2,
                                        border_width=12,  border_color="#D3D3D3",bg_color="white", fg_color="white")

entry_username.place(relx=0.5, rely=0.42, anchor="center")
login_error_label_username = customtkinter.CTkLabel(master=frame_login, text="", font=("Cambria", 18), text_color="#4B0082" )

login_error_label_username.place(relx=0.5, rely=0.49, anchor="center")

entry_password = customtkinter.CTkEntry(master=frame_login, placeholder_text="Mot de passe", show="*", width=600, height=80,corner_radius=2,
                                        border_width=12,  border_color="#D3D3D3",bg_color="white", fg_color="white")

entry_password.place(relx=0.5, rely=0.55, anchor="center")
login_error_label_password = customtkinter.CTkLabel(master=frame_login, text="", font=("Cambria", 18), text_color="#4B0082")
login_error_label_password.place(relx=0.5, rely=0.61, anchor="center")


button_frame= customtkinter.CTkFrame(master=frame_login, width=400, height=60, border_width=7, bg_color="black", fg_color="white")
button_frame.place(relx=0.5,rely=0.8, anchor="center")
button_frame.pack_propagate(False)

button_login = customtkinter.CTkButton(master=button_frame, text=" Se connecter ", font=("Cambria", 17), corner_radius=16,
                                       fg_color="#2F4F4F",bg_color="white", hover_color="#66BB6A", command=validate_login)
button_login.pack(side="left", padx=20)


button_forgot_password = customtkinter.CTkButton(master=button_frame, text="Reset password", font=("Cambria", 14),
                                                 corner_radius=16, fg_color="#FF0000", hover_color="#FF4444",
                                                 command=show_reset_password_frame)
button_forgot_password.pack(side="left", padx=40)


# Créer la frame pour les checkboxes avec les dimensions spécifiées
checkbox_frame = customtkinter.CTkFrame(master=frame_login, width=400, height=60, corner_radius=25, border_width=7, border_color="black",bg_color="black", fg_color="white")
checkbox_frame.place(relx=0.5, rely=0.68, anchor="center")
checkbox_frame.pack_propagate(False)

show_password_var_login = customtkinter.BooleanVar()
show_password_checkbox_login = customtkinter.CTkCheckBox(master=checkbox_frame, text="Afficher le mot de passe",
                                                         variable=show_password_var_login,
                                                         command=toggle_password_login)
show_password_checkbox_login.pack(side="left", padx=20)

checkbox_remember = customtkinter.CTkCheckBox(master=checkbox_frame, text="Se souvenir de moi")
checkbox_remember.pack(side="left", padx=5)



# Widgets d'inscription
entry_new_username = customtkinter.CTkEntry(master=frame_signup, placeholder_text="Username", width=600, height=70, corner_radius=65, bg_color="#D3D3D3", border_color="#D3D3D3")
entry_new_username.place(x=150, y=60)

signup_error_label_username = customtkinter.CTkLabel(master=frame_signup, text="", bg_color="black", font=("Cambria", 13), text_color="red")
signup_error_label_username.place(x=270, y=140)

entry_email = customtkinter.CTkEntry(master=frame_signup, placeholder_text="Email", width=600, height=70,corner_radius=65,bg_color="#D3D3D3",border_color="#D3D3D3")
entry_email.place(x=150, y=185)

signup_error_label_email = customtkinter.CTkLabel(master=frame_signup, text="",bg_color="black", font=("Cambria", 13), text_color="red")
signup_error_label_email.place(x=380, y=270)

entry_new_password = customtkinter.CTkEntry(master=frame_signup, placeholder_text="Password",  show="*", width=600, height=70,corner_radius=65,bg_color="#D3D3D3",border_color="#D3D3D3")
entry_new_password.place(x=150, y=310)

# Ajouter les cercles de robustesse du mot de passe
circle_frame = customtkinter.CTkFrame(master=frame_signup, fg_color="transparent",bg_color="black" , width=300, height=30)
circle_frame.place_forget()

circle_weak = customtkinter.CTkLabel(master=circle_frame, text="●", font=("Arial", 24), text_color="gray")
circle_weak.pack(side="left", padx=2)
circle_medium = customtkinter.CTkLabel(master=circle_frame, text="●", font=("Arial", 24), text_color="gray")
circle_medium.pack(side="left", padx=2)
circle_strong = customtkinter.CTkLabel(master=circle_frame, text="●", font=("Arial", 24), text_color="gray")
circle_strong.pack(side="left", padx=2)
circle_robust = customtkinter.CTkLabel(master=circle_frame, text="●", font=("Arial", 24), text_color="gray")
circle_robust.pack(side="left", padx=2)

signup_error_label_password = customtkinter.CTkLabel(master=frame_signup, text="",bg_color="black", font=("Cambria", 13), text_color="red")
signup_error_label_password.place(x=270, y=430)

entry_confirm_password = customtkinter.CTkEntry(master=frame_signup, placeholder_text="Confirm your password", show="*", width=600, height=70,corner_radius=65,bg_color="#D3D3D3",border_color="#D3D3D3")
entry_confirm_password.place(x=150, y=470)

signup_error_label_confirm_password = customtkinter.CTkLabel(master=frame_signup, text="",bg_color="black", font=("Cambria", 12), text_color="red")
signup_error_label_confirm_password.place(x=350, y=550)

show_password_var = customtkinter.BooleanVar()
show_password_checkbox = customtkinter.CTkCheckBox(master=frame_signup, text=" Afficher le mot de passe", text_color="white" ,variable=show_password_var,bg_color="black", command=toggle_password,width=300,height=30)
show_password_checkbox.place(x=310, y=595)




# Ajouter la sous-frame à la frame d'inscription
frame_details=customtkinter.CTkFrame(master=frame_signup, width=500, height=470,border_width=7 , border_color="purple", fg_color="white", bg_color="purple"  )
frame_details.place(x=1000, y=60)
frame_details.pack_propagate(False)




countries = fetch_countries()
country_var = StringVar(value="Select your country")
filter_delay = 900  # Délai avant de filtrer les résultats, en millisecondes
# Créer une Combobox avec la liste des pays
entry_country = ttk.Combobox(master=frame_details, textvariable=country_var, values=countries, width=70, height=27)
entry_country.pack(pady=10, padx=1)

# Style personnalisé pour la Combobox
style = ttk.Style()
style.theme_use("clam")

# Configurer la Combobox
style.configure("TCombobox",
                fieldbackground="white",  # Fond bleu clair pour la zone de saisie
                background="#E6E6FA",  # Fond blanc pour la liste déroulante
                foreground="black",  # Texte noir
                arrowcolor="black")  # Couleur de la flèche du menu déroulant

signup_error_label_country = customtkinter.CTkLabel(master=frame_details, text="",font=("Cambria", 10), text_color="red")
signup_error_label_country.pack(pady=5, padx=10)

timer = None  # Variable pour stocker le timer
# Ajouter des animations simples avec la méthode after
def animate_entry():
    current_color = entry_country.cget("background")
    new_color = "#E6E6FA" if current_color == "white" else "white"
    entry_country.config(background=new_color)
    root.after(500, animate_entry)

animate_entry()

label_texte= customtkinter.CTkLabel(master=frame_details, text="Genre",text_color="black", font=("Helvetica", 18, "bold"))
label_texte.pack(pady=3)
# Boutons radio pour le genre
gender_var = StringVar(value="Non précisé")
frame_gender = customtkinter.CTkFrame(master=frame_details, fg_color="white", width=100,height=60)
frame_gender.pack(pady=8)

def update_gender():
    selected_gender = gender_var.get()
    for button in gender_buttons:
        if button.cget("text") == selected_gender:
            button.configure(fg_color="#BA55D3", text_color="black")
        else:
            button.configure(fg_color="white", text_color="black")

genders = ["Homme", "Femme", "Non précisé"]
gender_buttons = []
for gender in genders:
    button = customtkinter.CTkButton(master=frame_gender, text=gender, width=25, height=50, corner_radius=25, bg_color="#4B0082", hover_color="#BA55D3", command=lambda g=gender: gender_var.set(g))
    button.pack(side="left", padx=25)
    gender_buttons.append(button)

# Mettre à jour les couleurs des boutons en fonction du genre sélectionné
gender_var.trace("w", lambda *args: update_gender())
update_gender()

signup_error_label_gender = customtkinter.CTkLabel(master=frame_details,  text="", font=("Cambria", 10), text_color="red")
signup_error_label_gender.pack(pady=5)


button_signup = customtkinter.CTkButton(master=frame_details, text="Sign Up", font=("Cambria", 14), command=validate_signup, corner_radius=16, fg_color="black", hover_color="purple")
button_signup.pack(pady=13,padx=16)

label_account_exists = customtkinter.CTkLabel(master=frame_details, text="Déjà un compte ? Connectez-vous maintenant", font=("Cambria", 14), text_color="black")
label_account_exists.pack(pady= 10)

button_back_to_login = customtkinter.CTkButton(master=frame_details, text="Sign In", font=("Cambria", 14), corner_radius=16, fg_color="black", hover_color="purple", command=show_login_form)
button_back_to_login.pack(pady=8,padx=12)

social_frame = customtkinter.CTkFrame(master=frame_signup,width=600,height=900, bg_color="black" , fg_color="black")
social_frame.place(x=600, y=830)

google_icon_path = "C:/Users/admin/Downloads/google.png"
google_image = Image.open(google_icon_path)
google_image = google_image.resize((90, 90), Image.Resampling.LANCZOS)
google_photo = ImageTk.PhotoImage(google_image)
google_button = customtkinter.CTkButton(master=social_frame, image=google_photo, text=" Sign in with Google", compound="left", command=google_login)
google_button.image = google_photo
google_button.pack(side="left", padx=3)

facebook_icon_path = "C:/Users/admin/Downloads/facebook.png"
facebook_image = Image.open(facebook_icon_path)
facebook_image = facebook_image.resize((90, 90), Image.Resampling.LANCZOS)
facebook_photo = ImageTk.PhotoImage(facebook_image)
facebook_button = customtkinter.CTkButton(master=social_frame, image=facebook_photo, text=" Sign in with Facebook", compound="left", command=lambda: None)
facebook_button.image = facebook_photo
facebook_button.pack(side="left", padx=3)

x_icon_path = "C:/Users/admin/Downloads/x.png"
x_image = Image.open(x_icon_path)
x_image = x_image.resize((90, 90), Image.Resampling.LANCZOS)
x_photo = ImageTk.PhotoImage(x_image)
x_button = customtkinter.CTkButton(master=social_frame, image=x_photo, text=" Sign in with X", compound="left", command=lambda: None)
x_button.image = x_photo
x_button.pack(side="left", padx=3)

# Ajouter le bouton de retour avec l'image dans la frame d'inscription
button_back_signup = customtkinter.CTkButton(master=frame_signup, image=back_photo, text="", width=60, height=60, fg_color="purple", bg_color="black", hover_color="#CCCCCC", command=reset_signup_form)
button_back_signup.place(relx=1, rely=0.0095, anchor="ne")

# Widgets pour la frame OTP
label_otp = customtkinter.CTkLabel(master=frame_otp, text="Entrez le code OTP envoyé à votre email", font=("Roboto Medium", 40))
label_otp.pack(pady=70)

otp_entry = customtkinter.CTkEntry(master=frame_otp, placeholder_text="Code OTP", width=400, height=60)
otp_entry.pack(pady=70)

otp_error_label = customtkinter.CTkLabel(master=frame_otp, text="", font=("Cambria", 20), text_color="red")
otp_error_label.pack()

button_validate_otp = customtkinter.CTkButton(master=frame_otp, text="Valider", font=("Cambria", 18), command=validate_otp, corner_radius=20, fg_color="black", hover_color="#66BB6A")
button_validate_otp.pack(pady=30)

# Ajout du texte d'instruction et du bouton pour renvoyer le code OTP
label_no_otp_received = customtkinter.CTkLabel(master=frame_otp, text="Vous n'avez pas reçu le code ?", font=("Cambria", 17), text_color="black")
label_no_otp_received.pack(pady=(10, 0))

button_resend_otp = customtkinter.CTkButton(master=frame_otp, text="Renvoyez le code", font=("Cambria", 14), corner_radius=16, fg_color="black", hover_color="#42A5F5", command=resend_otp)
button_resend_otp.pack(pady=10)

# Bouton Retour
button_back_otp = customtkinter.CTkButton(master=frame_otp, text="Retour", font=("Cambria", 18), corner_radius=20, fg_color="black", hover_color="#CCCCCC", command=show_signup_form)
button_back_otp.place(relx=1, rely=0, anchor="ne", x=-10, y=10)

# Widgets pour la frame de succès de l'inscription
label_signup_success = customtkinter.CTkLabel(master=frame_signup_success, text="", font=("Roboto Medium", 26), bg_color="transparent", fg_color="transparent")
label_signup_success.pack(pady=0)

# Charger l'image de fond
bg_image_path = "C:/Users/admin/Downloads/Modern Technology Background Desktop Wallpaper (3).png"
bg_image = Image.open(bg_image_path)
bg_image = bg_image.resize((2000, 1000), Image.Resampling.LANCZOS)  # Redimensionner l'image
bg_photo = ImageTk.PhotoImage(bg_image)

# Créer un label pour afficher l'image de fond
bg_label = tk.Label(frame_signup_success, image=bg_photo)
bg_label.image = bg_photo  # Garder une référence à l'image
bg_label.place(x=0, y=70)  # Ajuster la position pour laisser un espace en haut

# Ajouter le bouton "Suivant"
button_next = customtkinter.CTkButton(master=frame_signup_success, text="Suivant", font=("Cambria", 18), corner_radius=20, fg_color="black", hover_color="#00BFFF", command=show_game_frame)
button_next.place(relx=1, rely=0, anchor="ne", x=-10, y=10)  # Positionner le bouton en haut à droite

# Ajouter le bouton "Commencer le jeu"
button_start_game = customtkinter.CTkButton(master=frame_signup_success, text="Commencer le jeu", font=("Cambria", 26), corner_radius=2, fg_color="#FF00FF", hover_color="black", bg_color="black", command=show_game_frame)
button_start_game.place(x=9500000, y=600)

# Fonction pour activer le raccourci clavier
def activate_shortcut():
    root.bind("<space>", start_game)

# Fonction pour désactiver le raccourci clavier
def deactivate_shortcut():
    root.unbind("<space>")

# Fonction pour démarrer le jeu
def start_game(event=None):
    show_game_frame()

# Réorganiser les widgets au-dessus de l'image de fond
label_signup_success.lift()
button_start_game.lift()
button_next.lift()

# Désactiver le raccourci clavier initialement
deactivate_shortcut()




# Widgets pour la frame de bienvenue
# Ajouter l'image de bienvenue
welcome_image_path = "C:/Users/admin\Downloads\Modern Technology Background Desktop Wallpaper (4).png"
image_pil_welcome = Image.open(welcome_image_path)
image_pil_welcome = image_pil_welcome.resize((950, 650), Image.Resampling.LANCZOS)  # Ajustez la taille de l'image
image_photo_welcome = ImageTk.PhotoImage(image_pil_welcome)
image_label_welcome = customtkinter.CTkLabel(master=frame_welcome, image=image_photo_welcome, text="")
image_label_welcome.image = image_photo_welcome
image_label_welcome.pack(pady=10)

# Ajouter l'emoji à côté de l'image
emoji_label = customtkinter.CTkLabel(master=frame_welcome, text="🎉", font=("Arial", 100))
emoji_label.place(x=image_label_welcome.winfo_reqwidth(), y=image_label_welcome.winfo_y(), anchor="nw")

label_welcome = customtkinter.CTkLabel(master=frame_welcome, text="", font=("Roboto Bold", 50))
label_welcome.pack(pady=40)

# Ajouter les boutons dans un frame pour les centrer
button_frame = customtkinter.CTkFrame(master=frame_welcome, fg_color="transparent")
button_frame.pack(pady=(50, 50))

button_resume_game = customtkinter.CTkButton(master=button_frame, text="   Reprendre   ", font=("Cambria", 32),
                                             corner_radius=28, fg_color="#2196F3", hover_color="#42A5F5",
                                             command=show_game_frame)
button_resume_game.pack(side="left", padx=10)

button_logout = customtkinter.CTkButton(master=button_frame, text="Se déconnecter", font=("Cambria", 32),
                                        corner_radius=28, fg_color="#FF0000", hover_color="#FF4444",
                                        command=show_login_form)
button_logout.pack(side="right", padx=10)

# Fonction pour activer le raccourci clavier
def activate_shortcutt():
    root.bind("<space>", start_game)


# Fonction pour désactiver le raccourci clavier
def deactivate_shortcut():
    root.unbind("<space>")


# Fonction pour démarrer le jeu
def start_game(event=None):
    show_game_frame()

# Fonction pour se déconnecter
def logout(event=None):
    show_login_form()

# Associer les raccourcis clavier
root.bind("<space>", start_game)


# Désactiver le raccourci clavier initialement
deactivate_shortcut()
# Interface de jeu


# Ajouter les éléments d'interface au-dessus de la vidéo dans frame_game
entry_name1 = customtkinter.CTkEntry(master=frame_game, placeholder_text="Nom 1", width=600, height=65, border_width=4,
                                     border_color="#CCCCCC")
entry_name1.place(x=660, y=450)

entry_name2 = customtkinter.CTkEntry(master=frame_game, placeholder_text="Nom 2", width=600, height=65, border_width=4,
                                     border_color="#CCCCCC")
entry_name2.place(x=660, y=550 )

result_label = customtkinter.CTkLabel(master=frame_game, text="", font=("Roboto", 25, 'bold'))
result_label.place_forget()  # Cacher le label au début

# Fonction pour effacer les champs de saisie des noms
# Fonction pour effacer les champs de saisie des noms et réinitialiser l'interface
def reset_names():
    if entry_name1.get():
        entry_name1.delete(0, 'end')
    if entry_name2.get():
        entry_name2.delete(0, 'end')
    result_label.place_forget()
    progress_bar.place_forget()
    percentage_label.place_forget()
    entry_name1.focus()  # Placer le curseur dans l'entrée name1



# Fonction pour vérifier si le nom est valide (alphabétique avec un trait d'union optionnel au milieu)
def is_valid_name(name):
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return False  # Les noms ne doivent pas commencer/terminer par un trait d'union ou contenir deux traits d'union consécutifs
    parts = name.split('-')
    return len(parts) <= 2 and all(part.isalpha() for part in parts)

# Fonction pour calculer la relation entre les deux noms entrés
def calculate_relationship():
    name1 = entry_name1.get().strip().lower()
    name2 = entry_name2.get().strip().lower()

    if not name1 or not name2:
        show_result("Veuillez entrer deux noms.", "")
        return

    if name1 == name2:
        show_result("Veuillez entrer des noms différents.", "")
        return

    if len(name1) < 3 or len(name1) > 16 or len(name2) < 3 or len(name2) > 16:
        show_result("Les noms doivent contenir entre 3 et 16 caractères.", "")
        return

    if not all(part.isalpha() or part == '-' for part in name1.replace('-', '', 1)) or not all(
            part.isalpha() or part == '-' for part in name2.replace('-', '', 1)):
        show_result("Seules les lettres et les traits d'union simples sont autorisés.", "")
        return

    if not is_valid_name(name1) or not is_valid_name(name2):
        show_result("Le trait d'union, s'il est utilisé, ne doit pas être au début ou à la fin.", "")
        return

    # Afficher le message de calcul en cours et la barre de progression
    show_result("Calcul en cours...", "", show_progress=True)
    root.after(300, simulate_loading)


# Fonction pour afficher le résultat
def show_result(message, emoji, percentage=None, show_progress=False):
    if percentage is not None:
        result_label.configure(text=f"{emoji} {message} à {percentage}%", font=("Roboto", 30, 'bold'))
    else:
        result_label.configure(text=f"{emoji} {message}", font=("Roboto", 30, 'bold'))

    result_label.place(relx=0.5, rely=0.65, anchor="center")  # Afficher le label

    if show_progress:
        progress_bar.place(relx=0.5, rely=0.7, anchor="center")
        percentage_label.place(relx=0.5, rely=0.8, anchor="center")
        progress_bar.set(0)
    else:
        progress_bar.place_forget()
        percentage_label.place_forget()


# Fonction pour terminer le calcul de la relation et afficher le résultat
def finish_calculation():
    name1 = entry_name1.get().strip().lower()
    name2 = entry_name2.get().strip().lower()

    count1 = Counter(name1)
    count2 = Counter(name2)

    for char in count1.copy():
        if char in count2:
            del count1[char]
            del count2[char]

    total = sum(count1.values()) + sum(count2.values())
    result_index = total % len(K1)

    relation_key = K1[result_index]

    # Utiliser les relations supplémentaires selon le pourcentage
    percentage = random.randint(0, 100)  # Générer un pourcentage aléatoire
    if relation_key == 'H':
        relation_descriptions = [
            ('La relation est hypocrite', "😶"),
            ('La relation est honnête', "😇"),
            ('La relation est harmonieuse', "🎶")
        ]
    elif relation_key == 'E':
        relation_descriptions = [
            ('La relation est ennemi', "😡"),
            ('La relation est empathique', "😊"),
            ('La relation est épanouie', "🌸")
        ]
    elif relation_key == 'S':
        relation_descriptions = [
            ('La relation est solidaire', "🤝"),
            ('La relation est stable', "😌"),
            ('La relation est spéciale', "⭐")
        ]
    elif relation_key == 'T':
        relation_descriptions = [
            ('La relation est toxique', "☠️"),
            ('La relation est tenace', "💪"),
            ('La relation est tendre', "💖")
        ]
    elif relation_key == 'I':
        relation_descriptions = [
            ('La relation est intime', "❤️"),
            ('La relation est inspirante', "🌟"),
            ('La relation est incroyable', "😲")
        ]
    elif relation_key == 'M':
        relation_descriptions = [
            ('La relation est amicale', "😊"),
            ('La relation est mentorale', "👨‍🏫"),
            ('La relation est magnifique', "🌼")
        ]

    relation_description, emoji = random.choice(relation_descriptions)
    show_result(relation_description, emoji, percentage, show_progress=False)

    # Enregistrer le résultat du jeu
    save_game_result(current_user, name1, name2, relation_description)

# Fonction pour simuler le chargement avec une barre de progression
def simulate_loading():
    progress = 0
    max_progress = 100

    def update_progress():
        nonlocal progress
        if progress < max_progress:
            progress += random.randint(1, 10)
            if progress > max_progress:
                progress = max_progress
            progress_bar.set(progress / 100)
            root.after(300, update_progress)  # Délai de 300ms pour rendre la progression visible
        else:
            # Terminer le calcul une fois le chargement terminé
            finish_calculation()

    update_progress()

K1 = ['H', 'E', 'S', 'T', 'I', 'M']

frame_butons = customtkinter.CTkLabel(master=frame_game, width=800, height=100, text="", bg_color="#483D8B")
frame_butons.place(relx=0.5, rely=0.9, anchor="center")
frame_butons.propagate(False)

button_calculate = customtkinter.CTkButton(master=frame_butons, text="Calculer", font=("Cambria", 22),
                                           fg_color="#00BFFF", hover_color="#66BB6A", bg_color="#4169E1",
                                           command=calculate_relationship)
button_calculate.place(relx=0.1, rely=0.4, anchor="center")

button_reset = customtkinter.CTkButton(master=frame_butons, text="Reinitialiser", font=("Cambria", 22),
                                       fg_color="#00BFFF", hover_color="#FF4444", bg_color="#4169E1",
                                       command=reset_names)
button_reset.place(relx=0.5, rely=0.4, anchor="center")

button_share = customtkinter.CTkButton(master=frame_butons, text="Partager", font=("Cambria", 22),
                                       fg_color="#00BFFF", hover_color="#42A5F5", bg_color="#4169E1",
                                       command=open_share_dialog)
button_share.place(relx=0.9, rely=0.4, anchor="center")



# Ajouter une barre de progression
progress_bar = customtkinter.CTkProgressBar(master=frame_game, width=300, height=20)
progress_bar.place_forget()  # Assurez-vous que la barre de progression est cachée au départ
progress_bar.configure(fg_color="white", progress_color="#483D8B",bg_color="white")  # Fond gris, progression bleue

percentage_label = customtkinter.CTkLabel(master=frame_game, text="", font=("Roboto", 15, 'bold'))
percentage_label.place_forget()  # Assurez-vous que le label de pourcentage est caché au départ

# Bindings pour les touches "Enter" et "Esc"
entry_name1.bind("<Return>", lambda event: entry_name2.focus())
entry_name2.bind("<Return>", lambda event: calculate_relationship())
root.bind("<Escape>", lambda event: reset_names())

# Placer le curseur dans l'entrée name1 au démarrage
entry_name1.focus()


# Ajouter l'icône utilisateur en haut à gauche
user_icon_path = "C:/Users/admin/Downloads/user.ico"
image_pil_user_icon = Image.open(user_icon_path)
image_pil_user_icon = image_pil_user_icon.resize((50, 50), Image.Resampling.LANCZOS)
image_photo_user_icon = ImageTk.PhotoImage(image_pil_user_icon)
button_user_icon = customtkinter.CTkButton(master=frame_game, image=image_photo_user_icon, text="", width=50, height=50,
                                           fg_color="#483D8B",bg_color="#483D8B", hover_color="#00BFFF", command=show_profile_frame)
button_user_icon.place(x=10, y=10)

# Widgets pour la frame de profil
profile_info_frame = customtkinter.CTkFrame(master=frame_profile)
profile_info_frame.pack(pady=20, padx=20, fill="both", expand=True)

# Ajouter l'image de profil
# Titre du profil
label_profile_title = customtkinter.CTkLabel(master=profile_info_frame, text="Infos Compte", font=("Roboto Bold", 24))
label_profile_title.pack(pady=20)

info_icon_path = "C:/Users/admin/Downloads/info-symbol-1343394_960_720.png"
image_pil_info = Image.open(info_icon_path)
image_pil_info = image_pil_info.resize((100, 100), Image.Resampling.LANCZOS)
image_photo_info = ImageTk.PhotoImage(image_pil_info)
info_icon_label = customtkinter.CTkLabel(master=profile_info_frame, image=image_photo_info, text="")
info_icon_label.image = image_photo_info
info_icon_label.pack(pady=30)

# Informations du profil
label_profile_username = customtkinter.CTkLabel(master=profile_info_frame, text="", font=("Roboto Medium", 20))
label_profile_username.pack(pady=10)

label_profile_email = customtkinter.CTkLabel(master=profile_info_frame, text="", font=("Roboto Medium", 20))
label_profile_email.pack(pady=10)

label_profile_country = customtkinter.CTkLabel(master=profile_info_frame, text="", font=("Roboto Medium", 20))
label_profile_country.pack(pady=10)

label_profile_gender = customtkinter.CTkLabel(master=profile_info_frame, text="", font=("Roboto Medium", 20))
label_profile_gender.pack(pady=10)

# Frame pour les boutons
button_frame_profile = customtkinter.CTkFrame(master=frame_profile, fg_color="#87CEEB")
button_frame_profile.pack(pady=10, padx=20, fill="x")

# Bouton Retour au jeu
button_back_to_game = customtkinter.CTkButton(master=button_frame_profile, text="Retour au jeu", font=("Cambria", 20),
                                              corner_radius=16, fg_color="#2196F3", hover_color="#42A5F5",
                                              command=show_game_frame)
button_back_to_game.pack(side="left", padx=10, pady=10)

# Bouton Historique de jeu
button_game_history = customtkinter.CTkButton(master=button_frame_profile, text="Historique de jeu",
                                              font=("Cambria", 20), corner_radius=16, fg_color="#2196F3",
                                              hover_color="#42A5F5",
                                              command=show_game_history)  # Remplacez par la fonction qui affiche l'historique de jeu
button_game_history.pack(side="left", padx=10, pady=10)

# Bouton Se déconnecter
button_logout_profile = customtkinter.CTkButton(master=button_frame_profile, text="Se déconnecter",
                                                font=("Cambria", 20), corner_radius=16, fg_color="#FF0000",
                                                hover_color="#FF4444", command=show_login_form)
button_logout_profile.pack(side="left", padx=10, pady=10)

# Widgets pour la frame de réinitialisation du mot de passe

# Ajouter le bouton de retour à la frame de réinitialisation de mot de passe
button_back_reset_password = customtkinter.CTkButton(master=frame_reset_password, image=back_photo, text="", width=60, height=60,
                                                     fg_color="transparent", hover_color="#CCCCCC", command=reset_reset_password_form)
button_back_reset_password.place(relx=1, rely=0.0095, anchor="ne")  # Positionner le bouton en haut à droite


label_reset_password = customtkinter.CTkLabel(master=frame_reset_password, text="Réinitialisez votre mot de passe",
                                              font=("Roboto Medium", 40))
label_reset_password.pack(pady=40)

entry_reset_email = customtkinter.CTkEntry(master=frame_reset_password, placeholder_text="Email", width=500, height=50)
entry_reset_email.pack(pady=20)

reset_error_label = customtkinter.CTkLabel(master=frame_reset_password, text="", font=("Cambria", 12), text_color="red")
reset_error_label.pack(pady=10)

button_send_reset_code = customtkinter.CTkButton(master=frame_reset_password, text="Envoyer le code", font=("Cambria", 18),
                                                 corner_radius=20, fg_color="#4CAF50", hover_color="#42A5F5",
                                                 command=reset_password)
button_send_reset_code.pack(pady=10)


label_reset_code = customtkinter.CTkLabel(master=frame_reset_password, text="Entrez le code de réinitialisation",
                                          font=("Roboto Medium", 18))
label_reset_code.pack(pady=10)

entry_reset_code = customtkinter.CTkEntry(master=frame_reset_password, placeholder_text="Code de réinitialisation",
                                          width=200, height=50)
entry_reset_code.pack(pady=10)
# Texte en haut indiquant "Vous n'avez pas reçu le code ?"
label_no_code_received = customtkinter.CTkLabel(master=frame_reset_password, text="Vous n'avez pas reçu le code ?", font=("Cambria", 17), text_color="black")
label_no_code_received.pack(pady=10,padx=10)  # Positionner le texte en haut au centre

# Ajouter le bouton "Renvoyez le code"
button_resend_reset_code = customtkinter.CTkButton(master=frame_reset_password, text="Renvoyez le code", font=("Cambria", 18),
                                                   corner_radius=20, fg_color="#4CAF50", hover_color="#42A5F5",
                                                   command=reset_password)
button_resend_reset_code.pack(pady=10)



reset_error_label_code = customtkinter.CTkLabel(master=frame_reset_password, text="", font=("Cambria", 12),
                                                text_color="red")
reset_error_label_code.pack(pady=10)

label_new_reset_password = customtkinter.CTkLabel(master=frame_reset_password, text="Entrez votre nouveau mot de passe",
                                                  font=("Roboto Medium", 18))
label_new_reset_password.pack(pady=10)

entry_new_reset_password = customtkinter.CTkEntry(master=frame_reset_password, placeholder_text="Nouveau mot de passe",
                                                   width=500, height=50)
entry_new_reset_password.pack(pady=10)

# Ajouter les cercles de robustesse du mot de passe pour la réinitialisation
circle_frame_reset = customtkinter.CTkFrame(master=frame_reset_password, fg_color="transparent")

circle_weak_reset = customtkinter.CTkLabel(master=circle_frame_reset, text="●", font=("Arial", 24), text_color="gray")
circle_weak_reset.pack(side="left", padx=2)
circle_medium_reset = customtkinter.CTkLabel(master=circle_frame_reset, text="●", font=("Arial", 24), text_color="gray")
circle_medium_reset.pack(side="left", padx=2)
circle_strong_reset = customtkinter.CTkLabel(master=circle_frame_reset, text="●", font=("Arial", 24), text_color="gray")
circle_strong_reset.pack(side="left", padx=2)
circle_robust_reset = customtkinter.CTkLabel(master=circle_frame_reset, text="●", font=("Arial", 24), text_color="gray")
circle_robust_reset.pack(side="left", padx=2)

label_confirm_reset_password = customtkinter.CTkLabel(master=frame_reset_password, text="Confirmez votre nouveau mot de passe",
                                                      font=("Roboto Medium", 18))
label_confirm_reset_password.pack(pady=10)

entry_confirm_reset_password = customtkinter.CTkEntry(master=frame_reset_password, placeholder_text="Confirmer le mot de passe",
                                                       width=500, height=50)
entry_confirm_reset_password.pack(pady=10)

reset_error_label_password = customtkinter.CTkLabel(master=frame_reset_password, text="", font=("Cambria", 12),
                                                    text_color="red")
reset_error_label_password.pack(pady=10)

button_reset_password = customtkinter.CTkButton(master=frame_reset_password, text="Réinitialiser", font=("Cambria", 18),
                                                corner_radius=20, fg_color="#4CAF50", hover_color="#42A5F5",
                                                command=validate_reset_code)
button_reset_password.pack(pady=20)

# Widgets pour la frame de succès de réinitialisation
label_reset_success = customtkinter.CTkLabel(master=frame_reset_success, text="", font=("Roboto Medium", 50))
label_reset_success.pack(pady=50)

button_continue_reset = customtkinter.CTkButton(master=frame_reset_success, text="Continuer", font=("Cambria", 36),
                                                corner_radius=19, fg_color="#2196F3", hover_color="#42A5F5",
                                                command=show_welcome_frame)
button_continue_reset.pack(pady=40)

# Lier la fonction de vérification de la robustesse du mot de passe à l'événement KeyRelease
entry_new_password.bind("<KeyRelease>", check_password_strength)
entry_new_reset_password.bind("<KeyRelease>", check_password_strength_reset)
# Associer la fonction de filtrage à l'événement KeyRelease
entry_country.bind('<KeyRelease>', on_key_release)
entry_country.bind('<FocusIn>', clear_placeholderr)
entry_country.bind('<FocusOut>', restore_placeholder)
# Initialiser le placeholder avec la couleur grise
entry_country.config(foreground='grey')


show_login_form()
# Démarrer la boucle principale
root.mainloop()


# Libérer les vidéos après la fermeture de l'application
cap_login.release()
cap_signup.release()
cap_game.release()