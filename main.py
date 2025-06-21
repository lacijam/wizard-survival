import pygame
import math
import random
import os

# === CONFIG ===
FRAME_WIDTH, FRAME_HEIGHT = 8, 8
SCALE = 4
NUM_FRAMES = 4
ANIMATION_FPS = 10
BASE_MAX_CHICKENS = 3
MAX_CHICKENS_CAP = 15
MAX_EGG_INVENTORY = 3
MAX_HEALTH = 3
INVINCIBILITY_TIME = 1.0
GAME_OVER_DISPLAY_TIME = 2.0
WINDOW_WIDTH, WINDOW_HEIGHT = 1066, 800
GAME_WIDTH = 400
GAME_HEIGHT = int(GAME_WIDTH / (1066 / 800))
PANEL_HEIGHT = 56
FLICKER_START = 5.0 
FLICKER_MIN_SPEED = 0.5  # Hz
FLICKER_MAX_SPEED = 5.0 # Hz
CHARGE_INPUT_THRESHOLD = 0.12  # seconds

# === INIT ===
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.Font("PressStart2P.ttf", 12)

HIGHSCORE_FILE = "highscore.txt"
highscore = 0

def save_highscore(new_score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(new_score))

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

highscore = load_highscore()

# === SOUND ===
fire_sound = pygame.mixer.Sound("fire.wav")
hit_sound = pygame.mixer.Sound("hit.wav")
pickup_sound = pygame.mixer.Sound("pickup.wav")
explosion_sound = pygame.mixer.Sound("explosion.wav")
hurt_sound = pygame.mixer.Sound("hurt.wav")
dull_hit_sound = pygame.mixer.Sound("dull_hit.wav")
super_sound = pygame.mixer.Sound("super.wav")
empty_sound = pygame.mixer.Sound("empty.wav")
charge_full_sound = pygame.mixer.Sound("charge_full.wav")
charge_gain_sound = pygame.mixer.Sound("charge_gain.wav")
charge1_sound = pygame.mixer.Sound("charge_1.wav")
charge2_sound = pygame.mixer.Sound("charge_2.wav")

# === SPRITES ===
# -- Player --
player_sheet = pygame.image.load("player.png").convert_alpha()
def get_player_frames(row):
    return [pygame.transform.scale(
        player_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
    ) for i in range(NUM_FRAMES)]
frames_run_right  = get_player_frames(0)
frames_run_left   = get_player_frames(1)
frames_fire_right = get_player_frames(2)
frames_fire_left  = get_player_frames(3)
frames_charge_right = get_player_frames(4)  # Assuming row 4 for charging (right)
frames_charge_left  = get_player_frames(5)  # Assuming row 5 for charging (left)

# -- Fireball/Explosion --
fireball_sheet = pygame.image.load("fireball.png").convert_alpha()
def get_fireball_frames(row=0):
    return [pygame.transform.scale(
        fireball_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
    ) for i in range(NUM_FRAMES)]
frames_fireball = get_fireball_frames(0)
frames_explosion = get_fireball_frames(1)

CHARGE_FIREBALL_COLORS = [
    (255, 255, 255),   # Normal: white (no tint)
    (255, 120, 40),    # Stage 1: orange
    (100, 200, 255),   # Stage 2: blue
]

fireball_variants = []  # [ [normal_frames], [stage1_frames], [stage2_frames] ]
for color in CHARGE_FIREBALL_COLORS:
    colored_set = []
    for base_frame in frames_fireball:
        frame = base_frame.copy()
        frame.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        colored_set.append(frame)
    fireball_variants.append(colored_set)

# -- Piercing Orb Frames (Row 2, zero-indexed) --
def get_orb_frames(row):
    return [
        pygame.transform.scale(
            fireball_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
            (FRAME_WIDTH * SCALE * 1, FRAME_HEIGHT * SCALE * 1)  # Make the orb big
        )
        for i in range(4)
    ]

piercing_orb_frames = get_orb_frames(2)  # Row 2 = 3rd row (zero-indexed)

def get_orb_explosion_frames(row):
    return [
        pygame.transform.scale(
            fireball_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
            (FRAME_WIDTH * SCALE * 1, FRAME_HEIGHT * SCALE * 1)
        )
        for i in range(4)
    ]

piercing_orb_explosion_frames = get_orb_explosion_frames(3)  # 4th row, 0-indexed

# -- Chickens --
chicken_sheet = pygame.image.load("chicken.png").convert_alpha()
def get_chicken_frames(row):
    return [pygame.transform.scale(
        chicken_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
    ) for i in range(NUM_FRAMES)]
chicken_frames_right = get_chicken_frames(0)
chicken_frames_left  = get_chicken_frames(1)

# -- Goose --
goose_sheet = pygame.image.load("goose.png").convert_alpha()
def get_goose_frames(row):
    return [pygame.transform.scale(
        goose_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
    ) for i in range(NUM_FRAMES)]
goose_frames_right = get_goose_frames(0)
goose_frames_left  = get_goose_frames(1)

