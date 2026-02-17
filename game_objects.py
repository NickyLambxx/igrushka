import pygame
import math
import time
import random
from achievements import get_achievements_for_profile
from utils import (
    create_trail_particle,
    create_dust_particle,
    create_spark_particle,
    create_target,
    create_obstacle,
    update_particles,
)
from settings import (
    LIVES,
    SPEED_MULTIPLIER,
    TARGET_DURATION,
    load_images,
    load_fonts,
    EXPLOSION_RADIUS,
)
from entities import MainBird, Target, Obstacle, SmallBird, DefeatedPig

CAMPAIGN_GRID_SIZE = 7
SCORE_MAP = {3: 30, 4: 50, 5: 100, 6: 300, 7: 1000}
SQUARE_SCORE = 50
BASE_WIDTH = 800.0


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


def get_next_bird(game_state):
    mb = game_state.get("main_bird")
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
                if mb:
                    mb.image = None
                return
            else:
                game_state["show_training_popup"] = True
                game_state["training_popup_text"] = game_state["texts"][
                    "training_descriptions"
                ][game_state["training_bird_index"]]
                game_state["current_bird_img"] = None
                if mb:
                    mb.image = None
                return
        idx = game_state["training_bird_index"]
        game_state["current_bird_img"] = game_state["images"]["bird_imgs"][idx]
        if mb:
            mb.set_image(game_state["current_bird_img"], idx)
            mb.reset_to_sling()
    else:
        if game_state["lives"] <= 0 or not game_state["bird_queue"]:
            game_state["game_over"] = True
            game_state["current_bird_img"] = None
            if mb:
                mb.image = None
            return
        game_state["current_shot_hit"] = False
        bird_img = game_state["bird_queue"].pop(0)
        game_state["current_bird_img"] = bird_img
        game_state["bird_queue"].append(
            random.choice(game_state["images"]["bird_imgs"])
        )
        try:
            idx = game_state["images"]["bird_imgs"].index(bird_img)
        except:
            idx = 0
        if mb:
            mb.jump_start_pos = (
                int(40 * game_state["scale_factor"]),
                game_state["GROUND_LEVEL"] - game_state["object_size"] * 0.9,
            )
            mb.jump_image = bird_img
            mb.type_index = idx
            mb.state = "jumping"
            mb.jump_progress = 0


def update_max_combo(game_state, profile_name):
    if game_state["game_mode"] not in ["classic", "sharpshooter", "obstacle"]:
        return
    key = f"max_combo_{game_state['game_mode']}_{game_state['difficulty']}"
    cp_data = game_state["all_profiles_data"][profile_name]
    if game_state["combo"] > cp_data.get(key, 0):
        cp_data[key] = game_state["combo"]
        if profile_name == game_state["current_profile"]:
            game_state[key] = game_state["combo"]


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
    t1, t2 = board[r1][c1], board[r2][c2]
    if t1 is None or t2 is None:
        game_state["campaign_selected_tile"] = None
        return
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
    will_match = check_matches(board)
    board[r1][c1], board[r2][c2] = t1, t2
    game_state["campaign_is_swapping"] = True
    game_state["campaign_swap_anim"] = {
        "tile1_pos": pos1,
        "tile2_pos": pos2,
        "tile1_type": t1,
        "tile2_type": t2,
        "progress": 0.0,
        "reverse": not will_match,
    }
    game_state["campaign_selected_tile"] = None


