import pygame
import math
import random
from utils import draw_text, get_text
from game_states import State
from game_objects import CAMPAIGN_GRID_SIZE, update_all_volumes, reset_game

SCORE_MAP = {3: 30, 4: 50, 5: 100, 6: 300, 7: 1000}
SQUARE_SCORE = 50


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
    total_score = 0
    all_matched_tiles = set()

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
    board = game_state["campaign_board"]
    game_state["campaign_refilling_tiles"] = []
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


def reset_match3(game_state):
    from achievements import get_achievements_for_profile

    game_state.update(
        get_achievements_for_profile(
            game_state["all_profiles_data"], game_state["current_profile"]
        )
    )
    game_state.update(
        {
            "lives": float("inf"),
            "campaign_board": create_campaign_board(game_state),
            "campaign_score": 0,
            "campaign_level_complete": False,
            "campaign_selected_tile": None,
            "campaign_is_processing": False,
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
            "paused": False,
        }
    )


class Match3State(State):
    def __init__(self):
        self.ui_buttons = {}

    def handle_event(self, event, mx, my, game_state):
        is_paused = (
            game_state["paused"]
            or game_state["campaign_is_processing"]
            or game_state["campaign_is_swapping"]
            or game_state["campaign_level_complete"]
            or game_state.get("show_campaign_hint_popup")
        )

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state["campaign_level_complete"] = False
                game_state["state_manager"].change_state("main_menu", game_state)
            elif event.key == pygame.K_r:
                reset_match3(game_state)
            elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                if not game_state.get("show_campaign_hint_popup"):
                    game_state["paused"] = not game_state["paused"]

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state.get("show_campaign_hint_popup"):
                if self.ui_buttons.get("close_hint") and self.ui_buttons[
                    "close_hint"
                ].collidepoint(mx, my):
                    game_state["show_campaign_hint_popup"] = False
                    game_state["paused"] = False
                return
            if game_state.get("campaign_level_complete"):
                if self.ui_buttons.get("restart_btn") and self.ui_buttons[
                    "restart_btn"
                ].collidepoint(mx, my):
                    reset_match3(game_state)
                elif self.ui_buttons.get("exit_btn") and self.ui_buttons[
                    "exit_btn"
                ].collidepoint(mx, my):
                    game_state["campaign_level_complete"] = False
                    game_state["state_manager"].change_state("main_menu", game_state)
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
                game_state["show_campaign_hint_popup"] = True
                game_state["paused"] = True
                return

            if not is_paused:
                gr = game_state["campaign_grid_rect"]
                if gr.collidepoint(mx, my):
                    cs = game_state["campaign_cell_size"]
                    game_state["campaign_drag_start_pos"] = (mx, my)
                    game_state["campaign_drag_start_tile"] = (
                        int((my - gr.y) / cs),
                        int((mx - gr.x) / cs),
                    )
                    game_state["campaign_is_dragging_tile"] = True

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

    def update(self, dt, mx, my, game_state):
        dt_factor = dt * 60.0
        if game_state.get("paused"):
            return

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

        if game_state.get("campaign_is_processing"):
            update_campaign_board(dt, game_state)

    def draw(self, screen, mx, my, game_state):
        bg = game_state["images"]["background"]
        screen.blit(bg, bg.get_rect(center=screen.get_rect().center))
        self.ui_buttons = {}

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

        if game_state["paused"]:
            s = pygame.Surface(
                (game_state["WIDTH"], game_state["HEIGHT"]), pygame.SRCALPHA
            )
            s.fill((0, 0, 0, 128))
            screen.blit(s, (0, 0))
            if not game_state.get("show_campaign_hint_popup"):
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

        if game_state.get("show_campaign_hint_popup"):
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