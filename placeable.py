# placeable.py
import pygame
import os
from constants import *
from inventory import *

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


class Furnace(Placeable):
    def __init__(self, x, y):
        super().__init__(x, y, 'furnace', 'furnace.png')
        self.input_slot = None
        self.fuel_slot = None
        self.output_slot = None
        self.fuel_remaining = 0
        self.max_fuel_time = 30  # 30 segundos por madera
        self.burning = False
        self.timer = 0
        self.smelting_time = 3000  # 3 segundos por mineral

    def interact(self, player):
        # 🔥 Abre la interfaz del horno
        player.inventory.active_furnace = self
        player.inventory.furnace_open = True
        print("🔥 Horno abierto para fundir minerales")
        return True

    def add_fuel(self, item):
        """Carga combustible (solo madera)."""
        if item and item.name == "wood":
            self.fuel_remaining += self.max_fuel_time
            self.burning = True
            print(f"🔥 Combustible cargado: +{self.max_fuel_time}s (Total: {self.fuel_remaining:.1f}s)")
            return True
        return False

    def update(self, dt):
        """Procesa fundición - dt en milisegundos"""
        print(f"🔥 Horno update - Input: {self.input_slot}, Fuel: {self.fuel_slot}, Burning: {self.burning}")
        
        if self.input_slot:
            print(f"   Input: {self.input_slot.name} x{self.input_slot.quantity}")
        if self.fuel_slot:
            print(f"   Fuel: {self.fuel_slot.name} x{self.fuel_slot.quantity}")
        
        # Verificar si tenemos combustible y material
        has_mineral = (self.input_slot and 
                    self.input_slot.name == "mineral_iron" and 
                    self.input_slot.quantity > 0)
        
        has_fuel = (self.fuel_slot and 
                    self.fuel_slot.name == "wood" and 
                    self.fuel_slot.quantity > 0)
        
        print(f"   Has mineral: {has_mineral}, Has fuel: {has_fuel}")
        
        # Si no tenemos mineral o combustible, detener
        if not has_mineral or not has_fuel:
            if self.burning:
                print("❌ Horno detenido - falta mineral o combustible")
                self.burning = False
                self.timer = 0
            return
        
        # Si tenemos ambos, empezar/continuar quemando
        if not self.burning:
            print("🔥 Horno encendido - empezando fundición")
            self.burning = True
        
        # Reducir combustible (convertir dt a segundos)
        dt_seconds = dt / 1000.0
        self.fuel_remaining -= dt_seconds
        
        if self.fuel_remaining <= 0:
            # Consumir una madera del fuel_slot
            self.fuel_slot.quantity -= 1
            if self.fuel_slot.quantity <= 0:
                self.fuel_slot = None
            else:
                # Recargar combustible
                self.fuel_remaining = self.max_fuel_time
                print(f"🔥 Nueva madera consumida. Combustible: {self.fuel_remaining}s")
        
        # Procesar fundición
        self.timer += dt
        if self.timer >= self.smelting_time:
            self.timer = 0  # Reiniciar temporizador
            
            # Reducir mineral
            self.input_slot.quantity -= 1
            if self.input_slot.quantity <= 0:
                self.input_slot = None
            
            # Crear o aumentar hierro
            if not self.output_slot:
                self.output_slot = InventoryItem(
                    "ingot_iron", 
                    os.path.join("assets", "images", "ingot_iron.png"), 
                    1
                )
            else:
                self.output_slot.quantity += 1
            
            print(f"✅ Mineral fundido → Hierro obtenido! (Total: {self.output_slot.quantity})")
            
            # Si no hay más mineral, detener
            if not self.input_slot or self.input_slot.quantity <= 0:
                self.burning = False
                print("🏁 Fundición completada - sin más mineral")