import pygame
import sys
from entities import Entities
from world import World
from constants import *
from weapons import Weapon
from player import Player
from inventory import Inventory
from enemy import Enemy
from menu import MainMenu
from weather_system import WeatherSystem
from multiplayer_manager import MultiplayerManager
from minigame_well import start_well_minigame
from placeable import WaterPump, WaterTank

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Oasis21")
        self.clock = pygame.time.Clock()
        
        # Sistemas principales
        self.menu = MainMenu(self.screen)
        self.weather = WeatherSystem(WIDTH, HEIGHT)
        self.multiplayer = MultiplayerManager()
        
        # Estado del juego
        self.game_state = "menu"
        self.num_players = 1
        
        # Sistemas de juego
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        # Entidades
        self.player = None
        self.enemy = None
        self.world = None
        self.player_weapon = None
        
        # Cámara y tiempo
        self.camera_x = 0
        self.camera_y = 0
        self.current_time = 0
        self.running = True
        
        # UI
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

        # Inicializar mundo
        self.world = World(WIDTH * 3, HEIGHT * 3)

        # Conectar el sistema de clima con el mundo (NUEVO)
        self.weather.set_world_reference(self.world)

        # Buscar punto de spawn en TMX
        spawn_x, spawn_y = self._find_spawn_point()

        # Configurar jugadores
        self.multiplayer.setup_players(num_players)

        if self.multiplayer.players:
            self.player = self.multiplayer.players[0]
            self.player.x = spawn_x
            self.player.y = spawn_y
            self.player.rect.topleft = (spawn_x, spawn_y)

        # Ajustar spawn si está en colisión
        self._adjust_spawn_collision()

        # Crear enemigos y arma
        self.enemy = Enemy(WIDTH, HEIGHT)
        self.player_weapon = Weapon("Pistol", 25, 2.0, 10)
        
        # Configurar cámara
        self.camera_x = self.player.x - WIDTH // 2
        self.camera_y = self.player.y - HEIGHT // 2

    def _find_spawn_point(self):
        """Busca el punto de spawn en el mapa TMX"""
        if not self.world.tmx_map:
            return WIDTH // 2, HEIGHT // 2
            
        for obj in self.world.tmx_map.objects:
            # Manejar valores None de forma segura
            name = getattr(obj, "name", "")
            type_ = getattr(obj, "type", "")
            
            # Convertir a string y luego a minúsculas
            name_str = str(name).lower() if name is not None else ""
            type_str = str(type_).lower() if type_ is not None else ""
            
            if "spawn" in name_str or "spawn" in type_str:
                tile_h = self.world.tmx_map.tileheight
                spawn_x = int(obj.x)
                spawn_y = int(obj.y - tile_h)
                return spawn_x, spawn_y
        
        # Spawn por defecto si no se encuentra
        if self.world.tmx_map:
            tilemap_width = self.world.tmx_map.width * self.world.tmx_map.tilewidth
            tilemap_height = self.world.tmx_map.height * self.world.tmx_map.tileheight
            return tilemap_width // 2, tilemap_height // 2
        else:
            return WIDTH // 2, HEIGHT // 2

    def _adjust_spawn_collision(self):
        """Ajusta la posición del spawn si hay colisión"""
        if hasattr(self.world, "collision_rects") and self.player:
            for rect in self.world.collision_rects:
                if self.player.rect.colliderect(rect):
                    self.player.y += 32
                    self.player.rect.topleft = (self.player.x, self.player.y)
                    break

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Menú principal
            if self.game_state == "menu":
                self._handle_menu_events(event)
                continue

            # Eventos del juego
            if self.game_state == "playing":
                self._handle_game_events(event)

    def _handle_menu_events(self, event):
        """Maneja eventos del menú principal"""
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

    def _handle_game_events(self, event):
        """Maneja eventos durante el juego"""
        if event.type == pygame.KEYDOWN:
            # Jugador 1
            if event.key == pygame.K_SPACE:
                self.player_shoot(0)
            elif event.key == pygame.K_i:
                if not self.player.inventory.table_crafting_open:
                    self.player.show_inventory = not self.player.show_inventory
            elif event.key == pygame.K_b:
                self.player.drink_water()
            elif event.key == pygame.K_v:  # ✅ NUEVA TECLA para usar cubeta
                self.player.use_bucket(self.world)
            elif event.key == pygame.K_p:
                self.player.place_object(self.world)
            elif event.key == pygame.K_e:
                self._handle_interaction()
            elif event.key == pygame.K_ESCAPE:
                self._handle_escape()
            elif event.key == pygame.K_c:
                self.show_coordinates = True
            elif event.key == pygame.K_r:
                self.weather.start_rain()
            elif event.key == pygame.K_q:  
                self.player.pick_placeable(self.world)

            # Jugador 2
            if len(self.multiplayer.players) > 1:
                self._handle_player2_events(event)

        elif event.type == pygame.MOUSEBUTTONDOWN and self.game_state == "playing":
            self._handle_mouse_click(event)

    def _handle_interaction(self):
        """Maneja la interacción con objetos del mundo"""
        inv = self.player.inventory
        
        if inv.table_crafting_open:
            inv.close_table_crafting()
        elif hasattr(inv, "furnace_open") and inv.furnace_open:
            inv.furnace_open = False
            inv.active_furnace = None
        else:
            # Interactuar con el mundo (usando el nuevo sistema)
            self.player.show_inventory = False
            # Usar el método interact (no interact_with_objects)
            self.player.interact(self.world)  # ✅ CAMBIADO

    def _handle_escape(self):
        """Maneja la tecla ESC"""
        if self.player.inventory.table_crafting_open:
            self.player.inventory.close_table_crafting()
        elif self.player.show_inventory:
            self.player.show_inventory = False
        else:
            self.game_state = "menu"

    def _handle_player2_events(self, event):
        """Maneja eventos específicos del jugador 2"""
        player2 = self.multiplayer.players[1]
        
        if event.key == pygame.K_RETURN:
            if player2.inventory.table_crafting_open:
                player2.inventory.close_table_crafting()
            else:
                player2.show_inventory = False
                player2.interact(self.world)  # ✅ CAMBIADO
        elif event.key == pygame.K_RSHIFT:
            if not player2.inventory.table_crafting_open:
                player2.show_inventory = not player2.show_inventory
        elif event.key == pygame.K_RALT:
            player2.place_object(self.world)
        elif event.key == pygame.K_RCTRL:
            player2.running = True
        elif event.key == pygame.K_SLASH:  # ✅ AGREGADO para cubeta jugador 2
            player2.use_bucket(self.world)
        elif event.key == pygame.K_PERIOD:  # ✅ AGREGADO para beber jugador 2
            player2.drink_water()
    def _handle_mouse_click(self, event):
        """Maneja clicks del mouse en interfaces"""
        pos = pygame.mouse.get_pos()
        inv = self.player.inventory

        if hasattr(inv, "furnace_open") and inv.furnace_open:
            inv.handle_furnace_click(pos, event.button)
        elif inv.table_crafting_open:
            inv.handle_table_crafting_click(pos, event.button)
        elif self.player.show_inventory:
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
        
        obstacles = self._get_obstacles()

        # Actualizar sistemas
        self.weather.update(dt, self.camera_x, self.camera_y)
        self.multiplayer.update(dt * 1000, obstacles)
        
        # Actualizar jugador
        if self.player:
            self.player.update(dt * 1000, obstacles)
            self.player.update_animation(dt * 1000)
        
        # Actualizar horno si está activo
        self._update_furnace(dt)
        
        # Actualizar objetos colocables
        if hasattr(self.world, 'update_placeables'):
            self.world.update_placeables(dt * 1000, self.player)
        
        # Actualizar mundo
        self.world.update(self.player, dt * 1000, self.enemy_bullets, self.current_time)
        self.player_bullets.update(dt * 1000)
        self.enemy_bullets.update(dt * 1000)
        
        # Colisiones balas-jugador
        for bullet in self.enemy_bullets:
            if hasattr(bullet, 'hitbox') and bullet.hitbox.colliderect(self.player.rect):
                damage = self.player.take_damage(bullet.source, 'ranged')
                bullet.kill()
                if self.player.is_dead():
                    self.game_over()
        
        # Colisiones balas-enemigo
        for bullet in self.player_bullets:
            if hasattr(bullet, 'hitbox') and bullet.hitbox.colliderect(self.enemy.rect):
                damage = self.enemy.take_damage(bullet.source, 'ranged')
                bullet.kill()
                if self.enemy.is_dead():
                    self.enemy.drop_loot()

        # Actualizar cámara
        self.update_camera()
        
        self.cleanup_bullets()

    def _get_obstacles(self):
        """Obtiene todos los obstáculos del mundo"""
        obstacles = self.world.trees + self.world.placeable_objects + self.world.wells
        
        if hasattr(self.world, "collision_rects"):
            for rect in self.world.collision_rects:
                class DummyObstacle:
                    def __init__(self, rect):
                        self.rect = rect
                obstacles.append(DummyObstacle(rect))
                
        return obstacles

    def _update_furnace(self, dt):
        """Actualiza el horno si está activo"""
        if (hasattr(self.player.inventory, "active_furnace") and 
            self.player.inventory.active_furnace):
            furnace = self.player.inventory.active_furnace
            furnace.update(dt * 1000)

    def update_camera(self):
        """Actualiza la cámara para seguir a los jugadores"""
        if not self.multiplayer.players:
            return
            
        if len(self.multiplayer.players) == 1:
            # Cámara centrada en un jugador
            self.camera_x = self.multiplayer.players[0].x - WIDTH // 2
            self.camera_y = self.multiplayer.players[0].y - HEIGHT // 2
        else:
            # Cámara adaptativa para dos jugadores
            self._update_multiplayer_camera()

    def _update_multiplayer_camera(self):
        """Actualiza cámara para modo multijugador"""
        player1 = self.multiplayer.players[0]
        player2 = self.multiplayer.players[1]
        
        # Punto medio entre jugadores
        mid_x = (player1.x + player2.x) // 2
        mid_y = (player1.y + player2.y) // 2
        
        # Calcular zoom adaptativo
        distance_x = abs(player1.x - player2.x)
        distance_y = abs(player1.y - player2.y)
        zoom_factor = max(1.0, distance_x / (WIDTH * 0.6), distance_y / (HEIGHT * 0.6))
        
        # Aplicar cámara con zoom
        self.camera_x = mid_x - (WIDTH // 2) * zoom_factor
        self.camera_y = mid_y - (HEIGHT // 2) * zoom_factor
        
        # Limitar cámara a los bordes del mundo
        world_width = WIDTH * 3
        world_height = HEIGHT * 3
        self.camera_x = max(0, min(self.camera_x, world_width - WIDTH * zoom_factor))
        self.camera_y = max(0, min(self.camera_y, world_height - HEIGHT * zoom_factor))

    def cleanup_bullets(self):
        """Limpia balas que ya no son necesarias"""
        pass

    def game_over(self):
        """Maneja el game over"""
        self.game_state = "menu"
        
        # Resetear jugador
        if self.player:
            self.player.stats['health'] = self.player.stats['max_health']
            self.player.x = WIDTH // 2
            self.player.y = HEIGHT // 2
            self.player_bullets.empty()
            self.enemy_bullets.empty()

    def draw(self):
        self.screen.fill(BLACK)
        
        if self.game_state == "menu":
            self.menu.draw()
        elif self.game_state == "playing":
            self._draw_game()

        pygame.display.flip()

    def _draw_game(self):
        """Dibuja todos los elementos del juego"""
        # Mundo y efectos
        self.world.draw(self.screen, self.camera_x, self.camera_y, 
                    bullets_group=self.enemy_bullets, current_time=self.current_time)
        self.weather.draw(self.screen, self.camera_x, self.camera_y)
        
        # Objetos colocables (esto ya incluye las status bars del WaterTank)
        if hasattr(self.world, 'draw_placeables'):
            self.world.draw_placeables(self.screen, self.camera_x, self.camera_y)
        
        # Jugadores
        self.multiplayer.draw(self.screen, self.camera_x, self.camera_y)
        
        # Balas
        self._draw_bullets()
        
        # Interfaces
        self._draw_interfaces()

    def _draw_bullets(self):
        """Dibuja las balas en pantalla"""
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

    def _draw_interfaces(self):
        """Dibuja las interfaces de usuario"""
        inv = self.player.inventory

        if inv.table_crafting_open:
            inv.draw_crafting_table(self.screen)
        elif hasattr(inv, "furnace_open") and inv.furnace_open:
            inv.draw_furnace(self.screen)
        elif self.player.show_inventory:
            inv.draw(self.screen, show_inventory=True)
        else:
            inv.draw(self.screen, show_inventory=False)

        # HUD
        self.draw_hud()

    def draw_hud(self):
        """Dibuja la interfaz de usuario"""
        if self.game_state != "playing" or not self.player:
            return
            
        self.player.draw_status_bars(self.screen)
        self.player.update_status()
        
        # Barra de salud
        health_width = 200
        health_height = 20
        health_x, health_y = 10, 10
        
        health_ratio = self.player.stats['health'] / self.player.stats['max_health']
        current_width = int(health_width * health_ratio)
        
        pygame.draw.rect(self.screen, RED, (health_x, health_y, health_width, health_height))
        pygame.draw.rect(self.screen, GREEN, (health_x, health_y, current_width, health_height))
        pygame.draw.rect(self.screen, WHITE, (health_x, health_y, health_width, health_height), 2)
        
        # Textos informativos (NUEVO: añadir estado del clima)
        health_text = self.font.render(f"HP: {self.player.stats['health']}/{self.player.stats['max_health']}", True, WHITE)
        level_text = self.font.render(f"Nivel: {self.player.stats['level']}", True, WHITE)
        exp_text = self.font.render(f"EXP: {self.player.stats['experience']}", True, WHITE)
        weapon_text = self.font.render(f"Arma: {self.player_weapon.name}", True, WHITE)
        weather_text = self.font.render(f"Clima: {self.weather.get_weather_status()}", True, WHITE)  # NUEVO
        players_text = self.font.render(f"Jugadores: {self.num_players}", True, WHITE)
        
        self.screen.blit(health_text, (health_x + health_width + 10, health_height))
        self.screen.blit(level_text, (health_x, HEIGHT - health_y - health_height - 5))
        self.screen.blit(exp_text, (health_x, HEIGHT - health_y - health_height - 30))
        self.screen.blit(weapon_text, (WIDTH - 200, 10))
        self.screen.blit(weather_text, (WIDTH - 200, 30))  # NUEVO
        self.screen.blit(players_text, (WIDTH - 200, 50))
        
        # Instrucciones
        instructions = [
            "WASD: Moverse",
            "Shift: Correr", 
            "ESPACIO: Disparar",
            "I: Inventario",
            "E: Interactuar",
            "P: Colocar objeto",
            "B: Beber agua",
            "R: Lluvia (debug)",
            "ESC: Menú"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            self.screen.blit(text, (WIDTH - 250, 80 + i * 25))
            
        # Coordenadas (si están activas)
        if self.show_coordinates and self.player:
            coord_text = self.font.render(f"X: {int(self.player.x)}, Y: {int(self.player.y)}", True, WHITE)
            self.screen.blit(coord_text, (health_x, HEIGHT - health_y - health_height - 55))

    def run(self):
        """Bucle principal del juego"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()