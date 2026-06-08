import pygame
import math
import random

pygame.init()

WIDTH = 800
HEIGHT = 600
FPS = 60
MAX_WAVE = 50

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robo Style Tower Defense - Progress Demo")
clock = pygame.time.Clock()

money = 100
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

selected_tower_type = None
towers = []
enemies = []

font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 48)

path = [
    (0, 300), (200, 300), (200, 100), (400, 100),
    (400, 500), (600, 500), (600, 300), (800, 300)
]

tower_types = {
    "basic": {"name": "Basic", "cost": 50, "range": 120, "damage": 20, "cooldown": 40, "color": (0, 0, 255)},
    "sniper": {"name": "Sniper", "cost": 80, "range": 220, "damage": 45, "cooldown": 75, "color": (120, 0, 255)},
    "rapid": {"name": "Rapid", "cost": 65, "range": 100, "damage": 8, "cooldown": 12, "color": (0, 200, 255)},
    "cannon": {"name": "Cannon", "cost": 100, "range": 140, "damage": 80, "cooldown": 95, "color": (80, 80, 80)}
}


class Enemy:
    def __init__(self, enemy_type, wave_number):
        self.enemy_type = enemy_type
        self.x = path[0][0]
        self.y = path[0][1]
        self.path_index = 1
        self.width = 28
        self.height = 28

        hp_multiplier = 1 + (wave_number * 0.15)

        if enemy_type == "normal":
            self.max_hp = int(100 * hp_multiplier)
            self.speed = 2
            self.reward = 10
            self.color = (255, 0, 0)
        elif enemy_type == "fast":
            self.max_hp = int(65 * hp_multiplier)
            self.speed = 3.2
            self.reward = 8
            self.color = (255, 180, 0)
        elif enemy_type == "tank":
            self.max_hp = int(250 * hp_multiplier)
            self.speed = 1.2
            self.reward = 20
            self.color = (120, 255, 120)
        elif enemy_type == "boss":
            self.max_hp = 1000 + (wave_number * 300)
            self.speed = 0.9
            self.reward = 75
            self.color = (170, 0, 0)
            self.width = 42
            self.height = 42

        self.hp = self.max_hp

    def move(self):
        target_x, target_y = path[self.path_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= self.speed:
            self.x = target_x
            self.y = target_y
            self.path_index += 1
            return self.path_index >= len(path)

        self.x += self.speed * dx / distance
        self.y += self.speed * dy / distance
        return False

    def take_damage(self, damage):
        self.hp -= damage

    def is_dead(self):
        return self.hp <= 0

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (255, 0, 0), (self.x, self.y - 10, self.width, 5))
        pygame.draw.rect(screen, (0, 255, 0), (self.x, self.y - 10, self.width * max(self.hp, 0) / self.max_hp, 5))


class Tower:
    def __init__(self, x, y, tower_type):
        stats = tower_types[tower_type]
        self.x = x
        self.y = y
        self.tower_type = tower_type
        self.name = stats["name"]
        self.range = stats["range"]
        self.damage = stats["damage"]
        self.cooldown_max = stats["cooldown"]
        self.cooldown = 0
        self.color = stats["color"]

    def update(self, enemy_list):
        if self.cooldown > 0:
            self.cooldown -= 1

        enemies_in_range = []
        for enemy in enemy_list:
            if math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.range:
                enemies_in_range.append(enemy)

        if not enemies_in_range:
            return None

        target = max(enemies_in_range, key=lambda e: e.path_index)

        if self.cooldown <= 0:
            target.take_damage(self.damage)
            self.cooldown = self.cooldown_max

            if self.tower_type == "cannon":
                for enemy in enemy_list:
                    if enemy != target and math.hypot(enemy.x - target.x, enemy.y - target.y) <= 55:
                        enemy.take_damage(self.damage * 0.4)

        return target

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 18)
        pygame.draw.circle(screen, (90, 90, 90), (int(self.x), int(self.y)), self.range, 1)


