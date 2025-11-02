import pygame
import sys
from entities import Entities
from world import World
from constants import *
from weapons import Weapon
from player import Player
from inventory import Inventory
from enemy import Enemy
from menu import MainMenu  # NUEVO
from weather_system import WeatherSystem  # NUEVO
from multiplayer_manager import MultiplayerManager  # NUEVO

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Oasis21")
        self.clock = pygame.time.Clock()
        
        # NUEVO: Sistemas añadidos
        self.menu = MainMenu(self.screen)
        self.weather = WeatherSystem(WIDTH, HEIGHT)
        self.multiplayer = MultiplayerManager()
        
        # Estado del juego
        self.game_state = "menu"  # "menu", "playing", "game_over"
        self.num_players = 1  # Por defecto 1 jugador
        
        # Tus sistemas originales
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        # Jugador principal (se inicializará después)
        self.player = None
        self.enemy = None
        self.world = None
        self.player_weapon = None
        
        self.camera_x = 0
        self.camera_y = 0
        self.current_time = 0
        self.running = True
        
        self.font = pygame.font.Font(None, 24)
        
        self.show_inventory = False
        self.show_coordinates = False
    
    def start_game(self, num_players=1):
        """Inicializar el juego con el número de jugadores especificado"""
        self.game_state = "playing"
        self.num_players = num_players

        # Reiniciar sistemas
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()

        # --- 1️⃣ Inicializar el mundo (primero para tener acceso al TMX) ---
        self.world = World(WIDTH * 3, HEIGHT * 3)

        # --- 2️⃣ Buscar el punto de spawn en el TMX ---
        spawn_x, spawn_y = None, None
        if self.world.tmx_map:
            for obj in self.world.tmx_map.objects:
                name = getattr(obj, "name", None)
                type_ = getattr(obj, "type", None)

                if isinstance(name, str):
                    name = name.lower()
                else:
                    name = ""

                if isinstance(type_, str):
                    type_ = type_.lower()
                else:
                    type_ = ""

                if name == "spawn" or type_ == "spawn":
                    tile_h = self.world.tmx_map.tileheight
                    spawn_x = int(obj.x)
                    spawn_y = int(obj.y - tile_h)  # ✅ Corrige la base del objeto en Tiled
                    print(f"🎯 Punto de spawn corregido en ({spawn_x}, {spawn_y})")
                    break

        if spawn_x is None or spawn_y is None:
            print("⚠️ No se encontró punto de spawn, usando centro por defecto.")
            tilemap_width = self.world.tmx_map.width * self.world.tmx_map.tilewidth
            tilemap_height = self.world.tmx_map.height * self.world.tmx_map.tileheight
            spawn_x = tilemap_width // 2
            spawn_y = tilemap_height // 2

        # --- 3️⃣ Configurar jugadores ---
        self.multiplayer.setup_players(num_players)

        if self.multiplayer.players:
            self.player = self.multiplayer.players[0]
            self.player.x = spawn_x
            self.player.y = spawn_y
            self.player.rect.topleft = (spawn_x, spawn_y)
            print(f"🧍Jugador posicionado en: {spawn_x}, {spawn_y}")

        # --- 4️⃣ Evitar que el spawn esté en una colisión ---
        if hasattr(self.world, "collision_rects"):
            for rect in self.world.collision_rects:
                if self.player.rect.colliderect(rect):
                    self.player.y += 32
                    self.player.rect.topleft = (self.player.x, self.player.y)
                    print("⚠️ Ajuste: Spawn dentro de colisión, movido hacia abajo.")
                    break

        # --- 5️⃣ Crear enemigos y cámara ---
        self.enemy = Enemy(WIDTH, HEIGHT)
        self.player_weapon = Weapon("Pistol", 25, 2.0, 10)
        self.camera_x = self.player.x - WIDTH // 2
        self.camera_y = self.player.y - HEIGHT // 2

        print(f"🚀 Juego iniciado con {num_players} jugador(es).")

        

        

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # --- MENÚ PRINCIPAL ---
            if self.game_state == "menu":
                menu_result = self.menu.handle_event(event)
                if menu_result is not None:
                    if menu_result == 0:  # JUGAR
                        self.start_game(1)
                    elif menu_result == 1:  # MULTIJUGADOR
                        self.start_game(2)
                    elif menu_result == 2:  # CARGAR
                        self.start_game(1)
                    elif menu_result == 3:  # SALIR
                        self.running = False
                continue  # Evita procesar más eventos cuando estás en el menú

            # --- EVENTOS DEL JUEGO ---
            if self.game_state == "playing":

                # --- TECLAS PRESIONADAS ---
                if event.type == pygame.KEYDOWN:

                    # Jugador 1 (teclas originales)
                    if event.key == pygame.K_SPACE:
                        self.player_shoot(0)  # Disparar jugador 1

                    elif event.key == pygame.K_i:
                        if not self.player.inventory.table_crafting_open:
                            self.player.show_inventory = not self.player.show_inventory
                    
                    elif event.key == pygame.K_b:
                        self.player.drink_water()

                    elif event.key == pygame.K_p:
                        self.player.place_object(self.world)

                    elif event.key == pygame.K_e:
                        inv = self.player.inventory

                        # 1️⃣ Si la mesa está abierta → ciérrala
                        if inv.table_crafting_open:
                            inv.close_table_crafting()

                        # 2️⃣ Si el horno está abierto → ciérralo
                        elif hasattr(inv, "furnace_open") and inv.furnace_open:
                            inv.furnace_open = False
                            inv.active_furnace = None
                            print("🔥 Horno cerrado")

                        # 3️⃣ Si nada está abierto → intentar interactuar con el mundo
                        else:
                            self.player.show_inventory = False
                            self.player.interact_with_objects(self.world)

                    # Jugador 2 (nuevas teclas)
                    if len(self.multiplayer.players) > 1:
                        player2 = self.multiplayer.players[1]

                        if event.key == pygame.K_RETURN:  # Enter para interactuar P2
                            if player2.inventory.table_crafting_open:
                                player2.inventory.close_table_crafting()
                            else:
                                player2.show_inventory = False
                                player2.interact_with_objects(self.world)

                        elif event.key == pygame.K_RSHIFT:  # Inventario P2
                            if not player2.inventory.table_crafting_open:
                                player2.show_inventory = not player2.show_inventory

                        elif event.key == pygame.K_RALT:  # Colocar objeto P2
                            player2.place_object(self.world)

                        elif event.key == pygame.K_RCTRL:  # Correr P2
                            player2.running = True

                    # Teclas globales
                    if event.key == pygame.K_ESCAPE:
                        if self.player.inventory.table_crafting_open:
                            self.player.inventory.close_table_crafting()
                        elif self.player.show_inventory:
                            self.player.show_inventory = False
                        else:
                            self.game_state = "menu"

                    elif event.key == pygame.K_c:
                        self.show_coordinates = True

                    elif event.key == pygame.K_r:
                        self.weather.start_rain()

                # --- CLICS DE RATÓN ---
                # --- CLICS DE RATÓN ---
                elif event.type == pygame.MOUSEBUTTONDOWN and self.game_state == "playing":
                    pos = pygame.mouse.get_pos()
                    inv = self.player.inventory

                    # 🎯 ORDEN DE PRIORIDAD: Horno > Mesa > Inventario normal
                    if hasattr(inv, "furnace_open") and inv.furnace_open:
                        print("🔥 Procesando click en horno...")
                        inv.handle_furnace_click(pos, event.button)
                        
                    elif inv.table_crafting_open:
                        print("🪵 Procesando click en mesa...")
                        inv.handle_table_crafting_click(pos, event.button)
                        
                    elif self.player.show_inventory:
                        print("🎒 Procesando click en inventario...")
                        inv.handle_click(pos, event.button, show_inventory=True)
                        
                        
                        
    def player_shoot(self, player_id=0):
        """Manejar el disparo del jugador especificado"""
        if player_id == 0:
            shooter = self.player
        elif player_id == 1 and len(self.multiplayer.players) > 1:
            shooter = self.multiplayer.players[1]
        else:
            return
            
        direction = self.get_shoot_direction(shooter)
        
        bullet = self.player_weapon.shoot(
            shooter.x, 
            shooter.y, 
            direction,  
            shooter, 
            self.world.enemies,
            self.current_time
        )
        if bullet:
            self.player_bullets.add(bullet)

    def get_shoot_direction(self, player):
        """Convertir el current_state del jugador a dirección de disparo"""
        if player.current_state == WALK_UP or player.current_state == IDLE_UP:
            return "up"
        elif player.current_state == WALK_DOWN or player.current_state == IDLE_DOWN:
            return "down"
        elif player.current_state == WALK_RIGHT or player.current_state == IDLE_RIGHT:
            if player.facing_left:
                return "left"
            else:
                return "right"
        else:
            return "right"
    def update(self):
        if self.game_state != "playing":
            return
            
        dt = self.clock.tick(60) / 1000.0
        self.current_time = pygame.time.get_ticks()
        
        obstacles = self.world.trees + self.world.placeable_objects + self.world.wells

        # 🔸 Agregar colisiones del mapa (rectángulos de la capa "Colisiones")
        if hasattr(self.world, "collision_rects"):
            for rect in self.world.collision_rects:
                # Creamos un objeto temporal con .rect para que el sistema actual lo entienda igual
                class DummyObstacle:
                    def __init__(self, rect):
                        self.rect = rect
                obstacles.append(DummyObstacle(rect))

        self.weather.update(dt, self.camera_x, self.camera_y)
        self.multiplayer.update(dt * 1000, obstacles)
        
        if self.player:
            self.player.update(dt * 1000, obstacles)
            self.player.update_animation(dt * 1000)
        
        # 🔥 ACTUALIZAR HORNO SI ESTÁ ABIERTO
        if hasattr(self.player.inventory, "active_furnace") and self.player.inventory.active_furnace:
            furnace = self.player.inventory.active_furnace
            furnace.update(dt * 1000)  # Asegúrate de que el horno tenga método update
        
        if hasattr(self.world, 'update_placeables'):
            self.world.update_placeables(dt * 1000, self.player)
        
        # ... resto del código update
        
        self.world.update(self.player, dt * 1000, self.enemy_bullets, self.current_time)
        self.player_bullets.update(dt * 1000)
        self.enemy_bullets.update(dt * 1000)
        
        # Colisiones...
        for bullet in self.enemy_bullets:
            if hasattr(bullet, 'hitbox') and bullet.hitbox.colliderect(self.player.rect):
                damage = self.player.take_damage(bullet.source, 'ranged')
                bullet.kill()
                if self.player.is_dead():
                    self.game_over()
        
        for bullet in self.player_bullets:
            if hasattr(bullet, 'hitbox') and bullet.hitbox.colliderect(self.enemy.rect):
                damage = self.enemy.take_damage(bullet.source, 'ranged')
                bullet.kill()
                if self.enemy.is_dead():
                    self.enemy.drop_loot()

        # NUEVO: Sistema de cámara inteligente que sigue a ambos jugadores
        self.update_camera()
        
        self.cleanup_bullets()

    def update_camera(self):
        """Actualiza la cámara para mantener a ambos jugadores en vista"""
        if len(self.multiplayer.players) == 0:
            return
            
        if len(self.multiplayer.players) == 1:
            # Solo un jugador: cámara centrada en él
            self.camera_x = self.multiplayer.players[0].x - WIDTH // 2
            self.camera_y = self.multiplayer.players[0].y - HEIGHT // 2
        else:
            # Dos jugadores: cámara que se adapta a ambos
            player1 = self.multiplayer.players[0]
            player2 = self.multiplayer.players[1]
            
            # Calcular el punto medio entre ambos jugadores
            mid_x = (player1.x + player2.x) // 2
            mid_y = (player1.y + player2.y) // 2
            
            # Calcular la distancia entre jugadores
            distance_x = abs(player1.x - player2.x)
            distance_y = abs(player1.y - player2.y)
            
            # Ajustar el zoom según la distancia entre jugadores
            zoom_factor_x = max(1.0, distance_x / (WIDTH * 0.6))
            zoom_factor_y = max(1.0, distance_y / (HEIGHT * 0.6))
            zoom_factor = max(zoom_factor_x, zoom_factor_y)
            
            # Aplicar cámara con zoom adaptativo
            self.camera_x = mid_x - (WIDTH // 2) * zoom_factor
            self.camera_y = mid_y - (HEIGHT // 2) * zoom_factor
            
            # Limitar la cámara a los bordes del mundo si es necesario
            world_width = WIDTH * 3  # Ajusta según tu mundo
            world_height = HEIGHT * 3
            
            self.camera_x = max(0, min(self.camera_x, world_width - WIDTH * zoom_factor))
            self.camera_y = max(0, min(self.camera_y, world_height - HEIGHT * zoom_factor))
    
    def cleanup_bullets(self):
        pass

    def game_over(self):
        print("Game Over...")
        # NUEVO: Ir a pantalla de game over o menú
        self.game_state = "menu"
        
        # Opcional: resetear jugador
        if self.player:
            self.player.stats['health'] = self.player.stats['max_health']
            self.player.x = WIDTH // 2
            self.player.y = HEIGHT // 2
            self.player_bullets.empty()
            self.enemy_bullets.empty()

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.game_state == "menu":
            # NUEVO: Dibujar menú
            self.menu.draw()
            
        elif self.game_state == "playing":
            # --- MUNDO ---
            self.world.draw(
                self.screen, 
                self.camera_x, 
                self.camera_y, 
                bullets_group=self.enemy_bullets, 
                current_time=self.current_time
            )

            # --- EFECTOS CLIMÁTICOS ---
            self.weather.draw(self.screen, self.camera_x, self.camera_y)

            # --- OBJETOS COLOCABLES ---
            if hasattr(self.world, 'draw_placeables'):
                self.world.draw_placeables(self.screen, self.camera_x, self.camera_y)
            
            # --- JUGADORES ---
            self.multiplayer.draw(self.screen, self.camera_x, self.camera_y)
            
            # --- BALAS ---
            for bullet in self.player_bullets:
                screen_x = bullet.x - self.camera_x
                screen_y = bullet.y - self.camera_y
                if 0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT:
                    self.screen.blit(bullet.image, (screen_x, screen_y))

            for bullet in self.enemy_bullets:
                screen_x = bullet.x - self.camera_x
                screen_y = bullet.y - self.camera_y
                if 0 <= screen_x <= WIDTH and 0 <= screen_y <= HEIGHT:
                    self.screen.blit(bullet.image, (screen_x, screen_y))

            # --- INVENTARIO / INTERFACES ---
            inv = self.player.inventory

            # 🔸 Mesa de crafteo abierta
            if inv.table_crafting_open:
                inv.draw_crafting_table(self.screen)

            # 🔸 Horno abierto
            elif hasattr(inv, "furnace_open") and inv.furnace_open:
                inv.draw_furnace(self.screen)

            # 🔸 Inventario abierto
            elif self.player.show_inventory:
                inv.draw(self.screen, show_inventory=True)

            # 🔸 Hotbar visible siempre
            else:
                inv.draw(self.screen, show_inventory=False)

            # --- HUD ---
            self.draw_hud()
        
        pygame.display.flip()

    def draw_hud(self):
        """Dibujar interfaz de usuario"""
        if self.game_state != "playing":
            return
            
        self.player.draw_status_bars(self.screen)
        self.player.update_status()
        
        health_width = 200
        health_height = 20
        health_x = 10
        health_y = 10
        
        pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
        
        health_ratio = self.player.stats['health'] / self.player.stats['max_health']
        current_width = int(health_width * health_ratio)
        pygame.draw.rect(self.screen, GREEN, (health_x, health_y, current_width, health_height))
        
        pygame.draw.rect(self.screen, WHITE, (health_x, health_y, health_width, health_height), 2)
        
        health_text = self.font.render(f"HP: {self.player.stats['health']}/{self.player.stats['max_health']}", True, WHITE)
        self.screen.blit(health_text, (health_x + health_width + 10, health_height))
        
        level_text = self.font.render(f"Nivel: {self.player.stats['level']}", True, WHITE)
        exp_text = self.font.render(f"EXP: {self.player.stats['experience']}", True, WHITE)
        self.screen.blit(level_text, (health_x, HEIGHT - health_y - health_height - 5))
        self.screen.blit(exp_text, (health_x, HEIGHT - health_y - health_height - 30))
        
        weapon_text = self.font.render(f"Arma: {self.player_weapon.name}", True, WHITE)
        self.screen.blit(weapon_text, (WIDTH - 150, 10))
        
        # NUEVO: Info del clima y jugadores
        weather_text = self.font.render(f"Lluvia: {'SÍ' if self.weather.raining else 'NO'}", True, WHITE)
        players_text = self.font.render(f"Jugadores: {self.num_players}", True, WHITE)
        self.screen.blit(weather_text, (WIDTH - 150, 30))
        self.screen.blit(players_text, (WIDTH - 150, 50))
        
        instructions = [
            "WASD: Moverse",
            "Shift: Correr", 
            "ESPACIO: Disparar",
            "I: Inventario",
            "P: Poner",
            "R: Lluvia (debug)",
            "ESC: Menú"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            self.screen.blit(text, (WIDTH - 200, 80 + i * 25))
            
        if self.show_coordinates:
            coord_text = self.font.render(f"X: {int(self.player.x)}, Y: {int(self.player.y)}", True, WHITE)
            self.screen.blit(coord_text, (health_x, HEIGHT - health_y - health_height - 55))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()