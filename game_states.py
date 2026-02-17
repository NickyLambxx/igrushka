import pygame
import time
from utils import draw_text, get_text
from game_objects import (
    update_all_volumes,
    play_music_track,
    reset_game,
    apply_screen_settings,
)
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
                    sm.change_state("slingshot", game_state)
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
                        game_state["state_manager"].change_state("match3", game_state)
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