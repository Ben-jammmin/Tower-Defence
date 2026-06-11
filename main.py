import math
import random

import pygame

pygame.init()

# These constants control the game window and the main rules.
# Changing WIDTH/HEIGHT changes the size of the playable screen.
WIDTH = 1000
HEIGHT = 720
FPS = 60
MAX_WAVE = 50
HUD_TOP = 86
HUD_BOTTOM = 610
MAX_TOWER_LEVEL = 3

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robo Style Tower Defense")
clock = pygame.time.Clock()

# Fonts are created once, then reused whenever text is drawn.
font = pygame.font.SysFont(None, 28)
small_font = pygame.font.SysFont(None, 22)
tiny_font = pygame.font.SysFont(None, 18)
big_font = pygame.font.SysFont(None, 48)

# Game state variables store the player's current progress.
money = 150
score = 0
lives = 20
wave = 0
wave_active = False
game_started = False
game_paused = False
game_won = False
game_over = False
game_speed = 1

spawn_timer = 0
spawn_delay = 45
spawn_index = 0
current_wave_enemies = []

# These lists hold all objects currently active in the game.
# The update loop changes them, and the draw loop displays them.
selected_tower_type = None
selected_tower = None
towers = []
enemies = []
projectiles = []
effects = []
floating_texts = []
message_text = ""
message_timer = 0

path = [
    (0, 360), (240, 360), (240, 130), (510, 130),
    (510, 580), (760, 580), (760, 360), (1000, 360)
]

# This pre-calculates how far along the path each corner is.
# Towers use it to target enemies that are closest to escaping.
segment_start_distances = [0]
for index in range(len(path) - 1):
    start_x, start_y = path[index]
    end_x, end_y = path[index + 1]
    segment_length = math.hypot(end_x - start_x, end_y - start_y)
    segment_start_distances.append(segment_start_distances[-1] + segment_length)

decor_rng = random.Random(7)
# Speckles are generated once so the grass does not flicker every frame.
grass_speckles = [
    (decor_rng.randint(0, WIDTH), decor_rng.randint(HUD_TOP + 6, HUD_BOTTOM - 8))
    for _ in range(230)
]

# Tower stats live in this dictionary so balancing is easy:
# change cost, damage, range, or cooldown here to tune the game.
tower_types = {
    "basic": {
        "name": "Basic",
        "cost": 50,
        "range": 120,
        "damage": 20,
        "cooldown": 38,
        "color": (44, 109, 255),
        "projectile_speed": 10,
        "description": "Balanced"
    },
    "sniper": {
        "name": "Sniper",
        "cost": 85,
        "range": 230,
        "damage": 52,
        "cooldown": 72,
        "color": (138, 70, 255),
        "projectile_speed": 17,
        "description": "Long range"
    },
    "rapid": {
        "name": "Rapid",
        "cost": 65,
        "range": 105,
        "damage": 8,
        "cooldown": 10,
        "color": (0, 205, 255),
        "projectile_speed": 12,
        "description": "Fast fire"
    },
    "cannon": {
        "name": "Cannon",
        "cost": 105,
        "range": 145,
        "damage": 72,
        "cooldown": 88,
        "color": (96, 101, 108),
        "projectile_speed": 8,
        "splash_radius": 62,
        "description": "Splash"
    },
    "frost": {
        "name": "Frost",
        "cost": 75,
        "range": 115,
        "damage": 6,
        "cooldown": 28,
        "color": (92, 224, 255),
        "projectile_speed": 11,
        "slow_percent": 0.42,
        "slow_duration": 85,
        "description": "Slows"
    }
}

tower_order = ["basic", "sniper", "rapid", "cannon", "frost"]

# Names used by the HUD when it summarizes incoming waves.
enemy_names = {
    "normal": "Normal",
    "swarm": "Swarm",
    "fast": "Fast",
    "armored": "Armored",
    "tank": "Tank",
    "regenerator": "Regen",
    "shielded": "Shielded",
    "boss": "Boss"
}

shop_buttons = {
    tower_type: pygame.Rect(14 + index * 164, HUD_BOTTOM + 16, 154, 76)
    for index, tower_type in enumerate(tower_order)
}

action_buttons = {
    "wave": pygame.Rect(WIDTH - 310, 18, 96, 46),
    "speed": pygame.Rect(WIDTH - 204, 18, 76, 46),
    "pause": pygame.Rect(WIDTH - 118, 18, 104, 46),
}

selected_panel_rect = pygame.Rect(WIDTH - 276, HUD_TOP + 18, 252, 170)
upgrade_button_rect = pygame.Rect(selected_panel_rect.x + 14, selected_panel_rect.y + 124, 106, 34)
sell_button_rect = pygame.Rect(selected_panel_rect.x + 132, selected_panel_rect.y + 124, 106, 34)


def blend(color, target, amount):
    """Return a color between two colors."""
    return tuple(int(color[i] + (target[i] - color[i]) * amount) for i in range(3))


def draw_text_center(text, text_font, color, rect):
    """Draw text centered inside a rectangle."""
    rendered = text_font.render(text, True, color)
    text_rect = rendered.get_rect(center=rect.center)
    screen.blit(rendered, text_rect)


def set_message(text, timer=120):
    """Show a short message near the top of the play area."""
    global message_text, message_timer
    message_text = text
    message_timer = timer


