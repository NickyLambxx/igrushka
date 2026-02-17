# achievements.py

import json
import os

PROFILES_FILE = "profiles.json"
LAST_PROFILE_FILE = "last_profile.json"
USER_SETTINGS_FILE = "user_settings.json" # ОБЪЕДИНЕННЫЙ ФАЙЛ НАСТРОЕК

# НОВАЯ ФУНКЦИЯ: Создает пустую структуру для достижений
def create_default_achievements():
    achievements = {}
    modes = ['classic', 'sharpshooter', 'obstacle']
    difficulties = ['easy', 'medium', 'hard']
    for mode in modes:
        for difficulty in difficulties:
            key = f"max_combo_{mode}_{difficulty}"
            achievements[key] = 0
    return achievements

def load_all_profiles_data():
    if not os.path.exists(PROFILES_FILE):
        default_data = {"Guest": create_default_achievements()}
        save_all_profiles_data(default_data)
        return default_data
    try:
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка загрузки профилей: {e}. Создание профиля по умолчанию.")
        return {"Guest": create_default_achievements()}

def save_all_profiles_data(profiles_data):
    try:
        with open(PROFILES_FILE, "w") as f:
            json.dump(profiles_data, f, indent=4)
    except IOError as e:
        print(f"Ошибка сохранения профилей: {e}")

# ИЗМЕНЕНО: Создает новую структуру данных для нового профиля
def get_achievements_for_profile(profiles_data, profile_name):
    if profile_name not in profiles_data:
        profiles_data[profile_name] = create_default_achievements()
    # Проверка на случай, если у старого профиля нет новых ключей
    elif not all(key in profiles_data[profile_name] for key in create_default_achievements()):
        default_achievements = create_default_achievements()
        default_achievements.update(profiles_data[profile_name])
        profiles_data[profile_name] = default_achievements

    return profiles_data[profile_name]


def load_last_profile_name():
    try:
        if os.path.exists(LAST_PROFILE_FILE):
            with open(LAST_PROFILE_FILE, "r") as f:
                data = json.load(f)
                return data.get("last_profile", "Guest")
    except (json.JSONDecodeError, IOError):
        pass
    return "Guest"

def save_last_profile_name(profile_name):
    try:
        with open(LAST_PROFILE_FILE, "w") as f:
            json.dump({"last_profile": profile_name}, f)
    except IOError as e:
        print(f"Ошибка сохранения последнего профиля: {e}")

# ИЗМЕНЕНО: Загружает все пользовательские настройки
def load_user_settings():
    """Загружает все пользовательские настройки из одного файла."""
    # ИЗМЕНЕНО: Убран 'contrast' из настроек по умолчанию
    default_settings = {
        "audio": {"music_volume": 0.5, "sfx_volume": 0.5},
        "display": {"brightness": 1.0},
        "language": "ru"
    }
    try:
        if os.path.exists(USER_SETTINGS_FILE):
            with open(USER_SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                # Проверка на полноту данных, чтобы избежать ошибок при добавлении новых настроек
                if "audio" not in settings: settings["audio"] = default_settings["audio"]
                if "display" not in settings: settings["display"] = default_settings["display"]
                if "language" not in settings: settings["language"] = default_settings["language"]
                return settings
    except (json.JSONDecodeError, IOError):
        pass
    return default_settings

# ИЗМЕНЕНО: Сохраняет все пользовательские настройки
def save_user_settings(settings_data):
    """Сохраняет все пользовательские настройки в один файл."""
    try:
        with open(USER_SETTINGS_FILE, "w") as f:
            json.dump(settings_data, f, indent=4)
    except IOError as e:
        print(f"Ошибка сохранения настроек: {e}")