def find_and_score_matches(board):
    total_score, all_matched_tiles = 0, set()
    for r in range(CAMPAIGN_GRID_SIZE):
        for c in range(CAMPAIGN_GRID_SIZE):
            if (r, c) in all_matched_tiles:
                continue
            if c < CAMPAIGN_GRID_SIZE - 2 and board[r][c] is not None:
                m_type = board[r][c]
                line_len = 1
                for i in range(1, CAMPAIGN_GRID_SIZE - c):
                    if board[r][c + i] == m_type:
                        line_len += 1
                    else:
                        break
                if line_len >= 3:
                    total_score += SCORE_MAP.get(line_len, 1000)
                    for i in range(line_len):
                        all_matched_tiles.add((r, c + i))
            if r < CAMPAIGN_GRID_SIZE - 2 and board[r][c] is not None:
                m_type = board[r][c]
                line_len = 1
                for i in range(1, CAMPAIGN_GRID_SIZE - r):
                    if board[r + i][c] == m_type:
                        line_len += 1
                    else:
                        break
                if line_len >= 3:
                    total_score += SCORE_MAP.get(line_len, 1000)
                    for i in range(line_len):
                        all_matched_tiles.add((r + i, c))

    for r in range(CAMPAIGN_GRID_SIZE - 1):
        for c in range(CAMPAIGN_GRID_SIZE - 1):
            tile = board[r][c]
            if (
                tile is not None
                and tile == board[r + 1][c]
                and tile == board[r][c + 1]
                and tile == board[r + 1][c + 1]
            ):
                sq = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
                if not sq.intersection(all_matched_tiles):
                    total_score += SQUARE_SCORE
                    all_matched_tiles.update(sq)
    return total_score, list(all_matched_tiles)


def check_matches(board):
    for r in range(CAMPAIGN_GRID_SIZE):
        for c in range(CAMPAIGN_GRID_SIZE - 2):
            if (
                board[r][c] is not None
                and board[r][c] == board[r][c + 1] == board[r][c + 2]
            ):
                return True
    for c in range(CAMPAIGN_GRID_SIZE):
        for r in range(CAMPAIGN_GRID_SIZE - 2):
            if (
                board[r][c] is not None
                and board[r][c] == board[r + 1][c] == board[r + 2][c]
            ):
                return True
    return False


def create_campaign_board(game_state):
    b_types_count = len(game_state["images"]["bird_imgs"])
    while True:
        board = [
            [random.randint(0, b_types_count - 1) for _ in range(CAMPAIGN_GRID_SIZE)]
            for _ in range(CAMPAIGN_GRID_SIZE)
        ]
        if not check_matches(board):
            return board


def find_and_start_clearing_matches(game_state):
    score, matches = find_and_score_matches(game_state["campaign_board"])
    if not matches:
        game_state["campaign_is_processing"] = False
        game_state["campaign_board_state"] = "idle"
        return False
    game_state["campaign_score"] += score
    game_state["campaign_board_state"] = "clearing"
    game_state["campaign_matched_tiles"] = matches
    game_state["campaign_clear_progress"] = 0.0
    if game_state["campaign_score"] >= game_state["campaign_target_score"]:
        game_state["campaign_level_complete"] = True
    return True


def process_tile_clearing(dt, game_state):
    dt_factor = dt * 60.0
    game_state["campaign_clear_progress"] += 0.1 * dt_factor
    if game_state["campaign_clear_progress"] >= 1.0:
        board = game_state["campaign_board"]
        for r, c in game_state["campaign_matched_tiles"]:
            board[r][c] = None
        game_state["campaign_matched_tiles"] = []
        game_state["campaign_board_state"] = "falling"
        prepare_falling_tiles(game_state)


def prepare_falling_tiles(game_state):
    board = game_state["campaign_board"]
    game_state["campaign_falling_tiles"] = []
    for c in range(CAMPAIGN_GRID_SIZE):
        e_spots = 0
        for r in range(CAMPAIGN_GRID_SIZE - 1, -1, -1):
            if board[r][c] is None:
                e_spots += 1
            elif e_spots > 0:
                tile_type = board[r][c]
                game_state["campaign_falling_tiles"].append(
                    {
                        "type": tile_type,
                        "start_pos": (r, c),
                        "end_pos": (r + e_spots, c),
                        "progress": 0.0,
                    }
                )
                board[r + e_spots][c] = tile_type
                board[r][c] = None


def process_tile_falling(dt, game_state):
    if not game_state.get("campaign_falling_tiles"):
        game_state["campaign_board_state"] = "refilling"
        prepare_refill_tiles(game_state)
        return
    all_done = True
    for t in game_state["campaign_falling_tiles"]:
        if t["progress"] < 1.0:
            all_done = False
            t["progress"] += 0.15 * (dt * 60.0)
            t["progress"] = min(t["progress"], 1.0)
    if all_done:
        game_state["campaign_falling_tiles"] = []
        game_state["campaign_board_state"] = "refilling"
        prepare_refill_tiles(game_state)


