import pygame
import sys
import math
import random
import time
from settings import (
    load_images,
    load_sounds,
    load_fonts,
    EXPLOSION_RADIUS,
    MAX_EXPLOSION_FRAMES,
    SPEED_MULTIPLIER,
)
from utils import (
    draw_text,
    create_target,
    create_obstacle,
    create_trail_particle,
    create_dust_particle,
    create_spark_particle,
    update_particles,
    draw_particles,
    draw_dashed_trajectory,
    create_feather_explosion,
    update_and_draw_feathers,
    create_brick_shatter,
)
from achievements import (
    load_all_profiles_data,
    save_all_profiles_data,
    load_last_profile_name,
    save_last_profile_name,
    load_user_settings,
    save_user_settings,
    create_default_achievements,
)
from game_objects import (
    reset_game,
    update_game_state,
    split_bird,
    activate_boomerang,
    check_matches,
    update_campaign_board,
    CAMPAIGN_GRID_SIZE,
)
from game_states import (
    draw_menu,
    draw_settings,
    draw_game_mode_selection,
    draw_achievements,
    draw_gameplay,
    draw_achievements_reset_confirmation,
    draw_profile_selection,
    draw_profile_delete_confirmation,
    draw_birdpedia_menu,
    draw_birdpedia_detail_screen,
    draw_hint_popup,
    draw_training_popup,
    draw_training_complete_screen,
    draw_sound_settings,
    draw_screen_settings,
    draw_language_selection,
    draw_campaign_board,
    draw_level_selection,
    draw_campaign_hint_popup,
)
from localization import LANGUAGES


MUSIC_END_EVENT = pygame.USEREVENT + 1
BASE_WIDTH = 800.0


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
    campaign_cell_size = campaign_board_size / CAMPAIGN_GRID_SIZE

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
        "projectile_x": sling_x,
        "projectile_y": sling_y,
        "projectile_rect": pygame.Rect(
            sling_x - object_size // 2,
            sling_y - object_size // 2,
            object_size,
            object_size,
        ),
        "is_dragging": False,
        "is_moving": False,
        "show_rope": False,
        "velocity_x": 0,
        "velocity_y": 0,
        "gravity": 0.5 * game_scale_factor,
        "explosion_active": False,
        "explosion_center": (0, 0),
        "explosion_frames": 0,
        "third_bird_boosted": False,
        "boost_trail_start_time": None,
        "boost_available": False,
        "split_available": False,
        "boomerang_available": False,
        "paused": False,
        "small_birds": [],
        "combo": 0,
        "difficulty": "easy",
        "game_mode": "classic",
        "sound_on": True,
        "menu": False,
        "settings": False,
        "sound_settings_menu": False,
        "screen_settings_menu": False,
        "game_mode_menu": False,
        "achievements_menu": False,
        "profile_menu": True,
        "birdpedia_menu": False,
        "birdpedia_detail_menu": False,
        "language_menu": False,
        "initial_profile_selection": True,
        "level_selection_menu": False,
        "score": 0,
        "lives": 5,
        "game_over": False,
        "current_bird_img": None,
        "bird_queue": [],
        "targets": [],
        "target_speeds": [],
        "obstacles": [],
        "obstacle_speeds": [],
        "defeated_pigs": [],
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
        "bird_is_jumping": False,
        "jump_progress": 0,
        "jump_start_pos": (0, 0),
        "jump_bird_img": None,
        "current_music_track_index": random.randint(0, 4),
        "show_achievements_reset_confirm": False,
        "projectile_angle": 0,
        "is_tumbling": False,
        "tumble_timer": 0,
        "angular_velocity": 0,
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
        "campaign_cell_size": campaign_cell_size,
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

    reset_game(game_state)
    pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    update_all_volumes(game_state)
    play_music_track(game_state, game_state["current_music_track_index"])
    return game_state


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

    game_state["scale_factor"] = ui_scale_factor
    game_state["game_scale_factor"] = game_scale_factor
    game_state["object_size"] = int(50 * game_scale_factor)
    game_state["small_object_size"] = int(25 * game_scale_factor)
    game_state["gravity"] = 0.5 * game_scale_factor

    game_state["WIDTH"] = new_width
    game_state["HEIGHT"] = new_height
    game_state["GROUND_LEVEL"] = new_height - int(10 * ui_scale_factor)
    game_state["sling_x"] = int(new_width * 0.23)
    game_state["sling_y"] = new_height - int(new_height * 0.33)
    game_state["EXPLOSION_RADIUS"] = int(EXPLOSION_RADIUS * game_scale_factor)

    campaign_board_size = min(new_width * 0.6, new_height * 0.8)
    game_state["campaign_grid_rect"] = pygame.Rect(
        (new_width - campaign_board_size) / 2,
        (new_height - campaign_board_size) / 2,
        campaign_board_size,
        campaign_board_size,
    )
    game_state["campaign_cell_size"] = campaign_board_size / CAMPAIGN_GRID_SIZE

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
            track_path = game_state["sounds"]["music_playlist"][track_index]
            pygame.mixer.music.load(track_path)
            pygame.mixer.music.play()
            game_state["current_music_track_index"] = track_index
        except Exception as e:
            print(f"Не удалось запустить трек {track_index}: {e}")


def get_next_bird(game_state):
    if game_state["last_shot_path"]:
        game_state["path_display_timer"] = time.time() + 0.75

    if game_state["game_mode"] == "training":
        game_state["training_shots_fired"] += 1
        if game_state["training_shots_fired"] >= 3:
            game_state["training_shots_fired"] = 0
            game_state["training_bird_index"] += 1
            if game_state["training_bird_index"] >= len(
                game_state["images"]["bird_imgs"]
            ):
                game_state["training_complete"] = True
                game_state["current_bird_img"] = None
                return
            else:
                game_state["show_training_popup"] = True
                game_state["training_popup_text"] = game_state["texts"][
                    "training_descriptions"
                ][game_state["training_bird_index"]]
                game_state["current_bird_img"] = None
                return
    else:
        if game_state["lives"] <= 0:
            game_state["game_over"] = True
            game_state["current_bird_img"] = None
            return
        if not game_state["bird_queue"]:
            game_state["game_over"] = True
            game_state["current_bird_img"] = None
            return

    game_state["is_moving"] = False
    game_state["is_tumbling"] = False
    game_state["third_bird_boosted"] = False
    game_state["boost_available"] = False
    game_state["split_available"] = False
    game_state["boomerang_available"] = False
    game_state["projectile_angle"] = 0
    game_state["projectile_x"], game_state["projectile_y"] = (
        game_state["sling_x"],
        game_state["sling_y"],
    )

    if game_state["game_mode"] == "training":
        game_state["current_bird_img"] = game_state["images"]["bird_imgs"][
            game_state["training_bird_index"]
        ]
    else:
        game_state["bird_is_jumping"] = True
        game_state["jump_progress"] = 0
        game_state["jump_start_pos"] = (
            int(40 * game_state["scale_factor"]),
            game_state["GROUND_LEVEL"] - game_state["object_size"] * 0.9,
        )
        game_state["jump_bird_img"] = game_state["bird_queue"].pop(0)
        game_state["bird_queue"].append(
            random.choice(game_state["images"]["bird_imgs"])
        )


