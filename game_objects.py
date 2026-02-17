import pygame
import math
import time
import random
from achievements import get_achievements_for_profile
from utils import draw_text, create_trail_particle, create_dust_particle, create_spark_particle, create_target, create_obstacle, update_particles
from settings import LIVES, SPEED_MULTIPLIER, TARGET_DURATION

CAMPAIGN_GRID_SIZE = 7
SCORE_MAP = {3: 30, 4: 50, 5: 100, 6: 300, 7: 1000}
SQUARE_SCORE = 50

def find_and_score_matches(board):
    """Находит все совпадения, включая линии и квадраты, и подсчитывает очки."""
    total_score = 0
    all_matched_tiles = set()
    
    # 1. Проверка на линии (горизонтальные и вертикальные)
    for r in range(CAMPAIGN_GRID_SIZE):
        for c in range(CAMPAIGN_GRID_SIZE):
            if (r, c) in all_matched_tiles:
                continue
            
            # Горизонтальные
            if c < CAMPAIGN_GRID_SIZE - 2 and board[r][c] is not None:
                match_type = board[r][c]
                line_len = 1
                for i in range(1, CAMPAIGN_GRID_SIZE - c):
                    if board[r][c+i] == match_type:
                        line_len += 1
                    else:
                        break
                if line_len >= 3:
                    total_score += SCORE_MAP.get(line_len, 1000)
                    for i in range(line_len):
                        all_matched_tiles.add((r, c+i))
            
            # Вертикальные
            if r < CAMPAIGN_GRID_SIZE - 2 and board[r][c] is not None:
                match_type = board[r][c]
                line_len = 1
                for i in range(1, CAMPAIGN_GRID_SIZE - r):
                    if board[r+i][c] == match_type:
                        line_len += 1
                    else:
                        break
                if line_len >= 3:
                    total_score += SCORE_MAP.get(line_len, 1000)
                    for i in range(line_len):
                        all_matched_tiles.add((r+i, c))

    # 2. Проверка на квадраты 2x2
    for r in range(CAMPAIGN_GRID_SIZE - 1):
        for c in range(CAMPAIGN_GRID_SIZE - 1):
            tile = board[r][c]
            if tile is not None and \
               tile == board[r+1][c] and \
               tile == board[r][c+1] and \
               tile == board[r+1][c+1]:
                
                # Проверяем, не является ли этот квадрат частью уже найденной линии
                square_tiles = {(r, c), (r+1, c), (r, c+1), (r+1, c+1)}
                if not square_tiles.intersection(all_matched_tiles):
                    total_score += SQUARE_SCORE
                    all_matched_tiles.update(square_tiles)

    return total_score, list(all_matched_tiles)

def check_matches(board):
    """Простая проверка наличия хотя бы одного совпадения (без подсчета очков)."""
    # Проверка по горизонтали
    for r in range(CAMPAIGN_GRID_SIZE):
        for c in range(CAMPAIGN_GRID_SIZE - 2):
            if board[r][c] is not None and board[r][c] == board[r][c+1] == board[r][c+2]:
                return True

    # Проверка по вертикали
    for c in range(CAMPAIGN_GRID_SIZE):
        for r in range(CAMPAIGN_GRID_SIZE - 2):
            if board[r][c] is not None and board[r][c] == board[r+1][c] == board[r+2][c]:
                return True
    
    return False

def create_campaign_board(game_state):
    """Создает доску для режима 'Прохождение' без начальных совпадений."""
    bird_types_count = len(game_state['images']['bird_imgs'])
    while True:
        board = [[random.randint(0, bird_types_count - 1) for _ in range(CAMPAIGN_GRID_SIZE)] for _ in range(CAMPAIGN_GRID_SIZE)]
        if not check_matches(board):
            return board

# --- НОВАЯ АНИМИРОВАННАЯ ЛОГИКА ОБНОВЛЕНИЯ ДОСКИ ---

