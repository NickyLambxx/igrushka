import pygame
import os
import sys

pygame.init()

EXPLOSION_RADIUS = 120
MAX_EXPLOSION_FRAMES = 20
TARGET_DURATION = {"easy": 2.5, "medium": 2.0, "hard": 1.5}
LIVES = {"easy": 5, "medium": 5, "hard": 3}
SPEED_MULTIPLIER = {"easy": 0, "medium": 1.0, "hard": 1.6}


def scale_to_cover(image, screen_width, screen_height):
    """Масштабирует изображение, чтобы оно полностью покрыло экран, сохраняя пропорции."""
    orig_width, orig_height = image.get_size()
    orig_ratio = orig_width / orig_height
    screen_ratio = screen_width / screen_height

    if screen_ratio > orig_ratio:
        new_width = screen_width
        new_height = int(new_width / orig_ratio)
    else:
        new_height = screen_height
        new_width = int(new_height * orig_ratio)

    return pygame.transform.scale(image, (new_width, new_height))


def load_images(width, height, ui_scale, game_scale):
    try:
        bird_size = int(50 * game_scale)
        small_bird_size = int(25 * game_scale)
        icon_size = int(40 * ui_scale)
        lightbulb_w, lightbulb_h = int(60 * ui_scale), int(40 * ui_scale)

        orig_menu_background = pygame.image.load("menu_background.jpg")
        orig_background = pygame.image.load("background.jpg")

        menu_background = scale_to_cover(orig_menu_background, width, height)
        background = scale_to_cover(orig_background, width, height)

        cursor_img = pygame.image.load("cursor.png").convert_alpha()

        bird_imgs = [
            pygame.transform.scale(
                pygame.image.load(f"bird{i}.png").convert_alpha(),
                (bird_size, bird_size),
            )
            for i in range(1, 6)
        ]

        feather_imgs = [
            pygame.transform.scale(
                pygame.image.load(f"feather{i}.png").convert_alpha(),
                (int(20 * game_scale), int(20 * game_scale)),
            )
            for i in range(1, 6)
        ]

        small_bird_img = pygame.transform.scale(
            pygame.image.load("bird4_small.png").convert_alpha(),
            (small_bird_size, small_bird_size),
        )
        target_img = pygame.transform.scale(
            pygame.image.load("target.png").convert_alpha(), (bird_size, bird_size)
        )

        target_defeated_img = pygame.transform.scale(
            pygame.image.load("target_defeated.png").convert_alpha(),
            (bird_size, bird_size),
        )

        brick_img = pygame.transform.scale(
            pygame.image.load("brick.png").convert_alpha(), (bird_size, bird_size)
        )

        speaker_on_img = pygame.transform.scale(
            pygame.image.load("speaker_on.png").convert_alpha(), (icon_size, icon_size)
        )
        speaker_off_img = pygame.transform.scale(
            pygame.image.load("speaker_off.png").convert_alpha(), (icon_size, icon_size)
        )
        pause_img = pygame.transform.scale(
            pygame.image.load("pause.png").convert_alpha(), (icon_size, icon_size)
        )
        resume_img = pygame.transform.scale(
            pygame.image.load("play.png").convert_alpha(), (icon_size, icon_size)
        )
        lightbulb_img = pygame.transform.scale(
            pygame.image.load("lightbulb.png").convert_alpha(),
            (lightbulb_w, lightbulb_h),
        )

        smoke_img = pygame.transform.scale(
            pygame.image.load("smoke.png").convert_alpha(),
            (
                int(EXPLOSION_RADIUS * 2 * game_scale),
                int(EXPLOSION_RADIUS * 2 * game_scale),
            ),
        )

        return {
            "menu_background": menu_background,
            "background": background,
            "cursor_img": cursor_img,
            "bird_imgs": bird_imgs,
            "small_bird_img": small_bird_img,
            "target_img": target_img,
            "target_defeated_img": target_defeated_img,
            "brick_img": brick_img,
            "speaker_on_img": speaker_on_img,
            "speaker_off_img": speaker_off_img,
            "pause_img": pause_img,
            "resume_img": resume_img,
            "smoke_img": smoke_img,
            "feather_imgs": feather_imgs,
            "lightbulb_img": lightbulb_img,
        }
    except Exception as e:
        print(f"Ошибка загрузки изображений: {e}")
        pygame.quit()
        sys.exit()


def load_sounds():
    try:
        pygame.mixer.init()
        hit_sound = pygame.mixer.Sound("hit.wav")
        fly_sound = pygame.mixer.Sound("fly.wav")
        explosion_sound = pygame.mixer.Sound("explosion.wav")
        boost_sound = pygame.mixer.Sound("boost.wav")
        split_sound = pygame.mixer.Sound("split.wav")
        brick_sound = pygame.mixer.Sound("brick.wav")
        boomerang_sound = pygame.mixer.Sound("boomerang.wav")

        music_playlist = [f"music_track_{i}.mp3" for i in range(1, 6)]

        return {
            "hit_sound": hit_sound,
            "fly_sound": fly_sound,
            "explosion_sound": explosion_sound,
            "boost_sound": boost_sound,
            "split_sound": split_sound,
            "brick_sound": brick_sound,
            "boomerang_sound": boomerang_sound,
            "music_playlist": music_playlist,
        }
    except Exception as e:
        print(f"Ошибка загрузки звуков: {e}")
        return {}


def load_fonts(scale_factor=1.0):
    return {
        "font": pygame.font.Font(None, int(48 * scale_factor)),
        "large_font": pygame.font.Font(None, int(200 * scale_factor)),
        "small_font": pygame.font.Font(None, int(36 * scale_factor)),
        "achievement_font": pygame.font.Font(None, int(72 * scale_factor)),
        "boost_font": pygame.font.Font(None, int(72 * scale_factor)),
        "info_font": pygame.font.Font(None, int(24 * scale_factor)),
        "pedia_font": pygame.font.Font(None, int(28 * scale_factor)),
    }