def add_new_speed(game_state):
    speed_multiplier = SPEED_MULTIPLIER.get(game_state["difficulty"], 0)
    if speed_multiplier > 0:
        dx = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
        dy = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
        game_state["target_speeds"].append((dx, dy))
    else:
        game_state["target_speeds"].append((0, 0))


def update_max_combo(game_state, profile_name):
    mode = game_state["game_mode"]
    difficulty = game_state["difficulty"]
    combo = game_state["combo"]

    if mode not in ["classic", "sharpshooter", "obstacle"]:
        return

    key = f"max_combo_{mode}_{difficulty}"
    current_profile_data = game_state["all_profiles_data"][profile_name]

    if combo > current_profile_data.get(key, 0):
        current_profile_data[key] = combo
        if profile_name == game_state["current_profile"]:
            game_state[key] = combo


def start_swap_animation(game_state, pos1, pos2):
    r1, c1 = pos1
    r2, c2 = pos2
    board = game_state["campaign_board"]

    if not (
        0 <= r1 < CAMPAIGN_GRID_SIZE
        and 0 <= c1 < CAMPAIGN_GRID_SIZE
        and 0 <= r2 < CAMPAIGN_GRID_SIZE
        and 0 <= c2 < CAMPAIGN_GRID_SIZE
    ):
        game_state["campaign_selected_tile"] = None
        return

    type1 = board[r1][c1]
    type2 = board[r2][c2]
    if type1 is None or type2 is None:
        game_state["campaign_selected_tile"] = None
        return

    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
    will_match = check_matches(board)
    board[r1][c1], board[r2][c2] = type1, type2

    game_state["campaign_is_swapping"] = True
    game_state["campaign_swap_anim"] = {
        "tile1_pos": pos1,
        "tile2_pos": pos2,
        "tile1_type": type1,
        "tile2_type": type2,
        "progress": 0.0,
        "reverse": not will_match,
    }
    game_state["campaign_selected_tile"] = None


