import pygame

pygame.init()

WIDTH = 800
HEIGHT = 600

# Enemy object stores position, health, and movement
# information for enemies traveling along the path.
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.max_hp = 100
        self.hp = 100
        self.speed = 2
        self.height = 30
        self.width = 30

    def take_damage(self, damage):
        self.hp -= damage

    def is_dead(self):
        return self.hp <= 0
    
    
enemy = Enemy(0, 300)


wave = 1
money = 100
tower_damage = 20
tower_cooldown = 0



screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")

clock = pygame.time.Clock()


running = True


enemy_x=0
enemy_y=300
path = [(0, 300), (200, 300), (200, 100), (400, 100), (400, 500), (600, 500), (600, 300), (800, 300)]
current_point = 1

tower_x = 650
tower_y = 300       
tower_range = 150


while running:

    screen.fill((0, 0, 0))
    font = pygame.font.SysFont(None, 36)

    money_text = font.render(f"Money: ${money}", True, (255, 255, 255))
    screen.blit(money_text, (10, 10))

    wave_text = font.render(f"Wave: {wave}", True, (255, 255, 255))
    screen.blit(wave_text, (10, 50))
    
    


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

  
    for i in range(len(path) - 1):
        pygame.draw.line(screen,
                     (100, 100, 100),
                     path[i],
                     path[i + 1],
                     20)

    
    
    
    enemy_rect = pygame.Rect(
    enemy.x,
    enemy.y,
    enemy.width,
    enemy.height
)
    pygame.draw.rect(screen, (255, 0, 0), enemy_rect)
    pygame.draw.rect(screen, (255, 0, 0),
                 (enemy.x, enemy.y - 10, 30, 5))

    pygame.draw.rect(screen, (0, 255, 0),
                 (enemy.x, enemy.y - 10,
                 30 * (enemy.hp / enemy.max_hp), 5))

    pygame.draw.circle(screen, (0, 0, 255), (tower_x, tower_y), 20)
    pygame.draw.circle(screen, (100, 100, 100), (tower_x, tower_y), tower_range, 1)

    distance_x = enemy.x - tower_x
    distance_y = enemy.y - tower_y
    distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

    if distance < tower_range:
     pygame.draw.line(screen, (255, 255, 0), (tower_x, tower_y), (enemy.x, enemy.y), 3)
     if distance < tower_range:
        pygame.draw.line(screen, (255, 255, 0),
                     (tower_x, tower_y),
                     (enemy.x, enemy.y), 3)
        tower_cooldown += 1
        if tower_cooldown >= 30:
            tower_cooldown = 0
            enemy.take_damage(tower_damage)

    if enemy.is_dead():
        money += 10
        wave += 1

        enemy = Enemy(0, 300)
        enemy_y = 300
        current_point = 1

    

    if enemy.x < path[current_point][0]:
            enemy.x += 2
    elif enemy.x > path[current_point][0]:
            enemy.x -= 2
    elif enemy.y < path[current_point][1]:
            enemy.y += 2
    elif enemy.y > path[current_point][1]:
            enemy.y -= 2
    else:
        current_point += 1
        if current_point >= len(path):
            current_point = 0
 

    pygame.display.update()
    clock.tick(60)

pygame.quit()