import pygame

pygame.init()

WIDTH = 800
HEIGHT = 600

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

enemy_x = enemy.x
enemy_y = enemy.y
enemy_width = enemy.width
enemy_height = enemy.height
enemy_hp = enemy.hp

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
    
    


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

  
    for i in range(len(path) - 1):
        pygame.draw.line(screen,
                     (100, 100, 100),
                     path[i],
                     path[i + 1],
                     20)

    
    
    
    enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_width, enemy_height)
    pygame.draw.rect(screen, (255, 0, 0), enemy_rect)
    pygame.draw.rect(screen, (255, 0, 0),
                 (enemy_x, enemy_y - 10, 30, 5))

    pygame.draw.rect(screen, (0, 255, 0),
                 (enemy_x, enemy_y - 10,
                  30 * (enemy_hp / 100), 5))

    pygame.draw.circle(screen, (0, 0, 255), (tower_x, tower_y), 20)
    pygame.draw.circle(screen, (100, 100, 100), (tower_x, tower_y), tower_range, 1)

    distance_x = enemy_x - tower_x
    distance_y = enemy_y - tower_y
    distance = (distance_x ** 2 + distance_y ** 2) ** 0.5

    if distance < tower_range:
     pygame.draw.line(screen, (255, 255, 0), (tower_x, tower_y), (enemy_x, enemy_y), 3)
     if distance < tower_range:
        pygame.draw.line(screen, (255, 255, 0),
                     (tower_x, tower_y),
                     (enemy_x, enemy_y), 3)
        tower_cooldown += 1
        if tower_cooldown >= 30:
            tower_cooldown = 0
            enemy_hp -= tower_damage

    if enemy_hp <= 0:
        money += 10

        enemy_hp = 100
        enemy_x = 0
        enemy_y = 300
        current_point = 1

    

    
    
    
    if enemy_x < path[current_point][0]:
            enemy_x += 2
    elif enemy_x > path[current_point][0]:
            enemy_x -= 2
    elif enemy_y < path[current_point][1]:
            enemy_y += 2
    elif enemy_y > path[current_point][1]:
            enemy_y -= 2
    else:
        current_point += 1
        if current_point >= len(path):
            current_point = 0
 

    pygame.display.update()
    clock.tick(60)

pygame.quit()