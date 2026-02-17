import pygame
import math
import random
from localization import LANGUAGES


def draw_text(text, font, color):
    img = font.render(text, True, color)
    return img, img.get_rect()


def get_text(current_texts, key):
    text = current_texts.get(key)
    if text is not None:
        return text
    text = LANGUAGES["ru"].get(key)
    if text is not None:
        return text
    print(f"Warning: Localization key '{key}' not found in any language.")
    return f"[{key}]"


def create_target(WIDTH, HEIGHT, size):
    x_min, x_max = int(WIDTH * 0.4), WIDTH - size - 20
    y_min, y_max = int(HEIGHT * 0.2), HEIGHT - size - int(HEIGHT * 0.25)
    return pygame.Rect(
        random.randint(x_min, x_max), random.randint(y_min, y_max), size, size
    )


def create_obstacle(WIDTH, HEIGHT, size):
    x_min, x_max = int(WIDTH * 0.4), WIDTH - size - 50
    y_min, y_max = int(HEIGHT * 0.2), HEIGHT - size - int(HEIGHT * 0.3)
    return pygame.Rect(
        random.randint(x_min, x_max), random.randint(y_min, y_max), size, size
    )


def create_trail_particle(trail_particles, x, y):
    trail_particles.append(
        {
            "x": x,
            "y": y,
            "size": random.randint(3, 6),
            "life": random.randint(20, 30),
            "color": (255, 165, 0),
        }
    )


def create_dust_particle(dust_particles, x, y, count=1):
    for _ in range(count):
        dust_particles.append(
            {
                "x": x,
                "y": y,
                "size": random.randint(5, 9),
                "life": random.randint(20, 30),
                "dx": random.uniform(-2.5, 2.5),
                "dy": random.uniform(-2.5, 0),
                "color": (200, 200, 200),
            }
        )


def create_brick_shatter(dust_particles, x, y):
    for _ in range(15):
        dust_particles.append(
            {
                "x": x,
                "y": y,
                "size": random.randint(3, 7),
                "life": random.randint(30, 50),
                "dx": random.uniform(-3, 3),
                "dy": random.uniform(-4, 1),
                "color": (139, 69, 19),
            }
        )


def create_spark_particle(spark_particles, x, y):
    spark_particles.append(
        {
            "x": x,
            "y": y,
            "size": random.randint(2, 4),
            "life": random.randint(10, 20),
            "dx": random.uniform(-5, 5),
            "dy": random.uniform(-5, 5),
            "color": (255, 255, 0),
        }
    )


def create_feather_explosion(feather_particles, x, y, bird_index):
    for _ in range(15):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        feather_particles.append(
            {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "angle": random.uniform(0, 360),
                "angular_velocity": random.uniform(-5, 5),
                "life": random.randint(40, 60),
                "gravity": 0.1,
                "bird_index": bird_index,
            }
        )


def update_particles(particles, dt):
    dt_factor = dt * 60.0
    gravity = 0.2 * dt_factor
    for p in particles[:]:
        p["life"] -= 1 * dt_factor
        if "dx" in p:
            p["x"] += p["dx"] * dt_factor
            p["y"] += p["dy"] * dt_factor
            p["dy"] += gravity
        if p["life"] <= 0:
            particles.remove(p)


def draw_particles(screen, particles):
    for p in particles:
        alpha = min(255, max(0, int(p["life"] * 8)))
        color = (*p["color"], alpha)
        s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        if p["color"] == (139, 69, 19):
            pygame.draw.rect(s, color, (0, 0, p["size"], p["size"]))
        else:
            pygame.draw.circle(s, color, (p["size"], p["size"]), p["size"])
        screen.blit(s, (p["x"] - p["size"], p["y"] - p["size"]))


def update_feathers(feather_particles, dt):
    dt_factor = dt * 60.0
    for p in feather_particles[:]:
        p["life"] -= 1 * dt_factor
        if p["life"] <= 0:
            feather_particles.remove(p)
            continue
        p["vy"] += p["gravity"] * dt_factor
        p["x"] += p["vx"] * dt_factor
        p["y"] += p["vy"] * dt_factor
        p["angle"] += p["angular_velocity"] * dt_factor


def draw_feathers(screen, feather_particles, feather_imgs):
    for p in feather_particles:
        feather_img = feather_imgs[p.get("bird_index", 0)]
        rotated_img = pygame.transform.rotate(feather_img, p["angle"])
        new_rect = rotated_img.get_rect(center=(p["x"], p["y"]))
        alpha = max(0, min(255, int(255 * (p["life"] / 30))))
        rotated_img.set_alpha(alpha)
        screen.blit(rotated_img, new_rect)


def draw_dashed_trajectory(
    screen, start_x, start_y, velocity_x, velocity_y, gravity, steps=50
):
    points, x, y, vx, vy = [], start_x, start_y, velocity_x, velocity_y
    for _ in range(max(5, int(steps * 0.3))):
        x += vx
        y += vy
        vy += gravity
        points.append((x, y))
    if len(points) > 1:
        for i in range(len(points) - 1):
            if i % 4 < 2:
                pygame.draw.line(screen, (255, 0, 0), points[i], points[i + 1], 2)