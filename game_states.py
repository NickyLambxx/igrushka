import pygame
import math
import random
import time
from utils import draw_text, get_text
from game_objects import CAMPAIGN_GRID_SIZE

PEDIA_IMAGES = {
    "Красная Птица": ("bird_imgs", 0),
    "Взрывная Птица": ("bird_imgs", 1),
    "Ускоряющаяся Птица": ("bird_imgs", 2),
    "Птица-Дробилка": ("bird_imgs", 3),
    "Птица-Бумеранг": ("bird_imgs", 4),
    "Свинья-Мишень": "target_img",
    "Кирпич": "brick_img",
    "Red Bird": ("bird_imgs", 0),
    "Explosive Bird": ("bird_imgs", 1),
    "Speed-Up Bird": ("bird_imgs", 2),
    "Splitter Bird": ("bird_imgs", 3),
    "Boomerang Bird": ("bird_imgs", 4),
    "Target Pig": "target_img",
    "Brick": "brick_img",
}


def draw_campaign_board(screen, images, fonts, game_state, mx, my, texts):
    board_rect = game_state["campaign_grid_rect"]
    cell_size = game_state["campaign_cell_size"]
    board = game_state["campaign_board"]

    board_surface = pygame.Surface(board_rect.size, pygame.SRCALPHA)
    board_surface.fill((0, 0, 0, 100))

    animated_grid_positions = set()
    if game_state.get("campaign_is_swapping"):
        anim = game_state["campaign_swap_anim"]
        animated_grid_positions.add(anim["tile1_pos"])
        animated_grid_positions.add(anim["tile2_pos"])

    if game_state.get("campaign_is_dragging_tile"):
        animated_grid_positions.add(game_state["campaign_drag_start_tile"])

    if board:
        for r in range(CAMPAIGN_GRID_SIZE):
            for c in range(CAMPAIGN_GRID_SIZE):
                if (r, c) in animated_grid_positions:
                    continue

                bird_index = board[r][c]
                if bird_index is not None:
                    alpha = 255
                    size_factor = 0.9

                    if (
                        game_state.get("campaign_board_state") == "clearing"
                        and (r, c) in game_state["campaign_matched_tiles"]
                    ):
                        progress = game_state["campaign_clear_progress"]
                        alpha = int(255 * (1.0 - progress))
                        size_factor = 0.9 * (1.0 - progress)

                    if alpha > 0:
                        bird_img = images["bird_imgs"][bird_index]
                        scaled_size = int(cell_size * size_factor)
                        if scaled_size > 0:
                            scaled_bird = pygame.transform.scale(
                                bird_img, (scaled_size, scaled_size)
                            )
                            scaled_bird.set_alpha(alpha)
                            img_rect = scaled_bird.get_rect(
                                center=(
                                    c * cell_size + cell_size / 2,
                                    r * cell_size + cell_size / 2,
                                )
                            )
                            board_surface.blit(scaled_bird, img_rect)

    def draw_animated_tile_at(bird_type, center_x, center_y, alpha=255):
        img = pygame.transform.scale(
            images["bird_imgs"][bird_type], (int(cell_size * 0.9), int(cell_size * 0.9))
        )
        img.set_alpha(alpha)
        img_rect = img.get_rect(center=(center_x, center_y))
        board_surface.blit(img, img_rect)

    if game_state.get("campaign_is_swapping"):
        anim = game_state["campaign_swap_anim"]
        p = anim["progress"]
        r1, c1 = anim["tile1_pos"]
        r2, c2 = anim["tile2_pos"]
        x1, y1 = c1 * cell_size + cell_size / 2, r1 * cell_size + cell_size / 2
        x2, y2 = c2 * cell_size + cell_size / 2, r2 * cell_size + cell_size / 2
        curr_x1 = x1 + (x2 - x1) * p
        curr_y1 = y1 + (y2 - y1) * p
        curr_x2 = x2 + (x1 - x2) * p
        curr_y2 = y2 + (y1 - y2) * p
        draw_animated_tile_at(anim["tile1_type"], curr_x1, curr_y1)
        draw_animated_tile_at(anim["tile2_type"], curr_x2, curr_y2)

    if game_state.get("campaign_is_dragging_tile"):
        r, c = game_state["campaign_drag_start_tile"]
        bird_type = board[r][c]
        if bird_type is not None:
            # Отрисовка "призрака" на исходной позиции
            draw_animated_tile_at(
                bird_type,
                c * cell_size + cell_size / 2,
                r * cell_size + cell_size / 2,
                alpha=100,
            )
            # Отрисовка перетаскиваемой птицы под курсором
            drag_x = mx - board_rect.x
            drag_y = my - board_rect.y
            draw_animated_tile_at(bird_type, drag_x, drag_y, alpha=200)

    def get_animated_y(tile_data, is_refilling=False):
        p = tile_data["progress"]
        r_end, _ = tile_data["end_pos"]
        y_end = r_end * cell_size + cell_size / 2
        y_start = (
            (r_end + tile_data["start_y_offset"])
            if is_refilling
            else tile_data["start_pos"][0] * cell_size
        ) + cell_size / 2
        return y_start + (y_end - y_start) * p

    if game_state.get("campaign_board_state") == "falling":
        for tile in game_state["campaign_falling_tiles"]:
            draw_animated_tile_at(
                tile["type"],
                tile["end_pos"][1] * cell_size + cell_size / 2,
                get_animated_y(tile),
            )
    if game_state.get("campaign_board_state") == "refilling":
        for tile in game_state["campaign_refilling_tiles"]:
            draw_animated_tile_at(
                tile["type"],
                tile["end_pos"][1] * cell_size + cell_size / 2,
                get_animated_y(tile, True),
            )

    if game_state.get("campaign_selected_tile") and not game_state.get(
        "campaign_is_swapping"
    ):
        r, c = game_state["campaign_selected_tile"]
        pygame.draw.rect(
            board_surface,
            (255, 255, 0, 200),
            (c * cell_size, r * cell_size, cell_size, cell_size),
            4,
            border_radius=5,
        )

    screen.blit(board_surface, board_rect.topleft)

    score_text = f"{get_text(texts, 'score_colon')} {game_state['campaign_score']} / {game_state['campaign_target_score']}"
    score_surf, _ = draw_text(score_text, fonts["small_font"], (0, 0, 0))
    screen.blit(score_surf, (board_rect.left, board_rect.top - 40))

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    screen.blit(
        images["lightbulb_img"],
        (
            game_state["WIDTH"] // 2 - int(30 * game_state["scale_factor"]),
            int(10 * game_state["scale_factor"]),
        ),
    )

    if game_state["campaign_level_complete"]:
        overlay = pygame.Surface(
            (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        win_surf, win_rect = draw_text(
            get_text(texts, "campaign_win"), fonts["font"], (255, 215, 0)
        )
        win_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 - 50)
        screen.blit(win_surf, win_rect)
        buttons = {}
        restart_surf, restart_btn = draw_text(
            get_text(texts, "training_restart"), fonts["small_font"], (255, 255, 255)
        )
        restart_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 20)
        if restart_btn.collidepoint(mx, my):
            restart_surf, _ = draw_text(
                get_text(texts, "training_restart"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(restart_surf, restart_btn)
        buttons["restart_btn"] = restart_btn
        exit_surf, exit_btn = draw_text(
            get_text(texts, "training_exit_to_menu"),
            fonts["small_font"],
            (255, 255, 255),
        )
        exit_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 70)
        if exit_btn.collidepoint(mx, my):
            exit_surf, _ = draw_text(
                get_text(texts, "training_exit_to_menu"),
                fonts["small_font"],
                (255, 200, 0),
            )
        screen.blit(exit_surf, exit_btn)
        buttons["exit_btn"] = exit_btn
        return buttons
    return {}


def draw_level_selection(screen, fonts, game_state, mx, my, texts):
    buttons = {"levels": {}}
    title_surf, title_rect = draw_text(
        get_text(texts, "level_selection_title"), fonts["font"], (0, 0, 0)
    )
    title_rect.centerx = screen.get_width() // 2
    title_rect.y = 80
    screen.blit(title_surf, title_rect)

    cols = 5
    rows = 4
    total_levels = 20
    spacing = 100
    radius = 35
    start_x = (screen.get_width() - (cols - 1) * spacing) // 2
    start_y = title_rect.bottom + 80

    for i in range(total_levels):
        col = i % cols
        row = i // cols
        x = start_x + col * spacing
        y = start_y + row * spacing

        level_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        color = (100, 150, 255)
        if level_rect.collidepoint(mx, my):
            color = (150, 200, 255)

        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, (255, 255, 255), (x, y), radius, 3)

        level_text_surf, _ = draw_text(str(i + 1), fonts["small_font"], (255, 255, 255))
        level_text_rect = level_text_surf.get_rect(center=(x, y))
        screen.blit(level_text_surf, level_text_rect)
        buttons["levels"][i + 1] = level_rect

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_campaign_hint_popup(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    dialog_rect = pygame.Rect(0, 0, 700, 300)
    dialog_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    pygame.draw.rect(screen, (60, 60, 80), dialog_rect)
    pygame.draw.rect(screen, (210, 210, 230), dialog_rect, 3)

    title_surf, title_rect = draw_text(
        get_text(texts, "campaign_hint_title"), fonts["small_font"], (255, 215, 0)
    )
    title_rect.centerx = dialog_rect.centerx
    title_rect.y = dialog_rect.y + 20
    screen.blit(title_surf, title_rect)

    description_text = get_text(texts, "campaign_hint_text")
    font = fonts["pedia_font"]
    words = description_text.split(" ")
    line_spacing = font.get_linesize()
    max_width = dialog_rect.width - 40
    x, y = dialog_rect.left + 20, dialog_rect.y + 70
    space = font.size(" ")[0]
    for word in words:
        word_surface = font.render(word, True, (255, 255, 255))
        word_width, word_height = word_surface.get_size()
        if x + word_width >= dialog_rect.left + max_width:
            x = dialog_rect.left + 20
            y += line_spacing
        screen.blit(word_surface, (x, y))
        x += word_width + space

    close_surf, close_btn = draw_text(
        get_text(texts, "hint_popup_close"), fonts["small_font"], (255, 255, 255)
    )
    close_btn.center = (dialog_rect.centerx, dialog_rect.bottom - 40)
    if close_btn.collidepoint(mx, my):
        close_surf, _ = draw_text(
            get_text(texts, "hint_popup_close"), fonts["small_font"], (120, 255, 120)
        )
    screen.blit(close_surf, close_btn)
    buttons["close_btn"] = close_btn
    return buttons


def draw_menu(screen, images, fonts, game_state, mx, my, texts):
    buttons = {}
    y_step = 50
    start_y = game_state["HEIGHT"] // 2
    button_keys = [
        "start_btn",
        "profile_btn",
        "modes_btn",
        "set_btn",
        "achievements_btn",
    ]
    button_text_keys = [
        "start_game",
        "profile",
        "modes_difficulty",
        "settings",
        "achievements",
    ]
    hover_bird_size = int(40 * game_state["scale_factor"])
    bird_hover_images = [
        pygame.transform.scale(img, (hover_bird_size, hover_bird_size))
        for img in images["bird_imgs"]
    ]

    for i, text_key in enumerate(button_text_keys):
        y_pos = start_y + y_step * i
        text = get_text(texts, text_key)
        text_surf, text_rect = draw_text(text, fonts["small_font"], (0, 0, 0))
        text_rect.topleft = (game_state["WIDTH"] // 2 - 100, y_pos)
        if text_rect.collidepoint(mx, my):
            text_surf, _ = draw_text(text, fonts["small_font"], (255, 200, 0))
            bird_img = bird_hover_images[i]
            screen.blit(
                bird_img,
                (
                    text_rect.left - (hover_bird_size + 15),
                    text_rect.centery - hover_bird_size // 2,
                ),
            )
        screen.blit(text_surf, text_rect)
        buttons[button_keys[i]] = text_rect

    exit_surf, exit_btn = draw_text(
        get_text(texts, "exit"), fonts["small_font"], (0, 0, 0)
    )
    exit_btn.bottomright = (game_state["WIDTH"] - 20, game_state["HEIGHT"] - 20)
    if exit_btn.collidepoint(mx, my):
        exit_surf, _ = draw_text(
            get_text(texts, "exit"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(exit_surf, exit_btn)
    buttons["exit_btn"] = exit_btn

    pedia_surf, pedia_btn = draw_text(
        get_text(texts, "birdpedia"), fonts["small_font"], (0, 0, 0)
    )
    pedia_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if pedia_btn.collidepoint(mx, my):
        pedia_surf, _ = draw_text(
            get_text(texts, "birdpedia"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(pedia_surf, pedia_btn)
    buttons["birdpedia_btn"] = pedia_btn

    profile_text_surf, _ = draw_text(
        f"{get_text(texts, 'profile_colon')} {game_state['current_profile']}",
        fonts["info_font"],
        (0, 0, 0),
    )
    screen.blit(profile_text_surf, (10, 10))

    mode_map = get_text(texts, "mode_map")
    mode_name = mode_map.get(game_state["game_mode"], "Unknown")
    mode_text_str = f"{get_text(texts, 'mode_colon')} {mode_name}"
    mode_text_surf, _ = draw_text(mode_text_str, fonts["info_font"], (0, 0, 0))
    screen.blit(mode_text_surf, (10, 35))

    diff_name = get_text(texts, game_state["difficulty"])
    diff_text_str = f"{get_text(texts, 'difficulty_colon')} {diff_name}"
    diff_text_surf, _ = draw_text(diff_text_str, fonts["info_font"], (0, 0, 0))
    screen.blit(diff_text_surf, (10, 60))

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    return buttons


def draw_profile_selection(screen, fonts, game_state, mx, my, texts):
    buttons = {"profiles": {}, "delete_btns": {}}
    y_pos = 280
    for name in game_state["all_profiles_data"].keys():
        color = (0, 150, 0) if name == game_state["current_profile"] else (0, 0, 0)
        text_surf, text_rect = draw_text(name, fonts["small_font"], color)
        text_rect.topleft = (150, y_pos)
        if text_rect.collidepoint(mx, my) and name != game_state["current_profile"]:
            text_surf, _ = draw_text(name, fonts["small_font"], (255, 200, 0))
        screen.blit(text_surf, text_rect)
        buttons["profiles"][name] = text_rect
        if name != "Guest":
            delete_surf, delete_rect = draw_text("X", fonts["small_font"], (180, 0, 0))
            delete_rect.left = text_rect.right + 20
            delete_rect.centery = text_rect.centery
            if delete_rect.collidepoint(mx, my):
                delete_surf, _ = draw_text("X", fonts["small_font"], (255, 0, 0))
            screen.blit(delete_surf, delete_rect)
            buttons["delete_btns"][name] = delete_rect
        y_pos += 40
    input_box_rect = pygame.Rect(150, y_pos + 30, 250, 40)
    color = (255, 200, 0) if game_state["profile_input_active"] else (200, 200, 200)
    pygame.draw.rect(screen, (255, 255, 255), input_box_rect)
    pygame.draw.rect(screen, color, input_box_rect, 2)
    input_text = game_state["profile_input_text"]
    if game_state["profile_input_active"] and time.time() % 1 > 0.5:
        input_text += "|"
    input_surf, _ = draw_text(input_text, fonts["small_font"], (0, 0, 0))
    screen.blit(input_surf, (input_box_rect.x + 10, input_box_rect.y + 5))
    buttons["input_box"] = input_box_rect
    create_surf, create_btn = draw_text(
        get_text(texts, "create"), fonts["small_font"], (0, 0, 0)
    )
    create_btn.topleft = (input_box_rect.right + 20, input_box_rect.y)
    if create_btn.collidepoint(mx, my):
        create_surf, _ = draw_text(
            get_text(texts, "create"), fonts["small_font"], (0, 180, 0)
        )
    screen.blit(create_surf, create_btn)
    buttons["create_btn"] = create_btn

    is_initial_selection = game_state.get("initial_profile_selection", False)
    button_text = (
        get_text(texts, "exit") if is_initial_selection else get_text(texts, "back")
    )
    back_surf, back_btn = draw_text(button_text, fonts["small_font"], (0, 0, 0))
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(button_text, fonts["small_font"], (255, 200, 0))
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_profile_delete_confirmation(screen, fonts, game_state, mx, my, texts):
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    dialog_rect = pygame.Rect(0, 0, 600, 200)
    dialog_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    pygame.draw.rect(screen, (70, 50, 50), dialog_rect)
    pygame.draw.rect(screen, (220, 200, 200), dialog_rect, 3)
    question_text = f"{get_text(texts, 'confirm_delete_profile')} '{game_state['profile_to_delete']}'?"
    question_surf, question_rect = draw_text(
        question_text, fonts["small_font"], (255, 255, 255)
    )
    question_rect.centerx = dialog_rect.centerx
    question_rect.y = dialog_rect.y + 40
    screen.blit(question_surf, question_rect)
    yes_surf, yes_btn = draw_text(
        get_text(texts, "yes"), fonts["small_font"], (200, 80, 80)
    )
    yes_btn.center = (dialog_rect.centerx - 80, dialog_rect.centery + 40)
    if yes_btn.collidepoint(mx, my):
        yes_surf, _ = draw_text(
            get_text(texts, "yes"), fonts["small_font"], (255, 120, 120)
        )
    screen.blit(yes_surf, yes_btn)
    no_surf, no_btn = draw_text(
        get_text(texts, "no"), fonts["small_font"], (80, 200, 80)
    )
    no_btn.center = (dialog_rect.centerx + 80, dialog_rect.centery + 40)
    if no_btn.collidepoint(mx, my):
        no_surf, _ = draw_text(
            get_text(texts, "no"), fonts["small_font"], (120, 255, 120)
        )
    screen.blit(no_surf, no_btn)
    return {"yes_btn": yes_btn, "no_btn": no_btn}


def draw_settings(screen, images, fonts, game_state, mx, my, texts):
    buttons = {}
    y_step = 70
    start_y = game_state["HEIGHT"] // 2 + 50
    button_info = {
        "sound_btn": {"text_key": "sound", "y_offset": 0},
        "screen_btn": {"text_key": "screen", "y_offset": y_step},
        "language_btn": {"text_key": "language", "y_offset": y_step * 2},
    }
    for btn_key, info in button_info.items():
        text = get_text(texts, info["text_key"])
        text_surf, text_btn = draw_text(text, fonts["small_font"], (0, 0, 0))
        text_btn.center = (game_state["WIDTH"] // 2, start_y + info["y_offset"])
        if text_btn.collidepoint(mx, my):
            text_surf, _ = draw_text(text, fonts["small_font"], (255, 200, 0))
        screen.blit(text_surf, text_btn)
        buttons[btn_key] = text_btn
    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_sound_settings(screen, images, fonts, game_state, mx, my, texts):
    buttons = {}
    start_y = 280
    y_step = 80
    music_vol_surf, _ = draw_text(
        get_text(texts, "music_volume"), fonts["small_font"], (0, 0, 0)
    )
    screen.blit(music_vol_surf, (game_state["WIDTH"] // 2 - 150, start_y))
    music_slider = pygame.Rect(game_state["WIDTH"] // 2 - 150, start_y + 40, 300, 10)
    music_knob_radius = 10
    music_knob_x = music_slider.x + int(game_state["music_volume"] * music_slider.width)
    music_knob_center = (music_knob_x, music_slider.centery)
    pygame.draw.rect(screen, (150, 150, 150), music_slider)
    pygame.draw.rect(
        screen,
        (0, 150, 0),
        (
            music_slider.x,
            music_slider.y,
            music_knob_x - music_slider.x,
            music_slider.height,
        ),
    )
    pygame.draw.circle(screen, (0, 100, 0), music_knob_center, music_knob_radius)
    buttons["music_slider"] = music_slider

    sfx_vol_surf, _ = draw_text(
        get_text(texts, "sfx_volume"), fonts["small_font"], (0, 0, 0)
    )
    screen.blit(sfx_vol_surf, (game_state["WIDTH"] // 2 - 150, start_y + y_step))
    sfx_slider = pygame.Rect(
        game_state["WIDTH"] // 2 - 150, start_y + y_step + 40, 300, 10
    )
    sfx_knob_radius = 10
    sfx_knob_x = sfx_slider.x + int(game_state["sfx_volume"] * sfx_slider.width)
    sfx_knob_center = (sfx_knob_x, sfx_slider.centery)
    pygame.draw.rect(screen, (150, 150, 150), sfx_slider)
    pygame.draw.rect(
        screen,
        (0, 150, 0),
        (sfx_slider.x, sfx_slider.y, sfx_knob_x - sfx_slider.x, sfx_slider.height),
    )
    pygame.draw.circle(screen, (0, 100, 0), sfx_knob_center, sfx_knob_radius)
    buttons["sfx_slider"] = sfx_slider

    track_y = start_y + y_step * 2
    track_text = f"{get_text(texts, 'track_colon')} {game_state['current_music_track_index'] + 1}"
    track_surf, _ = draw_text(track_text, fonts["small_font"], (0, 0, 0))
    track_rect = track_surf.get_rect(center=(game_state["WIDTH"] // 2, track_y))
    screen.blit(track_surf, track_rect)
    prev_surf, prev_btn = draw_text(
        get_text(texts, "prev_track"), fonts["small_font"], (0, 0, 0)
    )
    prev_btn.topright = (track_rect.left - 20, track_rect.top)
    if prev_btn.collidepoint(mx, my):
        prev_surf, _ = draw_text(
            get_text(texts, "prev_track"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(prev_surf, prev_btn)
    buttons["prev_track_btn"] = prev_btn
    next_surf, next_btn = draw_text(
        get_text(texts, "next_track"), fonts["small_font"], (0, 0, 0)
    )
    next_btn.topleft = (track_rect.right + 20, track_rect.top)
    if next_btn.collidepoint(mx, my):
        next_surf, _ = draw_text(
            get_text(texts, "next_track"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(next_surf, next_btn)
    buttons["next_track_btn"] = next_btn

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    return buttons


def draw_screen_settings(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    start_y = 300
    y_step = 120
    slider_width = 300
    slider_x = game_state["WIDTH"] // 2 - slider_width // 2

    bright_text_surf, _ = draw_text(
        get_text(texts, "brightness"), fonts["small_font"], (0, 0, 0)
    )
    screen.blit(bright_text_surf, (slider_x, start_y))
    brightness_slider = pygame.Rect(slider_x, start_y + 40, slider_width, 10)
    knob_radius = 10
    knob_x = brightness_slider.x + int(
        game_state["brightness_slider_pos"] * brightness_slider.width
    )
    knob_center = (knob_x, brightness_slider.centery)
    pygame.draw.rect(screen, (150, 150, 150), brightness_slider)
    pygame.draw.rect(
        screen,
        (250, 250, 100),
        (
            brightness_slider.x,
            brightness_slider.y,
            knob_x - brightness_slider.x,
            brightness_slider.height,
        ),
    )
    pygame.draw.circle(screen, (200, 200, 50), knob_center, knob_radius)
    buttons["brightness_slider"] = brightness_slider

    res_y = start_y + y_step
    res_text_surf, _ = draw_text(
        get_text(texts, "resolution"), fonts["small_font"], (0, 0, 0)
    )
    screen.blit(res_text_surf, (slider_x, res_y))
    res_800x600 = (800, 600)
    is_800_selected = game_state["pending_screen_mode"] == res_800x600
    color_800 = (0, 150, 0) if is_800_selected else (0, 0, 0)
    res800_surf, res800_btn = draw_text("800 x 600", fonts["small_font"], color_800)
    res800_btn.topleft = (slider_x, res_y + 40)
    if not is_800_selected and res800_btn.collidepoint(mx, my):
        res800_surf, _ = draw_text("800 x 600", fonts["small_font"], (255, 200, 0))
    screen.blit(res800_surf, res800_btn)
    buttons["res_800_btn"] = res800_btn

    res_fullscreen_val = "fullscreen"
    is_fullscreen_selected = game_state["pending_screen_mode"] == res_fullscreen_val
    color_fullscreen = (0, 150, 0) if is_fullscreen_selected else (0, 0, 0)
    res_fullscreen_surf, res_fullscreen_btn = draw_text(
        get_text(texts, "fullscreen"), fonts["small_font"], color_fullscreen
    )
    res_fullscreen_btn.topleft = (res800_btn.right + 40, res800_btn.top)
    if not is_fullscreen_selected and res_fullscreen_btn.collidepoint(mx, my):
        res_fullscreen_surf, _ = draw_text(
            get_text(texts, "fullscreen"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(res_fullscreen_surf, res_fullscreen_btn)
    buttons["res_fullscreen_btn"] = res_fullscreen_btn

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_language_selection(screen, fonts, game_state, mx, my, texts):
    buttons = {}

    ru_color = (0, 150, 0) if game_state["language"] == "ru" else (0, 0, 0)
    ru_surf, ru_btn = draw_text("Русский", fonts["small_font"], ru_color)
    ru_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    if ru_btn.collidepoint(mx, my) and game_state["language"] != "ru":
        ru_surf, _ = draw_text("Русский", fonts["small_font"], (255, 200, 0))
    screen.blit(ru_surf, ru_btn)
    buttons["lang_ru_btn"] = ru_btn

    en_color = (0, 150, 0) if game_state["language"] == "en" else (0, 0, 0)
    en_surf, en_btn = draw_text("English", fonts["small_font"], en_color)
    en_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 60)
    if en_btn.collidepoint(mx, my) and game_state["language"] != "en":
        en_surf, _ = draw_text("English", fonts["small_font"], (255, 200, 0))
    screen.blit(en_surf, en_btn)
    buttons["lang_en_btn"] = en_btn

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_game_mode_selection(screen, images, fonts, game_state, mx, my, texts):
    buttons = {}
    y_step = 50
    start_y = 220

    modes_with_difficulty = ["classic", "sharpshooter", "obstacle"]

    def draw_mode_button(text_key, y_pos, key, mode_name):
        text = get_text(texts, text_key)
        color = (0, 150, 0) if game_state["game_mode"] == mode_name else (0, 0, 0)
        text_surf, text_rect = draw_text(text, fonts["small_font"], color)
        text_rect.topleft = (50, y_pos)
        if text_rect.collidepoint(mx, my) and game_state["game_mode"] != mode_name:
            text_surf, _ = draw_text(text, fonts["small_font"], (255, 200, 0))
        screen.blit(text_surf, text_rect)
        buttons[key] = text_rect

    draw_mode_button("classic", start_y, "classic_btn", "classic")
    draw_mode_button(
        "sharpshooter", start_y + y_step, "sharpshooter_btn", "sharpshooter"
    )
    draw_mode_button("obstacle_mode", start_y + y_step * 2, "obstacle_btn", "obstacle")
    draw_mode_button("campaign", start_y + y_step * 3, "campaign_btn", "campaign")
    draw_mode_button("training", start_y + y_step * 4, "training_btn", "training")
    draw_mode_button("dev_mode", start_y + y_step * 5, "developer_btn", "developer")

    if game_state["game_mode"] in modes_with_difficulty:
        slider = pygame.Rect(400, 350, 300, 10)
        pygame.draw.rect(screen, (200, 200, 200), slider)
        knob_radius = 10
        if game_state["difficulty"] == "easy":
            knob_pos = slider.x + knob_radius
        elif game_state["difficulty"] == "medium":
            knob_pos = slider.centerx
        else:
            knob_pos = slider.right - knob_radius
        knob_center = (knob_pos, slider.centery)
        pygame.draw.circle(screen, (255, 0, 0), knob_center, knob_radius)

        easy_surf, _ = draw_text(
            get_text(texts, "easy"), fonts["small_font"], (0, 0, 0)
        )
        screen.blit(easy_surf, (slider.x, slider.y + 15))
        med_surf, _ = draw_text(
            get_text(texts, "medium"), fonts["small_font"], (0, 0, 0)
        )
        screen.blit(
            med_surf, (slider.centerx - med_surf.get_width() // 2, slider.y + 15)
        )
        hard_surf, _ = draw_text(
            get_text(texts, "hard"), fonts["small_font"], (0, 0, 0)
        )
        screen.blit(hard_surf, (slider.right - hard_surf.get_width(), slider.y + 15))
        buttons["difficulty_slider"] = slider

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    return buttons


def draw_achievements(screen, images, fonts, game_state, mx, my, texts):
    buttons = {"profile_btns": {}, "difficulty_btns": {}}
    y_offset = 120
    profiles_title_surf, _ = draw_text(
        get_text(texts, "profiles"), fonts["small_font"], (0, 0, 0)
    )
    screen.blit(profiles_title_surf, (50, 150 + y_offset))
    y_pos = 200 + y_offset
    for name in game_state["all_profiles_data"].keys():
        is_viewing = name == game_state["achievements_viewing_profile"]
        color = (0, 150, 0) if is_viewing else (0, 0, 0)
        text_surf, text_rect = draw_text(name, fonts["small_font"], color)
        text_rect.topleft = (50, y_pos)
        if not is_viewing and text_rect.collidepoint(mx, my):
            text_surf, _ = draw_text(name, fonts["small_font"], (255, 200, 0))
        screen.blit(text_surf, text_rect)
        buttons["profile_btns"][name] = text_rect
        y_pos += 40

    viewed_profile_name = game_state["achievements_viewing_profile"]
    viewed_profile_data = game_state["all_profiles_data"].get(viewed_profile_name, {})
    stats_title_surf, _ = draw_text(
        f"{get_text(texts, 'stats_for')} '{viewed_profile_name}':",
        fonts["small_font"],
        (0, 0, 0),
    )
    screen.blit(stats_title_surf, (350, 150 + y_offset))

    difficulty_y = 200 + y_offset
    difficulties = {
        "easy": get_text(texts, "easy"),
        "medium": get_text(texts, "medium"),
        "hard": get_text(texts, "hard"),
    }
    current_x = 350
    for key, text in difficulties.items():
        is_selected = key == game_state["achievements_viewing_difficulty"]
        color = (0, 150, 0) if is_selected else (0, 0, 0)
        diff_surf, diff_rect = draw_text(text, fonts["info_font"], color)
        diff_rect.topleft = (current_x, difficulty_y)
        if not is_selected and diff_rect.collidepoint(mx, my):
            diff_surf, _ = draw_text(text, fonts["info_font"], (255, 200, 0))
        screen.blit(diff_surf, diff_rect)
        buttons["difficulty_btns"][key] = diff_rect
        current_x += diff_rect.width + 20

    stats_font = fonts["pedia_font"]
    viewed_difficulty = game_state["achievements_viewing_difficulty"]
    key_classic = f"max_combo_classic_{viewed_difficulty}"
    score_classic = viewed_profile_data.get(key_classic, 0)
    classic_surf, _ = draw_text(
        f"{get_text(texts, 'max_combo_classic')} {score_classic}", stats_font, (0, 0, 0)
    )
    screen.blit(classic_surf, (350, 270 + y_offset))
    key_ss = f"max_combo_sharpshooter_{viewed_difficulty}"
    score_ss = viewed_profile_data.get(key_ss, 0)
    ss_surf, _ = draw_text(
        f"{get_text(texts, 'max_combo_sharpshooter')} {score_ss}", stats_font, (0, 0, 0)
    )
    screen.blit(ss_surf, (350, 310 + y_offset))
    key_obs = f"max_combo_obstacle_{viewed_difficulty}"
    score_obs = viewed_profile_data.get(key_obs, 0)
    obs_surf, _ = draw_text(
        f"{get_text(texts, 'max_combo_obstacle')} {score_obs}", stats_font, (0, 0, 0)
    )
    screen.blit(obs_surf, (350, 350 + y_offset))

    reset_surf, reset_btn = draw_text(
        get_text(texts, "reset_profile"), fonts["small_font"], (180, 0, 0)
    )
    reset_btn.bottomright = (game_state["WIDTH"] - 20, game_state["HEIGHT"] - 20)
    if reset_btn.collidepoint(mx, my):
        reset_surf, _ = draw_text(
            get_text(texts, "reset_profile"), fonts["small_font"], (255, 0, 0)
        )
    screen.blit(reset_surf, reset_btn)
    buttons["reset_btn"] = reset_btn

    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    return buttons


def draw_achievements_reset_confirmation(screen, fonts, game_state, mx, my, texts):
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    dialog_rect = pygame.Rect(0, 0, 600, 200)
    dialog_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    pygame.draw.rect(screen, (50, 50, 70), dialog_rect)
    pygame.draw.rect(screen, (200, 200, 220), dialog_rect, 3)
    question_text = f"{get_text(texts, 'confirm_reset_stats')} '{game_state['achievements_viewing_profile']}'?"
    question_surf, question_rect = draw_text(
        question_text, fonts["small_font"], (255, 255, 255)
    )
    question_rect.centerx = dialog_rect.centerx
    question_rect.y = dialog_rect.y + 40
    screen.blit(question_surf, question_rect)
    yes_surf, yes_btn = draw_text(
        get_text(texts, "yes"), fonts["small_font"], (200, 80, 80)
    )
    yes_btn.center = (dialog_rect.centerx - 80, dialog_rect.centery + 40)
    if yes_btn.collidepoint(mx, my):
        yes_surf, _ = draw_text(
            get_text(texts, "yes"), fonts["small_font"], (255, 120, 120)
        )
    screen.blit(yes_surf, yes_btn)
    no_surf, no_btn = draw_text(
        get_text(texts, "no"), fonts["small_font"], (80, 200, 80)
    )
    no_btn.center = (dialog_rect.centerx + 80, dialog_rect.centery + 40)
    if no_btn.collidepoint(mx, my):
        no_surf, _ = draw_text(
            get_text(texts, "no"), fonts["small_font"], (120, 255, 120)
        )
    screen.blit(no_surf, no_btn)
    return {"yes_btn": yes_btn, "no_btn": no_btn}


def draw_birdpedia_menu(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    pedia_items = get_text(texts, "pedia_items")
    num_items = len(pedia_items)
    items_per_column = (num_items + 1) // 2
    col1_x = 150
    col2_x = 450
    start_y = 300
    y_step = 40
    for i, item_text in enumerate(pedia_items):
        if i < items_per_column:
            x, y = col1_x, start_y + i * y_step
        else:
            x, y = col2_x, start_y + (i - items_per_column) * y_step
        text_surf, text_rect = draw_text(item_text, fonts["small_font"], (0, 0, 0))
        text_rect.topleft = (x, y)
        if text_rect.collidepoint(mx, my):
            text_surf, _ = draw_text(item_text, fonts["small_font"], (255, 200, 0))
        screen.blit(text_surf, text_rect)
        buttons[item_text] = text_rect
    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_birdpedia_detail_screen(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    item_name = game_state.get("birdpedia_item_selected", "Описание")
    start_y_pos = 280
    image_key = PEDIA_IMAGES.get(item_name)
    if image_key:
        img_bg_rect = pygame.Rect(100, start_y_pos, 150, 150)
        pygame.draw.rect(screen, (20, 20, 20), img_bg_rect)
        if isinstance(image_key, tuple):
            item_img = game_state["images"][image_key[0]][image_key[1]]
        else:
            item_img = game_state["images"][image_key]
        scaled_img = pygame.transform.scale(item_img, (120, 120))
        img_rect = scaled_img.get_rect(center=img_bg_rect.center)
        screen.blit(scaled_img, img_rect)

    pedia_descriptions = get_text(texts, "pedia_descriptions")
    description_text = pedia_descriptions.get(
        item_name, get_text(texts, "pedia_not_found")
    )

    font = fonts["pedia_font"]
    words = description_text.split(" ")
    line_spacing = font.get_linesize()
    max_width = 450
    x, y = 300, start_y_pos
    space = font.size(" ")[0]
    for word in words:
        word_surface = font.render(word, True, (0, 0, 0))
        word_width, word_height = word_surface.get_size()
        if x + word_width >= 300 + max_width:
            x = 300
            y += line_spacing
        screen.blit(word_surface, (x, y))
        x += word_width + space
    back_surf, back_btn = draw_text(
        get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
    )
    back_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
    if back_btn.collidepoint(mx, my):
        back_surf, _ = draw_text(
            get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(back_surf, back_btn)
    buttons["back_btn"] = back_btn
    return buttons


def draw_hint_popup(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    dialog_rect = pygame.Rect(0, 0, 600, 250)
    dialog_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    pygame.draw.rect(screen, (60, 60, 80), dialog_rect)
    pygame.draw.rect(screen, (210, 210, 230), dialog_rect, 3)
    current_bird_img = game_state.get("current_bird_img")
    bird_name_ru = game_state.get("bird_image_to_name", {}).get(
        current_bird_img, "Неизвестная птица"
    )

    try:
        bird_idx = list(game_state.get("bird_image_to_name", {}).values()).index(
            bird_name_ru
        )
        bird_name = get_text(texts, "pedia_items")[bird_idx]
    except (ValueError, IndexError):
        bird_name = get_text(texts, "unknown_bird")

    pedia_descriptions = get_text(texts, "pedia_descriptions")
    description_text = pedia_descriptions.get(
        bird_name, get_text(texts, "no_bird_on_slingshot")
    )

    title_surf, title_rect = draw_text(bird_name, fonts["small_font"], (255, 215, 0))
    title_rect.centerx = dialog_rect.centerx
    title_rect.y = dialog_rect.y + 20
    screen.blit(title_surf, title_rect)
    font = fonts["pedia_font"]
    words = description_text.split(" ")
    line_spacing = font.get_linesize()
    max_width = dialog_rect.width - 40
    x, y = dialog_rect.left + 20, dialog_rect.y + 70
    space = font.size(" ")[0]
    for word in words:
        word_surface = font.render(word, True, (255, 255, 255))
        word_width, word_height = word_surface.get_size()
        if x + word_width >= dialog_rect.left + max_width:
            x = dialog_rect.left + 20
            y += line_spacing
        screen.blit(word_surface, (x, y))
        x += word_width + space
    close_surf, close_btn = draw_text(
        get_text(texts, "hint_popup_close"), fonts["small_font"], (255, 255, 255)
    )
    close_btn.center = (dialog_rect.centerx, dialog_rect.bottom - 30)
    if close_btn.collidepoint(mx, my):
        close_surf, _ = draw_text(
            get_text(texts, "hint_popup_close"), fonts["small_font"], (120, 255, 120)
        )
    screen.blit(close_surf, close_btn)
    buttons["close_btn"] = close_btn
    return buttons


def draw_training_popup(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    dialog_rect = pygame.Rect(0, 0, 700, 250)
    dialog_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
    pygame.draw.rect(screen, (50, 70, 50), dialog_rect)
    pygame.draw.rect(screen, (200, 220, 200), dialog_rect, 3)
    words = game_state.get("training_popup_text", "").split(" ")
    line_spacing = fonts["small_font"].get_linesize()
    x, y = dialog_rect.left + 20, dialog_rect.top + 20
    space = fonts["small_font"].size(" ")[0]
    for word in words:
        word_surface = fonts["small_font"].render(word, True, (255, 255, 255))
        word_width, word_height = word_surface.get_size()
        if x + word_width >= dialog_rect.right - 20:
            x = dialog_rect.left + 20
            y += line_spacing
        screen.blit(word_surface, (x, y))
        x += word_width + space
    continue_surf, continue_btn = draw_text(
        get_text(texts, "training_popup_continue"), fonts["small_font"], (255, 255, 255)
    )
    continue_btn.center = (dialog_rect.centerx, dialog_rect.bottom - 40)
    if continue_btn.collidepoint(mx, my):
        continue_surf, _ = draw_text(
            get_text(texts, "training_popup_continue"),
            fonts["small_font"],
            (120, 255, 120),
        )
    screen.blit(continue_surf, continue_btn)
    buttons["continue_btn"] = continue_btn
    return buttons


def draw_training_complete_screen(screen, fonts, game_state, mx, my, texts):
    buttons = {}
    overlay = pygame.Surface(
        (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
    )
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    title_surf, title_rect = draw_text(
        get_text(texts, "training_complete_title"), fonts["font"], (255, 215, 0)
    )
    title_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 - 50)
    screen.blit(title_surf, title_rect)
    restart_surf, restart_btn = draw_text(
        get_text(texts, "training_restart"), fonts["small_font"], (255, 255, 255)
    )
    restart_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 20)
    if restart_btn.collidepoint(mx, my):
        restart_surf, _ = draw_text(
            get_text(texts, "training_restart"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(restart_surf, restart_btn)
    buttons["restart_btn"] = restart_btn
    exit_surf, exit_btn = draw_text(
        get_text(texts, "training_exit_to_menu"), fonts["small_font"], (255, 255, 255)
    )
    exit_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 70)
    if exit_btn.collidepoint(mx, my):
        exit_surf, _ = draw_text(
            get_text(texts, "training_exit_to_menu"), fonts["small_font"], (255, 200, 0)
        )
    screen.blit(exit_surf, exit_btn)
    buttons["exit_btn"] = exit_btn
    return buttons


def draw_gameplay(screen, images, fonts, game_state, texts):
    GROUND_LEVEL = game_state["GROUND_LEVEL"]
    scale = game_state["scale_factor"]
    queue_start_x = int(40 * scale)
    queue_gap = int(60 * scale)
    bird_size = game_state["object_size"]

    for i, bird_img in enumerate(game_state["bird_queue"]):
        screen.blit(
            bird_img, (queue_start_x + i * queue_gap, GROUND_LEVEL - bird_size * 0.9)
        )
    pygame.draw.circle(
        screen,
        (139, 69, 19),
        (game_state["sling_x"], game_state["sling_y"]),
        int(5 * scale),
    )

    if game_state["is_dragging"] and not game_state["paused"]:
        dx = game_state["sling_x"] - game_state["projectile_x"]
        dy = game_state["sling_y"] - game_state["projectile_y"]
        power_bar_width = int(150 * scale)
        power_bar_height = int(15 * scale)
        max_drag_dist = int(150 * scale)
        distance = min(math.hypot(dx, dy), max_drag_dist)
        power_percent = distance / max_drag_dist
        bar_x = game_state["sling_x"] - power_bar_width // 2
        bar_y = game_state["sling_y"] + int(30 * scale)
        pygame.draw.rect(
            screen, (100, 100, 100), (bar_x, bar_y, power_bar_width, power_bar_height)
        )
        pygame.draw.rect(
            screen,
            (int(255 * power_percent), int(255 * (1 - power_percent)), 0),
            (bar_x, bar_y, int(power_bar_width * power_percent), power_bar_height),
        )
        power_text_surf, _ = draw_text(
            f"{get_text(texts, 'power_colon')} {int(power_percent * 100)}%",
            fonts["small_font"],
            (0, 0, 0),
        )
        screen.blit(
            power_text_surf,
            (
                game_state["sling_x"] - power_text_surf.get_width() // 2,
                bar_y + power_bar_height + 5,
            ),
        )

    if game_state["show_rope"]:
        pygame.draw.line(
            screen,
            (139, 69, 19),
            (game_state["sling_x"], game_state["sling_y"]),
            (game_state["projectile_x"], game_state["projectile_y"]),
            int(3 * scale),
        )

    if game_state["sound_on"]:
        screen.blit(images["speaker_on_img"], (game_state["WIDTH"] - 50, 10))
    else:
        screen.blit(images["speaker_off_img"], (game_state["WIDTH"] - 50, 10))
    if game_state["paused"]:
        screen.blit(images["resume_img"], (game_state["WIDTH"] - 100, 10))
    else:
        screen.blit(images["pause_img"], (game_state["WIDTH"] - 100, 10))
    if game_state["game_over"]:
        go_surf, go_rect = draw_text(
            get_text(texts, "game_over"), fonts["font"], (255, 0, 0)
        )
        go_rect.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
        screen.blit(go_surf, go_rect)
