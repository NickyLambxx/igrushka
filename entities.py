import pygame
import math
import pymunk


class MainBird(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, size, space):
        super().__init__()
        self.space = space
        self.start_x = start_x
        self.start_y = start_y
        self.size = size

        # PyMunk: Инициализация физического тела
        mass = 5.0
        radius = size // 2
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment, body_type=pymunk.Body.KINEMATIC)
        self.body.position = (start_x, start_y)

        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.5
        self.shape.friction = 0.8
        self.space.add(self.body, self.shape)

        self.original_image = None
        self.image = pygame.Surface((size, size))
        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.mask = pygame.mask.Mask((size, size))

        self.state = "idle"
        self.tumble_timer = 0
        self.type_index = 0

        self.boost_available = False
        self.is_boosted = False
        self.split_available = False
        self.boomerang_available = False

        self.jump_progress = 0.0
        self.jump_start_pos = (0, 0)
        self.jump_image = None

    def kill(self):
        if hasattr(self, "shape") and self.shape in self.space.shapes:
            self.space.remove(self.body, self.shape)
        super().kill()

    def die(self):
        self.state = "dead"
        self.kill()

    def set_image(self, img, type_index):
        if img.get_size() != (self.size, self.size):
            self.original_image = pygame.transform.scale(img, (self.size, self.size))
        else:
            self.original_image = img
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.type_index = type_index
        self.update_rect()

    def reset_to_sling(self):
        self.body.body_type = pymunk.Body.KINEMATIC
        self.body.position = (self.start_x, self.start_y)
        self.body.velocity = (0, 0)
        self.body.angular_velocity = 0
        self.body.angle = 0

        self.state = "idle"
        self.boost_available = False
        self.is_boosted = False
        self.split_available = False
        self.boomerang_available = False
        self.update_rect()

    def update_rect(self):
        if self.original_image:
            self.image = pygame.transform.rotate(
                self.original_image, math.degrees(-self.body.angle)
            )
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.image.get_rect(
                center=(int(self.body.position.x), int(self.body.position.y))
            )

    def start_drag(self):
        self.state = "dragging"

    def drag_to(self, mx, my, max_x, max_y):
        bird_radius = self.size // 2
        x = max(bird_radius, min(mx, max_x - bird_radius))
        y = max(bird_radius, min(my, max_y - bird_radius))
        self.body.position = (x, y)
        self.update_rect()

    def launch(self, sling_x, sling_y, scale_factor):
        self.state = "flying"
        self.body.body_type = pymunk.Body.DYNAMIC

        dx = sling_x - self.body.position.x
        dy = sling_y - self.body.position.y
        angle = math.atan2(dy, dx)
        max_drag_dist = int(150 * scale_factor)
        distance = min(math.hypot(dx, dy), max_drag_dist)

        power = distance / 7.0
        vx = power * math.cos(angle)
        vy = power * math.sin(angle)

        # Перевод пикселей/кадр в пиксели/сек для PyMunk
        self.body.velocity = (vx * 60, vy * 60)

        if self.type_index == 2:
            self.boost_available = True
        elif self.type_index == 3:
            self.split_available = True
        elif self.type_index == 4:
            self.boomerang_available = True

    def update(self, dt, gravity, ground_level, screen_width, screen_height):
        event = None
        if self.state in ["flying", "tumbling"]:
            if self.type_index == 4 and self.state == "flying":
                self.body.angular_velocity = -15.0

            if (
                self.state == "flying"
                and self.body.position.y >= ground_level - self.size
            ):
                self.state = "tumbling"
                self.tumble_timer = 2.0
                event = "hit_ground"

            elif (
                self.body.position.y > screen_height + 50
                or self.body.position.x < -50
                or self.body.position.x > screen_width + 50
            ):
                self.state = "out_of_bounds"
                event = "out_of_bounds"

        if self.state == "tumbling":
            self.tumble_timer -= dt
            if self.body.velocity.length < 10 or self.tumble_timer <= 0:
                self.state = "stopped"
                event = "stopped"

        elif self.state == "jumping":
            self.jump_progress += 0.05 * (dt * 60.0)
            p = min(1.0, self.jump_progress)
            sx, sy = self.jump_start_pos
            ex, ey = self.start_x, self.start_y
            x = sx + (ex - sx) * p
            parabola_offset = 150 * (self.size / 50.0) * math.sin(p * math.pi)
            y = sy + (ey - sy) * p - parabola_offset
            self.body.position = (x, y)
            if self.jump_progress >= 1.0:
                self.state = "idle"
                self.set_image(self.jump_image, self.type_index)
                self.jump_image = None
                self.jump_progress = 0
                self.reset_to_sling()
                event = "jump_complete"

        self.update_rect()
        self.x = self.body.position.x
        self.y = self.body.position.y
        return event