def get_wave_enemies(wave_number):
    if wave_number <= 5:
        normal_count = 3 + wave_number * 2
    elif wave_number <= 15:
        normal_count = 12 + wave_number * 2
    elif wave_number <= 30:
        normal_count = 25 + wave_number * 2
    else:
        normal_count = 45 + wave_number * 2

    fast_count = wave_number // 2 if wave_number >= 4 else 0
    tank_count = wave_number // 3 if wave_number >= 8 else 0
    boss_count = 1 if wave_number % 5 == 0 else 0

    if wave_number == MAX_WAVE:
        normal_count = 120
        fast_count = 80
        tank_count = 50
        boss_count = 1

    enemy_list = ["normal"] * normal_count + ["fast"] * fast_count + ["tank"] * tank_count + ["boss"] * boss_count
    random.shuffle(enemy_list)
    return enemy_list


def get_spawn_delay(wave_number):
    return max(12, 50 - wave_number)


def is_on_path(x, y):
    path_buffer = 35
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]

        if x1 == x2 and abs(x - x1) <= path_buffer and min(y1, y2) <= y <= max(y1, y2):
            return True

        if y1 == y2 and abs(y - y1) <= path_buffer and min(x1, x2) <= x <= max(x1, x2):
            return True

    return False


def is_on_hud(x, y):
    return y >= 520 or y <= 70


def can_place_tower(x, y):
    if is_on_path(x, y) or is_on_hud(x, y):
        return False

    for tower in towers:
        if math.hypot(tower.x - x, tower.y - y) < 45:
            return False

    return True


def reset_game():
    global money, score, lives, wave, wave_active, game_won, game_over
    global spawn_timer, spawn_delay, spawn_index, current_wave_enemies
    global selected_tower_type, towers, enemies, game_speed, game_paused

    money = 100
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
    towers = []
    enemies = []


def start_next_wave():
    global wave, wave_active, current_wave_enemies, spawn_index, spawn_timer, spawn_delay

    if wave_active or wave >= MAX_WAVE:
        return

    wave += 1
    wave_active = True
    current_wave_enemies = get_wave_enemies(wave)
    spawn_index = 0
    spawn_timer = 0
    spawn_delay = get_spawn_delay(wave)


def draw_path():
    for i in range(len(path) - 1):
        pygame.draw.line(screen, (100, 100, 100), path[i], path[i + 1], 24)


