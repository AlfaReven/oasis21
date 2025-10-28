# placeable.py
import pygame
import os
from constants import *

class Placeable:
    def __init__(self, x, y, object_type, image_filename):
        self.x = x
        self.y = y
        self.object_type = object_type
        self.size = GRASS
        self.image = self.load_image(image_filename)
        self.rect = self.image.get_rect(center=(x, y))
        self.is_interactable = True
        self.is_solid = True
        
    def load_image(self, filename):
        image_path = os.path.join('assets', 'images', filename)
        if os.path.exists(image_path):
            image = pygame.image.load(image_path).convert_alpha()
            return pygame.transform.scale(image, (self.size, self.size))
        else:
            # Placeholder
            surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(surface, (100, 100, 100, 128), (0, 0, self.size, self.size))
            return surface
    
    def is_near(self, obj):
        """Mismo método que Entities para consistencia"""
        return (abs(self.x - obj.x) <= max(ENTITY, obj.size) + 5 and
                abs(self.y - obj.y) <= max(ENTITY, obj.size) + 5)
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if (screen_x + self.size >= 0 and screen_x <= WIDTH and
            screen_y + self.size >= 0 and screen_y <= HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))
    
    def interact(self, player):
        return False

class CraftingTable(Placeable):
    def __init__(self, x, y):
        super().__init__(x, y, 'work_bench', 'work_bench.png')
        
    def interact(self, player):
        player.inventory.open_table_crafting()
        return True
