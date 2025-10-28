import pygame
import sys
from entities import Entities
from world import World
from constants import *
from weapons import Weapon
from player import Player
from inventory import Inventory
from enemy import Enemy

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Oasis21")
        self.clock = pygame.time.Clock()
        
        
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        
        
        self.player = Player(WIDTH // 2, HEIGHT // 2)
        self.enemy = Enemy(WIDTH, HEIGHT)
        self.world = World(WIDTH * 3, HEIGHT * 3)
        
        
        self.player_weapon = Weapon("Pistol", 25, 2.0, 10) 
        
        
        self.camera_x = 0
        self.camera_y = 0
        
        
        self.current_time = 0
        self.running = True
        
        
        self.font = pygame.font.Font(None, 24)
        
        
        self.show_inventory = False
        self.show_coordinates = False
    
    

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                
                if event.key == pygame.K_SPACE:
                    self.player_shoot()

                #esta tecla es para el inventario
                elif event.key == pygame.K_i:
                    if not self.player.inventory.table_crafting_open:
                        self.player.show_inventory = not self.player.show_inventory
                    else: 
                        return
                        

                #para poner objetos que tenga en los slots de las manos y que sea posible ponerlos
                elif event.key == pygame.K_p:
                    self.player.place_object(self.world)

                #tecla por default para interactuar con los objeto del mundo
                elif event.key == pygame.K_e:
                    if self.player.inventory.table_crafting_open:
                        self.player.inventory.close_table_crafting()
                    else:
                        self.player.show_inventory = False  
                        self.player.interact_with_objects(self.world)

                #la uso para 2 cosas o cerrar el juego o el inventario
                elif event.key == pygame.K_ESCAPE:
                    if self.player.inventory.table_crafting_open:
                        self.player.inventory.close_table_crafting()
                    elif self.player.show_inventory:
                        self.player.show_inventory = False
                    else:
                        self.running = False
                        
                elif event.key == pygame.K_c:
                    self.show_coordinates = True


            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if self.player.inventory.table_crafting_open:
                    self.player.inventory.handle_table_crafting_click(pos, event.button)
                
                elif self.player.show_inventory:
                    self.player.inventory.handle_click(pos, event.button, show_inventory=True)

                    
                    
    def player_shoot(self):
        """Manejar el disparo del jugador"""
        
        direction = self.get_shoot_direction()
        
        bullet = self.player_weapon.shoot(
            self.player.x, 
            self.player.y, 
            direction,  
            self.player, 
            self.world.enemies,
            self.current_time
        )
        if bullet:
            self.player_bullets.add(bullet)


    def get_shoot_direction(self):
        """Convertir el current_state del jugador a dirección de disparo, considerando facing_left"""
        if self.player.current_state == WALK_UP or self.player.current_state == IDLE_UP:
            return "up"
        elif self.player.current_state == WALK_DOWN or self.player.current_state == IDLE_DOWN:
            return "down"
        elif self.player.current_state == WALK_RIGHT or self.player.current_state == IDLE_RIGHT:
            
            if self.player.facing_left:
                return "left"
            else:
                return "right"
        else:
            return "right"  

    
    def update(self):
        dt = self.clock.tick(60)  
        self.current_time = pygame.time.get_ticks()
        
        
        obstacles = self.world.trees + self.world.placeable_objects
        self.player.update(dt, obstacles)
        self.player.update_animation(dt)
        
        if hasattr(self.world, 'update_placeables'):
            self.world.update_placeables(dt)
        
        
        self.world.update(self.player, dt, self.enemy_bullets, self.current_time)
        
        
        self.player_bullets.update(dt)
        
        
        self.enemy_bullets.update(dt)
        
        
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

        
        
        self.camera_x = self.player.x - WIDTH // 2
        self.camera_y = self.player.y - HEIGHT // 2
        
        
        self.cleanup_bullets()
    
    def cleanup_bullets(self):
        
        
        pass
    
    def game_over(self):
        print("Game Over...")
        
        self.player.stats['health'] = self.player.stats['max_health']
        self.player.x = WIDTH // 2
        self.player.y = HEIGHT // 2
        self.player_bullets.empty()
        self.enemy_bullets.empty()
    
    def draw(self):
        self.screen.fill(BLACK)
        
        
        self.world.draw(
            self.screen, 
            self.camera_x, 
            self.camera_y, 
            bullets_group=self.enemy_bullets, 
            current_time=self.current_time
        )

        
        if hasattr(self.world, 'draw_placeables'):
            self.world.draw_placeables(self.screen, self.camera_x, self.camera_y)
        
        
        inv = self.player.inventory

        if inv.table_crafting_open:
            
            inv.draw_crafting_table(self.screen)
        elif self.player.show_inventory:
            
            inv.draw(self.screen, show_inventory=True)
        else:
            
            inv.draw(self.screen, show_inventory=False)

        
        
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

        
        self.player.draw(self.screen, self.camera_x, self.camera_y)
        
        
        self.draw_hud()
        
        pygame.display.flip()

    
    def draw_hud(self):
        self.player.draw_status_bars(self.screen)
        self.player.update_status()
        
        """Dibujar interfaz de usuario"""
        
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
        
        
        instructions = [
            "WASD: Moverse",
            "Shift: Correr", 
            "ESPACIO: Disparar",
            "I: Inventario",
            "P: Poner",
            "ESC: Salir"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            self.screen.blit(text, (WIDTH - 200, 40 + i * 25))
            
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