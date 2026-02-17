import pygame
import sys
import random
import time
from utils import draw_text
from settings import (
    load_images,
    load_sounds,
    load_fonts,
    EXPLOSION_RADIUS,
    MAX_EXPLOSION_FRAMES,
)
from achievements import (
    load_all_profiles_data,
    save_all_profiles_data,
    load_last_profile_name,
    save_last_profile_name,
    load_user_settings,
    save_user_settings,
)
from game_objects import (
    update_all_volumes,
    play_music_track,
    reset_game,
    CAMPAIGN_GRID_SIZE,
    BASE_WIDTH,
)
from game_states import (
    StateManager,
    MainMenuState,
    ProfileMenuState,
    SettingsState,
    SoundSettingsState,
    ScreenSettingsState,
    LanguageMenuState,
    GameModeMenuState,
    AchievementsMenuState,
    BirdpediaMenuState,
    BirdpediaDetailState,
    LevelSelectionState,
)
from match3_game import Match3State
from slingshot_game import SlingshotState
from localization import LANGUAGES

MUSIC_END_EVENT = pygame.USEREVENT + 1


def init_game():
    pygame.init()
    INITIAL_WIDTH, INITIAL_HEIGHT = 800, 600
    screen = pygame.display.set_mode((INITIAL_WIDTH, INITIAL_HEIGHT))
    pygame.display.set_caption("Angry Birds Deluxe")
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    ui_scale_factor = INITIAL_WIDTH / BASE_WIDTH
    game_scale_factor = (ui_scale_factor + 1.0) / 2.0
    object_size = int(50 * game_scale_factor)
    small_object_size = int(25 * game_scale_factor)

    images = load_images(
        INITIAL_WIDTH, INITIAL_HEIGHT, ui_scale_factor, game_scale_factor
    )
    sounds = load_sounds()
    fonts = load_fonts(ui_scale_factor)

    sling_x = int(INITIAL_WIDTH * 0.23)
    sling_y = INITIAL_HEIGHT - int(INITIAL_HEIGHT * 0.33)

    all_profiles_data = load_all_profiles_data()
    last_profile = load_last_profile_name()
    if last_profile not in all_profiles_data:
        last_profile = "Guest"

    bird_names = [
        "Красная Птица",
        "Взрывная Птица",
        "Ускоряющаяся Птица",
        "Птица-Дробилка",
        "Птица-Бумеранг",
    ]
    bird_image_to_name = {
        img: name for img, name in zip(images["bird_imgs"], bird_names)
    }
    user_settings = load_user_settings()
    current_language = user_settings.get("language", "ru")

    campaign_board_size = min(INITIAL_WIDTH * 0.6, INITIAL_HEIGHT * 0.8)
    campaign_grid_rect = pygame.Rect(
        (INITIAL_WIDTH - campaign_board_size) / 2,
        (INITIAL_HEIGHT - campaign_board_size) / 2,
        campaign_board_size,
        campaign_board_size,
    )

    game_state = {
        "screen": screen,
        "clock": clock,
        "images": images,
        "sounds": sounds,
        "fonts": fonts,
        "WIDTH": INITIAL_WIDTH,
        "HEIGHT": INITIAL_HEIGHT,
        "scale_factor": ui_scale_factor,
        "game_scale_factor": game_scale_factor,
        "object_size": object_size,
        "small_object_size": small_object_size,
        "sling_x": sling_x,
        "sling_y": sling_y,
        "GROUND_LEVEL": INITIAL_HEIGHT - int(10 * ui_scale_factor),
        "EXPLOSION_RADIUS": int(EXPLOSION_RADIUS * game_scale_factor),
        "MAX_EXPLOSION_FRAMES": MAX_EXPLOSION_FRAMES,
        "gravity": 0.5 * game_scale_factor,
        "explosion_active": False,
        "explosion_center": (0, 0),
        "explosion_frames": 0,
        "boost_trail_start_time": None,
        "paused": False,
        "combo": 0,
        "difficulty": "easy",
        "game_mode": "classic",
        "sound_on": True,
        "initial_profile_selection": True,
        "score": 0,
        "lives": 5,
        "game_over": False,
        "current_bird_img": None,
        "bird_queue": [],
        "target_timer_start": None,
        "target_duration": 5,
        "trail_particles": [],
        "dust_particles": [],
        "spark_particles": [],
        "feather_particles": [],
        "achievement_text": "",
        "achievement_show_time": 0,
        "achievement_duration": 3,
        "music_volume": user_settings["audio"]["music_volume"],
        "sfx_volume": user_settings["audio"]["sfx_volume"],
        "brightness_slider_pos": user_settings["display"]["brightness"],
        "language": current_language,
        "texts": LANGUAGES.get(current_language, LANGUAGES["ru"]),
        "current_shot_hit": False,
        "screen_shake": 0,
        "current_music_track_index": random.randint(0, 4),
        "last_shot_path": [],
        "path_display_timer": 0,
        "all_profiles_data": all_profiles_data,
        "current_profile": last_profile,
        "achievements_viewing_profile": last_profile,
        "achievements_viewing_difficulty": "easy",
        "profile_input_active": False,
        "profile_input_text": "",
        "show_profile_delete_confirm": False,
        "profile_to_delete": "",
        "training_complete": False,
        "birdpedia_item_selected": None,
        "show_hint_popup": False,
        "show_campaign_hint_popup": False,
        "is_dragging_music_volume": False,
        "is_dragging_sfx_volume": False,
        "is_dragging_difficulty": False,
        "is_dragging_brightness": False,
        "bird_image_to_name": bird_image_to_name,
        "show_training_popup": False,
        "screen_mode": (INITIAL_WIDTH, INITIAL_HEIGHT),
        "pending_screen_mode": (INITIAL_WIDTH, INITIAL_HEIGHT),
        "campaign_board": None,
        "campaign_score": 0,
        "campaign_target_score": 10000,
        "campaign_level_complete": False,
        "campaign_selected_tile": None,
        "campaign_is_processing": False,
        "campaign_grid_rect": campaign_grid_rect,
        "campaign_cell_size": campaign_board_size / CAMPAIGN_GRID_SIZE,
        "campaign_board_state": "idle",
        "campaign_matched_tiles": [],
        "campaign_falling_tiles": [],
        "campaign_refilling_tiles": [],
        "campaign_clear_progress": 0.0,
        "campaign_is_swapping": False,
        "campaign_swap_anim": None,
        "campaign_drag_start_pos": None,
        "campaign_drag_start_tile": None,
        "campaign_is_dragging_tile": False,
    }

    state_manager = StateManager()
    state_manager.add_state("profile_menu", ProfileMenuState())
    state_manager.add_state("main_menu", MainMenuState())
    state_manager.add_state("level_selection", LevelSelectionState())
    state_manager.add_state("settings_menu", SettingsState())
    state_manager.add_state("sound_settings", SoundSettingsState())
    state_manager.add_state("screen_settings", ScreenSettingsState())
    state_manager.add_state("language_settings", LanguageMenuState())
    state_manager.add_state("game_mode_menu", GameModeMenuState())
    state_manager.add_state("achievements_menu", AchievementsMenuState())
    state_manager.add_state("birdpedia_menu", BirdpediaMenuState())
    state_manager.add_state("birdpedia_detail", BirdpediaDetailState())

    # Регистрация изолированных движков
    state_manager.add_state("match3", Match3State())
    state_manager.add_state("slingshot", SlingshotState())

    game_state["state_manager"] = state_manager
    state_manager.change_state("profile_menu", game_state)

    reset_game(game_state)
    pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    update_all_volumes(game_state)
    play_music_track(game_state, game_state["current_music_track_index"])
    return game_state