def main():
    game_state = init_game()
    running = True
    while running:
        shake_offset = (0, 0)
        if game_state["screen_shake"] > 0:
            game_state["screen_shake"] -= 1
            shake_offset = (random.randint(-5, 5), random.randint(-5, 5))

        in_any_menu = (
            game_state["menu"]
            or game_state["settings"]
            or game_state["sound_settings_menu"]
            or game_state["screen_settings_menu"]
            or game_state["game_mode_menu"]
            or game_state["achievements_menu"]
            or game_state["profile_menu"]
            or game_state["birdpedia_menu"]
            or game_state["birdpedia_detail_menu"]
            or game_state["language_menu"]
            or game_state.get("level_selection_menu")
        )

        is_gameplay_paused = game_state["paused"] or (
            game_state["game_mode"] == "campaign"
            and (
                game_state["campaign_is_processing"]
                or game_state["campaign_is_swapping"]
                or game_state["campaign_level_complete"]
                or game_state.get("show_campaign_hint_popup")
            )
        )

        background_to_draw = (
            game_state["images"]["menu_background"]
            if in_any_menu
            else game_state["images"]["background"]
        )
        bg_rect = background_to_draw.get_rect(
            center=game_state["screen"].get_rect().center
        )
        game_state["screen"].blit(
            background_to_draw,
            (bg_rect.left + shake_offset[0], bg_rect.top + shake_offset[1]),
        )
        mx, my = pygame.mouse.get_pos()
        click_processed = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == MUSIC_END_EVENT:
                new_track_index = (game_state["current_music_track_index"] + 1) % len(
                    game_state["sounds"]["music_playlist"]
                )
                play_music_track(game_state, new_track_index)
            elif event.type == pygame.KEYDOWN:
                if game_state["profile_input_active"]:
                    if event.key == pygame.K_BACKSPACE:
                        game_state["profile_input_text"] = game_state[
                            "profile_input_text"
                        ][:-1]
                    elif (
                        len(game_state["profile_input_text"]) < 15
                        and event.unicode.isalnum()
                    ):
                        game_state["profile_input_text"] += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    if game_state["initial_profile_selection"]:
                        pass
                    else:
                        game_state.update(
                            {
                                "menu": True,
                                "settings": False,
                                "game_mode_menu": False,
                                "achievements_menu": False,
                                "profile_menu": False,
                                "sound_settings_menu": False,
                                "screen_settings_menu": False,
                                "birdpedia_menu": False,
                                "language_menu": False,
                                "show_profile_delete_confirm": False,
                                "profile_to_delete": "",
                                "birdpedia_detail_menu": False,
                                "show_hint_popup": False,
                                "paused": False,
                                "training_complete": False,
                                "show_training_popup": False,
                                "level_selection_menu": False,
                                "show_campaign_hint_popup": False,
                            }
                        )
                        if game_state["game_mode"] == "campaign":
                            game_state["campaign_level_complete"] = False
                elif event.key == pygame.K_r and not in_any_menu:
                    reset_game(game_state)
                elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                    if (
                        not in_any_menu
                        and not game_state["training_complete"]
                        and not game_state["show_hint_popup"]
                        and not game_state["show_training_popup"]
                        and not game_state.get("show_campaign_hint_popup")
                    ):
                        game_state["paused"] = not game_state["paused"]
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    is_popup_active = (
                        game_state["show_hint_popup"]
                        or game_state.get("show_campaign_hint_popup")
                        or game_state["show_achievements_reset_confirm"]
                        or game_state["show_profile_delete_confirm"]
                        or game_state["training_complete"]
                        or game_state["show_training_popup"]
                        or (
                            game_state["game_mode"] == "campaign"
                            and game_state["campaign_level_complete"]
                        )
                    )
                    if is_popup_active:
                        click_processed = True
                        continue

                    speaker_rect = pygame.Rect(
                        game_state["WIDTH"] - int(50 * game_state["scale_factor"]),
                        int(10 * game_state["scale_factor"]),
                        int(40 * game_state["scale_factor"]),
                        int(40 * game_state["scale_factor"]),
                    )
                    pause_rect = pygame.Rect(
                        game_state["WIDTH"] - int(100 * game_state["scale_factor"]),
                        int(10 * game_state["scale_factor"]),
                        int(40 * game_state["scale_factor"]),
                        int(40 * game_state["scale_factor"]),
                    )
                    lightbulb_rect = pygame.Rect(
                        game_state["WIDTH"] // 2 - int(30 * game_state["scale_factor"]),
                        int(10 * game_state["scale_factor"]),
                        int(60 * game_state["scale_factor"]),
                        int(40 * game_state["scale_factor"]),
                    )

                    if speaker_rect.collidepoint(mx, my):
                        game_state["sound_on"] = not game_state["sound_on"]
                        update_all_volumes(game_state)
                        click_processed = True
                    elif pause_rect.collidepoint(mx, my) and not in_any_menu:
                        game_state["paused"] = not game_state["paused"]
                        click_processed = True
                    elif lightbulb_rect.collidepoint(mx, my) and not in_any_menu:
                        if game_state["game_mode"] == "campaign":
                            game_state["show_campaign_hint_popup"] = True
                        else:
                            game_state["show_hint_popup"] = True
                        game_state["paused"] = True
                        click_processed = True
                    elif in_any_menu:
                        click_processed = True

                    if not click_processed:
                        if (
                            game_state["game_mode"] == "campaign"
                            and not is_gameplay_paused
                        ):
                            grid_rect = game_state["campaign_grid_rect"]
                            if grid_rect.collidepoint(mx, my):
                                cell_size = game_state["campaign_cell_size"]
                                c = int((mx - grid_rect.x) / cell_size)
                                r = int((my - grid_rect.y) / cell_size)
                                game_state["campaign_drag_start_pos"] = (mx, my)
                                game_state["campaign_drag_start_tile"] = (r, c)
                                game_state["campaign_is_dragging_tile"] = True
                        elif (
                            game_state["current_bird_img"]
                            and not game_state["game_over"]
                            and not game_state["bird_is_jumping"]
                            and math.hypot(
                                mx - game_state["projectile_x"],
                                my - game_state["projectile_y"],
                            )
                            <= game_state["object_size"] // 2
                            and not game_state["is_moving"]
                            and not is_gameplay_paused
                        ):
                            game_state["is_dragging"] = True
                            game_state["show_rope"] = True
                        elif (
                            game_state["is_moving"]
                            and game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][2]
                            and game_state["boost_available"]
                            and not game_state["third_bird_boosted"]
                            and not is_gameplay_paused
                        ):
                            if game_state["sound_on"]:
                                game_state["sounds"]["boost_sound"].play()
                            game_state["velocity_x"] *= 2.0
                            game_state["velocity_y"] *= 2.0
                            game_state["third_bird_boosted"] = True
                            game_state["boost_trail_start_time"] = time.time()
                            create_spark_particle(
                                game_state["spark_particles"],
                                game_state["projectile_x"],
                                game_state["projectile_y"],
                            )
                        elif (
                            game_state["is_moving"]
                            and game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][3]
                            and game_state["split_available"]
                            and not is_gameplay_paused
                        ):
                            split_bird(
                                game_state,
                                game_state["projectile_x"],
                                game_state["projectile_y"],
                                game_state["velocity_x"],
                                game_state["velocity_y"],
                            )
                        elif (
                            game_state["is_moving"]
                            and game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][4]
                            and game_state["boomerang_available"]
                            and not is_gameplay_paused
                        ):
                            activate_boomerang(game_state)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    game_state["campaign_is_dragging_tile"] = False
                    if game_state["campaign_drag_start_tile"]:
                        start_r, start_c = game_state["campaign_drag_start_tile"]
                        start_mx, start_my = game_state["campaign_drag_start_pos"]
                        drag_dist = math.hypot(mx - start_mx, my - start_my)
                        cell_size = game_state["campaign_cell_size"]

                        if drag_dist < cell_size / 2:
                            if game_state["campaign_selected_tile"] is None:
                                game_state["campaign_selected_tile"] = (
                                    start_r,
                                    start_c,
                                )
                            else:
                                sel_r, sel_c = game_state["campaign_selected_tile"]
                                if abs(start_r - sel_r) + abs(start_c - sel_c) == 1:
                                    start_swap_animation(
                                        game_state, (sel_r, sel_c), (start_r, start_c)
                                    )
                                elif (start_r, start_c) == (sel_r, sel_c):
                                    game_state["campaign_selected_tile"] = None
                                else:
                                    game_state["campaign_selected_tile"] = (
                                        start_r,
                                        start_c,
                                    )
                        else:
                            dx = mx - start_mx
                            dy = my - start_my
                            end_r, end_c = start_r, start_c
                            if abs(dx) > abs(dy):
                                if dx > 0:
                                    end_c += 1
                                else:
                                    end_c -= 1
                            else:
                                if dy > 0:
                                    end_r += 1
                                else:
                                    end_r -= 1
                            start_swap_animation(
                                game_state, (start_r, start_c), (end_r, end_c)
                            )

                        game_state["campaign_drag_start_tile"] = None
                        game_state["campaign_drag_start_pos"] = None

                    game_state.update(
                        {
                            "is_dragging_music_volume": False,
                            "is_dragging_sfx_volume": False,
                            "is_dragging_difficulty": False,
                            "is_dragging_brightness": False,
                        }
                    )
                    if game_state["is_dragging"]:
                        game_state["is_dragging"] = False
                        dx = game_state["sling_x"] - game_state["projectile_x"]
                        dy = game_state["sling_y"] - game_state["projectile_y"]
                        angle = math.atan2(dy, dx)
                        max_drag_dist = int(150 * game_state["scale_factor"])
                        distance = min(math.hypot(dx, dy), max_drag_dist)
                        power = distance / 7.0
                        game_state["velocity_x"] = power * math.cos(angle)
                        game_state["velocity_y"] = power * math.sin(angle)
                        game_state["is_moving"] = True
                        game_state["show_rope"] = False
                        game_state["current_shot_hit"] = False
                        game_state["last_shot_path"] = []
                        if game_state["sound_on"]:
                            game_state["sounds"]["fly_sound"].play()
                        if (
                            game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][2]
                        ):
                            game_state["boost_available"] = True
                        elif (
                            game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][3]
                        ):
                            game_state["split_available"] = True
                        elif (
                            game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][4]
                        ):
                            game_state["boomerang_available"] = True

        if game_state["is_dragging"] and not is_gameplay_paused:
            bird_radius = game_state["object_size"] // 2
            game_state["projectile_x"] = max(
                bird_radius, min(mx, game_state["WIDTH"] - bird_radius)
            )
            game_state["projectile_y"] = max(
                bird_radius, min(my, game_state["HEIGHT"] - bird_radius)
            )

        # --- ИСПРАВЛЕНИЕ ОШИБКИ 1: Убрана проверка 'not is_gameplay_paused'
        if game_state["campaign_is_swapping"]:
            anim = game_state["campaign_swap_anim"]
            anim["progress"] += 0.15
            if anim["progress"] >= 1.0:
                anim["progress"] = 1.0
                r1, c1 = anim["tile1_pos"]
                r2, c2 = anim["tile2_pos"]
                board = game_state["campaign_board"]

                if not anim["reverse"]:
                    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
                    game_state["campaign_is_swapping"] = False
                    game_state["campaign_swap_anim"] = None
                    game_state["campaign_is_processing"] = True
                    game_state["campaign_board_state"] = "idle"
                else:
                    game_state["campaign_is_swapping"] = False
                    game_state["campaign_swap_anim"] = None

        # --- ИСПРАВЛЕНИЕ ОШИБКИ 2: Убрана проверка 'not is_gameplay_paused'
        if (
            game_state["game_mode"] == "campaign"
            and game_state["campaign_is_processing"]
        ):
            update_campaign_board(game_state)

        game_state = update_game_state(game_state)
        texts = game_state["texts"]

        if game_state.get("show_campaign_hint_popup"):
            popup_elements = draw_campaign_hint_popup(
                game_state["screen"], game_state["fonts"], game_state, mx, my, texts
            )
            if click_processed and popup_elements["close_btn"].collidepoint(mx, my):
                game_state["show_campaign_hint_popup"] = False
                game_state["paused"] = False
        elif game_state.get("show_training_popup"):
            popup_elements = draw_training_popup(
                game_state["screen"], game_state["fonts"], game_state, mx, my, texts
            )
            if click_processed and popup_elements["continue_btn"].collidepoint(mx, my):
                game_state["show_training_popup"] = False
                game_state["paused"] = False
                get_next_bird(game_state)
        elif game_state["show_hint_popup"]:
            popup_elements = draw_hint_popup(
                game_state["screen"], game_state["fonts"], game_state, mx, my, texts
            )
            if click_processed and popup_elements["close_btn"].collidepoint(mx, my):
                game_state["show_hint_popup"] = False
                game_state["paused"] = False
        elif in_any_menu:
            if game_state["menu"]:
                buttons = draw_menu(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if click_processed:
                    if buttons["start_btn"].collidepoint(mx, my):
                        if game_state["game_mode"] == "campaign":
                            game_state.update(
                                {"menu": False, "level_selection_menu": True}
                            )
                        else:
                            reset_game(game_state)
                            game_state["menu"] = False
                    elif buttons["profile_btn"].collidepoint(mx, my):
                        game_state.update({"profile_menu": True, "menu": False})
                    elif buttons["modes_btn"].collidepoint(mx, my):
                        game_state.update({"game_mode_menu": True, "menu": False})
                    elif buttons["set_btn"].collidepoint(mx, my):
                        game_state.update({"settings": True, "menu": False})
                    elif buttons["achievements_btn"].collidepoint(mx, my):
                        game_state.update(
                            {
                                "achievements_menu": True,
                                "menu": False,
                                "achievements_viewing_profile": game_state[
                                    "current_profile"
                                ],
                            }
                        )
                    elif buttons["birdpedia_btn"].collidepoint(mx, my):
                        game_state.update({"birdpedia_menu": True, "menu": False})
                    elif buttons["exit_btn"].collidepoint(mx, my):
                        running = False

            elif game_state.get("level_selection_menu"):
                buttons = draw_level_selection(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed:
                    if buttons["back_btn"].collidepoint(mx, my):
                        game_state.update({"level_selection_menu": False, "menu": True})
                    else:
                        for level_num, rect in buttons["levels"].items():
                            if rect.collidepoint(mx, my):
                                reset_game(game_state)
                                game_state["level_selection_menu"] = False
                                break

            elif game_state["profile_menu"]:
                elements = draw_profile_selection(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if game_state["show_profile_delete_confirm"]:
                    confirm_elements = draw_profile_delete_confirmation(
                        game_state["screen"],
                        game_state["fonts"],
                        game_state,
                        mx,
                        my,
                        texts,
                    )
                    if click_processed:
                        if confirm_elements["yes_btn"].collidepoint(mx, my):
                            profile_to_delete = game_state["profile_to_delete"]
                            if profile_to_delete in game_state["all_profiles_data"]:
                                del game_state["all_profiles_data"][profile_to_delete]
                                save_all_profiles_data(game_state["all_profiles_data"])
                                if game_state["current_profile"] == profile_to_delete:
                                    game_state["current_profile"] = "Guest"
                                    reset_game(game_state)
                            game_state.update(
                                {
                                    "show_profile_delete_confirm": False,
                                    "profile_to_delete": "",
                                }
                            )
                        elif confirm_elements["no_btn"].collidepoint(mx, my):
                            game_state.update(
                                {
                                    "show_profile_delete_confirm": False,
                                    "profile_to_delete": "",
                                }
                            )
                elif click_processed:
                    game_state["profile_input_active"] = False
                    if elements["input_box"].collidepoint(mx, my):
                        game_state["profile_input_active"] = True
                    elif elements["create_btn"].collidepoint(mx, my):
                        new_name = game_state["profile_input_text"].strip()
                        if new_name and new_name not in game_state["all_profiles_data"]:
                            game_state["all_profiles_data"][
                                new_name
                            ] = create_default_achievements()
                            save_all_profiles_data(game_state["all_profiles_data"])
                            game_state["current_profile"] = new_name
                            reset_game(game_state)
                            game_state["profile_input_text"] = ""
                    elif elements["back_btn"].collidepoint(mx, my):
                        if game_state["initial_profile_selection"]:
                            running = False
                        else:
                            game_state.update({"profile_menu": False, "menu": True})
                    else:
                        clicked_on_button = False
                        for name, rect in elements["delete_btns"].items():
                            if rect.collidepoint(mx, my):
                                game_state.update(
                                    {
                                        "show_profile_delete_confirm": True,
                                        "profile_to_delete": name,
                                    }
                                )
                                clicked_on_button = True
                                break
                        if not clicked_on_button:
                            for name, rect in elements["profiles"].items():
                                if rect.collidepoint(mx, my):
                                    game_state["current_profile"] = name
                                    reset_game(game_state)
                                    if game_state["initial_profile_selection"]:
                                        game_state.update(
                                            {
                                                "initial_profile_selection": False,
                                                "profile_menu": False,
                                                "menu": True,
                                            }
                                        )
                                    break
            elif game_state["settings"]:
                elements = draw_settings(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if click_processed:
                    if elements["sound_btn"].collidepoint(mx, my):
                        game_state.update(
                            {"settings": False, "sound_settings_menu": True}
                        )
                    elif elements["screen_btn"].collidepoint(mx, my):
                        game_state.update(
                            {"settings": False, "screen_settings_menu": True}
                        )
                    elif elements.get("language_btn") and elements[
                        "language_btn"
                    ].collidepoint(mx, my):
                        game_state.update({"settings": False, "language_menu": True})
                    elif elements["back_btn"].collidepoint(mx, my):
                        game_state.update({"settings": False, "menu": True})

            elif game_state["language_menu"]:
                elements = draw_language_selection(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed:
                    if (
                        elements["lang_ru_btn"].collidepoint(mx, my)
                        and game_state["language"] != "ru"
                    ):
                        game_state["language"] = "ru"
                        game_state["texts"] = LANGUAGES["ru"]
                    elif (
                        elements["lang_en_btn"].collidepoint(mx, my)
                        and game_state["language"] != "en"
                    ):
                        game_state["language"] = "en"
                        game_state["texts"] = LANGUAGES["en"]
                    elif elements["back_btn"].collidepoint(mx, my):
                        game_state.update({"language_menu": False, "settings": True})

            elif game_state["sound_settings_menu"]:
                elements = draw_sound_settings(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if click_processed:
                    if elements.get("music_slider") and elements[
                        "music_slider"
                    ].collidepoint(mx, my):
                        game_state["is_dragging_music_volume"] = True
                    elif elements.get("sfx_slider") and elements[
                        "sfx_slider"
                    ].collidepoint(mx, my):
                        game_state["is_dragging_sfx_volume"] = True
                    elif elements["prev_track_btn"].collidepoint(mx, my):
                        num_tracks = len(game_state["sounds"]["music_playlist"])
                        new_index = (
                            game_state["current_music_track_index"] - 1 + num_tracks
                        ) % num_tracks
                        play_music_track(game_state, new_index)
                    elif elements["next_track_btn"].collidepoint(mx, my):
                        num_tracks = len(game_state["sounds"]["music_playlist"])
                        new_index = (
                            game_state["current_music_track_index"] + 1
                        ) % num_tracks
                        play_music_track(game_state, new_index)
                    elif elements["back_btn"].collidepoint(mx, my):
                        game_state.update(
                            {"sound_settings_menu": False, "settings": True}
                        )
                if game_state["is_dragging_music_volume"]:
                    slider = elements["music_slider"]
                    new_volume = (mx - slider.x) / slider.width
                    game_state["music_volume"] = max(0.0, min(1.0, new_volume))
                    update_all_volumes(game_state)
                if game_state["is_dragging_sfx_volume"]:
                    slider = elements["sfx_slider"]
                    new_volume = (mx - slider.x) / slider.width
                    game_state["sfx_volume"] = max(0.0, min(1.0, new_volume))
                    update_all_volumes(game_state)

            elif game_state["screen_settings_menu"]:
                elements = draw_screen_settings(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed:
                    if elements.get("brightness_slider") and elements[
                        "brightness_slider"
                    ].collidepoint(mx, my):
                        game_state["is_dragging_brightness"] = True
                    elif elements.get("res_800_btn") and elements[
                        "res_800_btn"
                    ].collidepoint(mx, my):
                        game_state["pending_screen_mode"] = (800, 600)
                    elif elements.get("res_fullscreen_btn") and elements[
                        "res_fullscreen_btn"
                    ].collidepoint(mx, my):
                        game_state["pending_screen_mode"] = "fullscreen"
                    elif elements["back_btn"].collidepoint(mx, my):
                        apply_screen_settings(game_state)
                        game_state.update(
                            {"screen_settings_menu": False, "settings": True}
                        )
                if game_state["is_dragging_brightness"]:
                    slider = elements["brightness_slider"]
                    new_pos = (mx - slider.x) / slider.width
                    game_state["brightness_slider_pos"] = max(0.0, min(1.0, new_pos))

            elif game_state["game_mode_menu"]:
                elements = draw_game_mode_selection(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if click_processed:
                    if elements.get("difficulty_slider") and elements[
                        "difficulty_slider"
                    ].collidepoint(mx, my):
                        game_state["is_dragging_difficulty"] = True
                    elif elements["classic_btn"].collidepoint(mx, my):
                        game_state["game_mode"] = "classic"
                    elif elements["sharpshooter_btn"].collidepoint(mx, my):
                        game_state["game_mode"] = "sharpshooter"
                    elif elements["obstacle_btn"].collidepoint(mx, my):
                        game_state["game_mode"] = "obstacle"
                    elif elements.get("campaign_btn") and elements[
                        "campaign_btn"
                    ].collidepoint(mx, my):
                        game_state["game_mode"] = "campaign"
                    elif elements["training_btn"].collidepoint(mx, my):
                        game_state["game_mode"] = "training"
                    elif elements["developer_btn"].collidepoint(mx, my):
                        game_state["game_mode"] = "developer"
                    elif elements["back_btn"].collidepoint(mx, my):
                        game_state.update({"game_mode_menu": False, "menu": True})
                if game_state["is_dragging_difficulty"]:
                    slider = elements["difficulty_slider"]
                    rel_x = mx - slider.x
                    if rel_x < slider.width / 3:
                        game_state["difficulty"] = "easy"
                    elif rel_x < 2 * slider.width / 3:
                        game_state["difficulty"] = "medium"
                    else:
                        game_state["difficulty"] = "hard"

            elif game_state["achievements_menu"]:
                elements = draw_achievements(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if not game_state["show_achievements_reset_confirm"]:
                    if click_processed:
                        if elements["back_btn"].collidepoint(mx, my):
                            game_state.update(
                                {"achievements_menu": False, "menu": True}
                            )
                        elif elements["reset_btn"].collidepoint(mx, my):
                            game_state["show_achievements_reset_confirm"] = True
                        else:
                            for name, rect in elements["profile_btns"].items():
                                if rect.collidepoint(mx, my):
                                    game_state["achievements_viewing_profile"] = name
                                    break
                            for diff, rect in elements["difficulty_btns"].items():
                                if rect.collidepoint(mx, my):
                                    game_state["achievements_viewing_difficulty"] = diff
                                    break
                if game_state["show_achievements_reset_confirm"]:
                    confirm_elements = draw_achievements_reset_confirmation(
                        game_state["screen"],
                        game_state["fonts"],
                        game_state,
                        mx,
                        my,
                        texts,
                    )
                    if click_processed:
                        if confirm_elements["yes_btn"].collidepoint(mx, my):
                            profile_to_reset = game_state[
                                "achievements_viewing_profile"
                            ]
                            game_state["all_profiles_data"][
                                profile_to_reset
                            ] = create_default_achievements()
                            if profile_to_reset == game_state["current_profile"]:
                                game_state.update(
                                    game_state["all_profiles_data"][profile_to_reset]
                                )
                            game_state["show_achievements_reset_confirm"] = False
                        elif confirm_elements["no_btn"].collidepoint(mx, my):
                            game_state["show_achievements_reset_confirm"] = False

            elif game_state["birdpedia_menu"]:
                elements = draw_birdpedia_menu(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed:
                    if elements["back_btn"].collidepoint(mx, my):
                        game_state.update({"birdpedia_menu": False, "menu": True})
                    else:
                        for item_name, item_rect in elements.items():
                            if item_name != "back_btn" and item_rect.collidepoint(
                                mx, my
                            ):
                                game_state.update(
                                    {
                                        "birdpedia_item_selected": item_name,
                                        "birdpedia_menu": False,
                                        "birdpedia_detail_menu": True,
                                    }
                                )
                                break

            elif game_state["birdpedia_detail_menu"]:
                elements = draw_birdpedia_detail_screen(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed and elements["back_btn"].collidepoint(mx, my):
                    game_state.update(
                        {
                            "birdpedia_detail_menu": False,
                            "birdpedia_menu": True,
                            "birdpedia_item_selected": None,
                        }
                    )

        else:
            if game_state["game_mode"] == "campaign":
                campaign_buttons = draw_campaign_board(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    mx,
                    my,
                    texts,
                )
                if game_state["campaign_level_complete"] and click_processed:
                    if campaign_buttons["restart_btn"].collidepoint(mx, my):
                        reset_game(game_state)
                    elif campaign_buttons["exit_btn"].collidepoint(mx, my):
                        game_state["menu"] = True
                        game_state["campaign_level_complete"] = False

            elif not game_state["training_complete"]:
                if game_state["bird_is_jumping"] and not is_gameplay_paused:
                    game_state["jump_progress"] += 0.05
                    progress = min(1.0, game_state["jump_progress"])
                    start_x, start_y = game_state["jump_start_pos"]
                    end_x, end_y = game_state["sling_x"], game_state["sling_y"]
                    current_x = start_x + (end_x - start_x) * progress
                    parabola_offset = (
                        150 * game_state["scale_factor"] * math.sin(progress * math.pi)
                    )
                    current_y = start_y + (end_y - start_y) * progress - parabola_offset
                    if game_state["jump_bird_img"]:
                        game_state["screen"].blit(
                            game_state["jump_bird_img"],
                            (
                                current_x - game_state["object_size"] // 2,
                                current_y - game_state["object_size"] // 2,
                            ),
                        )
                    if game_state["jump_progress"] >= 1.0:
                        game_state["bird_is_jumping"] = False
                        game_state["current_bird_img"] = game_state["jump_bird_img"]
                        game_state["jump_bird_img"] = None
                        game_state["projectile_x"] = game_state["sling_x"]
                        game_state["projectile_y"] = game_state["sling_y"]
                        game_state["jump_progress"] = 0

                draw_gameplay(
                    game_state["screen"],
                    game_state["images"],
                    game_state["fonts"],
                    game_state,
                    texts,
                )

                for pig in game_state["defeated_pigs"][:]:
                    if not pig["on_ground"]:
                        pig["vy"] += game_state["gravity"]
                        pig["y"] += pig["vy"]
                        if (
                            pig["y"]
                            >= game_state["GROUND_LEVEL"]
                            - game_state["object_size"] // 2
                        ):
                            pig["y"] = (
                                game_state["GROUND_LEVEL"]
                                - game_state["object_size"] // 2
                            )
                            pig["on_ground"] = True
                            pig["timer"] = 15
                            create_dust_particle(
                                game_state["dust_particles"],
                                pig["x"],
                                pig["y"] + game_state["object_size"] // 2,
                                count=30,
                            )
                    if pig["on_ground"]:
                        pig["timer"] -= 1
                        if pig["timer"] <= 0:
                            game_state["defeated_pigs"].remove(pig)
                            if game_state["game_mode"] not in [
                                "training",
                                "developer",
                                "campaign",
                            ]:
                                existing_objects = (
                                    game_state["targets"] + game_state["obstacles"]
                                )
                                if game_state["game_mode"] != "sharpshooter":
                                    while True:
                                        new_target = create_target(
                                            game_state["WIDTH"],
                                            game_state["HEIGHT"],
                                            game_state["object_size"],
                                        )
                                        if not any(
                                            new_target.inflate(10, 10).colliderect(obj)
                                            for obj in existing_objects
                                        ):
                                            game_state["targets"].append(new_target)
                                            add_new_speed(game_state)
                                            break
                                else:
                                    game_state["targets"].append(
                                        create_target(
                                            game_state["WIDTH"],
                                            game_state["HEIGHT"],
                                            game_state["object_size"],
                                        )
                                    )
                                    add_new_speed(game_state)
                                    game_state["target_timer_start"] = time.time()
                    pig_rect = pygame.Rect(
                        pig["x"] - game_state["object_size"] // 2,
                        pig["y"] - game_state["object_size"] // 2,
                        game_state["object_size"],
                        game_state["object_size"],
                    )
                    game_state["screen"].blit(
                        game_state["images"]["target_defeated_img"], pig_rect
                    )

                if game_state["is_tumbling"]:
                    if not is_gameplay_paused:
                        game_state["tumble_timer"] -= 1
                        game_state["projectile_x"] += game_state["velocity_x"]
                        game_state["projectile_angle"] += game_state["angular_velocity"]
                        game_state["projectile_rect"].centerx = int(
                            game_state["projectile_x"]
                        )
                        game_state["velocity_x"] *= 0.95
                        game_state["angular_velocity"] *= 0.99
                        if abs(game_state["velocity_x"]) < 0.1:
                            game_state["velocity_x"] = 0
                        if (
                            game_state["tumble_timer"] <= 0
                            or game_state["velocity_x"] == 0
                        ):
                            game_state["is_tumbling"] = False
                            if not game_state["current_shot_hit"] and game_state[
                                "game_mode"
                            ] not in ["developer", "training", "campaign"]:
                                game_state["lives"] -= 1
                                game_state["combo"] = 0
                            get_next_bird(game_state)

                elif (
                    game_state["is_moving"]
                    and not game_state["game_over"]
                    and not is_gameplay_paused
                ):
                    if game_state["small_birds"]:
                        game_state["is_moving"] = False
                    game_state["projectile_x"] += game_state["velocity_x"]
                    game_state["projectile_y"] += game_state["velocity_y"]
                    game_state["velocity_y"] += game_state["gravity"]
                    game_state["projectile_rect"].center = (
                        int(game_state["projectile_x"]),
                        int(game_state["projectile_y"]),
                    )
                    if (
                        game_state["current_bird_img"]
                        == game_state["images"]["bird_imgs"][4]
                    ):
                        game_state["projectile_angle"] -= 15
                    game_state["last_shot_path"].append(
                        (game_state["projectile_x"], game_state["projectile_y"])
                    )
                    if random.random() < 0.5:
                        create_trail_particle(
                            game_state["trail_particles"],
                            game_state["projectile_x"],
                            game_state["projectile_y"],
                        )

                    if (
                        game_state["projectile_y"]
                        >= game_state["GROUND_LEVEL"] - game_state["object_size"] // 2
                        and not game_state["small_birds"]
                    ):
                        game_state["is_moving"] = False
                        game_state["is_tumbling"] = True
                        game_state["tumble_timer"] = 25
                        game_state["projectile_y"] = (
                            game_state["GROUND_LEVEL"] - game_state["object_size"] // 2
                        )
                        game_state["velocity_y"] = 0
                        game_state["angular_velocity"] = game_state["velocity_x"] * -1.5
                        create_dust_particle(
                            game_state["dust_particles"],
                            game_state["projectile_x"],
                            game_state["GROUND_LEVEL"],
                            count=20,
                        )

                    elif (
                        game_state["projectile_y"] > game_state["HEIGHT"] + 50
                        or game_state["projectile_x"] < -50
                        or game_state["projectile_x"] > game_state["WIDTH"] + 50
                    ) and not game_state["small_birds"]:
                        if not game_state["current_shot_hit"] and game_state[
                            "game_mode"
                        ] not in ["developer", "training", "campaign"]:
                            game_state["lives"] -= 1
                            game_state["combo"] = 0
                        get_next_bird(game_state)

                    for i, target in reversed(list(enumerate(game_state["targets"]))):
                        if game_state["projectile_rect"].colliderect(target):
                            try:
                                bird_index = game_state["images"]["bird_imgs"].index(
                                    game_state["current_bird_img"]
                                )
                            except (ValueError, TypeError):
                                bird_index = 0
                            if bird_index == 1:
                                game_state["current_shot_hit"] = True
                                explosion_center = target.center
                                game_state["screen_shake"] = 15
                                if game_state["sound_on"]:
                                    game_state["sounds"]["explosion_sound"].play()
                                game_state["explosion_center"] = explosion_center
                                game_state["explosion_active"] = True
                                game_state["explosion_frames"] = game_state[
                                    "MAX_EXPLOSION_FRAMES"
                                ]
                                targets_to_remove = [
                                    t
                                    for t in game_state["targets"]
                                    if math.hypot(
                                        t.centerx - explosion_center[0],
                                        t.centery - explosion_center[1],
                                    )
                                    <= game_state["EXPLOSION_RADIUS"]
                                ]
                                num_destroyed = 0
                                for t_to_remove in targets_to_remove:
                                    try:
                                        idx = game_state["targets"].index(t_to_remove)
                                        pig_to_defeat = game_state["targets"].pop(idx)
                                        game_state["defeated_pigs"].append(
                                            {
                                                "x": pig_to_defeat.centerx,
                                                "y": pig_to_defeat.centery,
                                                "vy": random.uniform(-2, 0),
                                                "on_ground": False,
                                                "timer": -1,
                                            }
                                        )
                                        if game_state["target_speeds"]:
                                            game_state["target_speeds"].pop(idx)
                                        num_destroyed += 1
                                    except (ValueError, IndexError):
                                        continue
                                if num_destroyed > 0:
                                    game_state["score"] += num_destroyed
                                    game_state["combo"] += num_destroyed
                                    update_max_combo(
                                        game_state, game_state["current_profile"]
                                    )
                                get_next_bird(game_state)
                                break
                            else:
                                create_feather_explosion(
                                    game_state["feather_particles"],
                                    target.centerx,
                                    target.centery,
                                    bird_index,
                                )
                                game_state["current_shot_hit"] = True
                                game_state["score"] += 1
                                game_state["combo"] += 1
                                update_max_combo(
                                    game_state, game_state["current_profile"]
                                )
                                if game_state["sound_on"]:
                                    game_state["sounds"]["hit_sound"].play()
                                pig_to_defeat = game_state["targets"].pop(i)
                                game_state["defeated_pigs"].append(
                                    {
                                        "x": pig_to_defeat.centerx,
                                        "y": pig_to_defeat.centery,
                                        "vy": -abs(game_state["velocity_y"] * 0.2),
                                        "on_ground": False,
                                        "timer": -1,
                                    }
                                )
                                if game_state["target_speeds"]:
                                    game_state["target_speeds"].pop(i)
                                get_next_bird(game_state)
                                break

                    if game_state["game_mode"] == "obstacle":
                        for i, obstacle in reversed(
                            list(enumerate(game_state["obstacles"]))
                        ):
                            if game_state["projectile_rect"].colliderect(obstacle):
                                create_brick_shatter(
                                    game_state["dust_particles"],
                                    obstacle.centerx,
                                    obstacle.centery,
                                )
                                game_state["obstacles"].pop(i)
                                game_state["obstacle_speeds"].pop(i)
                                game_state["velocity_x"] *= 0.5
                                game_state["velocity_y"] *= 0.5
                                if game_state["sound_on"]:
                                    game_state["sounds"]["brick_sound"].play()
                                break

                is_any_small_bird_active = False
                for bird in game_state["small_birds"]:
                    if bird["active"]:
                        is_any_small_bird_active = True
                        if bird.get("is_tumbling"):
                            if not is_gameplay_paused:
                                bird["tumble_timer"] -= 1
                                bird["x"] += bird["vx"]
                                bird["angle"] += bird["angular_velocity"]
                                bird["rect"].centerx = int(bird["x"])
                                bird["vx"] *= 0.95
                                bird["angular_velocity"] *= 0.99
                                if abs(bird["vx"]) < 0.1:
                                    bird["vx"] = 0
                                if bird["tumble_timer"] <= 0 or bird["vx"] == 0:
                                    bird["active"] = False
                        elif not is_gameplay_paused:
                            bird["x"] += bird["vx"]
                            bird["y"] += bird["vy"]
                            bird["vy"] += game_state["gravity"]
                            bird["rect"].center = (bird["x"], bird["y"])
                            if (
                                bird["y"]
                                >= game_state["GROUND_LEVEL"]
                                - game_state["small_object_size"] // 2
                            ):
                                bird["is_tumbling"] = True
                                bird["tumble_timer"] = 60
                                bird["y"] = (
                                    game_state["GROUND_LEVEL"]
                                    - game_state["small_object_size"] // 2
                                )
                                bird["vy"] = 0
                                bird["angular_velocity"] = bird["vx"] * -1.5
                                create_dust_particle(
                                    game_state["dust_particles"],
                                    bird["x"],
                                    game_state["GROUND_LEVEL"],
                                    count=10,
                                )
                            if game_state["game_mode"] == "obstacle":
                                for i, obstacle in reversed(
                                    list(enumerate(game_state["obstacles"]))
                                ):
                                    if bird["rect"].colliderect(obstacle):
                                        create_brick_shatter(
                                            game_state["dust_particles"],
                                            obstacle.centerx,
                                            obstacle.centery,
                                        )
                                        bird["vx"] *= 0.5
                                        bird["vy"] *= 0.5
                                        game_state["obstacles"].pop(i)
                                        game_state["obstacle_speeds"].pop(i)
                                        if game_state["sound_on"]:
                                            game_state["sounds"]["brick_sound"].play()
                                        break
                            for i, target in reversed(
                                list(enumerate(game_state["targets"]))
                            ):
                                if bird["rect"].colliderect(target):
                                    create_feather_explosion(
                                        game_state["feather_particles"],
                                        target.centerx,
                                        target.centery,
                                        3,
                                    )
                                    if not game_state["current_shot_hit"]:
                                        game_state["current_shot_hit"] = True
                                    game_state["score"] += 1
                                    game_state["combo"] += 1
                                    update_max_combo(
                                        game_state, game_state["current_profile"]
                                    )
                                    pig_to_defeat = game_state["targets"].pop(i)
                                    game_state["defeated_pigs"].append(
                                        {
                                            "x": pig_to_defeat.centerx,
                                            "y": pig_to_defeat.centery,
                                            "vy": 0,
                                            "on_ground": False,
                                            "timer": -1,
                                        }
                                    )
                                    if game_state["target_speeds"]:
                                        game_state["target_speeds"].pop(i)
                                    bird["active"] = False
                                    break

                if (
                    not is_any_small_bird_active
                    and game_state["small_birds"]
                    and not game_state["is_moving"]
                    and not game_state["is_tumbling"]
                ):
                    if not game_state["current_shot_hit"] and game_state[
                        "game_mode"
                    ] not in ["developer", "training", "campaign"]:
                        game_state["lives"] -= 1
                        game_state["combo"] = 0
                    game_state["small_birds"] = []
                    get_next_bird(game_state)

                if not game_state["bird_is_jumping"]:
                    if (
                        game_state["is_moving"] or game_state["is_tumbling"]
                    ) and game_state["current_bird_img"]:
                        if (
                            game_state["current_bird_img"]
                            == game_state["images"]["bird_imgs"][4]
                            or game_state["is_tumbling"]
                        ):
                            rotated_bird = pygame.transform.rotate(
                                game_state["current_bird_img"],
                                game_state["projectile_angle"],
                            )
                            new_rect = rotated_bird.get_rect(
                                center=game_state["projectile_rect"].center
                            )
                            game_state["screen"].blit(rotated_bird, new_rect)
                        else:
                            game_state["screen"].blit(
                                game_state["current_bird_img"],
                                game_state["projectile_rect"],
                            )
                    elif (
                        not game_state["is_moving"]
                        and not game_state["is_tumbling"]
                        and game_state["current_bird_img"]
                    ):
                        game_state["screen"].blit(
                            game_state["current_bird_img"],
                            (
                                game_state["projectile_x"]
                                - game_state["object_size"] // 2,
                                game_state["projectile_y"]
                                - game_state["object_size"] // 2,
                            ),
                        )

                for bird in game_state["small_birds"]:
                    if bird["active"]:
                        rotated_bird = pygame.transform.rotate(
                            game_state["images"]["small_bird_img"], bird["angle"]
                        )
                        new_rect = rotated_bird.get_rect(center=bird["rect"].center)
                        game_state["screen"].blit(rotated_bird, new_rect)

                for i, target in enumerate(game_state["targets"]):
                    game_state["screen"].blit(
                        game_state["images"]["target_img"], target
                    )
                    if (
                        not is_gameplay_paused
                        and game_state["game_mode"] != "sharpshooter"
                        and len(game_state["target_speeds"]) > i
                    ):
                        target.x += game_state["target_speeds"][i][0]
                        target.y += game_state["target_speeds"][i][1]
                        if not (0 < target.left and target.right < game_state["WIDTH"]):
                            game_state["target_speeds"][i] = (
                                -game_state["target_speeds"][i][0],
                                game_state["target_speeds"][i][1],
                            )
                        if not (
                            0 < target.top and target.bottom < game_state["HEIGHT"]
                        ):
                            game_state["target_speeds"][i] = (
                                game_state["target_speeds"][i][0],
                                -game_state["target_speeds"][i][1],
                            )
                if game_state["game_mode"] == "obstacle":
                    for i, obstacle in enumerate(game_state["obstacles"]):
                        game_state["screen"].blit(
                            game_state["images"]["brick_img"], obstacle
                        )

                texts = game_state["texts"]
                if game_state["game_mode"] != "sharpshooter":
                    score_surf, _ = draw_text(
                        f"{texts['score_colon']} {game_state['score']}",
                        game_state["fonts"]["small_font"],
                        (0, 0, 0),
                    )
                    game_state["screen"].blit(score_surf, (10, 10))
                    lives_text = (
                        texts["lives_infinite"]
                        if game_state["lives"] == float("inf")
                        else f"{texts['lives_colon']} {game_state['lives']}"
                    )
                    lives_surf, _ = draw_text(
                        lives_text, game_state["fonts"]["small_font"], (0, 0, 0)
                    )
                    game_state["screen"].blit(lives_surf, (10, 50))
                    combo_surf, _ = draw_text(
                        f"{texts['combo_colon']} {game_state['combo']}",
                        game_state["fonts"]["small_font"],
                        (0, 0, 0),
                    )
                    game_state["screen"].blit(combo_surf, (10, 90))
                else:
                    if (
                        not is_gameplay_paused
                        and not game_state["game_over"]
                        and len(game_state["targets"]) > 0
                    ):
                        time_left = max(
                            0,
                            game_state["target_duration"]
                            - (time.time() - game_state["target_timer_start"]),
                        )
                        if time_left <= 0:
                            game_state["targets"].pop(0)
                            if game_state["target_speeds"]:
                                game_state["target_speeds"].pop(0)
                            game_state["lives"] -= 1
                            game_state["combo"] = 0
                            if game_state["lives"] > 0:
                                game_state["targets"].append(
                                    create_target(
                                        game_state["WIDTH"],
                                        game_state["HEIGHT"],
                                        game_state["object_size"],
                                    )
                                )
                                add_new_speed(game_state)
                                game_state["target_timer_start"] = time.time()
                            else:
                                game_state["game_over"] = True
                    else:
                        time_left = 0

                    timer_surf, _ = draw_text(
                        f"{texts['time_colon']} {time_left:.1f}s",
                        game_state["fonts"]["small_font"],
                        (255, 0, 0),
                    )
                    game_state["screen"].blit(timer_surf, (10, 10))
                    score_surf, _ = draw_text(
                        f"{texts['score_colon']} {game_state['score']}",
                        game_state["fonts"]["small_font"],
                        (0, 0, 0),
                    )
                    game_state["screen"].blit(score_surf, (10, 50))
                    combo_surf, _ = draw_text(
                        f"{texts['combo_colon']} {game_state['combo']}",
                        game_state["fonts"]["small_font"],
                        (0, 0, 0),
                    )
                    game_state["screen"].blit(combo_surf, (10, 90))
                    lives_text = (
                        texts["lives_infinite"]
                        if game_state["lives"] == float("inf")
                        else f"{texts['lives_colon']} {game_state['lives']}"
                    )
                    lives_surf, _ = draw_text(
                        lives_text, game_state["fonts"]["small_font"], (0, 0, 0)
                    )
                    game_state["screen"].blit(lives_surf, (10, 130))

                if game_state["lives"] <= 0:
                    game_state["game_over"] = True
            elif game_state["training_complete"]:
                confirm_elements = draw_training_complete_screen(
                    game_state["screen"], game_state["fonts"], game_state, mx, my, texts
                )
                if click_processed:
                    if confirm_elements["restart_btn"].collidepoint(mx, my):
                        reset_game(game_state)
                    elif confirm_elements["exit_btn"].collidepoint(mx, my):
                        game_state.update({"training_complete": False, "menu": True})

        if game_state["paused"]:
            s = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            s.fill((0, 0, 0, 128))
            game_state["screen"].blit(s, (0, 0))
            if (
                not game_state["show_hint_popup"]
                and not game_state.get("show_training_popup")
                and not game_state.get("show_campaign_hint_popup")
            ):
                pause_surf, rect = draw_text(
                    texts["pause"], game_state["fonts"]["large_font"], (255, 255, 255)
                )
                rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
                game_state["screen"].blit(pause_surf, rect)

        draw_particles(game_state["screen"], game_state["trail_particles"])
        draw_particles(game_state["screen"], game_state["dust_particles"])
        draw_particles(game_state["screen"], game_state["spark_particles"])
        if not is_gameplay_paused:
            update_and_draw_feathers(
                game_state["screen"],
                game_state["feather_particles"],
                game_state["images"]["feather_imgs"],
            )

        brightness = game_state["brightness_slider_pos"]
        if brightness < 1.0:
            overlay = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            alpha = int(255 * (1.0 - brightness))
            overlay.fill((0, 0, 0, alpha))
            game_state["screen"].blit(overlay, (0, 0))

        if game_state["images"].get("cursor_img"):
            game_state["screen"].blit(game_state["images"]["cursor_img"], (mx, my))
        pygame.display.flip()
        game_state["clock"].tick(60)

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
