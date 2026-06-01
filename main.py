import pygame

pygame.init()

WIDTH = 800
HEIGHT = 600

enemy_x = 0
enemy_y = 300
enemy_width = 30
enemy_height = 30

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")

clock = pygame.time.Clock()


running = True

enemy_x=0
enemy_y=300
path = [(0, 300), (200, 300), (200, 100), (400, 100), (400, 500), (600, 500), (600, 300), (800, 300)]
current_point = 1

while running:

    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    enemy_rect = pygame.Rect(enemy_x, enemy_y, enemy_width, enemy_height)
    pygame.draw.rect(screen, (255, 0, 0), enemy_rect)

    

    
    
    
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