def find_and_start_clearing_matches(game_state):
    """Находит совпадения и готовит их к анимированному удалению."""
    board = game_state['campaign_board']
    score, matches = find_and_score_matches(board)
    
    if not matches:
        game_state['campaign_is_processing'] = False
        game_state['campaign_board_state'] = 'idle'
        return False

    game_state['campaign_score'] += score
    
    game_state['campaign_board_state'] = 'clearing'
    game_state['campaign_matched_tiles'] = matches
    game_state['campaign_clear_progress'] = 0.0
    
    if game_state['campaign_score'] >= game_state['campaign_target_score']:
        game_state['campaign_level_complete'] = True

    return True

def process_tile_clearing(game_state):
    """Анимирует удаление совпавших плиток."""
    game_state['campaign_clear_progress'] += 0.1
    if game_state['campaign_clear_progress'] >= 1.0:
        board = game_state['campaign_board']
        for r, c in game_state['campaign_matched_tiles']:
            board[r][c] = None
        
        game_state['campaign_matched_tiles'] = []
        game_state['campaign_board_state'] = 'falling'
        prepare_falling_tiles(game_state)

def prepare_falling_tiles(game_state):
    """Определяет, какие плитки должны упасть и как далеко."""
    board = game_state['campaign_board']
    game_state['campaign_falling_tiles'] = []
    
    for c in range(CAMPAIGN_GRID_SIZE):
        empty_spots = 0
        for r in range(CAMPAIGN_GRID_SIZE - 1, -1, -1):
            if board[r][c] is None:
                empty_spots += 1
            elif empty_spots > 0:
                tile_type = board[r][c]
                game_state['campaign_falling_tiles'].append({
                    'type': tile_type,
                    'start_pos': (r, c),
                    'end_pos': (r + empty_spots, c),
                    'progress': 0.0
                })
                board[r + empty_spots][c] = tile_type
                board[r][c] = None

def process_tile_falling(game_state):
    """Анимирует падение плиток."""
    if not game_state.get('campaign_falling_tiles') or len(game_state.get('campaign_falling_tiles')) == 0:
        game_state['campaign_board_state'] = 'refilling'
        prepare_refill_tiles(game_state)
        return

    all_done = True
    for tile in game_state['campaign_falling_tiles']:
        if tile['progress'] < 1.0:
            all_done = False
            tile['progress'] += 0.15
            tile['progress'] = min(tile['progress'], 1.0)
    
    if all_done:
        game_state['campaign_falling_tiles'] = []
        game_state['campaign_board_state'] = 'refilling'
        prepare_refill_tiles(game_state)

def prepare_refill_tiles(game_state):
    """Определяет, где должны появиться новые плитки."""
    board = game_state['campaign_board']
    bird_types_count = len(game_state['images']['bird_imgs'])
    game_state['campaign_refilling_tiles'] = []
    
    for c in range(CAMPAIGN_GRID_SIZE):
        empty_count_in_col = 0
        for r in range(CAMPAIGN_GRID_SIZE):
            if board[r][c] is None:
                empty_count_in_col += 1
                new_type = random.randint(0, bird_types_count - 1)
                board[r][c] = new_type
                game_state['campaign_refilling_tiles'].append({
                    'type': new_type,
                    'start_y_offset': -empty_count_in_col,
                    'end_pos': (r, c),
                    'progress': 0.0
                })

def process_tile_refilling(game_state):
    """Анимирует появление новых плиток сверху."""
    if not game_state.get('campaign_refilling_tiles') or len(game_state.get('campaign_refilling_tiles')) == 0:
        game_state['campaign_board_state'] = 'idle'
        find_and_start_clearing_matches(game_state)
        return

    all_done = True
    for tile in game_state['campaign_refilling_tiles']:
        if tile['progress'] < 1.0:
            all_done = False
            tile['progress'] += 0.15
            tile['progress'] = min(tile['progress'], 1.0)

    if all_done:
        game_state['campaign_refilling_tiles'] = []
        game_state['campaign_board_state'] = 'idle'
        is_new_match = find_and_start_clearing_matches(game_state)
        if not is_new_match:
             game_state['campaign_is_processing'] = False