class Target(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, size, space, image):
        super().__init__()
        self.space = space
        self.size = size
        if image.get_size() != (size, size):
            self.original_image = pygame.transform.scale(image, (size, size))
        else:
            self.original_image = image
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(x, y))

        mass = 1.0
        radius = size // 2
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.body.velocity = (vx * 60, vy * 60)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.4
        self.shape.friction = 0.6
        self.space.add(self.body, self.shape)

        self.x = self.body.position.x
        self.y = self.body.position.y

    def kill(self):
        if self.shape in self.space.shapes:
            self.space.remove(self.body, self.shape)
        super().kill()

    def update(self, dt, screen_width, screen_height):
        self.image = pygame.transform.rotate(
            self.original_image, math.degrees(-self.body.angle)
        )
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(
            center=(int(self.body.position.x), int(self.body.position.y))
        )
        self.x = self.body.position.x
        self.y = self.body.position.y


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, size, space, image):
        super().__init__()
        self.space = space
        self.size = size
        if image.get_size() != (size, size):
            self.original_image = pygame.transform.scale(image, (size, size))
        else:
            self.original_image = image
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(x, y))

        mass = 3.0
        moment = pymunk.moment_for_box(mass, (size, size))
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.body.velocity = (vx * 60, vy * 60)
        self.shape = pymunk.Poly.create_box(self.body, (size, size))
        self.shape.elasticity = 0.2
        self.shape.friction = 0.8
        self.space.add(self.body, self.shape)

        self.x = self.body.position.x
        self.y = self.body.position.y

    def kill(self):
        if self.shape in self.space.shapes:
            self.space.remove(self.body, self.shape)
        super().kill()

    def update(self, dt, screen_width, screen_height):
        self.image = pygame.transform.rotate(
            self.original_image, math.degrees(-self.body.angle)
        )
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(
            center=(int(self.body.position.x), int(self.body.position.y))
        )
        self.x = self.body.position.x
        self.y = self.body.position.y


class SmallBird(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, size, space, image):
        super().__init__()
        self.space = space
        self.size = size
        if image.get_size() != (size, size):
            self.original_image = pygame.transform.scale(image, (size, size))
        else:
            self.original_image = image
        self.image = self.original_image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=(x, y))

        mass = 0.5
        radius = size // 2
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.body.velocity = (vx, vy)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.5
        self.shape.friction = 0.8
        self.space.add(self.body, self.shape)

        self.state = "flying"
        self.tumble_timer = 0
        self.x = self.body.position.x
        self.y = self.body.position.y

    def kill(self):
        if self.shape in self.space.shapes:
            self.space.remove(self.body, self.shape)
        super().kill()

    def update(self, dt, gravity, ground_level):
        event = None
        if self.state == "flying":
            if self.body.position.y >= ground_level - self.size // 2:
                self.state = "tumbling"
                self.tumble_timer = 1.0
                event = "hit_ground"
        elif self.state == "tumbling":
            self.tumble_timer -= dt
            if self.body.velocity.length < 5 or self.tumble_timer <= 0:
                self.state = "dead"
                self.kill()

        self.image = pygame.transform.rotate(
            self.original_image, math.degrees(-self.body.angle)
        )
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(
            center=(int(self.body.position.x), int(self.body.position.y))
        )
        self.x = self.body.position.x
        self.y = self.body.position.y
        return event


class DefeatedPig(pygame.sprite.Sprite):
    def __init__(self, x, y, vy, size, space, image):
        super().__init__()
        self.space = space
        self.size = size
        if image.get_size() != (size, size):
            self.image = pygame.transform.scale(image, (size, size))
        else:
            self.image = image
        self.rect = self.image.get_rect(center=(x, y))

        mass = 1.0
        radius = size // 2
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = (x, y)
        self.body.velocity = ((x % 200 - 100) * 2, vy * 60)
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 0.3
        self.shape.friction = 0.9
        self.space.add(self.body, self.shape)

        self.on_ground = False
        self.timer = -1
        self.x = self.body.position.x
        self.y = self.body.position.y

    def kill(self):
        if self.shape in self.space.shapes:
            self.space.remove(self.body, self.shape)
        super().kill()

    def update(self, dt, gravity, ground_level):
        event = None
        if not self.on_ground:
            if self.body.position.y >= ground_level - self.size // 2:
                self.on_ground = True
                self.timer = 1.0
                event = "hit_ground"
        else:
            self.timer -= dt
            if self.timer <= 0:
                event = "dead"
                self.kill()

        self.rect.center = (int(self.body.position.x), int(self.body.position.y))
        self.x = self.body.position.x
        self.y = self.body.position.y
        return event