# -- Crab (Armored Enemy) --
crab_sheet = pygame.image.load("crab.png").convert_alpha()
def get_crab_frames(row):
    return [pygame.transform.scale(
        crab_sheet.subsurface((i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
    ) for i in range(NUM_FRAMES)]
crab_frames_right = get_crab_frames(0)
crab_frames_left  = get_crab_frames(1)

# -- Eggs & Hearts --
egg_sheet = pygame.image.load("egg.png").convert_alpha()
egg_frames = [pygame.transform.scale(
    egg_sheet.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)),
    (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
) for i in range(1)]
golden_egg_frames = [pygame.transform.scale(
    egg_sheet.subsurface((i * FRAME_WIDTH, FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
    (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
) for i in range(1)]

heart_sheet = pygame.image.load("heart.png").convert_alpha()
heart_full = pygame.transform.scale(
    heart_sheet.subsurface((0, 0, FRAME_WIDTH, FRAME_HEIGHT)),
    (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
)
heart_empty = pygame.transform.scale(
    heart_sheet.subsurface((0, FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)),
    (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
)

# -- Meter/Battery (Golden Power Meter) --
meter_sheet = pygame.image.load("meter.png").convert_alpha()

def get_meter_frames(row):
    return [
        pygame.transform.scale(
            meter_sheet.subsurface(
                (i * FRAME_WIDTH, row * FRAME_HEIGHT, FRAME_WIDTH, FRAME_HEIGHT)
            ),
            (FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)
        )
        for i in range(4)
    ]

# --- Charging animation ---
charge_frames = get_meter_frames(0)       # 0 = empty, 1/2/3 = filled
charge_full_anim = get_meter_frames(1)    # 4-frame animation for full
CHARGE_EFFECT_SCALE = 2 * SCALE

charge_anim_img = pygame.image.load("charge.png").convert_alpha()
charge_anim_frames = [
    pygame.transform.scale(
        charge_anim_img.subsurface((i * FRAME_WIDTH, 0, FRAME_WIDTH, FRAME_HEIGHT)),
        (FRAME_WIDTH * CHARGE_EFFECT_SCALE, FRAME_HEIGHT * CHARGE_EFFECT_SCALE)
    )
    for i in range(4)
]


# === HELPERS ===
def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

def colorize_frame(base_frame, rgb):
    frame = base_frame.copy()
    frame.fill(rgb, special_flags=pygame.BLEND_RGB_MULT)
    return frame

def clamp_to_playfield(x, y, w, h):
    clamped_x = clamp(x, 0, GAME_WIDTH - w)
    clamped_y = clamp(y, 0, GAME_HEIGHT - PANEL_HEIGHT - h)
    return clamped_x, clamped_y

def spawn_entity_outside(frames_right, frames_left, type, speed=32):
    side = random.choice([0, 1, 2, 3])
    if side == 0:
        x = -FRAME_WIDTH * SCALE
        y = random.randint(0, GAME_HEIGHT - FRAME_HEIGHT * SCALE)
    elif side == 1:
        x = GAME_WIDTH
        y = random.randint(0, GAME_HEIGHT - FRAME_HEIGHT * SCALE)
    elif side == 2:
        x = random.randint(0, GAME_WIDTH - FRAME_WIDTH * SCALE)
        y = -FRAME_HEIGHT * SCALE
    else:
        x = random.randint(0, GAME_WIDTH - FRAME_WIDTH * SCALE)
        y = GAME_HEIGHT
    return Enemy(x, y, frames_right, frames_left, type, speed=speed)

def animate_entity(entity, dt, move_x=0, move_y=0, num_frames=4, anim_fps=7):
    if move_x or move_y:
        entity.x += move_x * entity.speed * dt
        entity.y += move_y * entity.speed * dt
        if move_x > 0:
            entity.facing = "right"
        elif move_x < 0:
            entity.facing = "left"
        entity.timer += dt
        if entity.timer >= 1 / anim_fps:
            entity.timer -= 1 / anim_fps
            entity.frame_idx = (entity.frame_idx + 1) % num_frames
    else:
        entity.frame_idx = 0

def push_chickens_away_from_enemy(enemy, chickens, fudge=2):
    ex, ey, er = enemy.get_circle()
    for chicken in chickens:
        cx, cy, cr = chicken.get_circle()
        dx = cx - ex
        dy = cy - ey
        dist = math.hypot(dx, dy)
        min_dist = er + cr - fudge
        if dist < min_dist and dist != 0:
            overlap = min_dist - dist
            nx, ny = dx / dist, dy / dist
            chicken.x += nx * overlap
            chicken.y += ny * overlap

def handle_enemy_charge(enemy, player_x, player_y, dt, *,
                        charge_cooldown_range,
                        charge_duration,
                        charge_speed,
                        charge_windup,
                        charge_degree_limit=None):
    # Charging phase
    if getattr(enemy, 'is_charging', False):
        enemy.x += enemy.charge_dx * charge_speed * dt
        enemy.y += enemy.charge_dy * charge_speed * dt
        w = enemy.frames_right[0].get_width()
        h = enemy.frames_right[0].get_height()
        enemy.x, enemy.y = clamp_to_playfield(enemy.x, enemy.y, w, h)
        enemy.charge_time_left -= dt
        if enemy.charge_time_left <= 0:
            enemy.is_charging = False
            enemy.charge_timer = random.uniform(*charge_cooldown_range)
    elif getattr(enemy, 'is_winding_up', False):
        enemy.windup_time_left -= dt
        if enemy.windup_time_left <= 0:
            enemy.is_winding_up = False
            enemy.is_charging = True
            enemy.charge_time_left = charge_duration
    else:
        enemy.charge_timer -= dt
        if enemy.charge_timer <= 0:
            dx = player_x - enemy.x
            dy = player_y - enemy.y
            angle = math.atan2(dy, dx)
            if charge_degree_limit is not None:
                base_angle = 0 if dx >= 0 else math.pi
                delta_angle = angle - base_angle

                while delta_angle < -math.pi:
                    delta_angle += 2 * math.pi
                while delta_angle > math.pi:
                    delta_angle -= 2 * math.pi

                max_rad = math.radians(charge_degree_limit)
                clamped_delta = max(-max_rad, min(max_rad, delta_angle))
                charge_angle = base_angle + clamped_delta
                enemy.charge_dx = math.cos(charge_angle)
                enemy.charge_dy = math.sin(charge_angle)
            else:
                dist = math.hypot(dx, dy)
                if dist == 0:
                    enemy.charge_dx = 0
                    enemy.charge_dy = 0
                else:
                    enemy.charge_dx = dx / dist
                    enemy.charge_dy = dy / dist
            enemy.charge_target_x = enemy.x + enemy.charge_dx * int(charge_speed * charge_duration)
            enemy.charge_target_y = enemy.y + enemy.charge_dy * int(charge_speed * charge_duration)
            enemy.is_winding_up = True
            enemy.windup_time_left = charge_windup
        else:
            # Move slowly towards player (homing)
            enemy.update(dt, player_x, player_y)

def spawn_fireball(player, direction, charge_stage):
    BULLET_SPAWN_FACTOR = 0.5 # half way from the player origin
    x = player.x + (FRAME_WIDTH * SCALE * BULLET_SPAWN_FACTOR if direction == "right" else -FRAME_WIDTH * SCALE * BULLET_SPAWN_FACTOR)
    y = player.y  # Adjust for your origin
    bullets.append(Bullet(x, y, direction, charge_stage=charge_stage))

def handle_enemy_death(enemy, kind, items, explosions, explosion_type="normal"):
    global score

    if explosion_type == "orb":
        orb_explosions.append(OrbExplosion(enemy.x, enemy.y))
    else:
        explosions.append(Explosion(enemy.x, enemy.y))

    maybe_drop_item(enemy, items)
    hit_sound.play()

    if kind == "chicken":
        score += SCORE_CHICKEN
    elif kind == "goose":
        score += SCORE_GOOSE
    elif kind == "crab":
        score += SCORE_CRAB

def reset_game():
    global player
    player = Player(GAME_WIDTH // 2, GAME_HEIGHT // 2)
    global player_health, egg_inventory, score, chickens, bullets, items, explosions, invincibility_timer
    player_health = MAX_HEALTH
    egg_inventory = 0
    score = 0
    chickens.clear()
    geese.clear()
    crabs.clear()
    global chicken_spawn_timer
    chicken_spawn_timer = CHICKEN_SPAWN_INTERVAL
    global goose_present, goose_enemy, goose_respawn_timer
    global goose_ready_to_spawn, goose_random_delay
    goose_present = False
    goose_enemy = None
    goose_respawn_timer = GOOSE_SPAWN_INTERVAL
    goose_ready_to_spawn = False
    goose_random_delay = 0.0
    global crab_present, crab_enemy, crab_respawn_timer, crab_ready_to_spawn, crab_random_delay
    global crab_warning_timer
    crab_warning_timer = 0.0
    crab_present = False
    crab_enemy = None
    crab_respawn_timer = CRAB_SPAWN_INTERVAL
    crab_ready_to_spawn = False
    crab_random_delay = 0.0
    global charge_anim_timer, charge_anim_idx
    charge_anim_timer = 0.0
    charge_anim_idx = 0
    bullets.clear()
    items.clear()
    explosions.clear()
    for _ in range(BASE_MAX_CHICKENS):
        chickens.append(spawn_entity_outside(chicken_frames_right, chicken_frames_left, "chicken"))
    invincibility_timer = 0.0

def maybe_drop_item(chicken, items):
    rand = random.random()
    w, h = chicken.frames_right[0].get_width(), chicken.frames_right[0].get_height()
    base_x = chicken.x + w // 2 - egg_frames[0].get_width() // 2
    base_y = chicken.y + h // 2 - egg_frames[0].get_height() // 2

    def random_offset(n=8):
        return random.randint(-n, n)

    item_w, item_h = egg_frames[0].get_width(), egg_frames[0].get_height()

    if chicken.type == "goose":
        w, h = goose_frames_right[0].get_width(), goose_frames_right[0].get_height()
        item_x = chicken.x + w // 2 - golden_egg_frames[0].get_width() // 2 + random_offset()
        item_y = chicken.y + h // 2 - golden_egg_frames[0].get_height() // 2 + random_offset()
        item_x, item_y = clamp_to_playfield(item_x, item_y, item_w, item_h)
        items.append(Item(item_x, item_y, kind="golden_egg"))

    if rand < 0.09:
        item_x = base_x + random_offset()
        item_y = base_y + random_offset()
        item_x, item_y = clamp_to_playfield(item_x, item_y, item_w, item_h)
        items.append(Item(item_x, item_y, kind="egg"))
    elif rand < 0.13:
        item_x = base_x + random_offset()
        item_y = base_y + random_offset()
        item_x, item_y = clamp_to_playfield(item_x, item_y, item_w, item_h)
        items.append(Item(item_x, item_y, kind="heart"))

# === ENTITY CLASSES ===
class Player:
    def __init__(self, x, y, speed=120):
        self.x = x
        self.y = y
        self.facing = "right"
        self.frame_idx = 0
        self.timer = 0
        self.speed = speed
        self.firing = False
        self.fire_frame = 0
        self.fire_timer = 0
        self.charging = False
        self.charge_timer = 0.0
        self.charge_stage = 0
        self.charge_anim_frame = 0
        self.charge_anim_timer = 0.0
        self.pending_bullet_stage = None  # Stage to use when firing animation finishes
        self.facing_locked = False
        self.facing_locked_dir = self.facing
        self.charge_sfx_played = [False, False]  # For stage 1 and 2
        self.pending_fire = False

    def update(self, dt, keys, firing_allowed, is_charging=False):
        move_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        move_y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        length = math.hypot(move_x, move_y)
        if length > 0:
            norm_x = move_x / length
            norm_y = move_y / length
        else:
            norm_x, norm_y = 0, 0

        move_mult = 1.0
        if self.firing:
            move_mult = PLAYER_SHOOT_MOVE_MULT
        elif is_charging:
            move_mult = PLAYER_CHARGE_MOVE_MULT

        animate_entity(self, dt, norm_x * move_mult, norm_y * move_mult, num_frames=NUM_FRAMES, anim_fps=ANIMATION_FPS)

        self.x, self.y = clamp_to_playfield(self.x, self.y, FRAME_WIDTH * SCALE, FRAME_HEIGHT * SCALE)

    def get_circle(self):
        w = frames_run_right[0].get_width()
        h = frames_run_right[0].get_height()
        cx = self.x + w // 2
        cy = self.y + h // 2
        radius = int(w * 0.1)
        return (cx, cy, radius)

    def get_rect(self):
        w = frames_run_right[0].get_width()
        h = frames_run_right[0].get_height()
        return pygame.Rect(self.x, self.y, w, h)

    def draw(self, surface, invincible, firing):
        sprite = None
        facing = self.facing_locked_dir if self.facing_locked else self.facing
        if self.charging:
            charge_frames = frames_charge_right if facing == "right" else frames_charge_left
            sprite = charge_frames[self.charge_anim_frame % NUM_FRAMES]
        elif firing:
            sprite = frames_fire_right[min(self.fire_frame, 3)] if facing == "right" else frames_fire_left[min(self.fire_frame, 3)]
        else:
            if invincible and int(invincibility_timer * 10) % 2 == 0:
                sprite = None  # Flicker effect
            else:
                sprite = frames_run_right[self.frame_idx] if facing == "right" else frames_run_left[self.frame_idx]
        if sprite:
            surface.blit(sprite, (int(self.x), int(self.y)))
    
    def update_firing(self, dt):
        if player.firing:
            player.fire_timer += dt
            if player.fire_timer >= 1 / ANIMATION_FPS:
                player.fire_timer -= 1 / ANIMATION_FPS
                player.fire_frame += 1
                if player.fire_frame >= 4:
                    player.firing = False
                    player.fire_frame = 0
                    return True
        return False

    def start_firing(self):
        player.firing = True
        player.fire_frame = 0
        player.fire_timer = 0

class Enemy:
    def __init__(self, x, y, frames_right, frames_left, type, speed=32):
        self.x = x
        self.y = y
        self.frames_right = frames_right
        self.frames_left = frames_left
        self.facing = "right"
        self.frame_idx = 0
        self.timer = 0
        self.speed = speed
        self.type = type

    def update(self, dt, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        if distance != 0:
            move_x = dx / distance
            move_y = dy / distance
        else:
            move_x, move_y = 0, 0
        animate_entity(self, dt, move_x, move_y, num_frames=NUM_FRAMES, anim_fps=ANIMATION_FPS)

        w = self.frames_right[0].get_width()
        h = self.frames_right[0].get_height()
        center_x = self.x + w // 2
        center_y = self.y + h // 2

        margin = 20  # Tweak as needed

        min_x, max_x = 0 + margin, GAME_WIDTH - margin
        min_y, max_y = 0 + margin, GAME_HEIGHT - PANEL_HEIGHT - margin

        if min_x < center_x < max_x and min_y < center_y < max_y:
            self.x, self.y = clamp_to_playfield(self.x, self.y, w, h)

    def draw(self, surface):
        frames = self.frames_right if self.facing == "right" else self.frames_left
        surface.blit(frames[self.frame_idx], (int(self.x), int(self.y)))

    def get_rect(self):
        frames = self.frames_right if self.facing == "right" else self.frames_left
        frame = frames[self.frame_idx]
        w, h = frame.get_width(), frame.get_height()
        return pygame.Rect(self.x, self.y, w, h)

    def get_circle(self):
        frames = self.frames_right if self.facing == "right" else self.frames_left
        frame = frames[self.frame_idx]
        w, h = frame.get_width(), frame.get_height()
        cx = self.x + w // 2
        cy = self.y + h // 2
        radius = w // 2
        return (cx, cy, radius)

class Bullet:
    def __init__(self, x, y, direction, charge_stage=0):
        self.x = x
        self.y = y
        self.direction = direction
        self.charge_stage = charge_stage
        self.frame_idx = 0
        self.timer = 0
        self.piercing = charge_stage >= 1  # Only stage 1 and 2 pierce
        self.hit_enemies = set()

    def get_frame(self):
        return fireball_variants[self.charge_stage][self.frame_idx]

    def update(self, dt):
        dx = 200 * dt * (1 if self.direction == "right" else -1)
        self.x += dx
        self.timer += dt
        if self.timer >= 1 / ANIMATION_FPS:
            self.timer -= 1 / ANIMATION_FPS
            self.frame_idx = (self.frame_idx + 1) % NUM_FRAMES

    def draw(self, surface):
        surface.blit(bullet.get_frame(), (bullet.x, bullet.y))
        if False:
            cx, cy, radius = self.get_circle()
            pygame.draw.circle(surface, (0,255,0), (int(cx), int(cy)), radius, 1)

    def get_circle(self):
        frame = frames_fireball[self.frame_idx]
        w, h = frame.get_width(), frame.get_height()
        cx = self.x + w // 2
        cy = self.y + h // 2
        radius = 2 * SCALE  # Logical hitbox matches game scale
        return (cx, cy, radius)

class Explosion:
    def __init__(self, x, y, frames=frames_explosion, scale=1):
        self.x = x
        self.y = y
        self.frames = frames
        self.frame_idx = 0
        self.timer = 0
        self.finished = False
        self.scale = scale

    def update(self, dt):
        self.timer += dt
        if self.timer >= 1 / ANIMATION_FPS:
            self.timer -= 1 / ANIMATION_FPS
            self.frame_idx += 1
            if self.frame_idx >= len(self.frames):
                self.finished = True

    def draw(self, surface):
        if not self.finished:
            frame = self.frames[self.frame_idx % len(self.frames)]
            if self.scale != 1:
                w = frame.get_width() * self.scale
                h = frame.get_height() * self.scale
                scaled_frame = pygame.transform.scale(frame, (int(w), int(h)))
                surface.blit(scaled_frame, (int(self.x), int(self.y)))
            else:
                surface.blit(frame, (int(self.x), int(self.y)))

class OrbExplosion:
    def __init__(self, x, y, frames=piercing_orb_explosion_frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.frame_idx = 0
        self.timer = 0.0
        self.finished = False

    def update(self, dt):
        self.timer += dt
        if self.timer >= 0.07:
            self.timer -= 0.07
            self.frame_idx += 1
            if self.frame_idx >= len(self.frames):
                self.finished = True

    def draw(self, surface):
        if not self.finished:
            frame = self.frames[self.frame_idx % len(self.frames)]
            draw_x = int(self.x - frame.get_width() // 2)
            draw_y = int(self.y - frame.get_height() // 2)
            surface.blit(frame, (draw_x, draw_y))

class PiercingOrb:
    def __init__(self, x, y, direction, super_mode=False, custom_speed=None):
        self.x = x
        self.y = y
        self.dx, self.dy = direction
        self.super_mode = super_mode
        self.radius = (FRAME_WIDTH * SCALE) if not super_mode else (FRAME_WIDTH * SCALE * 1.5)
        self.speed = custom_speed if custom_speed is not None else (120 if super_mode else 80)
        self.frame_idx = 0
        self.anim_timer = 0.0
        self.enemies_hit = set()
        self.lifetime = 2.5 if super_mode else 2.0
        self.alive = True

    def update(self, dt):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.lifetime -= dt
        if (
            self.x < -self.radius or self.x > GAME_WIDTH + self.radius
            or self.y < -self.radius or self.y > GAME_HEIGHT + self.radius
            or self.lifetime <= 0
        ):
            self.alive = False
        self.anim_timer += dt
        if self.anim_timer > 0.12:
            self.anim_timer -= 0.12
            self.frame_idx = (self.frame_idx + 1) % 4

    def draw(self, surface):
        frame = piercing_orb_frames[self.frame_idx]
        draw_x = int(self.x - frame.get_width() // 2)
        draw_y = int(self.y - frame.get_height() // 2)
        surface.blit(frame, (draw_x, draw_y))

    def get_circle(self):
        return (self.x, self.y, self.radius)

class Item:
    def __init__(self, x, y, kind="egg"):
        self.x = x
        self.y = y
        self.kind = kind  # "egg", "golden_egg", "heart"
        if kind == "egg":
            self.frame = egg_frames[0]
        elif kind == "golden_egg":
            self.frame = golden_egg_frames[0]
        elif kind == "heart":
            self.frame = heart_full
        else:
            raise ValueError("Unknown item kind: " + kind)
        self.lifetime = 7.0  # seconds on ground (tweak as needed)
        self.flicker_timer = 0.0

    def update(self, dt):
        self.lifetime -= dt
        self.update_flicker(dt)

    def should_flicker(self):
        return self.lifetime <= FLICKER_START

    def is_gone(self):
        return self.lifetime <= 0

    def update_flicker(self, dt):
        if self.should_flicker():
            t = max(0, min(1, 1 - self.lifetime / FLICKER_START))
            flicker_speed = (1 - t) * FLICKER_MIN_SPEED + t * FLICKER_MAX_SPEED
            self.flicker_timer += dt * flicker_speed * 2 * math.pi

    def draw(self, surface):
        if self.should_flicker():
            if math.sin(self.flicker_timer) > 0:
                surface.blit(self.frame, (int(self.x), int(self.y)))
        else:
            surface.blit(self.frame, (int(self.x), int(self.y)))

    def get_rect(self):
        w, h = self.frame.get_width(), self.frame.get_height()
        return pygame.Rect(self.x, self.y, w, h)

# === GAME STATE ===
game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
running = True

player = Player(GAME_WIDTH // 2, GAME_HEIGHT // 2)

PLAYER_MOVE_SPEED = 120
PLAYER_SHOOT_MOVE_MULT = 0.2   # 0 = stand still while firing, try 0.2 for micro adjust
PLAYER_CHARGE_MOVE_MULT = 0.1  # 0 = stand still while charging, try 0.15 for micro adjust

CHARGE_STAGE_1 = 0.4    # seconds
CHARGE_STAGE_2 = 0.75    # seconds

bullets = []

explosions = []
orb_explosions = []
piercing_orbs = []
items = []
armored_enemies = []

# DEBUG
items.append(Item(GAME_WIDTH // 2, GAME_HEIGHT // 2, kind="golden_egg"))

egg_inventory = 0
score = 0
player_health = MAX_HEALTH
invincibility_timer = 0.0

SCORE_CHICKEN = 1
SCORE_GOOSE = 2
SCORE_CRAB = 5

chickens = [spawn_entity_outside(chicken_frames_right, chicken_frames_left, "chicken") for _ in range(BASE_MAX_CHICKENS)]
CHICKEN_SPAWN_INTERVAL = 1.0  # seconds (adjust as you like)
chicken_spawn_timer = CHICKEN_SPAWN_INTERVAL

geese = []
crabs = []

GOOSE_MIN_SCORE = 10
GOOSE_SPEED = 45  
GOOSE_SPAWN_INTERVAL = 7.0   # seconds between goose appearances (tweak as you like)
GOOSE_WARNING_TIME = 2.0  # seconds to display warning
GOOSE_CHARGE_COOLDOWN = (0.9, 1.2)  # Min/max seconds between charges
GOOSE_CHARGE_DURATION = 0.3        # How long the charge lasts
GOOSE_CHARGE_SPEED = 650            # Goose charge speed (pixels/sec)
GOOSE_CHARGE_WINDUP = 0.4             # Time goose stands still before charging
goose_spawn_timer = GOOSE_SPAWN_INTERVAL
goose_warning_timer = 0
goose_pending_spawn = False

CRAB_MIN_SCORE = 0
CRAB_SPEED = 10
CRAB_SPAWN_INTERVAL = 5.0  # seconds
CRAB_WARNING_TIME = 2.0  # seconds
CRAB_CHARGE_COOLDOWN = (0.3, 0.5)        # Time between charges
CRAB_CHARGE_DURATION = 3.0              # How long the charge lasts (tweak)
CRAB_CHARGE_SPEED = 120                  # Crab charge speed (pixels/sec)
CRAB_CHARGE_WINDUP = 0.15                 # Time crab stands still before charging
CRAB_CHARGE_DEGREE_LIMIT = 5            # Crab's charge can deviate ±10 degrees from horizontal
crab_spawn_timer = CRAB_SPAWN_INTERVAL
crab_warning_timer = 0
crab_pending_spawn = True

# Golden power
GOLDEN_POWER_REQUIRED = 3
golden_power = 0
charge_anim_timer = 0.0
charge_anim_idx = 0

# Game over
GAME_OVER_DISPLAY_TIME = 5.0
game_over = False
game_over_timer = 0.0
debug_explosion_circle = None

# === MAIN LOOP ===
while running:
    dt = clock.tick(60) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        if not game_over:
            if event.type == pygame.KEYDOWN:
                if not player.charging and not player.firing:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        player.facing = "left"
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        player.facing = "right"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not player.firing and not player.charging and not player.pending_fire:
                    player.pending_fire = True
                    player.fire_key_timer = 0.0

            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                if player.pending_fire and not player.charging:
                    player.facing_locked = True
                    player.facing_locked_dir = player.facing

                    player.pending_fire = False
                    player.firing = True
                    player.fire_frame = 0
                    player.fire_timer = 0.0
                    player.pending_bullet_stage = 0
                    fire_sound.play()
                elif player.charging:
                    stage = player.charge_stage
                    player.charging = False
                    player.charge_timer = 0.0
                    player.charge_stage = 0
                    player.facing_locked = False
                    player.firing = True
                    player.fire_frame = 0
                    player.fire_timer = 0.0
                    player.pending_bullet_stage = stage
                    fire_sound.play()
                player.pending_fire = False
                player.fire_key_timer = 0.0

            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    if golden_power > 0:
                        num_orbs = 8
                        center_x = player.x + frames_run_right[0].get_width() // 2
                        center_y = player.y + frames_run_right[0].get_height() // 2
                        angle_step = 2 * math.pi / num_orbs
                        speed = 140 if golden_power == GOLDEN_POWER_REQUIRED else 110

                        for i in range(num_orbs):
                            angles = [0, math.pi/2, math.pi, 3*math.pi/2]
                            for angle in angles:
                                dx = math.cos(angle)
                                dy = math.sin(angle)
                                piercing_orbs.append(PiercingOrb(
                                    player.x + FRAME_WIDTH * SCALE // 2, player.y + FRAME_WIDTH * SCALE // 2, (dx, dy), 
                                    super_mode=(golden_power == GOLDEN_POWER_REQUIRED), 
                                    custom_speed=speed
                                ))

                        if golden_power == GOLDEN_POWER_REQUIRED:
                            golden_power = 0
                        else:
                            golden_power -= 1
                        super_sound.play()
                    else:
                        empty_sound.play()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    if egg_inventory <= 0:
                        empty_sound.play()
                        continue

                    egg_inventory -= 1

                    px, py, pr = player.get_circle()
                    explosion_radius = 64  # Game pixels
                    explosion_scale = explosion_radius * 2 // frames_explosion[0].get_width()
                    explosions.append(Explosion(px - explosion_radius, py - explosion_radius, scale=explosion_scale))
                    explosion_sound.play()
                    #debug_explosion_circle = (px, py, explosion_radius, 0.2)

                    chickens_to_remove = set()
                    for chicken in chickens:
                        cx, cy, cr = chicken.get_circle()
                        dist_sq = (px - cx) ** 2 + (py - cy) ** 2
                        if dist_sq <= explosion_radius ** 2:
                            handle_enemy_death(chicken, "chicken", items, explosions)
                            chickens_to_remove.add(chicken)
                    for chicken in chickens_to_remove:
                        if chicken in chickens:
                            chickens.remove(chicken)

                    geese_to_remove = set()
                    for goose in geese:
                        gx, gy, gr = goose.get_circle()
                        dist_sq = (px - gx) ** 2 + (py - gy) ** 2
                        if dist_sq <= explosion_radius ** 2:
                            handle_enemy_death(goose, "goose", items, explosions)

                            geese_to_remove.add(goose)

                    for goose in geese_to_remove:
                        if goose in geese:
                            geese.remove(goose)

                    for crab in crabs:
                        cx, cy, cr = crab.get_circle()
                        dist_sq = (px - cx) ** 2 + (py - cy) ** 2
                        if dist_sq <= explosion_radius ** 2:
                            dull_hit_sound.play()

    if not running:
        break

    # --- Game Over Logic ---
    if game_over:
        game_over_timer -= dt
        
        if game_over_timer <= 0:
            reset_game()
            game_over = False
        
        game_surface.fill((32, 32, 40))

        msg = font.render("GAME OVER", False, (255, 60, 60))
        msg_x = GAME_WIDTH // 2 - msg.get_width() // 2
        msg_y = GAME_HEIGHT // 2 - msg.get_height() // 2
        game_surface.blit(msg, (msg_x, msg_y))

        scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        continue

    if invincibility_timer > 0:
        invincibility_timer -= dt

    if debug_explosion_circle:
        cx, cy, rad, timer = debug_explosion_circle
        timer -= dt
        if timer <= 0:
            debug_explosion_circle = None
        else:
            debug_explosion_circle = (cx, cy, rad, timer)

    keys = pygame.key.get_pressed()

    if player.pending_fire:
        player.fire_key_timer += dt
        if player.fire_key_timer >= CHARGE_INPUT_THRESHOLD and not player.charging:
            player.charging = True
            player.charge_timer = 0.0
            player.charge_stage = 0
            player.charge_anim_frame = 0
            player.charge_anim_timer = 0.0
            player.facing_locked = True
            player.facing_locked_dir = player.facing
            player.charge_sfx_played = [False, False]   # <-- RESET HERE!

    if player.charging:
        player.charge_timer += dt

        if player.charge_timer >= CHARGE_STAGE_2:
            player.charge_stage = 2
        elif player.charge_timer >= CHARGE_STAGE_1:
            player.charge_stage = 1
        else:
            player.charge_stage = 0

        if player.charge_stage == 1 and not player.charge_sfx_played[0]:
            charge1_sound.play()
            player.charge_sfx_played[0] = True
        elif player.charge_stage == 2 and not player.charge_sfx_played[1]:
            charge2_sound.play()
            player.charge_sfx_played[1] = True

        player.charge_anim_timer += dt
        if player.charge_anim_timer >= 1 / ANIMATION_FPS:
            player.charge_anim_timer -= 1 / ANIMATION_FPS
            player.charge_anim_frame = (player.charge_anim_frame + 1) % NUM_FRAMES
    else:
        player.charge_anim_frame = 0
        player.charge_anim_timer = 0.0

    player.update(dt, keys, firing_allowed=not player.firing, is_charging=player.charging)

    if player.update_firing(dt):
        if player.pending_bullet_stage is not None:
            spawn_fireball(player, player.facing_locked_dir, player.pending_bullet_stage)
            player.pending_bullet_stage = None
        player.facing_locked = False

    for chicken in chickens:
        chicken.update(dt, player.x, player.y)
    for bullet in bullets:
        bullet.update(dt)
    for explosion in explosions:
        explosion.update(dt)
    explosions = [e for e in explosions if not e.finished]

    # --- Chicken-Chicken Collision Resolution ---
    for i, a in enumerate(chickens):
        ax, ay, ar = a.get_circle()
        for j in range(i + 1, len(chickens)):
            b = chickens[j]
            bx, by, br = b.get_circle()
            dx = bx - ax
            dy = by - ay
            dist = math.hypot(dx, dy)
            min_dist = ar + br - 2  # Small gap to reduce jitter

            if dist < min_dist and dist != 0:
                overlap = (min_dist - dist)
                nx, ny = dx / dist, dy / dist
                a.x -= nx * overlap / 2
                a.y -= ny * overlap / 2
                b.x += nx * overlap / 2
                b.y += ny * overlap / 2

    for orb in piercing_orbs:
        orb.update(dt)
    piercing_orbs = [o for o in piercing_orbs if o.alive]

    for exp in orb_explosions:
        exp.update(dt)
    orb_explosions = [e for e in orb_explosions if not e.finished]

    if score >= GOOSE_MIN_SCORE:
        if not goose_pending_spawn:
            goose_spawn_timer -= dt
            if goose_spawn_timer <= 0:
                goose_warning_timer = GOOSE_WARNING_TIME
                goose_pending_spawn = True
                goose_spawn_timer = GOOSE_SPAWN_INTERVAL
        else:
            goose_warning_timer -= dt
            if goose_warning_timer <= 0:
                new_goose = spawn_entity_outside(goose_frames_right, goose_frames_left, "goose", speed=GOOSE_SPEED)
                new_goose.charge_timer = random.uniform(*GOOSE_CHARGE_COOLDOWN)
                new_goose.is_charging = False
                new_goose.charge_dx = 0.0
                new_goose.charge_dy = 0.0
                new_goose.charge_time_left = 0.0
                new_goose.is_winding_up = False
                new_goose.windup_time_left = 0.0
                new_goose.charge_target_x = 0.0
                new_goose.charge_target_y = 0.0
                geese.append(new_goose)
                goose_pending_spawn = False

    if goose_warning_timer > 0:
        goose_warning_timer -= dt

    if crab_warning_timer > 0:
        crab_warning_timer -= dt

    for goose in geese[:]:
        handle_enemy_charge(goose, player.x, player.y, dt,
            charge_cooldown_range=GOOSE_CHARGE_COOLDOWN,
            charge_duration=GOOSE_CHARGE_DURATION,
            charge_speed=GOOSE_CHARGE_SPEED,
            charge_windup=GOOSE_CHARGE_WINDUP,
            charge_degree_limit=None 
        )
        push_chickens_away_from_enemy(goose, chickens)

    for crab in crabs:
        handle_enemy_charge(crab, player.x, player.y, dt,
            charge_cooldown_range=CRAB_CHARGE_COOLDOWN,
            charge_duration=CRAB_CHARGE_DURATION,
            charge_speed=CRAB_CHARGE_SPEED,
            charge_windup=CRAB_CHARGE_WINDUP,
            charge_degree_limit=CRAB_CHARGE_DEGREE_LIMIT 
        )
        push_chickens_away_from_enemy(crab, chickens)

    if score >= CRAB_MIN_SCORE:
        if not crab_pending_spawn:
            crab_spawn_timer -= dt
            if crab_spawn_timer <= 0:
                crab_warning_timer = CRAB_WARNING_TIME
                crab_pending_spawn = True
                crab_spawn_timer = CRAB_SPAWN_INTERVAL
        else:
            crab_warning_timer -= dt
            if crab_warning_timer <= 0:
                new_crab = spawn_entity_outside(crab_frames_right, crab_frames_left, "crab", speed=CRAB_SPEED)
                new_crab.charge_timer = random.uniform(*CRAB_CHARGE_COOLDOWN)
                new_crab.is_charging = False
                new_crab.charge_dx = 0.0
                new_crab.charge_dy = 0.0
                new_crab.charge_time_left = 0.0
                new_crab.is_winding_up = False
                new_crab.windup_time_left = 0.0
                new_crab.charge_target_x = 0.0
                new_crab.charge_target_y = 0.0
                crabs.append(new_crab)
                crab_pending_spawn = False

    # --- Collisions: Player <-> Chickens ---
    pcx, pcy, pr = player.get_circle()
    chicken_hit_player = False
    for chicken in chickens:
        cx, cy, cr = chicken.get_circle()
        dist_sq = (pcx - cx) ** 2 + (pcy - cy) ** 2
        if dist_sq <= (pr + cr) ** 2:
            chicken_hit_player = True
            break

    goose_hit_player = False
    for goose in geese:
        gx, gy, gr = goose.get_circle()
        dist_sq = (pcx - gx) ** 2 + (pcy - gy) ** 2
        if dist_sq <= (pr + gr) ** 2:
            goose_hit_player = True
            break

    crab_hit_player = False
    for crab in crabs:
        cx, cy, cr = crab.get_circle()
        dist_sq = (pcx - cx) ** 2 + (pcy - cy) ** 2
        if dist_sq <= (pr + cr) ** 2:
            crab_hit_player = True
            break

    if (chicken_hit_player or goose_hit_player or crab_hit_player) and invincibility_timer <= 0:
        player_health -= 1
        invincibility_timer = INVINCIBILITY_TIME
        hurt_sound.play()
        if player_health < 0:
            player_health = 0
        if player_health <= 0 and not game_over:
            game_over = True
            game_over_timer = GAME_OVER_DISPLAY_TIME
            if score > highscore:
                highscore = score
                save_highscore(highscore)

    # --- Collisions: Bullet <-> Chickens ---
    bullets_to_remove = set()
    chickens_to_remove = set()
    for bullet in bullets[:]:
        bullet_hit = False
        bx, by, br = bullet.get_circle()
        for chicken in chickens[:]:
            if chicken in bullet.hit_enemies:
                continue
            cx, cy, cr = chicken.get_circle()
            if (bx - cx) ** 2 + (by - cy) ** 2 <= (br + cr) ** 2:
                bullet.hit_enemies.add(chicken)
                chickens_to_remove.add(chicken)
                handle_enemy_death(chicken, "chicken", items, explosions)
                if not bullet.piercing:
                    bullets_to_remove.add(bullet)
                    bullet_hit = True
                    break  # Only break for non-piercing bullets

        if not bullet_hit:
            for goose in geese:
                gx, gy, gr = goose.get_circle()
                dist_sq = (bx - gx) ** 2 + (by - gy) ** 2
                if dist_sq <= (br + gr) ** 2:
                    if bullet.charge_stage >= 1:
                        handle_enemy_death(goose, "goose", items, explosions)
                        geese.remove(goose)
                    else:
                        dull_hit_sound.play()
                    bullets_to_remove.add(bullet)
                    bullet_hit = True
                    break

        if not bullet_hit:
            for crab in crabs:
                cx, cy, cr = crab.get_circle()
                dist_sq = (bx - cx) ** 2 + (by - cy) ** 2
                if dist_sq <= (br + cr) ** 2:
                    if bullet.charge_stage >= 2:
                        handle_enemy_death(crab, "crab", items, explosions)
                        crabs.remove(crab)
                    else:
                        dull_hit_sound.play()
                    bullets_to_remove.add(bullet)
                    bullet_hit = True
                    break
                
    for bullet in bullets_to_remove:
        if bullet in bullets:
            bullets.remove(bullet)
    for chicken in chickens_to_remove:
        if chicken in chickens:
            chickens.remove(chicken)

    # Collision Orb --> Enemies
    for orb in piercing_orbs:
        ox, oy, orad = orb.get_circle()

        for chicken in list(chickens):
            cx, cy, cr = chicken.get_circle()
            dist_sq = (ox - cx)**2 + (oy - cy)**2
            if dist_sq <= (orad + cr)**2 and chicken not in orb.enemies_hit:
                orb.enemies_hit.add(chicken)
                chickens.remove(chicken)
                handle_enemy_death(chicken, "chicken", items, explosions, "orb")
        
        for goose in list(geese):
            if goose not in orb.enemies_hit:
                gx, gy, gr = goose.get_circle()
                dist_sq = (ox - gx) ** 2 + (oy - gy) ** 2
                if dist_sq <= (orad + gr) ** 2:
                    orb.enemies_hit.add(goose)
                    geese.remove(goose)
                    handle_enemy_death(goose, "goose", items, explosions, "orb")

        for crab in list(crabs):
            if crab not in orb.enemies_hit:
                cx, cy, cr = crab.get_circle()
                dist_sq = (ox - cx) ** 2 + (oy - cy) ** 2
                if dist_sq <= (orad + cr) ** 2:
                    orb.enemies_hit.add(crab)
                    crabs.remove(crab)
                    handle_enemy_death(crab, "crab", items, explosions, "orb")

    # --- Collisions: Player <-> Items ---
    items_to_remove = []
    for item in items:
        item_rect = item.get_rect()
        dx = (item_rect.centerx - pcx)
        dy = (item_rect.centery - pcy)
        if (dx**2 + dy**2) <= (pr + item_rect.width // 2) ** 2:
            if item.kind == "egg":
                if egg_inventory < MAX_EGG_INVENTORY:
                    egg_inventory += 1
                    pickup_sound.play()
                    items_to_remove.append(item)
                else:
                    score += 1  # Or show a "Bonus!" message
                    pickup_sound.play()
                    items_to_remove.append(item)

            elif item.kind == "golden_egg":
                charge_full_sound.play()
                if golden_power < GOLDEN_POWER_REQUIRED:
                    golden_power += 1
                    items_to_remove.append(item)

            elif item.kind == "heart":
                if player_health < MAX_HEALTH:
                    player_health += 1
                    pickup_sound.play()
                    items_to_remove.append(item)

    for item in items_to_remove:
        items.remove(item)

    bullets = [b for b in bullets if 0 <= b.x <= GAME_WIDTH and 0 <= b.y <= GAME_HEIGHT]

    max_chickens = min(BASE_MAX_CHICKENS + score // 5, MAX_CHICKENS_CAP)

    if len(chickens) < max_chickens:
        chicken_spawn_timer -= dt
        if chicken_spawn_timer <= 0:
            chickens.append(spawn_entity_outside(chicken_frames_right, chicken_frames_left, "chicken"))
            chicken_spawn_timer = CHICKEN_SPAWN_INTERVAL 
    else:
        chicken_spawn_timer = CHICKEN_SPAWN_INTERVAL 

    # Update items on ground
    for item in items:
        item.update(dt)
    items = [item for item in items if not item.is_gone()]

    # --- DRAW ---
    game_surface.fill((32, 32, 40))

    player.draw(game_surface, invincibility_timer > 0, player.firing)

    if player.charging:
        base_frame = charge_anim_frames[player.charge_anim_frame]

        charge_stage = player.charge_stage  # 0, 1, or 2
        charge_color = CHARGE_FIREBALL_COLORS[charge_stage]

        col_frame = colorize_frame(base_frame, charge_color)

        fx = int(player.x + FRAME_WIDTH * SCALE // 2 - col_frame.get_width() // 2)
        fy = int(player.y + FRAME_HEIGHT * SCALE // 2 - col_frame.get_height() // 2)
        game_surface.blit(col_frame, (fx, fy))

    if False:
        pcx, pcy, pr = player.get_circle()
        pygame.draw.circle(game_surface, (0,255,255), (int(pcx), int(pcy)), int(pr), 1)

    for chicken in chickens:
        chicken.draw(game_surface)

    for goose in geese:
        goose.draw(game_surface)
        if getattr(goose, 'is_winding_up', False):
            line_length = int(GOOSE_CHARGE_SPEED * GOOSE_CHARGE_DURATION)
            gx = int(goose.x + goose_frames_right[0].get_width() // 2)
            gy = int(goose.y + goose_frames_right[0].get_height() // 2)
            tx = int(gx + goose.charge_dx * line_length)
            ty = int(gy + goose.charge_dy * line_length)
            pygame.draw.line(game_surface, (255, 32, 32), (gx, gy), (tx, ty), 3)

    for crab in crabs:
        crab.draw(game_surface)
        if getattr(crab, 'is_winding_up', False):
            line_length = int(CRAB_CHARGE_SPEED * CRAB_CHARGE_DURATION)
            cx = int(crab.x + crab_frames_right[0].get_width() // 2)
            cy = int(crab.y + crab_frames_right[0].get_height() // 2)
            tx = int(cx + crab.charge_dx * line_length)
            ty = int(cy + crab.charge_dy * line_length)
            pygame.draw.line(game_surface, (32, 255, 200), (cx, cy), (tx, ty), 3)

    for bullet in bullets:
        bullet.draw(game_surface)
    for orb in piercing_orbs:
        orb.draw(game_surface)
    for explosion in explosions:
        explosion.draw(game_surface)
    for exp in orb_explosions:
        exp.draw(game_surface)

    if debug_explosion_circle:
        pass
        cx, cy, rad, timer = debug_explosion_circle
        pygame.draw.circle(game_surface, (255,255,0), (int(cx), int(cy)), int(rad), 2)

    for item in items:
        item.draw(game_surface)

    if goose_warning_timer > 0:
        warning = font.render("GOOSE!", False, (255, 255, 0))
        game_surface.blit(warning, (GAME_WIDTH//2 - warning.get_width()//2, 110))

    if crab_warning_timer > 0:
        warning = font.render("CRAB!", False, (255, 255, 0))
        game_surface.blit(warning, (GAME_WIDTH//2 - warning.get_width()//2, 110))

    panel_rect = pygame.Rect(0, GAME_HEIGHT - PANEL_HEIGHT, GAME_WIDTH, PANEL_HEIGHT)
    pygame.draw.rect(game_surface, (48,48,64), panel_rect)

    base_y = GAME_HEIGHT - PANEL_HEIGHT

    score_text = font.render(f"Score: {score}", False, (255, 255, 255))
    highscore_text = font.render(f"High Score: {highscore}", False, (255, 255, 100))
    game_surface.blit(score_text, (2, base_y + 2))
    game_surface.blit(highscore_text, (2, base_y + 16))  # Just below the score

    egg_text = font.render(f"Eggs: {egg_inventory} / {MAX_EGG_INVENTORY}", False, (255,255,0))
    game_surface.blit(egg_text, (2, base_y + 30))   # 18px down from previous, tweak as needed

    difficulty_text = font.render(f"Difficulty: {score // 5}", False, (180,180,255))
    game_surface.blit(difficulty_text, (2, base_y + 44))  # another ~18px down

    for i in range(MAX_HEALTH):
        x = 200 + i * (heart_full.get_width() + 4)
        y = base_y + 10  
        if i < player_health:
            game_surface.blit(heart_full, (x, y))
        else:
            game_surface.blit(heart_empty, (x, y))

    battery_x = GAME_WIDTH - 96  
    battery_y = GAME_HEIGHT - PANEL_HEIGHT + 8

    if golden_power == GOLDEN_POWER_REQUIRED:
        charge_anim_timer += dt
        if charge_anim_timer >= 0.15:
            charge_anim_timer -= 0.15
            charge_anim_idx = (charge_anim_idx + 1) % len(charge_full_anim)
        frame = charge_full_anim[charge_anim_idx]
    else:
        frame = charge_frames[golden_power]
        charge_anim_idx = 0
        charge_anim_timer = 0
    game_surface.blit(frame, (battery_x, battery_y))

    scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
    screen.blit(scaled_surface, (0, 0))
    pygame.display.flip()