def update_campaign_board(game_state):
    """Обрабатывает один шаг цикла обновления доски в 'Прохождении'."""
    board_state = game_state.get('campaign_board_state', 'idle')

    if board_state == 'clearing':
        process_tile_clearing(game_state)
    elif board_state == 'falling':
        process_tile_falling(game_state)
    elif board_state == 'refilling':
        process_tile_refilling(game_state)
    elif board_state == 'idle':
        find_and_start_clearing_matches(game_state)


def split_bird(game_state, x, y, vx, vy):
    small_bird_size = game_state['small_object_size']
    for i in range(3):
        angle = math.radians(120 * i)
        small_vx = vx + math.cos(angle) * 3
        small_vy = vy + math.sin(angle) * 3
        bird_rect = pygame.Rect(x - small_bird_size // 2, y - small_bird_size // 2, small_bird_size, small_bird_size)
        
        game_state['small_birds'].append({
            'x': x, 'y': y, 'vx': small_vx, 'vy': small_vy, 'rect': bird_rect, 'active': True,
            'on_ground': False, 'angle': 0, 'is_tumbling': False
        })
    
    if game_state['sound_on'] and game_state['sounds'].get('split_sound'):
        try: game_state['sounds']['split_sound'].play()
        except: pass
    
    game_state['split_available'] = False
    game_state['is_moving'] = False
    game_state['projectile_x'] = -100

def activate_boomerang(game_state):
    game_state['velocity_x'] = -15
    game_state['velocity_y'] = 0
    game_state['boomerang_available'] = False
    if game_state['sound_on'] and game_state['sounds'].get('boomerang_sound'):
        try: game_state['sounds']['boomerang_sound'].play()
        except: pass

def reset_game(game_state):
    profile_achievements = get_achievements_for_profile(game_state['all_profiles_data'], game_state['current_profile'])
    game_state.update(profile_achievements)
    
    game_state['bird_queue'] = []
    
    num_targets = 0
    num_obstacles = 0

    if game_state['game_mode'] == 'campaign':
        game_state['lives'] = float('inf')
        game_state['campaign_board'] = create_campaign_board(game_state)
        game_state['campaign_score'] = 0
        game_state['campaign_level_complete'] = False
        game_state['campaign_selected_tile'] = None
        game_state['campaign_is_processing'] = False
        game_state['campaign_board_state'] = 'idle'
    elif game_state['game_mode'] == 'training':
        game_state['training_complete'] = False
        game_state['show_training_popup'] = True
        game_state['training_bird_index'] = 0
        game_state['training_shots_fired'] = 0
        game_state['training_popup_text'] = game_state['texts']['training_descriptions'][0]
        game_state['current_bird_img'] = None 
        game_state['lives'] = float('inf')
        num_targets = 3
    else:
        game_state['bird_queue'] = [random.choice(game_state['images']['bird_imgs']) for _ in range(3)]
        game_state['current_bird_img'] = game_state['bird_queue'].pop(0)

        if game_state['game_mode'] == 'developer':
            game_state['lives'] = float('inf')
        elif game_state['game_mode'] == 'sharpshooter':
            game_state['lives'] = LIVES.get(game_state['difficulty'], 5)
            num_targets = 1
            game_state['target_duration'] = TARGET_DURATION.get(game_state['difficulty'], 2.5)
        elif game_state['game_mode'] == 'obstacle':
            game_state['lives'] = LIVES.get(game_state['difficulty'], 5)
            num_targets = 3
            num_obstacles = 3
            game_state['target_duration'] = 5
        else:  # classic
            game_state['lives'] = LIVES.get(game_state['difficulty'], 5)
            num_targets = 3
            game_state['target_duration'] = 5
        
    game_state['projectile_x'], game_state['projectile_y'] = game_state['sling_x'], game_state['sling_y']
    bird_size = game_state['object_size']
    game_state['projectile_rect'] = pygame.Rect(game_state['projectile_x'] - bird_size // 2, game_state['projectile_y'] - bird_size // 2, bird_size, bird_size)
    
    game_state['is_dragging'] = False
    game_state['is_moving'] = False
    game_state['show_rope'] = False
    game_state['velocity_x'] = 0
    game_state['velocity_y'] = 0
    game_state['score'] = 0
    game_state['game_over'] = False
    game_state['explosion_active'] = False
    game_state['explosion_frames'] = 0
    game_state['third_bird_boosted'] = False
    game_state['boost_trail_start_time'] = None
    game_state['boost_available'] = False
    game_state['split_available'] = False
    game_state['boomerang_available'] = False
    game_state['small_birds'] = []
    game_state['combo'] = 0
    game_state['trail_particles'] = []
    game_state['dust_particles'] = []
    game_state['spark_particles'] = []
    game_state['feather_particles'] = []
    
    game_state['last_shot_path'] = []
    game_state['path_display_timer'] = 0

    game_state['target_timer_start'] = time.time()
    
    obj_size = game_state['object_size']
    game_state['targets'] = []
    game_state['obstacles'] = []

    all_level_objects = []
    for _ in range(num_targets):
        while True:
            new_target = create_target(game_state['WIDTH'], game_state['HEIGHT'], obj_size)
            if not any(new_target.inflate(10, 10).colliderect(obj) for obj in all_level_objects):
                game_state['targets'].append(new_target)
                all_level_objects.append(new_target)
                break
    
    for _ in range(num_obstacles):
        while True:
            new_obstacle = create_obstacle(game_state['WIDTH'], game_state['HEIGHT'], obj_size)
            if not any(new_obstacle.inflate(10, 10).colliderect(obj) for obj in all_level_objects):
                game_state['obstacles'].append(new_obstacle)
                all_level_objects.append(new_obstacle)
                break

    speed_multiplier = SPEED_MULTIPLIER.get(game_state['difficulty'], 0)
    game_state['target_speeds'] = []
    game_state['obstacle_speeds'] = []
    for _ in game_state['targets']:
        if speed_multiplier > 0:
            dx = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
            dy = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
            game_state['target_speeds'].append((dx, dy))
        else:
            game_state['target_speeds'].append((0, 0))
    for _ in game_state['obstacles']:
        if speed_multiplier > 0:
            dx = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
            dy = random.uniform(0.5, 2.0) * speed_multiplier * random.choice([-1, 1])
            game_state['obstacle_speeds'].append((dx, dy))
        else:
            game_state['obstacle_speeds'].append((0, 0))
            
    return game_state

def update_game_state(game_state):
    if game_state.get('paused'):
        return game_state

    update_particles(game_state['trail_particles'])
    update_particles(game_state['dust_particles'])
    update_particles(game_state['spark_particles'])
    
    if game_state['explosion_active']:
        explosion_radius = game_state['EXPLOSION_RADIUS']
        max_explosion_frames = game_state['MAX_EXPLOSION_FRAMES']
        
        smoke_img_copy = game_state['images']['smoke_img'].copy()
        alpha = int(255 * (game_state['explosion_frames'] / max_explosion_frames))
        smoke_img_copy.set_alpha(alpha)
        game_state['screen'].blit(smoke_img_copy, (game_state['explosion_center'][0] - explosion_radius, game_state['explosion_center'][1] - explosion_radius))
        
        game_state['explosion_frames'] -= 1
        
        if game_state['explosion_frames'] <= 0:
            game_state['explosion_active'] = False
    
    if (game_state['achievement_text'] and time.time() < game_state['achievement_show_time']):
        achievement_surface = pygame.Surface((game_state['WIDTH'], 100), pygame.SRCALPHA)
        achievement_surface.fill((0, 0, 0, 150))
        game_state['screen'].blit(achievement_surface, (0, game_state['HEIGHT'] // 2 - 50))
        
        text_surf, text_rect = draw_text(game_state['achievement_text'], game_state['fonts']['achievement_font'], (255, 215, 0))
        text_rect.center = (game_state['WIDTH'] // 2, game_state['HEIGHT'] // 2)
        game_state['screen'].blit(text_surf, text_rect)
    elif game_state['achievement_text']:
        game_state['achievement_text'] = ""
        
    return game_state