class Enemy:
    """A moving enemy with health, speed, rewards, and special traits."""

    def __init__(self, enemy_type, wave_number):
        """Create an enemy and choose its stats based on type and wave."""
        self.enemy_type = enemy_type
        self.x = path[0][0]
        self.y = path[0][1]
        self.path_index = 1
        self.width = 28
        self.height = 28
        self.slow_timer = 0
        self.slow_factor = 1
        self.armor = 0
        self.regen = 0
        self.shield = 0
        self.max_shield = 0

        hp_multiplier = 1 + (wave_number * 0.12)

        # Each enemy type gets different stats, which makes waves feel different.
        if enemy_type == "normal":
            self.max_hp = int(95 * hp_multiplier)
            self.speed = 1.85
            self.reward = 10
            self.base_damage = 1
            self.color = (235, 63, 63)
        elif enemy_type == "swarm":
            self.max_hp = int(34 * hp_multiplier)
            self.speed = 3.7
            self.reward = 4
            self.base_damage = 1
            self.color = (255, 226, 86)
            self.width = 18
            self.height = 18
        elif enemy_type == "fast":
            self.max_hp = int(62 * hp_multiplier)
            self.speed = 3.15
            self.reward = 8
            self.base_damage = 1
            self.color = (255, 176, 48)
        elif enemy_type == "armored":
            self.max_hp = int(170 * hp_multiplier)
            self.speed = 1.45
            self.reward = 24
            self.base_damage = 2
            self.color = (118, 146, 168)
            self.armor = 7 + wave_number // 7
            self.width = 34
            self.height = 34
        elif enemy_type == "tank":
            self.max_hp = int(235 * hp_multiplier)
            self.speed = 1.15
            self.reward = 22
            self.base_damage = 2
            self.color = (117, 220, 112)
            self.width = 32
            self.height = 32
        elif enemy_type == "regenerator":
            self.max_hp = int(135 * hp_multiplier)
            self.speed = 1.62
            self.reward = 18
            self.base_damage = 1
            self.color = (196, 84, 220)
            self.regen = 0.08 + wave_number * 0.006
        elif enemy_type == "shielded":
            self.max_hp = int(125 * hp_multiplier)
            self.speed = 1.7
            self.reward = 21
            self.base_damage = 2
            self.color = (62, 126, 230)
            self.max_shield = int(82 * hp_multiplier)
            self.shield = self.max_shield
            self.width = 32
            self.height = 32
        elif enemy_type == "boss":
            self.max_hp = 850 + (wave_number * 275)
            self.speed = 0.82
            self.reward = 85
            self.base_damage = 5
            self.color = (158, 32, 45)
            self.width = 44
            self.height = 44

        self.hp = self.max_hp

    def move(self):
        """Move toward the next path point. Return True if it reaches the end."""
        if self.regen > 0 and self.hp > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen)

        speed = self.speed
        if self.slow_timer > 0:
            speed *= self.slow_factor
            self.slow_timer -= 1
        else:
            self.slow_factor = 1

        target_x, target_y = path[self.path_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= speed:
            self.x = target_x
            self.y = target_y
            self.path_index += 1
            return self.path_index >= len(path)

        self.x += speed * dx / distance
        self.y += speed * dy / distance
        return False

    def take_damage(self, damage):
        """Apply damage, letting armor and shields reduce it first."""
        damage = max(1, damage - self.armor)

        if self.shield > 0:
            shield_damage = min(self.shield, damage)
            self.shield -= shield_damage
            damage -= shield_damage

        if damage > 0:
            self.hp -= damage

    def apply_slow(self, percent, duration):
        """Temporarily reduce enemy speed."""
        factor = max(0.15, 1 - percent)
        if factor < self.slow_factor or self.slow_timer <= 0:
            self.slow_factor = factor
        self.slow_timer = max(self.slow_timer, duration)

    def is_dead(self):
        """Return True when the enemy has no health left."""
        return self.hp <= 0

    def progress(self):
        """Return how far this enemy has traveled along the path."""
        segment_index = max(0, self.path_index - 1)
        start_x, start_y = path[segment_index]
        return segment_start_distances[segment_index] + math.hypot(self.x - start_x, self.y - start_y)

    def draw(self):
        """Draw the enemy, health bar, and any special status indicators."""
        left = int(self.x - self.width / 2)
        top = int(self.y - self.height / 2)
        body_rect = pygame.Rect(left, top, self.width, self.height)
        body_color = self.color

        pygame.draw.rect(screen, (25, 34, 28), body_rect.move(2, 2), border_radius=6)
        pygame.draw.rect(screen, body_color, body_rect, border_radius=6)
        pygame.draw.rect(screen, blend(body_color, (255, 255, 255), 0.28), body_rect, 2, border_radius=6)

        if self.slow_timer > 0:
            pygame.draw.circle(screen, (92, 224, 255), (int(self.x), int(self.y)), self.width // 2 + 5, 2)

        if self.shield > 0:
            pygame.draw.circle(screen, (102, 205, 255), (int(self.x), int(self.y)), self.width // 2 + 9, 2)

        if self.armor > 0:
            plate_rect = pygame.Rect(left + 5, top + 5, self.width - 10, 5)
            pygame.draw.rect(screen, (216, 224, 228), plate_rect, border_radius=2)

        if self.regen > 0:
            pygame.draw.circle(screen, (255, 166, 250), (left + self.width - 5, top + 5), 4)

        bar_width = self.width + 8
        bar_x = int(self.x - bar_width / 2)
        bar_y = top - 12
        health_width = int(bar_width * max(self.hp, 0) / self.max_hp)
        pygame.draw.rect(screen, (90, 21, 21), (bar_x, bar_y, bar_width, 5), border_radius=2)
        pygame.draw.rect(screen, (88, 235, 92), (bar_x, bar_y, health_width, 5), border_radius=2)

        if self.max_shield > 0:
            shield_width = int(bar_width * max(self.shield, 0) / self.max_shield)
            pygame.draw.rect(screen, (20, 45, 78), (bar_x, bar_y - 6, bar_width, 4), border_radius=2)
            pygame.draw.rect(screen, (102, 205, 255), (bar_x, bar_y - 6, shield_width, 4), border_radius=2)


class Tower:
    """A tower placed by the player that finds enemies and fires projectiles."""

    def __init__(self, x, y, tower_type):
        """Create a tower at a position using stats from tower_types."""
        self.x = x
        self.y = y
        self.tower_type = tower_type
        self.name = tower_types[tower_type]["name"]
        self.level = 1
        self.cooldown = 0
        self.target = None
        self.total_spent = tower_types[tower_type]["cost"]
        self.refresh_stats()

    def refresh_stats(self):
        """Recalculate tower stats after it is created or upgraded."""
        stats = tower_types[self.tower_type]
        level_bonus = self.level - 1
        self.range = stats["range"] + level_bonus * 14
        self.damage = int(stats["damage"] * (1 + level_bonus * 0.45))
        self.cooldown_max = max(6, int(stats["cooldown"] * (1 - level_bonus * 0.14)))
        self.projectile_speed = stats["projectile_speed"] + level_bonus * 1.5
        self.color = stats["color"]
        self.splash_radius = stats.get("splash_radius", 0) + level_bonus * 9 if stats.get("splash_radius") else 0
        self.slow_percent = stats.get("slow_percent", 0) + level_bonus * 0.05
        self.slow_duration = stats.get("slow_duration", 0) + level_bonus * 14

    def upgrade_cost(self):
        """Return the cost of the next upgrade, or None at max level."""
        if self.level >= MAX_TOWER_LEVEL:
            return None
        base_cost = tower_types[self.tower_type]["cost"]
        return int(base_cost * (0.7 + self.level * 0.45))

    def upgrade(self, cost):
        """Increase tower level and record how much was spent on it."""
        self.level += 1
        self.total_spent += cost
        self.refresh_stats()

    def sell_value(self):
        """Return how much money the player gets for selling this tower."""
        return int(self.total_spent * 0.65)

    def find_target(self, enemy_list):
        """Pick the in-range enemy that is farthest along the path."""
        enemies_in_range = [
            enemy for enemy in enemy_list
            if not enemy.is_dead() and math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.range
        ]

        if not enemies_in_range:
            return None

        return max(enemies_in_range, key=lambda enemy: enemy.progress())

    def update(self, enemy_list):
        """Count down cooldown and create a projectile when ready to shoot."""
        if self.cooldown > 0:
            self.cooldown -= 1

        self.target = self.find_target(enemy_list)
        if self.target is None or self.cooldown > 0:
            return None

        self.cooldown = self.cooldown_max
        return Projectile(self, self.target)

    def draw(self):
        """Draw the tower, its barrel, level markers, and range if selected."""
        is_selected = self is selected_tower
        if is_selected:
            pygame.draw.circle(screen, (255, 238, 116), (int(self.x), int(self.y)), self.range, 2)
            pygame.draw.circle(screen, (255, 238, 116), (int(self.x), int(self.y)), 24, 2)

        pygame.draw.circle(screen, (20, 28, 30), (int(self.x) + 2, int(self.y) + 2), 22)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 20)
        pygame.draw.circle(screen, blend(self.color, (255, 255, 255), 0.33), (int(self.x), int(self.y)), 20, 2)

        if self.target is not None:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.hypot(dx, dy)
            if distance > 0:
                end_x = self.x + dx / distance * 25
                end_y = self.y + dy / distance * 25
                pygame.draw.line(screen, (28, 28, 28), (self.x, self.y), (end_x, end_y), 6)
                pygame.draw.line(screen, (240, 240, 240), (self.x, self.y), (end_x, end_y), 2)

        for marker in range(self.level):
            marker_x = int(self.x - 9 + marker * 9)
            pygame.draw.circle(screen, (255, 223, 89), (marker_x, int(self.y) + 26), 3)


class Projectile:
    """A shot fired by a tower that travels toward one enemy."""

    def __init__(self, tower, target):
        """Copy the tower's attack stats into a new projectile."""
        self.x = tower.x
        self.y = tower.y
        self.target = target
        self.damage = tower.damage
        self.speed = tower.projectile_speed
        self.color = blend(tower.color, (255, 255, 255), 0.18)
        self.radius = 5 if tower.tower_type != "cannon" else 7
        self.splash_radius = tower.splash_radius
        self.slow_percent = tower.slow_percent
        self.slow_duration = tower.slow_duration
        self.impact_radius = 18 if self.splash_radius == 0 else self.splash_radius
        self.impact_color = tower.color

    def update(self, enemy_list):
        """Move toward the target. Return True when the projectile is finished."""
        if self.target not in enemy_list or self.target.is_dead():
            return True

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.hypot(dx, dy)

        if distance <= self.speed:
            self.x = self.target.x
            self.y = self.target.y
            self.hit(enemy_list)
            return True

        self.x += self.speed * dx / distance
        self.y += self.speed * dy / distance
        return False

    def hit(self, enemy_list):
        """Damage the target and apply splash or slow effects."""
        self.target.take_damage(self.damage)
        if self.slow_percent:
            self.target.apply_slow(self.slow_percent, self.slow_duration)

        if self.splash_radius:
            for enemy in enemy_list:
                if enemy is self.target or enemy.is_dead():
                    continue
                distance = math.hypot(enemy.x - self.target.x, enemy.y - self.target.y)
                if distance <= self.splash_radius:
                    enemy.take_damage(int(self.damage * 0.45))

    def draw(self):
        """Draw the projectile as a small moving circle."""
        pygame.draw.circle(screen, (20, 24, 27), (int(self.x) + 1, int(self.y) + 1), self.radius)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


class ImpactEffect:
    """A short ring animation used for hits, upgrades, and selling."""

    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.life = 18
        self.max_life = self.life

    def update(self):
        """Shrink the remaining lifetime. Return True when done."""
        self.life -= 1
        return self.life <= 0

    def draw(self):
        """Draw the expanding ring."""
        age = 1 - self.life / self.max_life
        radius = int(8 + self.radius * age)
        color = blend(self.color, (255, 255, 255), age * 0.35)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), radius, 2)


