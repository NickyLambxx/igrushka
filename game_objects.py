import pygame
from settings import load_images, load_fonts, EXPLOSION_RADIUS

BASE_WIDTH = 800.0
CAMPAIGN_GRID_SIZE = 7


def apply_screen_settings(game_state):
    if game_state["screen_mode"] == game_state["pending_screen_mode"]:
        return
    game_state["screen_mode"] = game_state["pending_screen_mode"]

    if game_state["screen_mode"] == "fullscreen":
        info = pygame.display.Info()
        new_width, new_height = info.current_w, info.current_h
        game_state["screen"] = pygame.display.set_mode(
            (new_width, new_height), pygame.FULLSCREEN
        )
    else:
        new_width, new_height = game_state["screen_mode"]
        game_state["screen"] = pygame.display.set_mode((new_width, new_height))

    ui_scale_factor = new_width / BASE_WIDTH
    game_scale_factor = (ui_scale_factor + 1.0) / 2.0
    game_state.update(
        {
            "scale_factor": ui_scale_factor,
            "game_scale_factor": game_scale_factor,
            "object_size": int(50 * game_scale_factor),
            "small_object_size": int(25 * game_scale_factor),
            "gravity": 0.5 * game_scale_factor,
            "WIDTH": new_width,
            "HEIGHT": new_height,
            "GROUND_LEVEL": new_height - int(10 * ui_scale_factor),
            "sling_x": int(new_width * 0.23),
            "sling_y": new_height - int(new_height * 0.33),
            "EXPLOSION_RADIUS": int(EXPLOSION_RADIUS * game_scale_factor),
        }
    )

    c_size = min(new_width * 0.6, new_height * 0.8)
    game_state["campaign_grid_rect"] = pygame.Rect(
        (new_width - c_size) / 2, (new_height - c_size) / 2, c_size, c_size
    )
    game_state["campaign_cell_size"] = c_size / CAMPAIGN_GRID_SIZE

    game_state["images"] = load_images(
        new_width, new_height, ui_scale_factor, game_scale_factor
    )
    game_state["fonts"] = load_fonts(ui_scale_factor)
    bird_names_ru = [
        "Красная Птица",
        "Взрывная Птица",
        "Ускоряющаяся Птица",
        "Птица-Дробилка",
        "Птица-Бумеранг",
    ]
    game_state["bird_image_to_name"] = {
        img: name for img, name in zip(game_state["images"]["bird_imgs"], bird_names_ru)
    }
    reset_game(game_state)


def update_all_volumes(game_state):
    music_vol = game_state["music_volume"] if game_state["sound_on"] else 0.0
    sfx_vol = game_state["sfx_volume"] if game_state["sound_on"] else 0.0
    pygame.mixer.music.set_volume(music_vol)
    for key, sound in game_state["sounds"].items():
        if key != "music_playlist":
            sound.set_volume(sfx_vol)


def play_music_track(game_state, track_index):
    if game_state["sounds"].get("music_playlist"):
        try:
            pygame.mixer.music.load(game_state["sounds"]["music_playlist"][track_index])
            pygame.mixer.music.play()
            game_state["current_music_track_index"] = track_index
        except:
            pass


def reset_game(game_state):
    """Маршрутизатор сброса: направляет на нужный движок в зависимости от режима."""
    if game_state["game_mode"] == "campaign":
        from match3_game import reset_match3

        reset_match3(game_state)
    else:
        from slingshot_game import reset_slingshot

        reset_slingshot(game_state)