def prepare_refill_tiles(game_state):
    board, game_state["campaign_refilling_tiles"] = game_state["campaign_board"], []
    for c in range(CAMPAIGN_GRID_SIZE):
        empty = 0
        for r in range(CAMPAIGN_GRID_SIZE):
            if board[r][c] is None:
                empty += 1
                new_type = random.randint(0, len(game_state["images"]["bird_imgs"]) - 1)
                board[r][c] = new_type
                game_state["campaign_refilling_tiles"].append(
                    {
                        "type": new_type,
                        "start_y_offset": -empty,
                        "end_pos": (r, c),
                        "progress": 0.0,
                    }
                )


def process_tile_refilling(dt, game_state):
    if not game_state.get("campaign_refilling_tiles"):
        game_state["campaign_board_state"] = "idle"
        find_and_start_clearing_matches(game_state)
        return
    all_done = True
    for t in game_state["campaign_refilling_tiles"]:
        if t["progress"] < 1.0:
            all_done = False
            t["progress"] += 0.15 * (dt * 60.0)
            t["progress"] = min(t["progress"], 1.0)
    if all_done:
        game_state["campaign_refilling_tiles"] = []
        game_state["campaign_board_state"] = "idle"
        if not find_and_start_clearing_matches(game_state):
            game_state["campaign_is_processing"] = False


def update_campaign_board(dt, game_state):
    board_state = game_state.get("campaign_board_state", "idle")
    if board_state == "clearing":
        process_tile_clearing(dt, game_state)
    elif board_state == "falling":
        process_tile_falling(dt, game_state)
    elif board_state == "refilling":
        process_tile_refilling(dt, game_state)
    elif board_state == "idle":
        find_and_start_clearing_matches(game_state)


def split_bird(game_state):
    bird = game_state["main_bird"]
    sz = game_state["small_object_size"]
    img = game_state["images"]["small_bird_img"]
    for i in range(3):
        angle = math.radians(120 * i)
        game_state["small_birds"].add(
            SmallBird(
                bird.x,
                bird.y,
                bird.vx + math.cos(angle) * 3,
                bird.vy + math.sin(angle) * 3,
                sz,
                img,
            )
        )
    if game_state["sound_on"] and game_state["sounds"].get("split_sound"):
        try:
            game_state["sounds"]["split_sound"].play()
        except:
            pass
    bird.split_available = False
    bird.state = "dead"


def activate_boomerang(game_state):
    bird = game_state["main_bird"]
    bird.vx = -15
    bird.vy = 0
    bird.boomerang_available = False
    if game_state["sound_on"] and game_state["sounds"].get("boomerang_sound"):
        try:
            game_state["sounds"]["boomerang_sound"].play()
        except:
            pass


