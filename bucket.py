import pygame
import os

class Bucket:
    def __init__(self):
        self.name = "bucket"
        self.has_water = False
        self.purity = 1.0  # 1.0 = completamente puro
        self.size = 64  # Tamaño para dibujo si es necesario
        self.load_images()
        
    def load_images(self):
        """Carga las imágenes para la cubeta llena y vacía"""
        try:
            self.empty_image = pygame.image.load(os.path.join('assets', 'items', 'bucket_empty.png')).convert_alpha()
            self.full_image = pygame.image.load(os.path.join('assets', 'items', 'bucket_full.png')).convert_alpha()
        except:
            # Fallback si no hay imágenes
            self.empty_image = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.full_image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(self.empty_image, (100, 100, 100), (0, 0, 32, 32))
            pygame.draw.rect(self.full_image, (0, 100, 255), (0, 0, 32, 32))
    
    def fill(self, purity=0.8):
        """Llena la cubeta con agua de cierta pureza"""
        self.has_water = True
        self.purity = purity
    
    def empty(self):
        """Vacía la cubeta"""
        self.has_water = False
        self.purity = 1.0
    
    def get_image(self):
        """Devuelve la imagen correspondiente al estado"""
        return self.full_image if self.has_water else self.empty_image
    
    def get_info(self):
        """Devuelve información del estado"""
        if self.has_water:
            return f"Cubeta con agua ({self.purity*100:.1f}% pura)"
        return "Cubeta vacía"
    
    def draw(self, screen, x, y):
        """Dibuja la cubeta en la interfaz"""
        image = self.get_image()
        screen.blit(image, (x, y))