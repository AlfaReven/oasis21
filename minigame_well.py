import pygame
import random
from constants import *

def start_well_minigame(player, well):
    """
    Simula el descenso de la cubeta en el pozo, evitando obstáculos.
    Si choca demasiado, el agua se contamina o se derrama.
    """
    print("🎮 Minijuego: extrayendo agua del pozo...")

    # Crear ventana temporal (o superposición dentro del juego)
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Parámetros del juego
    width, height = 400, 600
    bucket_x = width // 2
    bucket_y = 50
    bucket_speed = 4
    bucket_size = 30
    
    obstacles = []
    obstacle_timer = 0
    hits = 0
    running = True

    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            bucket_x -= bucket_speed
        if keys[pygame.K_RIGHT]:
            bucket_x += bucket_speed
        if keys[pygame.K_ESCAPE]:
            running = False
        
        # Generar obstáculos aleatorios
        obstacle_timer += dt
        if obstacle_timer > 800:
            obstacle_timer = 0
            ox = random.randint(50, width - 50)
            oy = random.randint(height//3, height)
            obstacles.append(pygame.Rect(ox, oy, 20, 20))
        
        # Actualizar
        bucket_y += 1  # simula que baja con la cuerda
        if bucket_y > height - 80:
            running = False
        
        # Colisiones
        bucket_rect = pygame.Rect(bucket_x, bucket_y, bucket_size, bucket_size)
        for obs in obstacles:
            if bucket_rect.colliderect(obs):
                hits += 1
                obstacles.remove(obs)
        
        # Dibujar
        screen.fill((20, 20, 40))
        pygame.draw.rect(screen, (120, 200, 255), bucket_rect)
        for obs in obstacles:
            pygame.draw.rect(screen, (255, 60, 60), obs)
        
        pygame.display.flip()

    # Evaluación del resultado
    contamination = min(1.0, hits / 5)
    print(f"💧 Contaminación: {contamination:.2f}")
    
    if contamination > 0.6:
        print("⚠️ El agua está muy contaminada, no es potable.")
        player.update_thirst(-10)
    else:
        print("✅ Agua limpia obtenida.")
        player.update_thirst(+30)
        well.extract_water()
