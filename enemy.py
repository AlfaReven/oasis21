import pygame
from constants import *
from entities import Entities
import random
from weapons import Weapon

class Enemy(Entities):
    def __init__(self, x, y, enemy_type="basic"):
        super().__init__(x, y, "Player.png")
        
        
        if enemy_type == "basic":
            self.stats.update({
                'force': BASE_FORCE - 2,
                'health': MAX_HEALTH - 98,
                'max_health': MAX_HEALTH,
                'experience_value': 10
            })
        elif enemy_type == "strong":
            self.stats.update({
                'force': BASE_FORCE + 3,
                'health': MAX_HEALTH -98,
                'max_health': MAX_HEALTH,
                'experience_value': 25
            })
        
        self.enemy_type = enemy_type
        self.attack_cooldown = 0
        self.detection_range = RANGED_ATTACK_DISTANCE  
    
    def update(self, dt, player, obstacles):
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        
        distance_to_player = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        
        
        if distance_to_player <= self.detection_range:
            
            dx = player.x - self.x
            dy = player.y - self.y
            
            
            length = max((dx ** 2 + dy ** 2) ** 0.5, 0.1)
            dx /= length
            dy /= length
            
            
            self.move(dx * self.speed * 0.5, dy * self.speed * 0.5, obstacles)
            
            
            if distance_to_player <= self.melee_attack and self.attack_cooldown <= 0:
                self.attack(player)
                self.attack_cooldown = 1000  
        else:
            self.moving = False
        
        
        self.update_animation(dt)
        
    
    
    def attack(self, player):
        damage = player.take_damage(self, 'melee')
        return damage
    
    def drop_loot(self):
        
        loot_chance = random.random()
        if loot_chance > 0.7:  
            return "wood"
        elif loot_chance > 0.9:  
            return "stone"
        return None


class RangedEnemy(Enemy):  
    def __init__(self, x, y, enemy_type="ranged"):
        
        super().__init__(x, y, enemy_type)
        
        
        self.stats.update({
            'force': BASE_FORCE - 3,  
            'health': MAX_HEALTH - 98,
            'max_health': MAX_HEALTH,
            'weapon_skill': BASE_WEAPON_SKILL + 10,  
            'experience_value': 20
        })
        
        self.weapon = Weapon("Pistol", 15, 1.5, 8)
        self.attack_range = RANGED_ATTACK_DISTANCE
        self.detection_range = RANGED_ATTACK_DISTANCE + 100
        self.last_shot = 0
        
    def update(self, dt, player, obstacles, bullets_group, current_time):
        """Actualización para enemigos a distancia"""
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        
        distance_to_player = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        
        
        if distance_to_player <= self.detection_range:
            if distance_to_player > self.attack_range:
                
                dx = player.x - self.x
                dy = player.y - self.y
                length = max((dx ** 2 + dy ** 2) ** 0.5, 0.1)
                dx /= length
                dy /= length
                self.move(dx * self.speed * 0.3, dy * self.speed * 0.3, obstacles)
                self.moving = True
            else:
                
                self.moving = False
                if distance_to_player <= self.attack_range and self.weapon.can_shoot(current_time):
                    self.shoot(player, bullets_group, current_time)
        else:
            self.moving = False
        
        
        self.update_animation(dt)
        
        
    
    def update_with_bullets(self, dt, player, obstacles, bullets_group, current_time):
        """Método alternativo para compatibilidad con World"""
        self.update(dt, player, obstacles, bullets_group, current_time)
    
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
    
    
    def attack(self, player):
        pass