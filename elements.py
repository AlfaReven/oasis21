import pygame
import constants
import os
from constants import *
import math

class Tree:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.wood = 5
        
        tree_path = os.path.join('assets', 'images', 'tree.png')
        self.image = pygame.image.load(tree_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (constants.TREE, constants.TREE))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.size = self.image.get_width()
        
    def draw(self, screen, camera_x, camera_y):
        #CALCULAR LA POSICION EN LA PANTLLA RELATIVA A LA CAMARA
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        
        #solo vamos a dibujarlos si esta en pantalla para que no se muera la raspberry
        if (screen_x + self.size >= 0 and screen_x <= constants.WIDTH and
            screen_y + self.size >= 0 and screen_y <= constants.HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))
            
    
    def chop(self, with_axe=False):
        if self.wood > 0:
            if with_axe:
                self.wood -= 2
                if self.wood < 0:
                    self.wood = 0
            else:
                self.wood -= 1
            return True
        return False
    
    def is_depleted(self):
        return self.wood <= 0
        

class Smallstone:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.stone = 1
        
        small_stone_path = os.path.join('assets', 'images', 'small_stone.png')
        self.image = pygame.image.load(small_stone_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (constants.SMALL_STONE, constants.SMALL_STONE))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.size = self.image.get_width()
    
    def draw(self, screen, camera_x, camera_y):
        #hcaemos lo mismo que hicimos en la clase Tree
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        if (screen_x + self.size >= 0 and screen_x <= constants.WIDTH and
            screen_y + self.size >= 0 and screen_y <= constants.HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))

    def collect(self):
        if self.stone > 0:
            self.stone -= 1
            return True
        return False   
    
    def is_depleted(self):
        return self.stone <= 0
    
class MineralIron:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mineral_iron = 5
        
        
        mineral_iron_path = os.path.join('assets', 'images', 'iron_tile.png')
        self.image = pygame.image.load(mineral_iron_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (constants.MINERAL_IRON, constants.MINERAL_IRON))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.size = self.image.get_width()
    
    def draw(self, screen, camera_x, camera_y):
        #hcaemos lo mismo que hicimos en la clase Tree
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        if (screen_x + self.size >= 0 and screen_x <= constants.WIDTH and
            screen_y + self.size >= 0 and screen_y <= constants.HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))

    def collect(self):
        if self.mineral_iron > 0:
            self.mineral_iron -= 1
            return True
        return False   
    
    def is_depleted(self):
        return self.mineral_iron <= 0


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, power, source, target_group):
        super().__init__()
        self.x = x
        self.y = y
        self.speed = BASE_BULLET_SPEED
        self.damage = power
        self.direction = direction  # Dirección original
        self.source = source
        self.target_group = target_group
        self.lifetime = BULLET_LIFETIME
        self.created_time = pygame.time.get_ticks()
        
        # GUARDAR LA DIRECCIÓN REAL EN EL MOMENTO DEL DISPARO
        self.fixed_direction = self.calculate_fixed_direction(direction, source)
        
        # Crear superficie para la bala
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (4, 4), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(self.x - 4, self.y - 4, 8, 8)

    def calculate_fixed_direction(self, direction, source):
        """Calcular y guardar la dirección fija en el momento del disparo"""
        if direction == "right" or direction == WALK_RIGHT:
            if hasattr(source, 'facing_left') and source.facing_left:
                return "left"  # Disparo hacia la izquierda
            else:
                return "right"  # Disparo hacia la derecha
        elif direction == "left":
            return "left"
        elif direction == "up" or direction == WALK_UP:
            return "up"
        elif direction == "down" or direction == WALK_DOWN:
            return "down"
        return direction  # Fallback

    def update(self, dt):
        # Mover la bala usando la dirección FIJADA en el momento del disparo
        move_speed = self.speed * (dt / 16.0)
        
        # Usar fixed_direction en lugar de verificar source.facing_left cada frame
        if self.fixed_direction == "right":
            self.x += move_speed
        elif self.fixed_direction == "left":
            self.x -= move_speed
        elif self.fixed_direction == "up":
            self.y -= move_speed
        elif self.fixed_direction == "down":
            self.y += move_speed

        # Actualizar rectángulos
        self.rect.center = (self.x, self.y)
        self.hitbox.center = (self.x, self.y)
        
        # Reducir tiempo de vida
        current_time = pygame.time.get_ticks()
        if current_time - self.created_time > self.lifetime:
            self.kill()
            return

        # Detectar colisiones
        for entity in self.target_group:
            if (hasattr(entity, 'rect') and 
                self.hitbox.colliderect(entity.rect) and 
                entity != self.source):
                
                damage = entity.take_damage(self.source, 'ranged')
                print(f"Bala impacta a {entity.__class__.__name__}! Daño: {damage}")
                self.kill()  
                break

class FarmLand:
    def __init__(self, x , y):
        self.x = x
        self.y = y
        
        farmland_path = os.path.join('assets', 'images', 'farmland.png')
        self.image = pygame.image.load(farmland_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (constants.GRASS, constants.GRASS))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.size = self.image.get_width()
        
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if (screen_x + self.size >= 0 and screen_x <= WIDTH and
            screen_y + self.size >= 0 and screen_y <= HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))
            
class Water:
    def __init__(self, x, y, is_flowing = False):
        self.x = x
        self.y = y
        self.is_flowing = is_flowing
        self.is_drinkable = True
        self.size = GRASS
        
        #parametros para animacion simple de movimiento
        self.animation_frame = 0
        self.animation_timer = 0
    
    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer > 500:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if (screen_x + self.size >= 0 and screen_x <= WIDTH and
            screen_y + self.size >= 0 and screen_y <= HEIGHT):
            water_rect = pygame.Rect(screen_x, screen_y, self.size, self.size)
            offset_y = math.sin(self.animation_frame * math.pi / 2) * 2
            pygame.draw.rect(screen, WATER_COLOR, pygame.Rect(screen_x, screen_y, self.size, self.size))
            
        