def reset_game(game_state):
    game_state.update(
        get_achievements_for_profile(
            game_state["all_profiles_data"], game_state["current_profile"]
        )
    )
    game_state["bird_queue"] = []
    num_targets = 0
    num_obstacles = 0

    if game_state["game_mode"] == "campaign":
        game_state.update(
            {
                "lives": float("inf"),
                "campaign_board": create_campaign_board(game_state),
                "campaign_score": 0,
                "campaign_level_complete": False,
                "campaign_selected_tile": None,
                "campaign_is_processing": False,
                "campaign_board_state": "idle",
            }
        )
    elif game_state["game_mode"] == "training":
        game_state.update(
            {
                "training_complete": False,
                "show_training_popup": True,
                "training_bird_index": 0,
                "training_shots_fired": 0,
                "training_popup_text": game_state["texts"]["training_descriptions"][0],
                "current_bird_img": None,
                "lives": float("inf"),
            }
        )
        num_targets = 3
    else:
        game_state["bird_queue"] = [
            random.choice(game_state["images"]["bird_imgs"]) for _ in range(3)
        ]
        game_state["current_bird_img"] = game_state["bird_queue"].pop(0)
        if game_state["game_mode"] == "developer":
            game_state["lives"] = float("inf")
        elif game_state["game_mode"] == "sharpshooter":
            game_state["lives"] = LIVES.get(game_state["difficulty"], 5)
            num_targets = 1
            game_state["target_duration"] = TARGET_DURATION.get(
                game_state["difficulty"], 2.5
            )
        elif game_state["game_mode"] == "obstacle":
            game_state["lives"] = LIVES.get(game_state["difficulty"], 5)
            num_targets = 3
            num_obstacles = 3
            game_state["target_duration"] = 5
        else:
            game_state["lives"] = LIVES.get(game_state["difficulty"], 5)
            num_targets = 3
            game_state["target_duration"] = 5

    game_state["main_bird"] = MainBird(
        game_state["sling_x"], game_state["sling_y"], game_state["object_size"]
    )
    if game_state.get("current_bird_img"):
        try:
            t_idx = game_state["images"]["bird_imgs"].index(
                game_state["current_bird_img"]
            )
        except:
            t_idx = 0
        game_state["main_bird"].set_image(game_state["current_bird_img"], t_idx)

    game_state["targets"] = pygame.sprite.Group()
    game_state["obstacles"] = pygame.sprite.Group()
    game_state["small_birds"] = pygame.sprite.Group()
    game_state["defeated_pigs"] = pygame.sprite.Group()

    game_state.update(
        {
            "score": 0,
            "game_over": False,
            "explosion_active": False,
            "explosion_frames": 0,
            "combo": 0,
            "trail_particles": [],
            "dust_particles": [],
            "spark_particles": [],
            "feather_particles": [],
            "last_shot_path": [],
            "path_display_timer": 0,
            "target_timer_start": time.time(),
        }
    )

    sm = SPEED_MULTIPLIER.get(game_state["difficulty"], 0)
    target_img = game_state["images"]["target_img"]
    obs_img = game_state["images"]["brick_img"]

    for _ in range(num_targets):
        while True:
            nr = create_target(
                game_state["WIDTH"], game_state["HEIGHT"], game_state["object_size"]
            )
            if not any(
                nr.inflate(10, 10).colliderect(t.rect) for t in game_state["targets"]
            ) and not any(
                nr.inflate(10, 10).colliderect(o.rect) for o in game_state["obstacles"]
            ):
                game_state["targets"].add(
                    Target(
                        nr,
                        (
                            random.uniform(0.5, 2.0) * sm * random.choice([-1, 1])
                            if sm > 0
                            else 0
                        ),
                        (
                            random.uniform(0.5, 2.0) * sm * random.choice([-1, 1])
                            if sm > 0
                            else 0
                        ),
                        target_img,
                    )
                )
                break
    for _ in range(num_obstacles):
        while True:
            nr = create_obstacle(
                game_state["WIDTH"], game_state["HEIGHT"], game_state["object_size"]
            )
            if not any(
                nr.inflate(10, 10).colliderect(t.rect) for t in game_state["targets"]
            ) and not any(
                nr.inflate(10, 10).colliderect(o.rect) for o in game_state["obstacles"]
            ):
                game_state["obstacles"].add(
                    Obstacle(
                        nr,
                        (
                            random.uniform(0.5, 2.0) * sm * random.choice([-1, 1])
                            if sm > 0
                            else 0
                        ),
                        (
                            random.uniform(0.5, 2.0) * sm * random.choice([-1, 1])
                            if sm > 0
                            else 0
                        ),
                        obs_img,
                    )
                )
                break
    return game_state


def update_game_state(dt, game_state):
    if game_state.get("paused"):
        return game_state
    dt_factor = dt * 60.0

    update_particles(game_state["trail_particles"], dt)
    update_particles(game_state["dust_particles"], dt)
    update_particles(game_state["spark_particles"], dt)

    if game_state["explosion_active"]:
        game_state["explosion_frames"] -= 1 * dt_factor
        if game_state["explosion_frames"] <= 0:
            game_state["explosion_active"] = False

    return game_state