def main():
    game_state = init_game()
    sm = game_state["state_manager"]
    clock = game_state["clock"]

    while sm.running:
        dt = clock.tick(60) / 1000.0
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sm.running = False
            elif event.type == MUSIC_END_EVENT:
                new_track_index = (game_state["current_music_track_index"] + 1) % len(
                    game_state["sounds"]["music_playlist"]
                )
                play_music_track(game_state, new_track_index)
            else:
                sm.current_state.handle_event(event, mx, my, game_state)

        sm.current_state.update(dt, mx, my, game_state)
        sm.current_state.draw(game_state["screen"], mx, my, game_state)

        brightness = game_state["brightness_slider_pos"]
        if brightness < 1.0:
            overlay = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, int(255 * (1.0 - brightness))))
            game_state["screen"].blit(overlay, (0, 0))

        if (
            game_state.get("achievement_text")
            and time.time() < game_state["achievement_show_time"]
        ):
            ach_surface = pygame.Surface((game_state["WIDTH"], 100), pygame.SRCALPHA)
            ach_surface.fill((0, 0, 0, 150))
            game_state["screen"].blit(ach_surface, (0, game_state["HEIGHT"] // 2 - 50))
            text_surf, text_rect = draw_text(
                game_state["achievement_text"],
                game_state["fonts"]["achievement_font"],
                (255, 215, 0),
            )
            text_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
            game_state["screen"].blit(text_surf, text_rect)
        elif game_state.get("achievement_text"):
            game_state["achievement_text"] = ""

        if game_state["images"].get("cursor_img"):
            game_state["screen"].blit(game_state["images"]["cursor_img"], (mx, my))

        pygame.display.flip()

    user_settings = {
        "audio": {
            "music_volume": game_state["music_volume"],
            "sfx_volume": game_state["sfx_volume"],
        },
        "display": {"brightness": game_state["brightness_slider_pos"]},
        "language": game_state["language"],
    }
    save_user_settings(user_settings)
    save_last_profile_name(game_state["current_profile"])
    save_all_profiles_data(game_state["all_profiles_data"])
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()