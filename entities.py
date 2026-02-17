import pygame
import math


class MainBird(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, size):
        super().__init__()
        self.start_x = start_x
        self.start_y = start_y
        self.size = size
        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = 0.0
        self.vy = 0.0

        self.original_image = None
        self.image = None
        self.rect = pygame.Rect(start_x - size // 2, start_y - size // 2, size, size)

        self.state = "idle"
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.tumble_timer = 0
        self.type_index = 0

        self.boost_available = False
        self.is_boosted = False
        self.split_available = False
        self.boomerang_available = False

        self.jump_progress = 0.0
        self.jump_start_pos = (0, 0)
        self.jump_image = None

    def set_image(self, img, type_index):
        if img.get_size() != (self.size, self.size):
            self.original_image = pygame.transform.scale(img, (self.size, self.size))
        else:
            self.original_image = img
        self.image = self.original_image
        self.type_index = type_index
        self.update_rect()

    def reset_to_sling(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.state = "idle"
        self.boost_available = False
        self.is_boosted = False
        self.split_available = False
        self.boomerang_available = False
        self.update_rect()

    def update_rect(self):
        if self.image:
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        else:
            self.rect.center = (int(self.x), int(self.y))

    def start_drag(self):
        self.state = "dragging"

    def drag_to(self, mx, my, max_x, max_y):
        bird_radius = self.size // 2
        self.x = max(bird_radius, min(mx, max_x - bird_radius))
        self.y = max(bird_radius, min(my, max_y - bird_radius))
        self.update_rect()

    def launch(self, sling_x, sling_y, scale_factor):
        self.state = "flying"
        dx = sling_x - self.x
        dy = sling_y - self.y
        angle = math.atan2(dy, dx)
        max_drag_dist = int(150 * scale_factor)
        distance = min(math.hypot(dx, dy), max_drag_dist)
        power = distance / 7.0

        self.vx = power * math.cos(angle)
        self.vy = power * math.sin(angle)

        if self.type_index == 2:
            self.boost_available = True
        elif self.type_index == 3:
            self.split_available = True
        elif self.type_index == 4:
            self.boomerang_available = True

    def update(self, dt, gravity, ground_level, screen_width, screen_height):
        dt_factor = dt * 60.0
        event = None
        if self.state == "flying":
            self.x += self.vx * dt_factor
            self.y += self.vy * dt_factor
            self.vy += gravity * dt_factor
            if self.type_index == 4:
                self.angle -= 15 * dt_factor

            if self.y >= ground_level - self.size // 2:
                self.state = "tumbling"
                self.tumble_timer = 25
                self.y = ground_level - self.size // 2
                self.vy = 0
                self.angular_velocity = self.vx * -1.5
                event = "hit_ground"

            elif (
                self.y > screen_height + 50
                or self.x < -50
                or self.x > screen_width + 50
            ):
                self.state = "out_of_bounds"
                event = "out_of_bounds"

        elif self.state == "tumbling":
            self.tumble_timer -= 1 * dt_factor
            self.x += self.vx * dt_factor
            self.angle += self.angular_velocity * dt_factor

            self.vx *= 0.95**dt_factor
            self.angular_velocity *= 0.99**dt_factor

            if abs(self.vx) < 0.1:
                self.vx = 0
            if self.tumble_timer <= 0 or self.vx == 0:
                self.state = "stopped"
                event = "stopped"

        elif self.state == "jumping":
            self.jump_progress += 0.05 * dt_factor
            p = min(1.0, self.jump_progress)
            sx, sy = self.jump_start_pos
            ex, ey = self.start_x, self.start_y
            self.x = sx + (ex - sx) * p
            parabola_offset = 150 * (self.size / 50.0) * math.sin(p * math.pi)
            self.y = sy + (ey - sy) * p - parabola_offset
            if self.jump_progress >= 1.0:
                self.state = "idle"
                self.set_image(self.jump_image, self.type_index)
                self.jump_image = None
                self.jump_progress = 0
                self.reset_to_sling()
                event = "jump_complete"

        if self.original_image and self.state in ["flying", "tumbling"]:
            if self.type_index == 4 or self.state == "tumbling":
                self.image = pygame.transform.rotate(self.original_image, self.angle)
            else:
                self.image = self.original_image
        elif self.original_image:
            self.image = self.original_image

        self.update_rect()
        return event


class Target(pygame.sprite.Sprite):
    def __init__(self, rect, vx, vy, image):
        super().__init__()
        if image.get_size() != (rect.width, rect.height):
            self.image = pygame.transform.scale(image, (rect.width, rect.height))
        else:
            self.image = image
        self.rect = self.image.get_rect(center=rect.center)
        self.vx = vx
        self.vy = vy
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def update(self, dt, screen_width, screen_height):
        dt_factor = dt * 60.0
        if self.vx != 0 or self.vy != 0:
            self.x += self.vx * dt_factor
            self.y += self.vy * dt_factor
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

            if not (0 < self.rect.left and self.rect.right < screen_width):
                self.vx = -self.vx
            if not (0 < self.rect.top and self.rect.bottom < screen_height):
                self.vy = -self.vy


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, rect, vx, vy, image):
        super().__init__()
        if image.get_size() != (rect.width, rect.height):
            self.image = pygame.transform.scale(image, (rect.width, rect.height))
        else:
            self.image = image
        self.rect = self.image.get_rect(center=rect.center)
        self.vx = vx
        self.vy = vy
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

    def update(self, dt, screen_width, screen_height):
        dt_factor = dt * 60.0
        if self.vx != 0 or self.vy != 0:
            self.x += self.vx * dt_factor
            self.y += self.vy * dt_factor
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)

            if not (0 < self.rect.left and self.rect.right < screen_width):
                self.vx = -self.vx
            if not (0 < self.rect.top and self.rect.bottom < screen_height):
                self.vy = -self.vy