class FloatingText:
    """Short text that floats upward, such as money gained or lives lost."""

    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 45

    def update(self):
        """Move upward each frame. Return True when the text should disappear."""
        self.y -= 0.45
        self.life -= 1
        return self.life <= 0

    def draw(self):
        """Draw the floating text."""
        rendered = small_font.render(self.text, True, self.color)
        screen.blit(rendered, (int(self.x), int(self.y)))


def get_wave_enemies(wave_number):
    """Build a shuffled list of enemy types for the next wave."""
    if wave_number <= 5:
        normal_count = 4 + wave_number * 2
    elif wave_number <= 15:
        normal_count = 11 + wave_number * 2
    elif wave_number <= 30:
        normal_count = 22 + wave_number * 2
    else:
        normal_count = 38 + wave_number * 2

    swarm_count = wave_number * 2 if wave_number >= 2 else 0
    fast_count = wave_number // 2 if wave_number >= 4 else 0
    armored_count = wave_number // 3 if wave_number >= 6 else 0
    tank_count = wave_number // 4 if wave_number >= 8 else 0
    regenerator_count = wave_number // 4 if wave_number >= 11 else 0
    shielded_count = wave_number // 5 if wave_number >= 14 else 0
    boss_count = 1 if wave_number % 5 == 0 else 0

    if wave_number == MAX_WAVE:
        normal_count = 90
        swarm_count = 120
        fast_count = 75
        armored_count = 45
        tank_count = 45
        regenerator_count = 35
        shielded_count = 35
        boss_count = 1

    enemy_list = ["normal"] * normal_count + ["swarm"] * swarm_count
    enemy_list += ["fast"] * fast_count + ["armored"] * armored_count
    enemy_list += ["tank"] * tank_count + ["regenerator"] * regenerator_count
    enemy_list += ["shielded"] * shielded_count + ["boss"] * boss_count
    random.shuffle(enemy_list)
    return enemy_list


