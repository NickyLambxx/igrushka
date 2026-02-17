import pygame
import math
import random
import time
from utils import (
    draw_text,
    get_text,
    create_trail_particle,
    create_dust_particle,
    create_spark_particle,
    update_particles,
    draw_particles,
    draw_dashed_trajectory,
    create_feather_explosion,
    update_feathers,
    draw_feathers,
    create_brick_shatter,
    create_target,
)
from game_objects import (
    CAMPAIGN_GRID_SIZE,
    reset_game,
    apply_screen_settings,
    update_all_volumes,
    play_music_track,
    get_next_bird,
    update_max_combo,
    start_swap_animation,
    split_bird,
    activate_boomerang,
    update_game_state,
    update_campaign_board,
)
from entities import Target, DefeatedPig
from settings import SPEED_MULTIPLIER
from achievements import save_all_profiles_data, create_default_achievements
from localization import LANGUAGES

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


class StateManager:
    def __init__(self):
        self.states = {}
        self.current_state = None
        self.running = True

    def add_state(self, name, state):
        self.states[name] = state

    def change_state(self, name, game_state):
        if self.current_state:
            self.current_state.exit(game_state)
        self.current_state = self.states[name]
        self.current_state.enter(game_state)


class State:
    def enter(self, game_state):
        pass

    def exit(self, game_state):
        pass

    def handle_event(self, event, mx, my, game_state):
        pass

    def update(self, dt, mx, my, game_state):
        pass

    def draw(self, screen, mx, my, game_state):
        pass


