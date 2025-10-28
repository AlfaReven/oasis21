import pygame
from elements import Bullet
from constants import *

class Weapon:
    def __init__(self, name, damage, fire_rate, bullet_speed, range=1000):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate  
        self.bullet_speed = bullet_speed
        self.range = range
        self.last_shot = 0
        
    def can_shoot(self, current_time):
        return current_time - self.last_shot >= 1000 / self.fire_rate
    
    def shoot(self, x, y, direction, source, target_group, current_time):
        if self.can_shoot(current_time):
            self.last_shot = current_time
            return Bullet(x, y, direction, self.damage, source, target_group)
        return None

class RangedEnemy:
    def __init__(self, x, y, enemy_type="ranged"):
        super().__init__(x, y, f"enemy_{enemy_type}.png")
        self.weapon = Weapon("Pistol", 15, 1.5, 8)
        self.attack_range = RANGED_ATTACK_DISTANCE
        self.last_shot = 0
        
    def update(self, dt, player, obstacles, bullets_group, current_time):
        distance_to_player = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        
        if distance_to_player <= self.detection_range:
            if distance_to_player > self.attack_range:
    
                dx = player.x - self.x
                dy = player.y - self.y
                length = max((dx ** 2 + dy ** 2) ** 0.5, 0.1)
                dx /= length
                dy /= length
                self.move(dx * self.speed * 0.3, dy * self.speed * 0.3, obstacles)
            else:
    
                self.moving = False
                if distance_to_player <= self.attack_range and self.weapon.can_shoot(current_time):
                    self.shoot(player, bullets_group, current_time)
        
        self.update_animation(dt)
    
    def shoot(self, player, bullets_group, current_time):
        dx = player.x - self.x
        dy = player.y - self.y
        length = max((dx ** 2 + dy ** 2) ** 0.5, 0.1)
        
        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "down" if dy > 0 else "up"
        
        bullet = self.weapon.shoot(self.x, self.y, direction, self, [player], current_time)
        if bullet:
            bullets_group.add(bullet)
            
    