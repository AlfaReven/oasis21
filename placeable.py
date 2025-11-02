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
        
        
        # Si no tenemos mineral o combustible, detener
        if not has_mineral or not has_fuel:
            if self.burning:
                self.burning = False
                self.timer = 0
            return
        
        # Si tenemos ambos, empezar/continuar quemando
        if not self.burning:
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
            
            # Si no hay más mineral, detener
            if not self.input_slot or self.input_slot.quantity <= 0:
                self.burning = False
              



class WaterPump(Placeable):
    def __init__(self, x, y):
        super().__init__(x, y, 'pump', 'pump.png')
        self.size = GRASS * 2
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect(center=(x, y))
        self.active = False
        self.progress = 0.0

    def update(self, dt, world, player):
        """Extrae agua si hay un pozo cerca y una cubeta disponible."""
        self.active = False
        near_well = None

        # Buscar pozo cercano
        for well in world.wells:
            dx = abs(well.x - self.x)
            dy = abs(well.y - self.y)
            if dx < self.size and dy < self.size:
                near_well = well
                break

        # Si no hay pozo, reinicia progreso
        if not near_well or near_well.remaining <= 0:
            self.progress = 0
            return

        # Verificar si Eduardo tiene cubeta (en manos o inventario)
        has_bucket = any(
            "bucket" in item.name and getattr(item, "fill_level", 0) < 2
            for item in player.inventory.all_items()
        )

        if not has_bucket:
            self.progress = 0
            return  # No hay cubetas vacías o medias, no bombea

        # Activar la bomba
        self.active = True
        self.progress += dt / 2000  # ≈2 s por ciclo

        # Si completó el ciclo de bombeo
        if self.progress >= 1:
            self.progress = 0
            near_well.remaining = max(0, near_well.remaining - int(near_well.capacity / 2))

            # Llenar una cubeta
            for item in player.inventory.all_items():
                if "bucket" in item.name and getattr(item, "fill_level", 0) < 2:
                    item.fill()
                    print("💧 La bomba llenó una cubeta con agua limpia.")
                    break

            # Si todas las cubetas están llenas
            else:
                print("🚫 Todas las cubetas ya están llenas.")

    def draw(self, screen, camera_x, camera_y):
        """Dibuja la bomba y una barra de progreso cuando está activa."""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        screen.blit(self.image, (screen_x, screen_y))

        # Si está activa, dibujar barra azul
        if self.active:
            bar_width = int(self.size * 0.8)
            bar_height = 8
            bar_x = screen_x + (self.size - bar_width) // 2
            bar_y = screen_y - 15

            # Fondo gris
            pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
            # Progreso azul
            fill_width = int(bar_width * self.progress)
            pygame.draw.rect(screen, (0, 180, 255), (bar_x, bar_y, fill_width, bar_height))