def get_enemy_counts(enemy_list):
    """Count how many enemies of each type are in a wave list."""
    counts = {}
    for enemy_type in enemy_list:
        counts[enemy_type] = counts.get(enemy_type, 0) + 1
    return counts


def summarize_enemy_list(enemy_list, max_parts=5):
    """Turn a wave list into short HUD text like 'Fast x4, Tank x2'."""
    counts = get_enemy_counts(enemy_list)
    parts = []

    for enemy_type in enemy_names:
        count = counts.get(enemy_type, 0)
        if count:
            parts.append(f"{enemy_names[enemy_type]} x{count}")

    if len(parts) > max_parts:
        visible = parts[:max_parts]
        visible.append(f"+{len(parts) - max_parts} types")
        return ", ".join(visible)

    return ", ".join(parts) if parts else "No enemies"


def get_spawn_delay(wave_number):
    """Make later waves spawn enemies faster."""
    return max(10, int(50 - wave_number * 0.8))


def is_on_path(x, y):
    """Return True if a point is too close to the road."""
    path_buffer = 35
    for index in range(len(path) - 1):
        x1, y1 = path[index]
        x2, y2 = path[index + 1]

        if x1 == x2 and abs(x - x1) <= path_buffer and min(y1, y2) <= y <= max(y1, y2):
            return True

        if y1 == y2 and abs(y - y1) <= path_buffer and min(x1, x2) <= x <= max(x1, x2):
            return True

    return False


def is_on_hud(x, y):
    """Return True if a point is inside the top or bottom HUD."""
    return y >= HUD_BOTTOM or y <= HUD_TOP


def is_on_ui(x, y):
    """Return True if a point is on any user interface panel."""
    if is_on_hud(x, y):
        return True
    return selected_tower is not None and selected_panel_rect.collidepoint(x, y)


def can_place_tower(x, y):
    """Check all placement rules before allowing a tower to be built."""
    if is_on_ui(x, y) or is_on_path(x, y):
        return False

    # Do not allow towers to overlap or sit too close together.
    for tower in towers:
        if math.hypot(tower.x - x, tower.y - y) < 48:
            return False

    return True


def get_tower_at(x, y):
    """Return the tower under the mouse, if there is one."""
    for tower in reversed(towers):
        if math.hypot(tower.x - x, tower.y - y) <= 24:
            return tower
    return None