class SmallBird(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, size, image):
        super().__init__()
        if image.get_size() != (size, size):
            self.original_image = pygame.transform.scale(image, (size, size))
        else:
            self.original_image = image
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.size = size
        self.state = "flying"
        self.tumble_timer = 0
        self.angle = 0.0
        self.angular_velocity = 0.0

    def update(self, dt, gravity, ground_level):
        dt_factor = dt * 60.0
        event = None
        if self.state == "flying":
            self.x += self.vx * dt_factor
            self.y += self.vy * dt_factor
            self.vy += gravity * dt_factor
            if self.y >= ground_level - self.size // 2:
                self.state = "tumbling"
                self.tumble_timer = 60
                self.y = ground_level - self.size // 2
                self.vy = 0
                self.angular_velocity = self.vx * -1.5
                event = "hit_ground"
        elif self.state == "tumbling":
            self.tumble_timer -= 1 * dt_factor
            self.x += self.vx * dt_factor
            self.angle += self.angular_velocity * dt_factor

            self.vx *= 0.95**dt_factor
            self.angular_velocity *= 0.99**dt_factor

            if abs(self.vx) < 0.1:
                self.vx = 0
            if self.tumble_timer <= 0 or self.vx == 0:
                self.state = "dead"
                self.kill()

        if self.angle != 0:
            self.image = pygame.transform.rotate(self.original_image, self.angle)
        else:
            self.image = self.original_image
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        return event


class DefeatedPig(pygame.sprite.Sprite):
    def __init__(self, x, y, vy, size, image):
        super().__init__()
        if image.get_size() != (size, size):
            self.image = pygame.transform.scale(image, (size, size))
        else:
            self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)
        self.vy = float(vy)
        self.size = size
        self.on_ground = False
        self.timer = -1

    def update(self, dt, gravity, ground_level):
        dt_factor = dt * 60.0
        event = None
        if not self.on_ground:
            self.vy += gravity * dt_factor
            self.y += self.vy * dt_factor
            if self.y >= ground_level - self.size // 2:
                self.y = ground_level - self.size // 2
                self.on_ground = True
                self.timer = 15
                event = "hit_ground"
        else:
            self.timer -= 1 * dt_factor
            if self.timer <= 0:
                event = "dead"
                self.kill()

        self.rect.center = (int(self.x), int(self.y))
        return event