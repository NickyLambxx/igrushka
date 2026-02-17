import pygame
import math
import random
import time
import pymunk
from utils import (
    draw_text,
    get_text,
    create_trail_particle,
    create_dust_particle,
    create_spark_particle,
    update_particles,
    draw_particles,
    create_feather_explosion,
    update_feathers,
    draw_feathers,
    create_brick_shatter,
    create_target,
    create_obstacle,
)
from entities import MainBird, Target, Obstacle, SmallBird, DefeatedPig
from settings import SPEED_MULTIPLIER, LIVES, TARGET_DURATION
from game_states import State
from game_objects import update_all_volumes, reset_game


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
                    mb.die()
                return
            else:
                game_state["show_training_popup"] = True
                game_state["training_popup_text"] = game_state["texts"][
                    "training_descriptions"
                ][game_state["training_bird_index"]]
                game_state["current_bird_img"] = None
                if mb:
                    mb.die()
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
                mb.die()
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


def split_bird(game_state):
    bird = game_state["main_bird"]
    sz = game_state["small_object_size"]
    img = game_state["images"]["small_bird_img"]
    for i in range(3):
        angle = math.radians(120 * i)
        vx = bird.body.velocity.x + math.cos(angle) * 300
        vy = bird.body.velocity.y + math.sin(angle) * 300
        game_state["small_birds"].add(
            SmallBird(
                bird.body.position.x,
                bird.body.position.y,
                vx,
                vy,
                sz,
                game_state["space"],
                img,
            )
        )
    if game_state["sound_on"] and game_state["sounds"].get("split_sound"):
        try:
            game_state["sounds"]["split_sound"].play()
        except:
            pass
    bird.split_available = False
    bird.die()


def activate_boomerang(game_state):
    bird = game_state["main_bird"]
    bird.body.velocity = (-900, 0)
    bird.boomerang_available = False
    if game_state["sound_on"] and game_state["sounds"].get("boomerang_sound"):
        try:
            game_state["sounds"]["boomerang_sound"].play()
        except:
            pass


def reset_slingshot(game_state):
    from achievements import get_achievements_for_profile

    game_state.update(
        get_achievements_for_profile(
            game_state["all_profiles_data"], game_state["current_profile"]
        )
    )

    game_state["bird_queue"] = []
    num_targets = 0
    num_obstacles = 0

    if game_state["game_mode"] == "training":
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

    # PyMunk Space Setup
    game_state["space"] = pymunk.Space()
    game_state["space"].gravity = (0, 1800)

    floor = pymunk.Segment(
        game_state["space"].static_body,
        (-2000, game_state["GROUND_LEVEL"]),
        (game_state["WIDTH"] + 2000, game_state["GROUND_LEVEL"]),
        50,
    )
    floor.friction = 1.0
    floor.elasticity = 0.5
    game_state["space"].add(floor)

    walls = [
        pymunk.Segment(
            game_state["space"].static_body, (0, -2000), (0, game_state["HEIGHT"]), 50
        ),
        pymunk.Segment(
            game_state["space"].static_body,
            (game_state["WIDTH"], -2000),
            (game_state["WIDTH"], game_state["HEIGHT"]),
            50,
        ),
        pymunk.Segment(
            game_state["space"].static_body,
            (-2000, -2000),
            (game_state["WIDTH"] + 2000, -2000),
            50,
        ),
    ]
    for w in walls:
        w.elasticity = 0.8
        w.friction = 0.5
        game_state["space"].add(w)

    game_state["main_bird"] = MainBird(
        game_state["sling_x"],
        game_state["sling_y"],
        game_state["object_size"],
        game_state["space"],
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
            "paused": False,
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
                        nr.centerx,
                        nr.centery,
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
                        game_state["object_size"],
                        game_state["space"],
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
                        nr.centerx,
                        nr.centery,
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
                        game_state["object_size"],
                        game_state["space"],
                        obs_img,
                    )
                )
                break