def reset_game():
    """Put all game state back to the starting values."""
    global money, score, lives, wave, wave_active, game_won, game_over
    global spawn_timer, spawn_delay, spawn_index, current_wave_enemies
    global selected_tower_type, selected_tower, towers, enemies, projectiles
    global effects, floating_texts, game_speed, game_paused

    money = 150
    score = 0
    lives = 20
    wave = 0
    wave_active = False
    game_won = False
    game_over = False
    game_paused = False
    game_speed = 1

    spawn_timer = 0
    spawn_delay = 45
    spawn_index = 0
    current_wave_enemies = []

    selected_tower_type = None
    selected_tower = None
    towers = []
    enemies = []
    projectiles = []
    effects = []
    floating_texts = []
    set_message("Build a few towers, then start Wave 1.", 180)


def start_next_wave():
    """Start spawning the next wave if the current one is finished."""
    global wave, wave_active, current_wave_enemies, spawn_index, spawn_timer, spawn_delay

    if wave_active:
        set_message("Clear the current wave first.")
        return

    if wave >= MAX_WAVE:
        return

    wave += 1
    wave_active = True
    current_wave_enemies = get_wave_enemies(wave)
    spawn_index = 0
    spawn_timer = get_spawn_delay(wave)
    spawn_delay = get_spawn_delay(wave)
    wave_summary = summarize_enemy_list(current_wave_enemies)
    set_message(f"Wave {wave}: {len(current_wave_enemies)} enemies - {wave_summary}", 150)


def select_tower_type(tower_type):
    """Choose which tower type will be built on the next valid click."""
    global selected_tower_type, selected_tower
    selected_tower_type = tower_type
    selected_tower = None
    stats = tower_types[tower_type]
    set_message(f"Building {stats['name']}: ${stats['cost']} ({stats['description']})")


def upgrade_selected_tower():
    """Upgrade the selected tower if the player has enough money."""
    global money

    if selected_tower is None:
        set_message("Click a tower first, then press U to upgrade.")
        return

    cost = selected_tower.upgrade_cost()
    if cost is None:
        set_message(f"{selected_tower.name} is already max level.")
        return

    if money < cost:
        set_message(f"Need ${cost - money} more to upgrade.")
        return

    money -= cost
    selected_tower.upgrade(cost)
    effects.append(ImpactEffect(selected_tower.x, selected_tower.y, 46, (255, 223, 89)))
    set_message(f"Upgraded {selected_tower.name} to Level {selected_tower.level}.")


def sell_selected_tower():
    """Sell the selected tower and refund part of its cost."""
    global money, selected_tower

    if selected_tower is None:
        set_message("Click a tower first, then press S to sell.")
        return

    value = selected_tower.sell_value()
    money += value
    effects.append(ImpactEffect(selected_tower.x, selected_tower.y, 36, (96, 255, 156)))
    towers.remove(selected_tower)
    set_message(f"Sold tower for ${value}.")
    selected_tower = None


def place_selected_tower(x, y):
    """Build the currently selected tower at the clicked position."""
    global money, selected_tower_type, selected_tower

    if selected_tower_type is None:
        return

    stats = tower_types[selected_tower_type]
    if money < stats["cost"]:
        set_message(f"Need ${stats['cost'] - money} more for {stats['name']}.")
        return

    if not can_place_tower(x, y):
        set_message("Build on open grass, away from the road and other towers.")
        return

    tower = Tower(x, y, selected_tower_type)
    towers.append(tower)
    money -= stats["cost"]
    selected_tower = tower
    selected_tower_type = None
    effects.append(ImpactEffect(x, y, 40, stats["color"]))
    set_message(f"Placed {stats['name']}. Click it for upgrades.")


def handle_mouse_click(pos, button):
    """Route mouse clicks to buttons, tower placement, or tower selection."""
    global selected_tower_type, selected_tower, game_paused, game_speed

    x, y = pos

    if button == 3:
        selected_tower_type = None
        selected_tower = None
        set_message("Selection cancelled.")
        return

    if button != 1:
        return

    if action_buttons["wave"].collidepoint(x, y):
        start_next_wave()
        return

    if action_buttons["speed"].collidepoint(x, y):
        game_speed = 2 if game_speed == 1 else 4 if game_speed == 2 else 1
        set_message(f"Game speed set to {game_speed}x.")
        return

    if action_buttons["pause"].collidepoint(x, y):
        game_paused = not game_paused
        set_message("Paused." if game_paused else "Resumed.")
        return

    for tower_type, rect in shop_buttons.items():
        if rect.collidepoint(x, y):
            select_tower_type(tower_type)
            return

    if selected_tower is not None and upgrade_button_rect.collidepoint(x, y):
        upgrade_selected_tower()
        return

    if selected_tower is not None and sell_button_rect.collidepoint(x, y):
        sell_selected_tower()
        return

    if selected_tower_type is not None:
        place_selected_tower(x, y)
        return

    clicked_tower = get_tower_at(x, y)
    selected_tower = clicked_tower
    if clicked_tower is not None:
        set_message(f"Selected {clicked_tower.name} Level {clicked_tower.level}.")