class MainMenuState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sm = game_state["state_manager"]
            if self.buttons.get("start_btn") and self.buttons["start_btn"].collidepoint(
                mx, my
            ):
                if game_state["game_mode"] == "campaign":
                    sm.change_state("level_selection", game_state)
                else:
                    reset_game(game_state)
                    sm.change_state("gameplay", game_state)
            elif self.buttons.get("profile_btn") and self.buttons[
                "profile_btn"
            ].collidepoint(mx, my):
                sm.change_state("profile_menu", game_state)
            elif self.buttons.get("modes_btn") and self.buttons[
                "modes_btn"
            ].collidepoint(mx, my):
                sm.change_state("game_mode_menu", game_state)
            elif self.buttons.get("set_btn") and self.buttons["set_btn"].collidepoint(
                mx, my
            ):
                sm.change_state("settings_menu", game_state)
            elif self.buttons.get("achievements_btn") and self.buttons[
                "achievements_btn"
            ].collidepoint(mx, my):
                game_state["achievements_viewing_profile"] = game_state[
                    "current_profile"
                ]
                sm.change_state("achievements_menu", game_state)
            elif self.buttons.get("birdpedia_btn") and self.buttons[
                "birdpedia_btn"
            ].collidepoint(mx, my):
                sm.change_state("birdpedia_menu", game_state)
            elif self.buttons.get("exit_btn") and self.buttons["exit_btn"].collidepoint(
                mx, my
            ):
                sm.running = False

            speaker_rect = pygame.Rect(
                game_state["WIDTH"] - int(50 * game_state["scale_factor"]),
                int(10 * game_state["scale_factor"]),
                int(40 * game_state["scale_factor"]),
                int(40 * game_state["scale_factor"]),
            )
            if speaker_rect.collidepoint(mx, my):
                game_state["sound_on"] = not game_state["sound_on"]
                update_all_volumes(game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        self.buttons = {}
        y_step = 50
        start_y = game_state["HEIGHT"] // 2
        keys = ["start_btn", "profile_btn", "modes_btn", "set_btn", "achievements_btn"]
        text_keys = [
            "start_game",
            "profile",
            "modes_difficulty",
            "settings",
            "achievements",
        ]

        hover_size = int(40 * game_state["scale_factor"])
        hover_imgs = [
            pygame.transform.scale(img, (hover_size, hover_size))
            for img in game_state["images"]["bird_imgs"]
        ]

        for i, text_key in enumerate(text_keys):
            text_surf, text_rect = draw_text(
                get_text(game_state["texts"], text_key),
                game_state["fonts"]["small_font"],
                (0, 0, 0),
            )
            text_rect.topleft = (game_state["WIDTH"] // 2 - 100, start_y + y_step * i)
            if text_rect.collidepoint(mx, my):
                text_surf, _ = draw_text(
                    get_text(game_state["texts"], text_key),
                    game_state["fonts"]["small_font"],
                    (255, 200, 0),
                )
                screen.blit(
                    hover_imgs[i],
                    (
                        text_rect.left - (hover_size + 15),
                        text_rect.centery - hover_size // 2,
                    ),
                )
            screen.blit(text_surf, text_rect)
            self.buttons[keys[i]] = text_rect

        exit_surf, exit_btn = draw_text(
            get_text(game_state["texts"], "exit"),
            game_state["fonts"]["small_font"],
            (0, 0, 0),
        )
        exit_btn.bottomright = (game_state["WIDTH"] - 20, game_state["HEIGHT"] - 20)
        if exit_btn.collidepoint(mx, my):
            exit_surf, _ = draw_text(
                get_text(game_state["texts"], "exit"),
                game_state["fonts"]["small_font"],
                (255, 200, 0),
            )
        screen.blit(exit_surf, exit_btn)
        self.buttons["exit_btn"] = exit_btn

        pedia_surf, pedia_btn = draw_text(
            get_text(game_state["texts"], "birdpedia"),
            game_state["fonts"]["small_font"],
            (0, 0, 0),
        )
        pedia_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if pedia_btn.collidepoint(mx, my):
            pedia_surf, _ = draw_text(
                get_text(game_state["texts"], "birdpedia"),
                game_state["fonts"]["small_font"],
                (255, 200, 0),
            )
        screen.blit(pedia_surf, pedia_btn)
        self.buttons["birdpedia_btn"] = pedia_btn

        screen.blit(
            draw_text(
                f"{get_text(game_state['texts'], 'profile_colon')} {game_state['current_profile']}",
                game_state["fonts"]["info_font"],
                (0, 0, 0),
            )[0],
            (10, 10),
        )
        screen.blit(
            draw_text(
                f"{get_text(game_state['texts'], 'mode_colon')} {get_text(game_state['texts'], 'mode_map').get(game_state['game_mode'], 'Unknown')}",
                game_state["fonts"]["info_font"],
                (0, 0, 0),
            )[0],
            (10, 35),
        )
        screen.blit(
            draw_text(
                f"{get_text(game_state['texts'], 'difficulty_colon')} {get_text(game_state['texts'], game_state['difficulty'])}",
                game_state["fonts"]["info_font"],
                (0, 0, 0),
            )[0],
            (10, 60),
        )

        if game_state["sound_on"]:
            screen.blit(
                game_state["images"]["speaker_on_img"], (game_state["WIDTH"] - 50, 10)
            )
        else:
            screen.blit(
                game_state["images"]["speaker_off_img"], (game_state["WIDTH"] - 50, 10)
            )


class ProfileMenuState(State):
    def __init__(self):
        self.buttons, self.del_buttons, self.conf_buttons = {}, {}, {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN:
            if game_state["profile_input_active"]:
                if event.key == pygame.K_BACKSPACE:
                    game_state["profile_input_text"] = game_state["profile_input_text"][
                        :-1
                    ]
                elif (
                    len(game_state["profile_input_text"]) < 15
                    and event.unicode.isalnum()
                ):
                    game_state["profile_input_text"] += event.unicode
            elif (
                event.key == pygame.K_ESCAPE
                and not game_state["initial_profile_selection"]
            ):
                game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.get("show_profile_delete_confirm"):
                if self.conf_buttons.get("yes_btn") and self.conf_buttons[
                    "yes_btn"
                ].collidepoint(mx, my):
                    ptd = game_state["profile_to_delete"]
                    if ptd in game_state["all_profiles_data"]:
                        del game_state["all_profiles_data"][ptd]
                        save_all_profiles_data(game_state["all_profiles_data"])
                        if game_state["current_profile"] == ptd:
                            game_state["current_profile"] = "Guest"
                            reset_game(game_state)
                    game_state["show_profile_delete_confirm"] = False
                elif self.conf_buttons.get("no_btn") and self.conf_buttons[
                    "no_btn"
                ].collidepoint(mx, my):
                    game_state["show_profile_delete_confirm"] = False
                return

            game_state["profile_input_active"] = False
            if self.buttons.get("input_box") and self.buttons["input_box"].collidepoint(
                mx, my
            ):
                game_state["profile_input_active"] = True
            elif self.buttons.get("create_btn") and self.buttons[
                "create_btn"
            ].collidepoint(mx, my):
                new_name = game_state["profile_input_text"].strip()
                if new_name and new_name not in game_state["all_profiles_data"]:
                    game_state["all_profiles_data"][
                        new_name
                    ] = create_default_achievements()
                    save_all_profiles_data(game_state["all_profiles_data"])
                    game_state["current_profile"] = new_name
                    reset_game(game_state)
                    game_state["profile_input_text"] = ""
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                if game_state["initial_profile_selection"]:
                    game_state["state_manager"].running = False
                else:
                    game_state["state_manager"].change_state("main_menu", game_state)
            else:
                for name, rect in self.del_buttons.items():
                    if rect.collidepoint(mx, my):
                        game_state["show_profile_delete_confirm"] = True
                        game_state["profile_to_delete"] = name
                        return
                for name, rect in self.buttons.get("profiles", {}).items():
                    if rect.collidepoint(mx, my):
                        game_state["current_profile"] = name
                        reset_game(game_state)
                        if game_state["initial_profile_selection"]:
                            game_state["initial_profile_selection"] = False
                            game_state["state_manager"].change_state(
                                "main_menu", game_state
                            )
                        break

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {"profiles": {}}
        self.del_buttons = {}
        y_pos = 280
        for name in game_state["all_profiles_data"].keys():
            color = (0, 150, 0) if name == game_state["current_profile"] else (0, 0, 0)
            text_surf, text_rect = draw_text(name, fonts["small_font"], color)
            text_rect.topleft = (150, y_pos)
            if text_rect.collidepoint(mx, my) and name != game_state["current_profile"]:
                text_surf, _ = draw_text(name, fonts["small_font"], (255, 200, 0))
            screen.blit(text_surf, text_rect)
            self.buttons["profiles"][name] = text_rect
            if name != "Guest":
                del_surf, del_rect = draw_text("X", fonts["small_font"], (180, 0, 0))
                del_rect.left, del_rect.centery = (
                    text_rect.right + 20,
                    text_rect.centery,
                )
                if del_rect.collidepoint(mx, my):
                    del_surf, _ = draw_text("X", fonts["small_font"], (255, 0, 0))
                screen.blit(del_surf, del_rect)
                self.del_buttons[name] = del_rect
            y_pos += 40

        ib_rect = pygame.Rect(150, y_pos + 30, 250, 40)
        pygame.draw.rect(screen, (255, 255, 255), ib_rect)
        pygame.draw.rect(
            screen,
            (255, 200, 0) if game_state["profile_input_active"] else (200, 200, 200),
            ib_rect,
            2,
        )
        txt = game_state["profile_input_text"] + (
            "|" if game_state["profile_input_active"] and time.time() % 1 > 0.5 else ""
        )
        screen.blit(
            draw_text(txt, fonts["small_font"], (0, 0, 0))[0],
            (ib_rect.x + 10, ib_rect.y + 5),
        )
        self.buttons["input_box"] = ib_rect

        c_surf, c_btn = draw_text(
            get_text(texts, "create"), fonts["small_font"], (0, 0, 0)
        )
        c_btn.topleft = (ib_rect.right + 20, ib_rect.y)
        if c_btn.collidepoint(mx, my):
            c_surf, _ = draw_text(
                get_text(texts, "create"), fonts["small_font"], (0, 180, 0)
            )
        screen.blit(c_surf, c_btn)
        self.buttons["create_btn"] = c_btn

        b_txt = (
            get_text(texts, "exit")
            if game_state.get("initial_profile_selection")
            else get_text(texts, "back")
        )
        b_surf, b_btn = draw_text(b_txt, fonts["small_font"], (0, 0, 0))
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(b_txt, fonts["small_font"], (255, 200, 0))
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn

        if game_state.get("show_profile_delete_confirm"):
            overlay = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            dr = pygame.Rect(0, 0, 600, 200)
            dr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
            pygame.draw.rect(screen, (70, 50, 50), dr)
            pygame.draw.rect(screen, (220, 200, 200), dr, 3)
            q_surf, q_rect = draw_text(
                f"{get_text(texts, 'confirm_delete_profile')} '{game_state['profile_to_delete']}'?",
                fonts["small_font"],
                (255, 255, 255),
            )
            q_rect.centerx, q_rect.y = dr.centerx, dr.y + 40
            screen.blit(q_surf, q_rect)
            y_surf, y_btn = draw_text(
                get_text(texts, "yes"), fonts["small_font"], (200, 80, 80)
            )
            y_btn.center = (dr.centerx - 80, dr.centery + 40)
            if y_btn.collidepoint(mx, my):
                y_surf, _ = draw_text(
                    get_text(texts, "yes"), fonts["small_font"], (255, 120, 120)
                )
            screen.blit(y_surf, y_btn)
            n_surf, n_btn = draw_text(
                get_text(texts, "no"), fonts["small_font"], (80, 200, 80)
            )
            n_btn.center = (dr.centerx + 80, dr.centery + 40)
            if n_btn.collidepoint(mx, my):
                n_surf, _ = draw_text(
                    get_text(texts, "no"), fonts["small_font"], (120, 255, 120)
                )
            screen.blit(n_surf, n_btn)
            self.conf_buttons = {"yes_btn": y_btn, "no_btn": n_btn}


class SettingsState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sm = game_state["state_manager"]
            if self.buttons.get("sound_btn") and self.buttons["sound_btn"].collidepoint(
                mx, my
            ):
                sm.change_state("sound_settings", game_state)
            elif self.buttons.get("screen_btn") and self.buttons[
                "screen_btn"
            ].collidepoint(mx, my):
                sm.change_state("screen_settings", game_state)
            elif self.buttons.get("language_btn") and self.buttons[
                "language_btn"
            ].collidepoint(mx, my):
                sm.change_state("language_settings", game_state)
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                sm.change_state("main_menu", game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        self.buttons = {}
        y_step = 70
        start_y = game_state["HEIGHT"] // 2 + 50
        infos = [
            ("sound_btn", "sound", 0),
            ("screen_btn", "screen", y_step),
            ("language_btn", "language", y_step * 2),
        ]
        for key, t_key, offset in infos:
            text = get_text(game_state["texts"], t_key)
            t_surf, t_btn = draw_text(
                text, game_state["fonts"]["small_font"], (0, 0, 0)
            )
            t_btn.center = (game_state["WIDTH"] // 2, start_y + offset)
            if t_btn.collidepoint(mx, my):
                t_surf, _ = draw_text(
                    text, game_state["fonts"]["small_font"], (255, 200, 0)
                )
            screen.blit(t_surf, t_btn)
            self.buttons[key] = t_btn

        b_surf, b_btn = draw_text(
            get_text(game_state["texts"], "back"),
            game_state["fonts"]["small_font"],
            (0, 0, 0),
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(game_state["texts"], "back"),
                game_state["fonts"]["small_font"],
                (255, 200, 0),
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class SoundSettingsState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("settings_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("music_slider") and self.buttons[
                "music_slider"
            ].collidepoint(mx, my):
                game_state["is_dragging_music_volume"] = True
            elif self.buttons.get("sfx_slider") and self.buttons[
                "sfx_slider"
            ].collidepoint(mx, my):
                game_state["is_dragging_sfx_volume"] = True
            elif self.buttons.get("prev_track_btn") and self.buttons[
                "prev_track_btn"
            ].collidepoint(mx, my):
                n_idx = (
                    game_state["current_music_track_index"]
                    - 1
                    + len(game_state["sounds"]["music_playlist"])
                ) % len(game_state["sounds"]["music_playlist"])
                play_music_track(game_state, n_idx)
            elif self.buttons.get("next_track_btn") and self.buttons[
                "next_track_btn"
            ].collidepoint(mx, my):
                play_music_track(
                    game_state,
                    (game_state["current_music_track_index"] + 1)
                    % len(game_state["sounds"]["music_playlist"]),
                )
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("settings_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            game_state["is_dragging_music_volume"] = False
            game_state["is_dragging_sfx_volume"] = False

    def update(self, dt, mx, my, game_state):
        if game_state.get("is_dragging_music_volume"):
            game_state["music_volume"] = max(
                0.0,
                min(
                    1.0,
                    (mx - self.buttons["music_slider"].x)
                    / self.buttons["music_slider"].width,
                ),
            )
            update_all_volumes(game_state)
        if game_state.get("is_dragging_sfx_volume"):
            game_state["sfx_volume"] = max(
                0.0,
                min(
                    1.0,
                    (mx - self.buttons["sfx_slider"].x)
                    / self.buttons["sfx_slider"].width,
                ),
            )
            update_all_volumes(game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}
        sy = 280
        screen.blit(
            draw_text(get_text(texts, "music_volume"), fonts["small_font"], (0, 0, 0))[
                0
            ],
            (game_state["WIDTH"] // 2 - 150, sy),
        )
        ms = pygame.Rect(game_state["WIDTH"] // 2 - 150, sy + 40, 300, 10)
        pygame.draw.rect(screen, (150, 150, 150), ms)
        pygame.draw.rect(
            screen,
            (0, 150, 0),
            (ms.x, ms.y, int(game_state["music_volume"] * ms.width), ms.height),
        )
        pygame.draw.circle(
            screen,
            (0, 100, 0),
            (ms.x + int(game_state["music_volume"] * ms.width), ms.centery),
            10,
        )
        self.buttons["music_slider"] = ms

        screen.blit(
            draw_text(get_text(texts, "sfx_volume"), fonts["small_font"], (0, 0, 0))[0],
            (game_state["WIDTH"] // 2 - 150, sy + 80),
        )
        ss = pygame.Rect(game_state["WIDTH"] // 2 - 150, sy + 120, 300, 10)
        pygame.draw.rect(screen, (150, 150, 150), ss)
        pygame.draw.rect(
            screen,
            (0, 150, 0),
            (ss.x, ss.y, int(game_state["sfx_volume"] * ss.width), ss.height),
        )
        pygame.draw.circle(
            screen,
            (0, 100, 0),
            (ss.x + int(game_state["sfx_volume"] * ss.width), ss.centery),
            10,
        )
        self.buttons["sfx_slider"] = ss

        ty = sy + 160
        t_surf, t_rect = draw_text(
            f"{get_text(texts, 'track_colon')} {game_state['current_music_track_index'] + 1}",
            fonts["small_font"],
            (0, 0, 0),
        )
        t_rect.center = (game_state["WIDTH"] // 2, ty)
        screen.blit(t_surf, t_rect)

        p_surf, p_btn = draw_text(
            get_text(texts, "prev_track"), fonts["small_font"], (0, 0, 0)
        )
        p_btn.topright = (t_rect.left - 20, t_rect.top)
        if p_btn.collidepoint(mx, my):
            p_surf, _ = draw_text(
                get_text(texts, "prev_track"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(p_surf, p_btn)
        self.buttons["prev_track_btn"] = p_btn

        n_surf, n_btn = draw_text(
            get_text(texts, "next_track"), fonts["small_font"], (0, 0, 0)
        )
        n_btn.topleft = (t_rect.right + 20, t_rect.top)
        if n_btn.collidepoint(mx, my):
            n_surf, _ = draw_text(
                get_text(texts, "next_track"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(n_surf, n_btn)
        self.buttons["next_track_btn"] = n_btn

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class ScreenSettingsState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            apply_screen_settings(game_state)
            game_state["state_manager"].change_state("settings_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("brightness_slider") and self.buttons[
                "brightness_slider"
            ].collidepoint(mx, my):
                game_state["is_dragging_brightness"] = True
            elif self.buttons.get("res_800_btn") and self.buttons[
                "res_800_btn"
            ].collidepoint(mx, my):
                game_state["pending_screen_mode"] = (800, 600)
            elif self.buttons.get("res_fs_btn") and self.buttons[
                "res_fs_btn"
            ].collidepoint(mx, my):
                game_state["pending_screen_mode"] = "fullscreen"
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                apply_screen_settings(game_state)
                game_state["state_manager"].change_state("settings_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            game_state["is_dragging_brightness"] = False

    def update(self, dt, mx, my, game_state):
        if game_state.get("is_dragging_brightness"):
            game_state["brightness_slider_pos"] = max(
                0.0,
                min(
                    1.0,
                    (mx - self.buttons["brightness_slider"].x)
                    / self.buttons["brightness_slider"].width,
                ),
            )

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}
        sx = game_state["WIDTH"] // 2 - 150

        screen.blit(
            draw_text(get_text(texts, "brightness"), fonts["small_font"], (0, 0, 0))[0],
            (sx, 300),
        )
        bs = pygame.Rect(sx, 340, 300, 10)
        kx = bs.x + int(game_state["brightness_slider_pos"] * bs.width)
        pygame.draw.rect(screen, (150, 150, 150), bs)
        pygame.draw.rect(screen, (250, 250, 100), (bs.x, bs.y, kx - bs.x, bs.height))
        pygame.draw.circle(screen, (200, 200, 50), (kx, bs.centery), 10)
        self.buttons["brightness_slider"] = bs

        screen.blit(
            draw_text(get_text(texts, "resolution"), fonts["small_font"], (0, 0, 0))[0],
            (sx, 420),
        )
        is_800 = game_state["pending_screen_mode"] == (800, 600)
        r8_surf, r8_btn = draw_text(
            "800 x 600", fonts["small_font"], (0, 150, 0) if is_800 else (0, 0, 0)
        )
        r8_btn.topleft = (sx, 460)
        if not is_800 and r8_btn.collidepoint(mx, my):
            r8_surf, _ = draw_text("800 x 600", fonts["small_font"], (255, 200, 0))
        screen.blit(r8_surf, r8_btn)
        self.buttons["res_800_btn"] = r8_btn

        is_fs = game_state["pending_screen_mode"] == "fullscreen"
        fs_surf, fs_btn = draw_text(
            get_text(texts, "fullscreen"),
            fonts["small_font"],
            (0, 150, 0) if is_fs else (0, 0, 0),
        )
        fs_btn.topleft = (r8_btn.right + 40, r8_btn.top)
        if not is_fs and fs_btn.collidepoint(mx, my):
            fs_surf, _ = draw_text(
                get_text(texts, "fullscreen"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(fs_surf, fs_btn)
        self.buttons["res_fs_btn"] = fs_btn

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class LanguageMenuState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("settings_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("ru_btn") and self.buttons["ru_btn"].collidepoint(
                mx, my
            ):
                game_state["language"], game_state["texts"] = "ru", LANGUAGES["ru"]
            elif self.buttons.get("en_btn") and self.buttons["en_btn"].collidepoint(
                mx, my
            ):
                game_state["language"], game_state["texts"] = "en", LANGUAGES["en"]
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("settings_menu", game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}

        ru_surf, ru_btn = draw_text(
            "Русский",
            fonts["small_font"],
            (0, 150, 0) if game_state["language"] == "ru" else (0, 0, 0),
        )
        ru_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
        if ru_btn.collidepoint(mx, my) and game_state["language"] != "ru":
            ru_surf, _ = draw_text("Русский", fonts["small_font"], (255, 200, 0))
        screen.blit(ru_surf, ru_btn)
        self.buttons["ru_btn"] = ru_btn

        en_surf, en_btn = draw_text(
            "English",
            fonts["small_font"],
            (0, 150, 0) if game_state["language"] == "en" else (0, 0, 0),
        )
        en_btn.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 60)
        if en_btn.collidepoint(mx, my) and game_state["language"] != "en":
            en_surf, _ = draw_text("English", fonts["small_font"], (255, 200, 0))
        screen.blit(en_surf, en_btn)
        self.buttons["en_btn"] = en_btn

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class GameModeMenuState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("diff_slider") and self.buttons[
                "diff_slider"
            ].collidepoint(mx, my):
                game_state["is_dragging_difficulty"] = True
            elif self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("main_menu", game_state)
            else:
                for mode, btn in self.buttons.items():
                    if mode not in ["diff_slider", "back_btn"] and btn.collidepoint(
                        mx, my
                    ):
                        game_state["game_mode"] = mode.replace("_btn", "")
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            game_state["is_dragging_difficulty"] = False

    def update(self, dt, mx, my, game_state):
        if game_state.get("is_dragging_difficulty"):
            slider = self.buttons["diff_slider"]
            rel = mx - slider.x
            if rel < slider.width / 3:
                game_state["difficulty"] = "easy"
            elif rel < 2 * slider.width / 3:
                game_state["difficulty"] = "medium"
            else:
                game_state["difficulty"] = "hard"

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}
        sy, modes = 220, [
            "classic",
            "sharpshooter",
            "obstacle",
            "campaign",
            "training",
            "developer",
        ]
        for i, m in enumerate(modes):
            t_key = (
                m
                if m not in ["obstacle", "developer"]
                else ("obstacle_mode" if m == "obstacle" else "dev_mode")
            )
            color = (0, 150, 0) if game_state["game_mode"] == m else (0, 0, 0)
            t_surf, t_btn = draw_text(
                get_text(texts, t_key), fonts["small_font"], color
            )
            t_btn.topleft = (50, sy + 50 * i)
            if t_btn.collidepoint(mx, my) and game_state["game_mode"] != m:
                t_surf, _ = draw_text(
                    get_text(texts, t_key), fonts["small_font"], (255, 200, 0)
                )
            screen.blit(t_surf, t_btn)
            self.buttons[f"{m}_btn"] = t_btn

        if game_state["game_mode"] in ["classic", "sharpshooter", "obstacle"]:
            sl = pygame.Rect(400, 350, 300, 10)
            pygame.draw.rect(screen, (200, 200, 200), sl)
            kp = (
                sl.x + 10
                if game_state["difficulty"] == "easy"
                else (
                    sl.centerx
                    if game_state["difficulty"] == "medium"
                    else sl.right - 10
                )
            )
            pygame.draw.circle(screen, (255, 0, 0), (kp, sl.centery), 10)
            screen.blit(
                draw_text(get_text(texts, "easy"), fonts["small_font"], (0, 0, 0))[0],
                (sl.x, sl.y + 15),
            )
            m_surf = draw_text(
                get_text(texts, "medium"), fonts["small_font"], (0, 0, 0)
            )[0]
            screen.blit(m_surf, (sl.centerx - m_surf.get_width() // 2, sl.y + 15))
            h_surf = draw_text(get_text(texts, "hard"), fonts["small_font"], (0, 0, 0))[
                0
            ]
            screen.blit(h_surf, (sl.right - h_surf.get_width(), sl.y + 15))
            self.buttons["diff_slider"] = sl

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class AchievementsMenuState(State):
    def __init__(self):
        self.buttons, self.conf_buttons = {}, {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.get("show_achievements_reset_confirm"):
                if self.conf_buttons.get("yes_btn") and self.conf_buttons[
                    "yes_btn"
                ].collidepoint(mx, my):
                    ptr = game_state["achievements_viewing_profile"]
                    game_state["all_profiles_data"][ptr] = create_default_achievements()
                    if ptr == game_state["current_profile"]:
                        game_state.update(game_state["all_profiles_data"][ptr])
                    game_state["show_achievements_reset_confirm"] = False
                elif self.conf_buttons.get("no_btn") and self.conf_buttons[
                    "no_btn"
                ].collidepoint(mx, my):
                    game_state["show_achievements_reset_confirm"] = False
                return

            if self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("main_menu", game_state)
            elif self.buttons.get("reset_btn") and self.buttons[
                "reset_btn"
            ].collidepoint(mx, my):
                game_state["show_achievements_reset_confirm"] = True
            else:
                for name, btn in self.buttons.get("profiles", {}).items():
                    if btn.collidepoint(mx, my):
                        game_state["achievements_viewing_profile"] = name
                        return
                for diff, btn in self.buttons.get("diffs", {}).items():
                    if btn.collidepoint(mx, my):
                        game_state["achievements_viewing_difficulty"] = diff
                        return

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {"profiles": {}, "diffs": {}}
        yo = 120
        screen.blit(
            draw_text(get_text(texts, "profiles"), fonts["small_font"], (0, 0, 0))[0],
            (50, 150 + yo),
        )
        yp = 200 + yo
        for name in game_state["all_profiles_data"].keys():
            iv = name == game_state.get("achievements_viewing_profile")
            t_surf, t_btn = draw_text(
                name, fonts["small_font"], (0, 150, 0) if iv else (0, 0, 0)
            )
            t_btn.topleft = (50, yp)
            if not iv and t_btn.collidepoint(mx, my):
                t_surf, _ = draw_text(name, fonts["small_font"], (255, 200, 0))
            screen.blit(t_surf, t_btn)
            self.buttons["profiles"][name] = t_btn
            yp += 40

        vp_data = game_state["all_profiles_data"].get(
            game_state.get("achievements_viewing_profile", ""), {}
        )
        screen.blit(
            draw_text(
                f"{get_text(texts, 'stats_for')} '{game_state.get('achievements_viewing_profile')}':",
                fonts["small_font"],
                (0, 0, 0),
            )[0],
            (350, 150 + yo),
        )

        diffs, cx = {
            "easy": get_text(texts, "easy"),
            "medium": get_text(texts, "medium"),
            "hard": get_text(texts, "hard"),
        }, 350
        for k, txt in diffs.items():
            iss = k == game_state.get("achievements_viewing_difficulty", "easy")
            d_surf, d_btn = draw_text(
                txt, fonts["info_font"], (0, 150, 0) if iss else (0, 0, 0)
            )
            d_btn.topleft = (cx, 200 + yo)
            if not iss and d_btn.collidepoint(mx, my):
                d_surf, _ = draw_text(txt, fonts["info_font"], (255, 200, 0))
            screen.blit(d_surf, d_btn)
            self.buttons["diffs"][k] = d_btn
            cx += d_btn.width + 20

        df, sf = (
            game_state.get("achievements_viewing_difficulty", "easy"),
            fonts["pedia_font"],
        )
        screen.blit(
            draw_text(
                f"{get_text(texts, 'max_combo_classic')} {vp_data.get(f'max_combo_classic_{df}', 0)}",
                sf,
                (0, 0, 0),
            )[0],
            (350, 270 + yo),
        )
        screen.blit(
            draw_text(
                f"{get_text(texts, 'max_combo_sharpshooter')} {vp_data.get(f'max_combo_sharpshooter_{df}', 0)}",
                sf,
                (0, 0, 0),
            )[0],
            (350, 310 + yo),
        )
        screen.blit(
            draw_text(
                f"{get_text(texts, 'max_combo_obstacle')} {vp_data.get(f'max_combo_obstacle_{df}', 0)}",
                sf,
                (0, 0, 0),
            )[0],
            (350, 350 + yo),
        )

        r_surf, r_btn = draw_text(
            get_text(texts, "reset_profile"), fonts["small_font"], (180, 0, 0)
        )
        r_btn.bottomright = (game_state["WIDTH"] - 20, game_state["HEIGHT"] - 20)
        if r_btn.collidepoint(mx, my):
            r_surf, _ = draw_text(
                get_text(texts, "reset_profile"), fonts["small_font"], (255, 0, 0)
            )
        screen.blit(r_surf, r_btn)
        self.buttons["reset_btn"] = r_btn

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn

        if game_state.get("show_achievements_reset_confirm"):
            overlay = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            dr = pygame.Rect(0, 0, 600, 200)
            dr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
            pygame.draw.rect(screen, (50, 50, 70), dr)
            pygame.draw.rect(screen, (200, 200, 220), dr, 3)
            q_surf, q_rect = draw_text(
                f"{get_text(texts, 'confirm_reset_stats')} '{game_state.get('achievements_viewing_profile')}'?",
                fonts["small_font"],
                (255, 255, 255),
            )
            q_rect.centerx, q_rect.y = dr.centerx, dr.y + 40
            screen.blit(q_surf, q_rect)
            y_surf, y_btn = draw_text(
                get_text(texts, "yes"), fonts["small_font"], (200, 80, 80)
            )
            y_btn.center = (dr.centerx - 80, dr.centery + 40)
            if y_btn.collidepoint(mx, my):
                y_surf, _ = draw_text(
                    get_text(texts, "yes"), fonts["small_font"], (255, 120, 120)
                )
            screen.blit(y_surf, y_btn)
            n_surf, n_btn = draw_text(
                get_text(texts, "no"), fonts["small_font"], (80, 200, 80)
            )
            n_btn.center = (dr.centerx + 80, dr.centery + 40)
            if n_btn.collidepoint(mx, my):
                n_surf, _ = draw_text(
                    get_text(texts, "no"), fonts["small_font"], (120, 255, 120)
                )
            screen.blit(n_surf, n_btn)
            self.conf_buttons = {"yes_btn": y_btn, "no_btn": n_btn}


class BirdpediaMenuState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("main_menu", game_state)
            else:
                for item, btn in self.buttons.items():
                    if item != "back_btn" and btn.collidepoint(mx, my):
                        game_state["birdpedia_item_selected"] = item
                        game_state["state_manager"].change_state(
                            "birdpedia_detail", game_state
                        )

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}
        items = get_text(texts, "pedia_items")
        ipc = (len(items) + 1) // 2
        for i, item in enumerate(items):
            x, y = 150 if i < ipc else 450, 300 + (i if i < ipc else i - ipc) * 40
            t_surf, t_btn = draw_text(item, fonts["small_font"], (0, 0, 0))
            t_btn.topleft = (x, y)
            if t_btn.collidepoint(mx, my):
                t_surf, _ = draw_text(item, fonts["small_font"], (255, 200, 0))
            screen.blit(t_surf, t_btn)
            self.buttons[item] = t_btn

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class BirdpediaDetailState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("birdpedia_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("birdpedia_menu", game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {}

        item = game_state.get("birdpedia_item_selected", "Описание")
        img_key = PEDIA_IMAGES.get(item)
        if img_key:
            bg_rect = pygame.Rect(100, 280, 150, 150)
            pygame.draw.rect(screen, (20, 20, 20), bg_rect)
            img = (
                game_state["images"][img_key[0]][img_key[1]]
                if isinstance(img_key, tuple)
                else game_state["images"][img_key]
            )
            s_img = pygame.transform.scale(img, (120, 120))
            screen.blit(s_img, s_img.get_rect(center=bg_rect.center))

        words = (
            get_text(texts, "pedia_descriptions")
            .get(item, get_text(texts, "pedia_not_found"))
            .split(" ")
        )
        x, y, sp = 300, 280, fonts["pedia_font"].size(" ")[0]
        for w in words:
            ws = fonts["pedia_font"].render(w, True, (0, 0, 0))
            if x + ws.get_width() >= 750:
                x, y = 300, y + fonts["pedia_font"].get_linesize()
            screen.blit(ws, (x, y))
            x += ws.get_width() + sp

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class LevelSelectionState(State):
    def __init__(self):
        self.buttons = {}

    def handle_event(self, event, mx, my, game_state):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            game_state["state_manager"].change_state("main_menu", game_state)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.buttons.get("back_btn") and self.buttons["back_btn"].collidepoint(
                mx, my
            ):
                game_state["state_manager"].change_state("main_menu", game_state)
            else:
                for lvl, btn in self.buttons.get("levels", {}).items():
                    if btn.collidepoint(mx, my):
                        reset_game(game_state)
                        game_state["state_manager"].change_state("gameplay", game_state)
                        break

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["menu_background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        fonts, texts = game_state["fonts"], game_state["texts"]
        self.buttons = {"levels": {}}

        t_surf, t_rect = draw_text(
            get_text(texts, "level_selection_title"), fonts["font"], (0, 0, 0)
        )
        t_rect.centerx, t_rect.y = screen.get_width() // 2, 80
        screen.blit(t_surf, t_rect)
        cols, total, sp, r = 5, 20, 100, 35
        sx, sy = (screen.get_width() - (cols - 1) * sp) // 2, t_rect.bottom + 80

        for i in range(total):
            x, y = sx + (i % cols) * sp, sy + (i // cols) * sp
            lr = pygame.Rect(x - r, y - r, r * 2, r * 2)
            c = (150, 200, 255) if lr.collidepoint(mx, my) else (100, 150, 255)
            pygame.draw.circle(screen, c, (x, y), r)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), r, 3)
            ts, _ = draw_text(str(i + 1), fonts["small_font"], (255, 255, 255))
            screen.blit(ts, ts.get_rect(center=(x, y)))
            self.buttons["levels"][i + 1] = lr

        b_surf, b_btn = draw_text(
            get_text(texts, "back"), fonts["small_font"], (0, 0, 0)
        )
        b_btn.bottomleft = (20, game_state["HEIGHT"] - 20)
        if b_btn.collidepoint(mx, my):
            b_surf, _ = draw_text(
                get_text(texts, "back"), fonts["small_font"], (255, 200, 0)
            )
        screen.blit(b_surf, b_btn)
        self.buttons["back_btn"] = b_btn


class GameplayState(State):
    def __init__(self):
        self.ui_buttons = {}

    def handle_event(self, event, mx, my, game_state):
        mb = game_state.get("main_bird")
        is_paused = game_state["paused"] or (
            game_state["game_mode"] == "campaign"
            and (
                game_state["campaign_is_processing"]
                or game_state["campaign_is_swapping"]
                or game_state["campaign_level_complete"]
                or game_state.get("show_campaign_hint_popup")
            )
        )

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state["state_manager"].change_state("main_menu", game_state)
                if game_state["game_mode"] == "campaign":
                    game_state["campaign_level_complete"] = False
            elif event.key == pygame.K_r:
                reset_game(game_state)
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                if (
                    not game_state.get("training_complete")
                    and not game_state.get("show_hint_popup")
                    and not game_state.get("show_training_popup")
                    and not game_state.get("show_campaign_hint_popup")
                ):
                    game_state["paused"] = not game_state["paused"]

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.get("show_campaign_hint_popup"):
                if self.ui_buttons.get("close_hint") and self.ui_buttons[
                    "close_hint"
                ].collidepoint(mx, my):
                    game_state["show_campaign_hint_popup"], game_state["paused"] = (
                        False,
                        False,
                    )
                return
            if game_state.get("show_training_popup"):
                if self.ui_buttons.get("cont_training") and self.ui_buttons[
                    "cont_training"
                ].collidepoint(mx, my):
                    game_state["show_training_popup"], game_state["paused"] = (
                        False,
                        False,
                    )
                    get_next_bird(game_state)
                return
            if game_state.get("show_hint_popup"):
                if self.ui_buttons.get("close_hint") and self.ui_buttons[
                    "close_hint"
                ].collidepoint(mx, my):
                    game_state["show_hint_popup"], game_state["paused"] = False, False
                return
            if game_state.get("campaign_level_complete"):
                if self.ui_buttons.get("restart_btn") and self.ui_buttons[
                    "restart_btn"
                ].collidepoint(mx, my):
                    reset_game(game_state)
                elif self.ui_buttons.get("exit_btn") and self.ui_buttons[
                    "exit_btn"
                ].collidepoint(mx, my):
                    game_state["state_manager"].change_state("main_menu", game_state)
                    game_state["campaign_level_complete"] = False
                return
            if game_state.get("training_complete"):
                if self.ui_buttons.get("restart_btn") and self.ui_buttons[
                    "restart_btn"
                ].collidepoint(mx, my):
                    reset_game(game_state)
                elif self.ui_buttons.get("exit_btn") and self.ui_buttons[
                    "exit_btn"
                ].collidepoint(mx, my):
                    game_state["state_manager"].change_state("main_menu", game_state)
                    game_state["training_complete"] = False
                return

            sc = game_state["scale_factor"]
            sp_r = pygame.Rect(
                game_state["WIDTH"] - int(50 * sc),
                int(10 * sc),
                int(40 * sc),
                int(40 * sc),
            )
            ps_r = pygame.Rect(
                game_state["WIDTH"] - int(100 * sc),
                int(10 * sc),
                int(40 * sc),
                int(40 * sc),
            )
            lb_r = pygame.Rect(
                game_state["WIDTH"] // 2 - int(30 * sc),
                int(10 * sc),
                int(60 * sc),
                int(40 * sc),
            )

            if sp_r.collidepoint(mx, my):
                game_state["sound_on"] = not game_state["sound_on"]
                update_all_volumes(game_state)
                return
            if ps_r.collidepoint(mx, my):
                game_state["paused"] = not game_state["paused"]
                return
            if lb_r.collidepoint(mx, my):
                if game_state["game_mode"] == "campaign":
                    game_state["show_campaign_hint_popup"] = True
                else:
                    game_state["show_hint_popup"] = True
                game_state["paused"] = True
                return

            if game_state["game_mode"] == "campaign" and not is_paused:
                gr = game_state["campaign_grid_rect"]
                if gr.collidepoint(mx, my):
                    cs = game_state["campaign_cell_size"]
                    game_state["campaign_drag_start_pos"] = (mx, my)
                    game_state["campaign_drag_start_tile"] = (
                        int((my - gr.y) / cs),
                        int((mx - gr.x) / cs),
                    )
                    game_state["campaign_is_dragging_tile"] = True
            elif mb and not game_state.get("game_over") and not is_paused:
                if mb.state == "idle" and mb.rect.collidepoint(mx, my):
                    mb.start_drag()
                    game_state["show_rope"] = True
                elif (
                    mb.state == "flying"
                    and mb.type_index == 2
                    and mb.boost_available
                    and not mb.is_boosted
                ):
                    if game_state["sound_on"]:
                        game_state["sounds"]["boost_sound"].play()
                    mb.vx *= 2.0
                    mb.vy *= 2.0
                    mb.is_boosted = True
                    game_state["boost_trail_start_time"] = time.time()
                    create_spark_particle(game_state["spark_particles"], mb.x, mb.y)
                elif mb.state == "flying" and mb.type_index == 3 and mb.split_available:
                    split_bird(game_state)
                elif (
                    mb.state == "flying"
                    and mb.type_index == 4
                    and mb.boomerang_available
                ):
                    activate_boomerang(game_state)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            game_state["campaign_is_dragging_tile"] = False
            if game_state.get("campaign_drag_start_tile"):
                sr, sc = game_state["campaign_drag_start_tile"]
                smx, smy = game_state["campaign_drag_start_pos"]
                dist = math.hypot(mx - smx, my - smy)
                if dist < game_state["campaign_cell_size"] / 2:
                    if game_state.get("campaign_selected_tile") is None:
                        game_state["campaign_selected_tile"] = (sr, sc)
                    else:
                        sel_r, sel_c = game_state["campaign_selected_tile"]
                        if abs(sr - sel_r) + abs(sc - sel_c) == 1:
                            start_swap_animation(game_state, (sel_r, sel_c), (sr, sc))
                        elif (sr, sc) == (sel_r, sel_c):
                            game_state["campaign_selected_tile"] = None
                        else:
                            game_state["campaign_selected_tile"] = (sr, sc)
                else:
                    dx, dy = mx - smx, my - smy
                    er, ec = sr, sc
                    if abs(dx) > abs(dy):
                        ec += 1 if dx > 0 else -1
                    else:
                        er += 1 if dy > 0 else -1
                    start_swap_animation(game_state, (sr, sc), (er, ec))
                game_state["campaign_drag_start_tile"] = None
                game_state["campaign_drag_start_pos"] = None

            if mb and mb.state == "dragging":
                mb.launch(
                    game_state["sling_x"],
                    game_state["sling_y"],
                    game_state["scale_factor"],
                )
                (
                    game_state["show_rope"],
                    game_state["current_shot_hit"],
                    game_state["last_shot_path"],
                ) = (False, False, [])
                if game_state["sound_on"]:
                    game_state["sounds"]["fly_sound"].play()

    def update(self, dt, mx, my, game_state):
        mb = game_state.get("main_bird")
        dt_factor = dt * 60.0
        is_paused = game_state["paused"] or (
            game_state["game_mode"] == "campaign"
            and (
                game_state["campaign_is_processing"]
                or game_state["campaign_is_swapping"]
                or game_state["campaign_level_complete"]
                or game_state.get("show_campaign_hint_popup")
            )
        )

        if game_state.get("screen_shake", 0) > 0:
            game_state["screen_shake"] -= 1 * dt_factor
            game_state["shake_offset"] = (random.randint(-5, 5), random.randint(-5, 5))
        else:
            game_state["shake_offset"] = (0, 0)

        if mb and mb.state == "dragging" and not is_paused:
            mb.drag_to(mx, my, game_state["WIDTH"], game_state["HEIGHT"])

        if game_state.get("campaign_is_swapping"):
            anim = game_state["campaign_swap_anim"]
            anim["progress"] += 0.15 * dt_factor
            if anim["progress"] >= 1.0:
                anim["progress"] = 1.0
                r1, c1 = anim["tile1_pos"]
                r2, c2 = anim["tile2_pos"]
                if not anim["reverse"]:
                    (
                        game_state["campaign_board"][r1][c1],
                        game_state["campaign_board"][r2][c2],
                    ) = (
                        game_state["campaign_board"][r2][c2],
                        game_state["campaign_board"][r1][c1],
                    )
                    game_state["campaign_is_processing"] = True
                    game_state["campaign_board_state"] = "idle"
                game_state["campaign_is_swapping"] = False
                game_state["campaign_swap_anim"] = None

        if game_state["game_mode"] == "campaign" and game_state.get(
            "campaign_is_processing"
        ):
            update_campaign_board(dt, game_state)
        update_game_state(dt, game_state)

        if (
            not is_paused
            and not game_state.get("game_over")
            and not game_state.get("training_complete")
        ):
            if mb and mb.state == "jumping":
                mb.update(
                    dt,
                    game_state["gravity"],
                    game_state["GROUND_LEVEL"],
                    game_state["WIDTH"],
                    game_state["HEIGHT"],
                )
            elif mb and mb.state in ["flying", "tumbling"]:
                if (
                    len(game_state["last_shot_path"]) == 0
                    or math.hypot(
                        game_state["last_shot_path"][-1][0] - mb.x,
                        game_state["last_shot_path"][-1][1] - mb.y,
                    )
                    > 20
                ):
                    game_state["last_shot_path"].append((mb.x, mb.y))
                if random.random() < 0.5:
                    create_trail_particle(game_state["trail_particles"], mb.x, mb.y)
                if (
                    mb.update(
                        dt,
                        game_state["gravity"],
                        game_state["GROUND_LEVEL"],
                        game_state["WIDTH"],
                        game_state["HEIGHT"],
                    )
                    == "hit_ground"
                ):
                    create_dust_particle(
                        game_state["dust_particles"],
                        mb.x,
                        game_state["GROUND_LEVEL"],
                        count=20,
                    )

            if "targets" in game_state:
                game_state["targets"].update(
                    dt, game_state["WIDTH"], game_state["HEIGHT"]
                )
            if "obstacles" in game_state:
                game_state["obstacles"].update(
                    dt, game_state["WIDTH"], game_state["HEIGHT"]
                )

            for sb in game_state.get("small_birds", []):
                if (
                    sb.update(dt, game_state["gravity"], game_state["GROUND_LEVEL"])
                    == "hit_ground"
                ):
                    create_dust_particle(
                        game_state["dust_particles"],
                        sb.x,
                        game_state["GROUND_LEVEL"],
                        count=10,
                    )
            for dp in game_state.get("defeated_pigs", []):
                if (
                    dp.update(dt, game_state["gravity"], game_state["GROUND_LEVEL"])
                    == "hit_ground"
                ):
                    create_dust_particle(
                        game_state["dust_particles"],
                        dp.x,
                        dp.y + dp.size // 2,
                        count=30,
                    )

            update_feathers(game_state["feather_particles"], dt)
            td_img = game_state["images"]["target_defeated_img"]

            if mb and mb.state in ["flying", "tumbling"]:
                for t in pygame.sprite.spritecollide(
                    mb, game_state.get("targets", []), False
                ):
                    game_state["current_shot_hit"] = True
                    if mb.type_index == 1:
                        game_state["screen_shake"] = 15
                        game_state["explosion_center"] = t.rect.center
                        game_state["explosion_active"] = True
                        game_state["explosion_frames"] = game_state[
                            "MAX_EXPLOSION_FRAMES"
                        ]
                        if game_state["sound_on"]:
                            game_state["sounds"]["explosion_sound"].play()
                        rem = [
                            x
                            for x in game_state["targets"]
                            if math.hypot(
                                x.rect.centerx - t.rect.centerx,
                                x.rect.centery - t.rect.centery,
                            )
                            <= game_state["EXPLOSION_RADIUS"]
                        ]
                        for x in rem:
                            game_state["defeated_pigs"].add(
                                DefeatedPig(
                                    x.rect.centerx,
                                    x.rect.centery,
                                    random.uniform(-2, 0),
                                    game_state["object_size"],
                                    td_img,
                                )
                            )
                            x.kill()
                        if rem:
                            game_state["score"] += len(rem)
                            game_state["combo"] += len(rem)
                            update_max_combo(game_state, game_state["current_profile"])
                    else:
                        create_feather_explosion(
                            game_state["feather_particles"],
                            t.rect.centerx,
                            t.rect.centery,
                            mb.type_index,
                        )
                        game_state["score"] += 1
                        game_state["combo"] += 1
                        update_max_combo(game_state, game_state["current_profile"])
                        if game_state["sound_on"]:
                            game_state["sounds"]["hit_sound"].play()
                        game_state["defeated_pigs"].add(
                            DefeatedPig(
                                t.rect.centerx,
                                t.rect.centery,
                                -abs(mb.vy * 0.2),
                                game_state["object_size"],
                                td_img,
                            )
                        )
                        t.kill()
                    mb.state = "dead"
                    break

                if game_state["game_mode"] == "obstacle" and mb.state in [
                    "flying",
                    "tumbling",
                ]:
                    for o in pygame.sprite.spritecollide(
                        mb, game_state.get("obstacles", []), False
                    ):
                        create_brick_shatter(
                            game_state["dust_particles"], o.rect.centerx, o.rect.centery
                        )
                        o.kill()
                        mb.vx *= 0.5
                        mb.vy *= 0.5
                        if game_state["sound_on"]:
                            game_state["sounds"]["brick_sound"].play()
                        break

            for sb in game_state.get("small_birds", []):
                if sb.state in ["flying", "tumbling"]:
                    for t in pygame.sprite.spritecollide(
                        sb, game_state.get("targets", []), False
                    ):
                        create_feather_explosion(
                            game_state["feather_particles"],
                            t.rect.centerx,
                            t.rect.centery,
                            3,
                        )
                        game_state["current_shot_hit"] = True
                        game_state["score"] += 1
                        game_state["combo"] += 1
                        update_max_combo(game_state, game_state["current_profile"])
                        game_state["defeated_pigs"].add(
                            DefeatedPig(
                                t.rect.centerx,
                                t.rect.centery,
                                0,
                                game_state["object_size"],
                                td_img,
                            )
                        )
                        t.kill()
                        sb.state = "dead"
                        sb.kill()
                        break
                    if game_state["game_mode"] == "obstacle" and sb.state != "dead":
                        for o in pygame.sprite.spritecollide(
                            sb, game_state.get("obstacles", []), False
                        ):
                            create_brick_shatter(
                                game_state["dust_particles"],
                                o.rect.centerx,
                                o.rect.centery,
                            )
                            o.kill()
                            sb.vx *= 0.5
                            sb.vy *= 0.5
                            if game_state["sound_on"]:
                                game_state["sounds"]["brick_sound"].play()
                            break

            for dp in [
                x
                for x in game_state.get("defeated_pigs", [])
                if x.timer <= 0 and x.on_ground
            ]:
                dp.kill()
                if game_state["game_mode"] not in ["training", "developer", "campaign"]:
                    sm = SPEED_MULTIPLIER.get(game_state["difficulty"], 0)
                    t_img = game_state["images"]["target_img"]
                    if game_state["game_mode"] != "sharpshooter":
                        while True:
                            nr = create_target(
                                game_state["WIDTH"],
                                game_state["HEIGHT"],
                                game_state["object_size"],
                            )
                            if not any(
                                nr.inflate(10, 10).colliderect(t.rect)
                                for t in game_state["targets"]
                            ) and not any(
                                nr.inflate(10, 10).colliderect(o.rect)
                                for o in game_state["obstacles"]
                            ):
                                game_state["targets"].add(
                                    Target(
                                        nr,
                                        (
                                            random.uniform(0.5, 2.0)
                                            * sm
                                            * random.choice([-1, 1])
                                            if sm > 0
                                            else 0
                                        ),
                                        (
                                            random.uniform(0.5, 2.0)
                                            * sm
                                            * random.choice([-1, 1])
                                            if sm > 0
                                            else 0
                                        ),
                                        t_img,
                                    )
                                )
                                break
                    else:
                        game_state["targets"].add(
                            Target(
                                create_target(
                                    game_state["WIDTH"],
                                    game_state["HEIGHT"],
                                    game_state["object_size"],
                                ),
                                (
                                    random.uniform(0.5, 2.0)
                                    * sm
                                    * random.choice([-1, 1])
                                    if sm > 0
                                    else 0
                                ),
                                (
                                    random.uniform(0.5, 2.0)
                                    * sm
                                    * random.choice([-1, 1])
                                    if sm > 0
                                    else 0
                                ),
                                t_img,
                            )
                        )
                        game_state["target_timer_start"] = time.time()

            if (
                mb
                and mb.state in ["stopped", "out_of_bounds", "dead"]
                and len(game_state.get("small_birds", [])) == 0
            ):
                if mb.state in ["stopped", "out_of_bounds"]:
                    if not game_state["current_shot_hit"] and game_state[
                        "game_mode"
                    ] not in ["developer", "training", "campaign"]:
                        game_state["lives"] -= 1
                        game_state["combo"] = 0
                    mb.state = "dead"
                get_next_bird(game_state)

            if (
                game_state["game_mode"] == "sharpshooter"
                and len(game_state.get("targets", [])) > 0
            ):
                if (
                    game_state["target_duration"]
                    - (time.time() - game_state["target_timer_start"])
                    <= 0
                ):
                    for t in game_state["targets"]:
                        t.kill()
                    game_state["lives"] -= 1
                    game_state["combo"] = 0
                    if game_state["lives"] > 0:
                        sm = SPEED_MULTIPLIER.get(game_state["difficulty"], 0)
                        t_img = game_state["images"]["target_img"]
                        game_state["targets"].add(
                            Target(
                                create_target(
                                    game_state["WIDTH"],
                                    game_state["HEIGHT"],
                                    game_state["object_size"],
                                ),
                                (
                                    random.uniform(0.5, 2.0)
                                    * sm
                                    * random.choice([-1, 1])
                                    if sm > 0
                                    else 0
                                ),
                                (
                                    random.uniform(0.5, 2.0)
                                    * sm
                                    * random.choice([-1, 1])
                                    if sm > 0
                                    else 0
                                ),
                                t_img,
                            )
                        )
                        game_state["target_timer_start"] = time.time()
                    else:
                        game_state["game_over"] = True

    def draw(self, screen, mx, my, game_state):
        shake = game_state.get("shake_offset", (0, 0))
        bg = game_state["images"]["background"]
        screen.blit(
            bg,
            (
                bg.get_rect(center=screen.get_rect().center).left + shake[0],
                bg.get_rect(center=screen.get_rect().center).top + shake[1],
            ),
        )
        self.ui_buttons = {}

        if game_state["game_mode"] == "campaign":
            self._draw_campaign(screen, mx, my, game_state)
        elif not game_state.get("training_complete"):
            self._draw_normal(screen, mx, my, game_state)
        else:
            self._draw_tc(screen, mx, my, game_state)

        if game_state["paused"]:
            s = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            s.fill((0, 0, 0, 128))
            screen.blit(s, (0, 0))
            if (
                not game_state.get("show_hint_popup")
                and not game_state.get("show_training_popup")
                and not game_state.get("show_campaign_hint_popup")
            ):
                p_surf, rect = draw_text(
                    game_state["texts"]["pause"],
                    game_state["fonts"]["large_font"],
                    (255, 255, 255),
                )
                screen.blit(
                    p_surf,
                    p_surf.get_rect(
                        center=(game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
                    ),
                )

        draw_particles(screen, game_state["trail_particles"])
        draw_particles(screen, game_state["dust_particles"])
        draw_particles(screen, game_state["spark_particles"])
        draw_feathers(
            screen,
            game_state["feather_particles"],
            game_state["images"]["feather_imgs"],
        )

        if game_state["explosion_active"]:
            er, mx_f = (
                game_state["EXPLOSION_RADIUS"],
                game_state["MAX_EXPLOSION_FRAMES"],
            )
            sm_copy = game_state["images"]["smoke_img"].copy()
            sm_copy.set_alpha(
                max(
                    0,
                    min(
                        255, int(255 * (max(0, game_state["explosion_frames"]) / mx_f))
                    ),
                )
            )
            screen.blit(
                sm_copy,
                (
                    game_state["explosion_center"][0] - er,
                    game_state["explosion_center"][1] - er,
                ),
            )

        if game_state.get("show_campaign_hint_popup"):
            self._draw_chp(screen, mx, my, game_state)
        elif game_state.get("show_training_popup"):
            self._draw_tp(screen, mx, my, game_state)
        elif game_state.get("show_hint_popup"):
            self._draw_hp(screen, mx, my, game_state)

    def _draw_campaign(self, screen, mx, my, game_state):
        br, cs, board = (
            game_state["campaign_grid_rect"],
            game_state["campaign_cell_size"],
            game_state["campaign_board"],
        )
        bs = pygame.Surface(br.size, pygame.SRCALPHA)
        bs.fill((0, 0, 0, 100))
        anim_pos = set()
        if game_state.get("campaign_is_swapping"):
            anim_pos.update(
                [
                    game_state["campaign_swap_anim"]["tile1_pos"],
                    game_state["campaign_swap_anim"]["tile2_pos"],
                ]
            )
        if game_state.get("campaign_is_dragging_tile"):
            anim_pos.add(game_state["campaign_drag_start_tile"])

        if board:
            for r in range(CAMPAIGN_GRID_SIZE):
                for c in range(CAMPAIGN_GRID_SIZE):
                    if (r, c) in anim_pos:
                        continue
                    b_idx = board[r][c]
                    if b_idx is not None:
                        alpha, sf = 255, 0.9
                        if game_state.get("campaign_board_state") == "clearing" and (
                            r,
                            c,
                        ) in game_state.get("campaign_matched_tiles", []):
                            p = game_state["campaign_clear_progress"]
                            alpha, sf = int(255 * (1.0 - p)), 0.9 * (1.0 - p)
                        if alpha > 0:
                            si = int(cs * sf)
                            if si > 0:
                                simg = pygame.transform.scale(
                                    game_state["images"]["bird_imgs"][b_idx], (si, si)
                                )
                                simg.set_alpha(alpha)
                                bs.blit(
                                    simg,
                                    simg.get_rect(
                                        center=(c * cs + cs / 2, r * cs + cs / 2)
                                    ),
                                )

        def draw_at(idx, cx, cy, al=255):
            img = pygame.transform.scale(
                game_state["images"]["bird_imgs"][idx], (int(cs * 0.9), int(cs * 0.9))
            )
            img.set_alpha(al)
            bs.blit(img, img.get_rect(center=(cx, cy)))

        if game_state.get("campaign_is_swapping"):
            anim = game_state["campaign_swap_anim"]
            p = anim["progress"]
            r1, c1 = anim["tile1_pos"]
            r2, c2 = anim["tile2_pos"]
            x1, y1 = c1 * cs + cs / 2, r1 * cs + cs / 2
            x2, y2 = c2 * cs + cs / 2, r2 * cs + cs / 2
            draw_at(anim["tile1_type"], x1 + (x2 - x1) * p, y1 + (y2 - y1) * p)
            draw_at(anim["tile2_type"], x2 + (x1 - x2) * p, y2 + (y1 - y2) * p)

        if game_state.get("campaign_is_dragging_tile"):
            r, c = game_state["campaign_drag_start_tile"]
            if board[r][c] is not None:
                draw_at(board[r][c], c * cs + cs / 2, r * cs + cs / 2, 100)
                draw_at(board[r][c], mx - br.x, my - br.y, 200)

        def get_ay(td, ref=False):
            return (
                (
                    (
                        (td["end_pos"][0] + td["start_y_offset"])
                        if ref
                        else td["start_pos"][0]
                    )
                    * cs
                )
                + cs / 2
                + (
                    (
                        (td["end_pos"][0] * cs + cs / 2)
                        - (
                            (
                                (
                                    (td["end_pos"][0] + td["start_y_offset"])
                                    if ref
                                    else td["start_pos"][0]
                                )
                                * cs
                            )
                            + cs / 2
                        )
                    )
                    * td["progress"]
                )
            )

        if game_state.get("campaign_board_state") == "falling":
            for t in game_state.get("campaign_falling_tiles", []):
                draw_at(t["type"], t["end_pos"][1] * cs + cs / 2, get_ay(t))
        if game_state.get("campaign_board_state") == "refilling":
            for t in game_state.get("campaign_refilling_tiles", []):
                draw_at(t["type"], t["end_pos"][1] * cs + cs / 2, get_ay(t, True))

        if game_state.get("campaign_selected_tile") and not game_state.get(
            "campaign_is_swapping"
        ):
            pygame.draw.rect(
                bs,
                (255, 255, 0, 200),
                (
                    game_state["campaign_selected_tile"][1] * cs,
                    game_state["campaign_selected_tile"][0] * cs,
                    cs,
                    cs,
                ),
                4,
                border_radius=5,
            )

        screen.blit(bs, br.topleft)
        screen.blit(
            draw_text(
                f"{get_text(game_state['texts'], 'score_colon')} {game_state['campaign_score']} / {game_state['campaign_target_score']}",
                game_state["fonts"]["small_font"],
                (0, 0, 0),
            )[0],
            (br.left, br.top - 40),
        )

        if game_state["sound_on"]:
            screen.blit(
                game_state["images"]["speaker_on_img"], (game_state["WIDTH"] - 50, 10)
            )
        else:
            screen.blit(
                game_state["images"]["speaker_off_img"], (game_state["WIDTH"] - 50, 10)
            )
        if game_state["paused"]:
            screen.blit(
                game_state["images"]["resume_img"], (game_state["WIDTH"] - 100, 10)
            )
        else:
            screen.blit(
                game_state["images"]["pause_img"], (game_state["WIDTH"] - 100, 10)
            )
        screen.blit(
            game_state["images"]["lightbulb_img"],
            (
                game_state["WIDTH"] // 2 - int(30 * game_state["scale_factor"]),
                int(10 * game_state["scale_factor"]),
            ),
        )

        if game_state.get("campaign_level_complete"):
            ov = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            ov.fill((0, 0, 0, 180))
            screen.blit(ov, (0, 0))
            ws, wr = draw_text(
                get_text(game_state["texts"], "campaign_win"),
                game_state["fonts"]["font"],
                (255, 215, 0),
            )
            wr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 - 50)
            screen.blit(ws, wr)
            rs, rb = draw_text(
                get_text(game_state["texts"], "training_restart"),
                game_state["fonts"]["small_font"],
                (255, 255, 255),
            )
            rb.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 20)
            if rb.collidepoint(mx, my):
                rs, _ = draw_text(
                    get_text(game_state["texts"], "training_restart"),
                    game_state["fonts"]["small_font"],
                    (255, 200, 0),
                )
            screen.blit(rs, rb)
            self.ui_buttons["restart_btn"] = rb
            es, eb = draw_text(
                get_text(game_state["texts"], "training_exit_to_menu"),
                game_state["fonts"]["small_font"],
                (255, 255, 255),
            )
            eb.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 70)
            if eb.collidepoint(mx, my):
                es, _ = draw_text(
                    get_text(game_state["texts"], "training_exit_to_menu"),
                    game_state["fonts"]["small_font"],
                    (255, 200, 0),
                )
            screen.blit(es, eb)
            self.ui_buttons["exit_btn"] = eb

    def _draw_normal(self, screen, mx, my, game_state):
        gl, sc, qx, qg, bs = (
            game_state["GROUND_LEVEL"],
            game_state["scale_factor"],
            int(40 * game_state["scale_factor"]),
            int(60 * game_state["scale_factor"]),
            game_state["object_size"],
        )
        for i, b in enumerate(game_state["bird_queue"]):
            screen.blit(b, (qx + i * qg, gl - bs * 0.9))
        pygame.draw.circle(
            screen,
            (139, 69, 19),
            (game_state["sling_x"], game_state["sling_y"]),
            int(5 * sc),
        )

        mb = game_state.get("main_bird")
        if mb and mb.state == "dragging" and not game_state.get("paused"):
            dx, dy = game_state["sling_x"] - mb.x, game_state["sling_y"] - mb.y
            bw, bh, md = int(150 * sc), int(15 * sc), int(150 * sc)
            pp = min(math.hypot(dx, dy), md) / md
            bx, by = game_state["sling_x"] - bw // 2, game_state["sling_y"] + int(
                30 * sc
            )
            pygame.draw.rect(screen, (100, 100, 100), (bx, by, bw, bh))
            pygame.draw.rect(
                screen,
                (int(255 * pp), int(255 * (1 - pp)), 0),
                (bx, by, int(bw * pp), bh),
            )
            pts, _ = draw_text(
                f"{get_text(game_state['texts'], 'power_colon')} {int(pp * 100)}%",
                game_state["fonts"]["small_font"],
                (0, 0, 0),
            )
            screen.blit(
                pts, (game_state["sling_x"] - pts.get_width() // 2, by + bh + 5)
            )
            if game_state.get("show_rope"):
                pygame.draw.line(
                    screen,
                    (139, 69, 19),
                    (game_state["sling_x"], game_state["sling_y"]),
                    (int(mb.x), int(mb.y)),
                    int(3 * sc),
                )

        # Отрисовка главной птицы
        if mb and mb.state != "dead":
            if mb.state == "jumping" and mb.jump_image:
                screen.blit(mb.jump_image, (mb.x - mb.size // 2, mb.y - mb.size // 2))
            elif mb.image:
                screen.blit(mb.image, mb.rect)

        # МАССОВАЯ ОТРИСОВКА ЧЕРЕЗ GROUP.DRAW()
        game_state.get("targets", pygame.sprite.Group()).draw(screen)
        game_state.get("obstacles", pygame.sprite.Group()).draw(screen)
        game_state.get("defeated_pigs", pygame.sprite.Group()).draw(screen)
        game_state.get("small_birds", pygame.sprite.Group()).draw(screen)

        if game_state["sound_on"]:
            screen.blit(
                game_state["images"]["speaker_on_img"], (game_state["WIDTH"] - 50, 10)
            )
        else:
            screen.blit(
                game_state["images"]["speaker_off_img"], (game_state["WIDTH"] - 50, 10)
            )
        if game_state["paused"]:
            screen.blit(
                game_state["images"]["resume_img"], (game_state["WIDTH"] - 100, 10)
            )
        else:
            screen.blit(
                game_state["images"]["pause_img"], (game_state["WIDTH"] - 100, 10)
            )
        screen.blit(
            game_state["images"]["lightbulb_img"],
            (
                game_state["WIDTH"] // 2 - int(30 * game_state["scale_factor"]),
                int(10 * game_state["scale_factor"]),
            ),
        )

        if game_state.get("game_over"):
            go, gr = draw_text(
                get_text(game_state["texts"], "game_over"),
                game_state["fonts"]["font"],
                (255, 0, 0),
            )
            screen.blit(
                go,
                go.get_rect(
                    center=(game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
                ),
            )

        if game_state["game_mode"] != "sharpshooter":
            screen.blit(
                draw_text(
                    f"{game_state['texts']['score_colon']} {game_state['score']}",
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 10),
            )
            screen.blit(
                draw_text(
                    (
                        game_state["texts"]["lives_infinite"]
                        if game_state["lives"] == float("inf")
                        else f"{game_state['texts']['lives_colon']} {game_state['lives']}"
                    ),
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 50),
            )
            screen.blit(
                draw_text(
                    f"{game_state['texts']['combo_colon']} {game_state['combo']}",
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 90),
            )
        else:
            tl = (
                max(
                    0,
                    game_state["target_duration"]
                    - (time.time() - game_state["target_timer_start"]),
                )
                if not game_state.get("paused")
                and not game_state.get("game_over")
                and len(game_state.get("targets", [])) > 0
                else 0
            )
            screen.blit(
                draw_text(
                    f"{game_state['texts']['time_colon']} {tl:.1f}s",
                    game_state["fonts"]["small_font"],
                    (255, 0, 0),
                )[0],
                (10, 10),
            )
            screen.blit(
                draw_text(
                    f"{game_state['texts']['score_colon']} {game_state['score']}",
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 50),
            )
            screen.blit(
                draw_text(
                    f"{game_state['texts']['combo_colon']} {game_state['combo']}",
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 90),
            )
            screen.blit(
                draw_text(
                    (
                        game_state["texts"]["lives_infinite"]
                        if game_state["lives"] == float("inf")
                        else f"{game_state['texts']['lives_colon']} {game_state['lives']}"
                    ),
                    game_state["fonts"]["small_font"],
                    (0, 0, 0),
                )[0],
                (10, 130),
            )

    def _draw_tc(self, screen, mx, my, game_state):
        ov = pygame.Surface(
            (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
        )
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        ts, tr = draw_text(
            get_text(game_state["texts"], "training_complete_title"),
            game_state["fonts"]["font"],
            (255, 215, 0),
        )
        screen.blit(
            ts,
            ts.get_rect(
                center=(game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 - 50)
            ),
        )
        rs, rb = draw_text(
            get_text(game_state["texts"], "training_restart"),
            game_state["fonts"]["small_font"],
            (255, 255, 255),
        )
        rb.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 20)
        if rb.collidepoint(mx, my):
            rs, _ = draw_text(
                get_text(game_state["texts"], "training_restart"),
                game_state["fonts"]["small_font"],
                (255, 200, 0),
            )
        screen.blit(rs, rb)
        self.ui_buttons["restart_btn"] = rb
        es, eb = draw_text(
            get_text(game_state["texts"], "training_exit_to_menu"),
            game_state["fonts"]["small_font"],
            (255, 255, 255),
        )
        eb.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2 + 70)
        if eb.collidepoint(mx, my):
            es, _ = draw_text(
                get_text(game_state["texts"], "training_exit_to_menu"),
                game_state["fonts"]["small_font"],
                (255, 200, 0),
            )
        screen.blit(es, eb)
        self.ui_buttons["exit_btn"] = eb

    def _draw_chp(self, screen, mx, my, game_state):
        ov = pygame.Surface(
            (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
        )
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        dr = pygame.Rect(0, 0, 700, 300)
        dr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
        pygame.draw.rect(screen, (60, 60, 80), dr)
        pygame.draw.rect(screen, (210, 210, 230), dr, 3)
        ts, tr = draw_text(
            get_text(game_state["texts"], "campaign_hint_title"),
            game_state["fonts"]["small_font"],
            (255, 215, 0),
        )
        screen.blit(ts, ts.get_rect(centerx=dr.centerx, y=dr.y + 20))

        f, x, y, sp = (
            game_state["fonts"]["pedia_font"],
            dr.left + 20,
            dr.y + 70,
            game_state["fonts"]["pedia_font"].size(" ")[0],
        )
        for w in get_text(game_state["texts"], "campaign_hint_text").split(" "):
            ws = f.render(w, True, (255, 255, 255))
            if x + ws.get_width() >= dr.right - 20:
                x, y = dr.left + 20, y + f.get_linesize()
            screen.blit(ws, (x, y))
            x += ws.get_width() + sp

        cs, cb = draw_text(
            get_text(game_state["texts"], "hint_popup_close"),
            game_state["fonts"]["small_font"],
            (255, 255, 255),
        )
        cb.center = (dr.centerx, dr.bottom - 40)
        if cb.collidepoint(mx, my):
            cs, _ = draw_text(
                get_text(game_state["texts"], "hint_popup_close"),
                game_state["fonts"]["small_font"],
                (120, 255, 120),
            )
        screen.blit(cs, cb)
        self.ui_buttons["close_hint"] = cb

    def _draw_tp(self, screen, mx, my, game_state):
        ov = pygame.Surface(
            (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
        )
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        dr = pygame.Rect(0, 0, 700, 250)
        dr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
        pygame.draw.rect(screen, (50, 70, 50), dr)
        pygame.draw.rect(screen, (200, 220, 200), dr, 3)

        f, x, y, sp = (
            game_state["fonts"]["small_font"],
            dr.left + 20,
            dr.y + 20,
            game_state["fonts"]["small_font"].size(" ")[0],
        )
        for w in game_state.get("training_popup_text", "").split(" "):
            ws = f.render(w, True, (255, 255, 255))
            if x + ws.get_width() >= dr.right - 20:
                x, y = dr.left + 20, y + f.get_linesize()
            screen.blit(ws, (x, y))
            x += ws.get_width() + sp

        cs, cb = draw_text(
            get_text(game_state["texts"], "training_popup_continue"),
            game_state["fonts"]["small_font"],
            (255, 255, 255),
        )
        cb.center = (dr.centerx, dr.bottom - 40)
        if cb.collidepoint(mx, my):
            cs, _ = draw_text(
                get_text(game_state["texts"], "training_popup_continue"),
                game_state["fonts"]["small_font"],
                (120, 255, 120),
            )
        screen.blit(cs, cb)
        self.ui_buttons["cont_training"] = cb

    def _draw_hp(self, screen, mx, my, game_state):
        ov = pygame.Surface(
            (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
        )
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))
        dr = pygame.Rect(0, 0, 600, 250)
        dr.center = (game_state["WIDTH"] // 2, game_state["HEIGHT"] // 2)
        pygame.draw.rect(screen, (60, 60, 80), dr)
        pygame.draw.rect(screen, (210, 210, 230), dr, 3)

        bn_ru = game_state.get("bird_image_to_name", {}).get(
            game_state.get("current_bird_img"), "Неизвестная птица"
        )
        try:
            bn = get_text(game_state["texts"], "pedia_items")[
                list(game_state.get("bird_image_to_name", {}).values()).index(bn_ru)
            ]
        except:
            bn = get_text(game_state["texts"], "unknown_bird")

        ts, tr = draw_text(bn, game_state["fonts"]["small_font"], (255, 215, 0))
        screen.blit(ts, ts.get_rect(centerx=dr.centerx, y=dr.y + 20))

        f, x, y, sp = (
            game_state["fonts"]["pedia_font"],
            dr.left + 20,
            dr.y + 70,
            game_state["fonts"]["pedia_font"].size(" ")[0],
        )
        for w in (
            get_text(game_state["texts"], "pedia_descriptions")
            .get(bn, get_text(game_state["texts"], "no_bird_on_slingshot"))
            .split(" ")
        ):
            ws = f.render(w, True, (255, 255, 255))
            if x + ws.get_width() >= dr.right - 20:
                x, y = dr.left + 20, y + f.get_linesize()
            screen.blit(ws, (x, y))
            x += ws.get_width() + sp

        cs, cb = draw_text(
            get_text(game_state["texts"], "hint_popup_close"),
            game_state["fonts"]["small_font"],
            (255, 255, 255),
        )
        cb.center = (dr.centerx, dr.bottom - 30)
        if cb.collidepoint(mx, my):
            cs, _ = draw_text(
                get_text(game_state["texts"], "hint_popup_close"),
                game_state["fonts"]["small_font"],
                (120, 255, 120),
            )
        screen.blit(cs, cb)
        self.ui_buttons["close_hint"] = cb