def draw_hud():
    pygame.draw.rect(screen, (25, 25, 25), (0, 0, WIDTH, 70))
    pygame.draw.rect(screen, (25, 25, 25), (0, 520, WIDTH, 80))

    screen.blit(font.render(f"Money: ${money}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 35))
    screen.blit(font.render(f"Wave: {wave}/{MAX_WAVE}", True, (255, 255, 255)), (160, 10))
    screen.blit(font.render(f"Lives: {lives}", True, (255, 80, 80)), (160, 35))
    screen.blit(font.render(f"Speed: {game_speed}x", True, (255, 255, 255)), (270, 10))

    screen.blit(font.render("1 Basic $50", True, (255, 255, 255)), (20, 540))
    screen.blit(font.render("2 Sniper $80", True, (255, 255, 255)), (175, 540))
    screen.blit(font.render("3 Rapid $65", True, (255, 255, 255)), (345, 540))
    screen.blit(font.render("4 Cannon $100", True, (255, 255, 255)), (510, 540))
    screen.blit(font.render("SPACE Wave | F Speed | P Pause | R Restart", True, (255, 255, 0)), (20, 570))

    if selected_tower_type:
        stats = tower_types[selected_tower_type]
        text = f"Selected: {stats['name']}  Damage:{stats['damage']}  Range:{stats['range']}"
        screen.blit(font.render(text, True, (0, 255, 0)), (370, 15))
    else:
        screen.blit(font.render("Press 1-4 then click grass to place tower", True, (255, 255, 0)), (370, 15))

    if wave_active:
        remaining = len(current_wave_enemies) - spawn_index + len(enemies)
        screen.blit(font.render(f"Enemies left: {remaining}", True, (255, 255, 255)), (370, 40))


def draw_tower_preview():
    if selected_tower_type is None:
        return

    mouse_x, mouse_y = pygame.mouse.get_pos()
    stats = tower_types[selected_tower_type]
    preview_color = (0, 255, 0) if can_place_tower(mouse_x, mouse_y) and money >= stats["cost"] else (255, 0, 0)
    pygame.draw.circle(screen, preview_color, (mouse_x, mouse_y), 18, 2)
    pygame.draw.circle(screen, preview_color, (mouse_x, mouse_y), stats["range"], 1)


def draw_start_screen():
    screen.fill((35, 100, 35))
    draw_path()
    screen.blit(big_font.render("ROBO STYLE TOWER DEFENSE", True, (255, 255, 255)), (125, 110))

    lines = [
        "Progress Demo",
        "",
        "Goal: survive to Wave 50.",
        "Start cash: $100.",
        "",
        "Controls:",
        "1 Basic | 2 Sniper | 3 Rapid | 4 Cannon",
        "Click grass to place towers. You cannot place towers on the road.",
        "SPACE starts next wave. F changes speed. P pauses. R restarts.",
        "",
        "Press ENTER to start."
    ]

    y = 180
    for line in lines:
        color = (255, 255, 0) if line == "Press ENTER to start." else (255, 255, 255)
        screen.blit(font.render(line, True, color), (80, y))
        y += 30


def draw_end_message():
    if game_won:
        screen.blit(big_font.render("YOU BEAT WAVE 50!", True, (255, 255, 0)), (235, 250))
        screen.blit(font.render("Press R to restart or ESC to quit", True, (255, 255, 255)), (250, 305))

    if game_over:
        screen.blit(big_font.render("GAME OVER", True, (255, 0, 0)), (300, 250))
        screen.blit(font.render("Press R to restart or ESC to quit", True, (255, 255, 255)), (250, 305))


running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
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
                    selected_tower_type = "basic"
                if event.key == pygame.K_2:
                    selected_tower_type = "sniper"
                if event.key == pygame.K_3:
                    selected_tower_type = "rapid"
                if event.key == pygame.K_4:
                    selected_tower_type = "cannon"
                if event.key == pygame.K_SPACE:
                    start_next_wave()
                if event.key == pygame.K_p:
                    game_paused = not game_paused
                if event.key == pygame.K_f:
                    game_speed = 2 if game_speed == 1 else 4 if game_speed == 2 else 1

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_started and not game_paused and not game_over and not game_won:
                if selected_tower_type is not None:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    stats = tower_types[selected_tower_type]

                    if can_place_tower(mouse_x, mouse_y) and money >= stats["cost"]:
                        towers.append(Tower(mouse_x, mouse_y, selected_tower_type))
                        money -= stats["cost"]

    if not game_started:
        draw_start_screen()
        pygame.display.update()
        continue

    if not game_paused and not game_over and not game_won:
        for _ in range(game_speed):
            if wave_active:
                spawn_timer += 1

                if spawn_index < len(current_wave_enemies) and spawn_timer >= spawn_delay:
                    enemies.append(Enemy(current_wave_enemies[spawn_index], wave))
                    spawn_index += 1
                    spawn_timer = 0

                if spawn_index >= len(current_wave_enemies) and len(enemies) == 0:
                    wave_active = False
                    money += 25 + wave * 2

                    if wave >= MAX_WAVE:
                        game_won = True

            for tower in towers:
                tower.update(enemies)

            for enemy in enemies[:]:
                reached_end = enemy.move()

                if reached_end:
                    enemies.remove(enemy)
                    lives -= 1
                    continue

                if enemy.is_dead():
                    money += enemy.reward
                    score += enemy.reward
                    enemies.remove(enemy)
                    continue

            if lives <= 0:
                game_over = True

    screen.fill((40, 120, 40))

    for _ in range(25):
        gx = random.randint(0, WIDTH)
        gy = random.randint(72, 518)
        pygame.draw.circle(screen, (35, 100, 35), (gx, gy), 1)

    draw_path()

    for tower in towers:
        target = None
        for enemy in enemies:
            if math.hypot(enemy.x - tower.x, enemy.y - tower.y) <= tower.range:
                target = enemy
                break

        tower.draw()

        if target and not game_paused and not game_over and not game_won:
            pygame.draw.line(screen, (255, 255, 0), (int(tower.x), int(tower.y)), (int(target.x), int(target.y)), 2)

    for enemy in enemies:
        enemy.draw()

    draw_tower_preview()
    draw_hud()

    if game_paused:
        screen.blit(big_font.render("PAUSED", True, (255, 255, 0)), (330, 260))

    draw_end_message()
    pygame.display.update()

pygame.quit()
