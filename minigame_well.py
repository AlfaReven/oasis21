import pygame
import random
from constants import *

def start_well_minigame(player, well, bucket):
    """
    Minijuego mejorado de extracción de agua - COMPATIBLE CON SISTEMA DE LITROS
    """
    print(f"🎮 Extrayendo agua del pozo... ({well.remaining:.0f}L restantes)")
    
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    
    # Parámetros del juego
    width, height = 400, 500
    game_surface = pygame.Surface((width, height))
    
    # Posición del minijuego en pantalla
    game_x = (WIDTH - width) // 2
    game_y = (HEIGHT - height) // 2
    
    # Elementos del juego
    bucket_x = width // 2
    bucket_y = 50
    bucket_speed = 5
    bucket_size = 30
    rope_length = 0
    max_rope_length = height - 100
    
    obstacles = []
    obstacle_timer = 0
    hits = 0
    max_hits = 3
    water_collected_liters = 0  # Cambiado a litros
    max_water_per_extraction = 20  # Máximo que se puede extraer en una tirada
    
    running = True
    game_over = False
    
    font = pygame.font.Font(None, 24)

    while running:
        dt = clock.tick(60)
        
        # Manejar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
        
        if not game_over:
            # Controles
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                bucket_x = max(bucket_size//2, bucket_x - bucket_speed)
            if keys[pygame.K_RIGHT]:
                bucket_x = min(width - bucket_size//2, bucket_x + bucket_speed)
            if keys[pygame.K_DOWN]:
                rope_length = min(max_rope_length, rope_length + 2)
            if keys[pygame.K_UP]:
                rope_length = max(0, rope_length - 2)
            
            # Generar obstáculos
            obstacle_timer += dt
            if obstacle_timer > 600:  # Cada 600ms
                obstacle_timer = 0
                ox = random.randint(30, width - 30)
                obstacles.append({
                    'rect': pygame.Rect(ox, 0, 20, 20),
                    'speed': random.uniform(1.0, 3.0)
                })
            
            # Actualizar obstáculos
            for obstacle in obstacles[:]:
                obstacle['rect'].y += obstacle['speed']
                if obstacle['rect'].y > height:
                    obstacles.remove(obstacle)
            
            # Colisiones
            bucket_rect = pygame.Rect(bucket_x - bucket_size//2, 
                                    bucket_y + rope_length - bucket_size//2, 
                                    bucket_size, bucket_size)
            
            for obstacle in obstacles[:]:
                if bucket_rect.colliderect(obstacle['rect']):
                    hits += 1
                    obstacles.remove(obstacle)
                    if hits >= max_hits:
                        game_over = True
            
            # Recolectar agua si llegó al fondo
            if rope_length >= max_rope_length - 10 and not game_over:
                # Calcular cuánta agua extraer (considerando espacio en cubeta)
                space_in_bucket = bucket.max_liters - bucket.current_liters
                water_available = well.remaining
                
                water_to_collect = min(max_water_per_extraction, space_in_bucket, water_available)
                water_collected_liters = water_to_collect
                
                # Extraer agua del pozo
                actual_extracted = well.extract_water(water_to_collect)
                water_collected_liters = actual_extracted  # En caso de que no haya suficiente
                
                game_over = True
        
        # Dibujar
        game_surface.fill((30, 30, 60))  # Fondo azul oscuro (pozo)
        
        # Dibujar pozo
        pygame.draw.rect(game_surface, (20, 20, 40), (50, 50, width-100, height-100), 2)
        
        # Dibujar cuerda
        pygame.draw.line(game_surface, (200, 200, 200), 
                        (bucket_x, bucket_y), 
                        (bucket_x, bucket_y + rope_length), 2)
        
        # Dibujar cubeta
        bucket_color = (180, 120, 60)  # Color madera
        
        # Calcular visual del agua en la cubeta (basado en lo recolectado vs capacidad máxima)
        if water_collected_liters > 0:
            fill_ratio = water_collected_liters / max_water_per_extraction
            fill_height = int(bucket_size * fill_ratio)
            pygame.draw.rect(game_surface, (0, 100, 255), 
                           (bucket_x - bucket_size//2, 
                            bucket_y + rope_length - bucket_size//2 + (bucket_size - fill_height),
                            bucket_size, fill_height))
        
        pygame.draw.rect(game_surface, bucket_color, bucket_rect, 2)
        
        # Dibujar obstáculos
        for obstacle in obstacles:
            pygame.draw.rect(game_surface, (255, 60, 60), obstacle['rect'])
        
        # UI del minijuego - ACTUALIZADA
        hits_text = font.render(f"Golpes: {hits}/{max_hits}", True, (255, 255, 255))
        water_text = font.render(f"Agua: {water_collected_liters}L", True, (255, 255, 255))
        depth_text = font.render(f"Profundidad: {rope_length:.0f}/{max_rope_length}", True, (255, 255, 255))
        
        # Información de capacidad de cubeta
        bucket_space = bucket.max_liters - bucket.current_liters
        capacity_text = font.render(f"Espacio cubeta: {bucket_space}L", True, (200, 200, 100))
        
        game_surface.blit(hits_text, (10, 10))
        game_surface.blit(water_text, (10, 40))
        game_surface.blit(depth_text, (10, 70))
        game_surface.blit(capacity_text, (10, 100))
        
        if game_over:
            result_text = font.render("¡Terminado! Presiona ESC", True, (255, 255, 0))
            game_surface.blit(result_text, (width//2 - 100, height//2))
        
        # Dibujar superficie del juego en la pantalla principal
        screen.blit(game_surface, (game_x, game_y))
        pygame.display.flip()

    # RESULTADO FINAL - COMPATIBLE CON SISTEMA DE LITROS
    if water_collected_liters > 0:
        # Calcular agua perdida por golpes
        if hits > 0:
            water_lost_percentage = hits / max_hits  # 0%, 33%, 66% perdido
            water_actually_collected = water_collected_liters * (1 - water_lost_percentage)
        else:
            water_actually_collected = water_collected_liters
        
        # Añadir agua a la cubeta
        actual_water_added = bucket.add_water(water_actually_collected)
        
        # Mensajes según resultado
        if hits == 0:
            print(f"✅ Agua limpia recolectada: {actual_water_added}L")
            print(f"💧 Cubeta ahora tiene: {bucket.current_liters}/{bucket.max_liters}L")
        elif hits == 1:
            print(f"⚠️ Agua ligeramente contaminada: {actual_water_added}L recolectados")
            print(f"💧 Cubeta ahora tiene: {bucket.current_liters}/{bucket.max_liters}L")
        else:
            water_lost = water_collected_liters - actual_water_added
            if actual_water_added > 0:
                print(f"🚫 Mucha agua perdida: {actual_water_added}L recolectados de {water_collected_liters}L")
                print(f"💧 Cubeta ahora tiene: {bucket.current_liters}/{bucket.max_liters}L")
            else:
                print("💦 ¡Toda el agua se derramó!")
                
        # Informar si la cubeta se llenó
        if bucket.current_liters >= bucket.max_liters:
            print("🪣 ¡Cubeta llena!")
            
    else:
        print("❌ No se pudo recolectar agua")
        
    # Informar estado del pozo
    if well.remaining <= 0:
        print("🏜️ ¡El pozo se ha secado!")
    else:
        print(f"📊 Pozo: {well.remaining:.0f}L restantes")