def update_game_tick():
    """Advance the game by one simulation tick."""
    global wave_active, spawn_timer, spawn_index, money, score, lives, game_won, game_over
    global selected_tower

    # Spawn enemies one at a time while a wave is active.
    if wave_active:
        spawn_timer += 1

        if spawn_index < len(current_wave_enemies) and spawn_timer >= spawn_delay:
            enemies.append(Enemy(current_wave_enemies[spawn_index], wave))
            spawn_index += 1
            spawn_timer = 0

    # Give every tower a chance to fire.
    for tower in towers:
        projectile = tower.update(enemies)
        if projectile is not None:
            projectiles.append(projectile)

    # Move projectiles and remove them when they hit or lose their target.
    for projectile in projectiles[:]:
        if projectile.update(enemies):
            effects.append(ImpactEffect(projectile.x, projectile.y, projectile.impact_radius, projectile.impact_color))
            projectiles.remove(projectile)

    # Move enemies, pay rewards for kills, and subtract lives for leaks.
    for enemy in enemies[:]:
        if enemy.is_dead():
            money += enemy.reward
            score += enemy.reward
            floating_texts.append(FloatingText(f"+${enemy.reward}", enemy.x - 12, enemy.y - 26, (255, 234, 110)))
            enemies.remove(enemy)
            continue

        reached_end = enemy.move()
        if reached_end:
            enemies.remove(enemy)
            lives = max(0, lives - enemy.base_damage)
            floating_texts.append(FloatingText(f"-{enemy.base_damage}", WIDTH - 60, enemy.y - 18, (255, 95, 95)))

    # When every enemy is gone, end the wave and pay a clear bonus.
    if wave_active and spawn_index >= len(current_wave_enemies) and len(enemies) == 0:
        wave_active = False
        bonus = 30 + wave * 3
        money += bonus
        score += wave * 5
        projectiles.clear()
        set_message(f"Wave {wave} cleared! Bonus ${bonus}.", 160)

        if wave >= MAX_WAVE:
            game_won = True

    if lives <= 0:
        game_over = True
        selected_tower = None


def update_screen_effects():
    """Update short-lived visual effects that are not part of game balance."""
    global message_timer

    # Iterate over copies because finished effects are removed during the loop.
    for effect in effects[:]:
        if effect.update():
            effects.remove(effect)

    for floating_text in floating_texts[:]:
        if floating_text.update():
            floating_texts.remove(floating_text)

    if message_timer > 0:
        message_timer -= 1


def draw_path():
    """Draw the road that enemies follow."""
    for index in range(len(path) - 1):
        pygame.draw.line(screen, (46, 48, 49), path[index], path[index + 1], 32)
        pygame.draw.line(screen, (106, 103, 91), path[index], path[index + 1], 24)

    for point in path[1:-1]:
        pygame.draw.circle(screen, (106, 103, 91), point, 13)
        pygame.draw.circle(screen, (46, 48, 49), point, 16, 2)


def draw_grass():
    """Draw the background grass and tiny static speckles."""
    screen.fill((45, 118, 54))
    for x, y in grass_speckles:
        color = (38, 101, 47) if (x + y) % 2 == 0 else (54, 135, 65)
        pygame.draw.circle(screen, color, (x, y), 1)


def draw_button(rect, label, sublabel, active=False, enabled=True, swatch_color=None):
    """Draw a reusable button for shop, actions, upgrades, and selling."""
    base_color = (46, 54, 60) if enabled else (37, 40, 43)
    if active:
        base_color = (67, 91, 112)
    pygame.draw.rect(screen, (18, 22, 25), rect.move(2, 2), border_radius=6)
    pygame.draw.rect(screen, base_color, rect, border_radius=6)
    pygame.draw.rect(screen, (255, 238, 116) if active else (88, 101, 108), rect, 2, border_radius=6)

    text_color = (255, 255, 255) if enabled else (145, 145, 145)
    label_render = small_font.render(label, True, text_color)
    sub_render = tiny_font.render(sublabel, True, (211, 218, 220) if enabled else (110, 110, 110))

    if rect.height < 42:
        screen.blit(label_render, label_render.get_rect(center=rect.center))
    else:
        sub_y = rect.y + 36 if rect.height >= 60 else rect.y + 28
        screen.blit(label_render, (rect.x + 8, rect.y + 8))
        screen.blit(sub_render, (rect.x + 8, sub_y))

    if swatch_color is not None:
        pygame.draw.circle(screen, (18, 22, 25), (rect.right - 20, rect.y + 20), 10)
        pygame.draw.circle(screen, swatch_color, (rect.right - 20, rect.y + 20), 8)


def draw_stat_card(x, y, width, label, value, color):
    """Draw one compact stat box in the top HUD."""
    rect = pygame.Rect(x, y, width, 54)
    pygame.draw.rect(screen, (18, 22, 25), rect.move(2, 2), border_radius=6)
    pygame.draw.rect(screen, (35, 42, 48), rect, border_radius=6)
    pygame.draw.rect(screen, (74, 86, 94), rect, 1, border_radius=6)
    screen.blit(tiny_font.render(label, True, (172, 184, 190)), (rect.x + 10, rect.y + 8))
    screen.blit(font.render(value, True, color), (rect.x + 10, rect.y + 25))