class SlingshotState(State):
    def __init__(self):
        self.ui_buttons = {}

    def handle_event(self, event, mx, my, game_state):
        mb = game_state.get("main_bird")
        is_paused = game_state.get("paused", False)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state["state_manager"].change_state("main_menu", game_state)
            elif event.key == pygame.K_r:
                reset_slingshot(game_state)
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                if (
                    not game_state.get("training_complete")
                    and not game_state.get("show_hint_popup")
                    and not game_state.get("show_training_popup")
                ):
                    game_state["paused"] = not game_state["paused"]

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.get("show_training_popup"):
                if self.ui_buttons.get("cont_training") and self.ui_buttons[
                    "cont_training"
                ].collidepoint(mx, my):
                    game_state["show_training_popup"] = False
                    game_state["paused"] = False
                    get_next_bird(game_state)
                return
            if game_state.get("show_hint_popup"):
                if self.ui_buttons.get("close_hint") and self.ui_buttons[
                    "close_hint"
                ].collidepoint(mx, my):
                    game_state["show_hint_popup"] = False
                    game_state["paused"] = False
                return
            if game_state.get("training_complete"):
                if self.ui_buttons.get("restart_btn") and self.ui_buttons[
                    "restart_btn"
                ].collidepoint(mx, my):
                    reset_slingshot(game_state)
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
                game_state["show_hint_popup"] = True
                game_state["paused"] = True
                return

            if mb and not game_state.get("game_over") and not is_paused:
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
                    mb.body.velocity = (
                        mb.body.velocity.x * 2.0,
                        mb.body.velocity.y * 2.0,
                    )
                    mb.is_boosted = True
                    game_state["boost_trail_start_time"] = time.time()
                    create_spark_particle(
                        game_state["spark_particles"],
                        mb.body.position.x,
                        mb.body.position.y,
                    )
                elif mb.state == "flying" and mb.type_index == 3 and mb.split_available:
                    split_bird(game_state)
                elif (
                    mb.state == "flying"
                    and mb.type_index == 4
                    and mb.boomerang_available
                ):
                    activate_boomerang(game_state)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
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
        is_paused = game_state.get("paused", False)

        if game_state.get("screen_shake", 0) > 0:
            game_state["screen_shake"] -= 1 * dt_factor
            game_state["shake_offset"] = (random.randint(-5, 5), random.randint(-5, 5))
        else:
            game_state["shake_offset"] = (0, 0)

        if mb and mb.state == "dragging" and not is_paused:
            mb.drag_to(mx, my, game_state["WIDTH"], game_state["HEIGHT"])

        if is_paused:
            return

        # ДВИЖОК: Шаг симуляции физики PyMunk
        game_state["space"].step(dt)

        update_particles(game_state["trail_particles"], dt)
        update_particles(game_state["dust_particles"], dt)
        update_particles(game_state["spark_particles"], dt)

        if game_state["explosion_active"]:
            game_state["explosion_frames"] -= 1 * dt_factor
            if game_state["explosion_frames"] <= 0:
                game_state["explosion_active"] = False

        if not game_state.get("game_over") and not game_state.get("training_complete"):
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

            # ГИБРИДНЫЕ КОЛЛИЗИИ: Pygame Masks для обработки урона поверх физики PyMunk
            if mb and mb.state in ["flying", "tumbling"]:
                for t in pygame.sprite.spritecollide(
                    mb, game_state.get("targets", []), False, pygame.sprite.collide_mask
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
                                    random.uniform(-120, 0),
                                    game_state["object_size"],
                                    game_state["space"],
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
                                -abs(mb.body.velocity.y * 0.05),
                                game_state["object_size"],
                                game_state["space"],
                                td_img,
                            )
                        )
                        t.kill()
                    mb.die()
                    break

                if game_state["game_mode"] == "obstacle" and mb.state in [
                    "flying",
                    "tumbling",
                ]:
                    for o in pygame.sprite.spritecollide(
                        mb,
                        game_state.get("obstacles", []),
                        False,
                        pygame.sprite.collide_mask,
                    ):
                        create_brick_shatter(
                            game_state["dust_particles"], o.rect.centerx, o.rect.centery
                        )
                        o.kill()  # Физически убираем препятствие из пространства
                        mb.body.velocity = (
                            mb.body.velocity.x * 0.5,
                            mb.body.velocity.y * 0.5,
                        )  # Потеря кинетической энергии
                        if game_state["sound_on"]:
                            game_state["sounds"]["brick_sound"].play()
                        break

            for sb in game_state.get("small_birds", []):
                if sb.state in ["flying", "tumbling"]:
                    for t in pygame.sprite.spritecollide(
                        sb,
                        game_state.get("targets", []),
                        False,
                        pygame.sprite.collide_mask,
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
                                game_state["space"],
                                td_img,
                            )
                        )
                        t.kill()
                        sb.kill()
                        sb.state = "dead"
                        break
                    if game_state["game_mode"] == "obstacle" and sb.state != "dead":
                        for o in pygame.sprite.spritecollide(
                            sb,
                            game_state.get("obstacles", []),
                            False,
                            pygame.sprite.collide_mask,
                        ):
                            create_brick_shatter(
                                game_state["dust_particles"],
                                o.rect.centerx,
                                o.rect.centery,
                            )
                            o.kill()
                            sb.body.velocity = (
                                sb.body.velocity.x * 0.5,
                                sb.body.velocity.y * 0.5,
                            )
                            if game_state["sound_on"]:
                                game_state["sounds"]["brick_sound"].play()
                            break

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
                    mb.die()
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
                                game_state["WIDTH"] // 2,
                                game_state["HEIGHT"] // 2,
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
                                game_state["object_size"],
                                game_state["space"],
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

        if not game_state.get("training_complete"):
            self._draw_normal(screen, mx, my, game_state)
        else:
            self._draw_tc(screen, mx, my, game_state)

        if game_state["paused"]:
            s = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            s.fill((0, 0, 0, 128))
            screen.blit(s, (0, 0))
            if not game_state.get("show_hint_popup") and not game_state.get(
                "show_training_popup"
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

        if game_state.get("show_training_popup"):
            self._draw_tp(screen, mx, my, game_state)
        elif game_state.get("show_hint_popup"):
            self._draw_hp(screen, mx, my, game_state)

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

        if mb and mb.state != "dead":
            if mb.state == "jumping" and mb.jump_image:
                screen.blit(mb.jump_image, (mb.x - mb.size // 2, mb.y - mb.size // 2))
            elif mb.image:
                screen.blit(mb.image, mb.rect)

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