def draw_hud():
    """Draw the top stats, bottom shop, action buttons, and messages."""
    pygame.draw.rect(screen, (24, 27, 31), (0, 0, WIDTH, HUD_TOP))
    pygame.draw.rect(screen, (24, 27, 31), (0, HUD_BOTTOM, WIDTH, HEIGHT - HUD_BOTTOM))

    draw_stat_card(14, 16, 112, "MONEY", f"${money}", (255, 255, 255))
    draw_stat_card(136, 16, 104, "LIVES", str(lives), (255, 105, 105))
    draw_stat_card(250, 16, 116, "WAVE", f"{wave}/{MAX_WAVE}", (255, 238, 116))
    draw_stat_card(376, 16, 104, "SCORE", str(score), (226, 235, 240))

    if wave_active:
        remaining = len(current_wave_enemies) - spawn_index + len(enemies)
        status_title = "WAVE ACTIVE"
        status = f"{remaining} left"
        wave_mix = summarize_enemy_list(current_wave_enemies, max_parts=3)
    else:
        status_title = "BUILD PHASE"
        status = "Ready for next wave"
        wave_mix = "Place, upgrade, or sell towers"

    if selected_tower_type:
        stats = tower_types[selected_tower_type]
        selection = f"{stats['name']} selected: click grass to build"
    elif selected_tower:
        selection = f"{selected_tower.name} L{selected_tower.level}: U upgrade, S sell"
    else:
        selection = "Keys 1-5 build | Click towers to upgrade"

    status_rect = pygame.Rect(492, 16, 184, 54)
    pygame.draw.rect(screen, (18, 22, 25), status_rect.move(2, 2), border_radius=6)
    pygame.draw.rect(screen, (35, 42, 48), status_rect, border_radius=6)
    pygame.draw.rect(screen, (74, 86, 94), status_rect, 1, border_radius=6)
    screen.blit(tiny_font.render(status_title, True, (172, 184, 190)), (status_rect.x + 10, status_rect.y + 8))
    screen.blit(small_font.render(status, True, (255, 238, 116)), (status_rect.x + 10, status_rect.y + 26))
    screen.blit(tiny_font.render(wave_mix[:28], True, (219, 228, 232)), (status_rect.x + 10, status_rect.y + 42))

    wave_label = "Wave" if not wave_active else "Busy"
    draw_button(action_buttons["wave"], wave_label, "Space", active=False, enabled=not wave_active)
    draw_button(action_buttons["speed"], f"{game_speed}x", "F", active=game_speed > 1)
    draw_button(action_buttons["pause"], "Pause" if not game_paused else "Resume", "P", active=game_paused)

    for index, tower_type in enumerate(tower_order, start=1):
        stats = tower_types[tower_type]
        rect = shop_buttons[tower_type]
        label = f"{index} {stats['name']} ${stats['cost']}"
        sublabel = f"D{stats['damage']} R{stats['range']} {stats['description']}"
        draw_button(
            rect,
            label,
            sublabel,
            active=selected_tower_type == tower_type,
            enabled=money >= stats["cost"],
            swatch_color=stats["color"]
        )

    help_rect = pygame.Rect(WIDTH - 166, HUD_BOTTOM + 16, 152, 76)
    pygame.draw.rect(screen, (18, 22, 25), help_rect.move(2, 2), border_radius=6)
    pygame.draw.rect(screen, (35, 42, 48), help_rect, border_radius=6)
    pygame.draw.rect(screen, (74, 86, 94), help_rect, 1, border_radius=6)
    screen.blit(tiny_font.render("CURRENT ACTION", True, (172, 184, 190)), (help_rect.x + 10, help_rect.y + 8))
    screen.blit(small_font.render(selection[:18], True, (255, 255, 255)), (help_rect.x + 10, help_rect.y + 28))
    screen.blit(tiny_font.render("R restart | Esc quit", True, (219, 228, 232)), (help_rect.x + 10, help_rect.y + 54))

    if message_timer > 0 and message_text:
        display_message = message_text
        while small_font.size(display_message)[0] > WIDTH - 64 and len(display_message) > 8:
            display_message = display_message[:-4] + "..."

        rendered = small_font.render(display_message, True, (255, 255, 255))
        rect = rendered.get_rect(center=(WIDTH // 2, HUD_TOP + 18))
        bubble = rect.inflate(24, 10)
        pygame.draw.rect(screen, (25, 30, 35), bubble, border_radius=6)
        pygame.draw.rect(screen, (255, 238, 116), bubble, 1, border_radius=6)
        screen.blit(rendered, rect)


def draw_selected_panel():
    """Draw the upgrade/sell panel for the currently selected tower."""
    if selected_tower is None:
        return

    tower = selected_tower
    dps = tower.damage * FPS / tower.cooldown_max
    pygame.draw.rect(screen, (18, 23, 27), selected_panel_rect.move(3, 3), border_radius=7)
    pygame.draw.rect(screen, (32, 39, 45), selected_panel_rect, border_radius=7)
    pygame.draw.rect(screen, (255, 238, 116), selected_panel_rect, 2, border_radius=7)

    title = f"{tower.name} Level {tower.level}"
    screen.blit(font.render(title, True, (255, 255, 255)), (selected_panel_rect.x + 12, selected_panel_rect.y + 10))
    screen.blit(small_font.render(f"Damage: {tower.damage}", True, (218, 226, 230)), (selected_panel_rect.x + 14, selected_panel_rect.y + 44))
    screen.blit(small_font.render(f"Range: {tower.range}", True, (218, 226, 230)), (selected_panel_rect.x + 132, selected_panel_rect.y + 44))
    screen.blit(small_font.render(f"Cooldown: {tower.cooldown_max}", True, (218, 226, 230)), (selected_panel_rect.x + 14, selected_panel_rect.y + 70))
    screen.blit(small_font.render(f"DPS: {dps:.1f}", True, (218, 226, 230)), (selected_panel_rect.x + 132, selected_panel_rect.y + 70))

    note = tower_types[tower.tower_type]["description"]
    screen.blit(tiny_font.render(f"Spent ${tower.total_spent} | {note}", True, (172, 184, 190)), (selected_panel_rect.x + 14, selected_panel_rect.y + 100))

    cost = tower.upgrade_cost()
    upgrade_label = "Max" if cost is None else f"U ${cost}"
    draw_button(upgrade_button_rect, upgrade_label, "Upgrade", active=False, enabled=cost is not None and money >= cost)
    draw_button(sell_button_rect, f"S ${tower.sell_value()}", "Sell", active=False, enabled=True)


def draw_tower_preview():
    """Draw a build preview around the mouse when placing a tower."""
    if selected_tower_type is None:
        return

    mouse_x, mouse_y = pygame.mouse.get_pos()
    stats = tower_types[selected_tower_type]
    can_build = can_place_tower(mouse_x, mouse_y) and money >= stats["cost"]
    preview_color = (96, 255, 156) if can_build else (255, 95, 95)
    pygame.draw.circle(screen, preview_color, (mouse_x, mouse_y), stats["range"], 1)
    pygame.draw.circle(screen, preview_color, (mouse_x, mouse_y), 20, 2)


def draw_start_screen():
    """Draw the title screen before the player presses Enter."""
    draw_grass()
    draw_path()
    title = big_font.render("ROBO STYLE TOWER DEFENSE", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, 118)))

    lines = [
        "Survive to Wave 50 on a bigger battlefield with projectiles, upgrades, splash, and slows.",
        "",
        "1 Basic | 2 Sniper | 3 Rapid | 4 Cannon | 5 Frost",
        "New enemies appear over time: swarms, armor, regeneration, shields, tanks, and bosses.",
        "Click grass to build. Click a tower to upgrade or sell it.",
        "Space starts the next wave. F changes speed. P pauses. R restarts.",
        "",
        "Press ENTER to start."
    ]

    y = 184
    for line in lines:
        color = (255, 238, 116) if line == "Press ENTER to start." else (255, 255, 255)
        rendered = font.render(line, True, color)
        screen.blit(rendered, rendered.get_rect(center=(WIDTH // 2, y)))
        y += 31


def draw_end_message():
    """Draw the win or game-over overlay."""
    if not game_won and not game_over:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 135))
    screen.blit(overlay, (0, 0))

    if game_won:
        headline = "YOU BEAT WAVE 50!"
        color = (255, 238, 116)
    else:
        headline = "GAME OVER"
        color = (255, 95, 95)

    rendered = big_font.render(headline, True, color)
    screen.blit(rendered, rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    detail = font.render("Press R to restart or ESC to quit", True, (255, 255, 255))
    screen.blit(detail, detail.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 12)))


def draw_game():
    """Draw one complete frame of gameplay."""
    draw_grass()
    draw_path()

    # Draw order matters: background first, then towers, shots, enemies, effects, and HUD.
    for tower in towers:
        tower.draw()

    for projectile in projectiles:
        projectile.draw()

    for enemy in enemies:
        enemy.draw()

    for effect in effects:
        effect.draw()

    for floating_text in floating_texts:
        floating_text.draw()

    draw_tower_preview()
    draw_hud()
    draw_selected_panel()

    if game_paused and not game_over and not game_won:
        rendered = big_font.render("PAUSED", True, (255, 238, 116))
        screen.blit(rendered, rendered.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    draw_end_message()


running = True

# This is the main game loop. It repeats until the player quits.
# Each pass handles input, updates the game, draws a frame, and shows it.
while running:
    clock.tick(FPS)

    # Read every keyboard/mouse/window event that happened since last frame.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Starting or restarting resets all state before gameplay begins.
            if not game_started and event.key == pygame.K_RETURN:
                game_started = True
                reset_game()

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_r:
                game_started = True
                reset_game()

            if game_started and not game_over and not game_won:
                if event.key == pygame.K_1:
                    select_tower_type("basic")
                if event.key == pygame.K_2:
                    select_tower_type("sniper")
                if event.key == pygame.K_3:
                    select_tower_type("rapid")
                if event.key == pygame.K_4:
                    select_tower_type("cannon")
                if event.key == pygame.K_5:
                    select_tower_type("frost")
                if event.key == pygame.K_SPACE:
                    start_next_wave()
                if event.key == pygame.K_p:
                    game_paused = not game_paused
                    set_message("Paused." if game_paused else "Resumed.")
                if event.key == pygame.K_f:
                    game_speed = 2 if game_speed == 1 else 4 if game_speed == 2 else 1
                    set_message(f"Game speed set to {game_speed}x.")
                if event.key == pygame.K_u:
                    upgrade_selected_tower()
                if event.key == pygame.K_s:
                    sell_selected_tower()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_started and not game_over and not game_won:
                handle_mouse_click(pygame.mouse.get_pos(), event.button)

    # The start screen has its own drawing path and skips gameplay updates.
    if not game_started:
        draw_start_screen()
        pygame.display.update()
        continue

    # game_speed lets the simulation run multiple ticks during one visible frame.
    if not game_paused and not game_over and not game_won:
        for _ in range(game_speed):
            update_game_tick()

    # Visual effects keep updating even when gameplay is paused.
    update_screen_effects()
    draw_game()
    pygame.display.update()

pygame.quit()
