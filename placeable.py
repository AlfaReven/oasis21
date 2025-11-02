# placeable.py
import pygame
import os
from constants import *
from inventory import *
import random

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
            screen.blit(self.image, (screen_x - self.rect.x, screen_y - self.rect.y))
    
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
        self.associated_well = None
        self.debug_timer = 0
        
        
        self.capacity = random.randint(30, 60)  # 30-60L capacidad
        self.remaining = random.randint(10, 40)  # 10-40L agua inicial
        self.recharge_rate = 0.02
        self.purity = random.uniform(0.6, 0.8)
        self.max_purity = 0.85
        
    

    def update(self, dt, world, player):
        """Extrae agua según la capacidad de las cubetas"""
        self.active = False
        
        # Depuración cada 5 segundos (no tan spam)
        self.debug_timer += dt
        if self.debug_timer > 5000:
            self.debug_timer = 0
            print(f"🔧 BOMBA - Pozos en mundo: {len(world.wells)}")
            print(f"🔧 BOMBA - Pozo asociado: {self.associated_well is not None}")
            if self.associated_well:
                print(f"🔧 BOMBA - Agua en pozo: {self.associated_well.remaining}L")
        
        if not self.associated_well:
            self._find_nearby_well(world)
            if self.associated_well:
                print(f"🔧 BOMBA - Conectada al pozo ({self.associated_well.remaining}L)")
        
        if not self.associated_well or self.associated_well.remaining <= 0:
            self.progress = 0
            return

        # Buscar cubetas que necesiten agua (en TODO el inventario)
        buckets_needing_water = []
        for item in player.inventory.all_items():
            if "bucket" in item.name and getattr(item, 'current_liters', 0) < getattr(item, 'max_liters', 20):
                buckets_needing_water.append(item)

        if not buckets_needing_water:
            self.progress = 0
            return

        # Bombeo activo
        self.active = True
        self.progress += dt / 5000  # 5 segundos por ciclo (más lento)

        if self.progress >= 1:
            self.progress = 0
            
            # Para cada cubeta que necesite agua
            for bucket in buckets_needing_water:
                if self.associated_well.remaining <= 0:
                    break
                    
                # Calcular cuánta agua puede recibir la cubeta
                space_in_bucket = bucket.max_liters - bucket.current_liters
                water_available = self.associated_well.remaining
                
                # Extraer solo lo que la cubeta puede almacenar (máximo 10L por ciclo)
                water_to_extract = min(space_in_bucket, water_available, 10)
                
                if water_to_extract > 0:
                    actual_water = self.associated_well.extract_water(water_to_extract)
                    water_added = bucket.add_water(actual_water)
                    print(f"💧 BOMBA - Añadió {water_added}L a cubeta ({bucket.current_liters}/{bucket.max_liters}L)")
                    
                    # Si el pozo se secó
                    if self.associated_well.remaining <= 0:
                        print("🏜️ BOMBA - ¡Pozo seco!")
                        break

    def _find_nearby_well(self, world):
        """Encuentra el pozo más cercano"""
        closest_well = None
        closest_distance = float('inf')
        
        for well in world.wells:
            distance = ((self.x - well.x) ** 2 + (self.y - well.y) ** 2) ** 0.5
            if distance < 100 and distance < closest_distance:  # 100 píxeles de radio
                closest_well = well
                closest_distance = distance
        
        self.associated_well = closest_well

    def draw(self, screen, camera_x, camera_y):
        """Dibuja la bomba con efectos visuales"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Solo dibujar si está en pantalla
        if (-self.size <= screen_x <= WIDTH and -self.size <= screen_y <= HEIGHT):
            # Dibujar la bomba
            screen.blit(self.image, (screen_x, screen_y))
            
            # Dibujar efectos visuales si está activa
            if self.active:
                # Barra de progreso
                bar_width = 60
                bar_height = 6
                bar_x = screen_x + (self.size - bar_width) // 2
                bar_y = screen_y - 15
                
                # Fondo de la barra
                pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
                
                # Progreso actual
                fill_width = int(bar_width * self.progress)
                pygame.draw.rect(screen, (0, 200, 255), (bar_x, bar_y, fill_width, bar_height))
                
                # Borde de la barra
                pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
                
                # Partículas de agua cuando está bombeando
                if random.random() < 0.3:  # 30% de probabilidad por frame
                    particle_x = screen_x + random.randint(10, self.size - 10)
                    particle_y = screen_y + random.randint(10, self.size - 10)
                    particle_size = random.randint(2, 4)
                    pygame.draw.circle(screen, (100, 200, 255), (particle_x, particle_y), particle_size)

    def interact(self, player):
        """Permite al jugador interactuar con la bomba"""
        if self.associated_well:
            status = "activa" if self.active else "inactiva"
            well_status = f"{self.associated_well.remaining}L" if self.associated_well.remaining > 0 else "seco"
            print(f"🔧 Bomba {status} - Pozo: {well_status}")
        else:
            print("🔧 Bomba desconectada - No hay pozo cercano")
        return True

    def is_near(self, obj):
        """Verifica si está cerca de otro objeto"""
        distance = ((self.x - obj.x) ** 2 + (self.y - obj.y) ** 2) ** 0.5
        return distance < max(self.size, getattr(obj, 'size', 0)) + 20
    
    

class WaterTank(Placeable):
    def __init__(self, x, y):
        super().__init__(x, y, 'empty_tank', 'empty_tank.png')
        
        # Tamaños
        self.size = 192               # tamaño visual
        self.collision_size = 128     # caja de colisión más pequeña
        self.capacity = 200
        self.current_water = 0
        self.purity = 1.0

        # Imagen inicial
        self.update_image()
        
        # ✅ Centrar correctamente la imagen y el rect
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect(center=(self.x, self.y))

        # ✅ Rectángulo de colisión centrado (más pequeño)
        self.collision_rect = pygame.Rect(0, 0, self.collision_size, self.collision_size)
        self.collision_rect.center = (self.x, self.y)


    def update_image(self):
        """Actualiza la imagen basado en el nivel de agua"""
        if self.current_water == 0:
            self.image = self.load_image("empty_tank.png")  # ✅ Vacío
        elif self.current_water < self.capacity * 0.8:
            self.image = self.load_image("tank_half.png")   # ✅ Medio lleno
        else:
            self.image = self.load_image("water_tank.png")  # ✅ Lleno
        
        if self.image.get_size() != (self.size, self.size):
            self.image = pygame.transform.scale(self.image, (self.size, self.size))

    def collect_rainwater(self, amount):
        """Recolecta agua de lluvia (más pura)"""
        if self.current_water >= self.capacity:
            return 0
            
        rainwater = min(amount, self.capacity - self.current_water)
        self.current_water += rainwater
        
        # El agua de lluvia es más pura (90-100%)
        rain_purity = random.uniform(0.9, 1.0)
        # Mezclar la pureza existente con la nueva
        if self.current_water > 0:
            self.purity = ((self.purity * (self.current_water - rainwater)) + 
                          (rain_purity * rainwater)) / self.current_water
        
        self.update_image()
        return rainwater

    def interact(self, player):
        """Permite llenar/vaciar cubetas y ver estado"""
        for item in player.inventory.all_items():
            if hasattr(item, 'name') and item.name == "bucket":
                # Vaciar cubeta en tanque
                if item.has_water and self.current_water < self.capacity:
                    water_amount = 10
                    transfer_amount = min(water_amount, self.capacity - self.current_water)
                    self.current_water += transfer_amount
                    
                    # Mezclar pureza
                    if self.current_water > 0:
                        self.purity = ((self.purity * (self.current_water - transfer_amount)) + 
                                    (item.purity * transfer_amount)) / self.current_water
                    
                    item.empty()
                    self.update_image()
                    print(f"💧 Cubeta vaciada en tanque ({self.current_water}/{self.capacity}L)")
                    return True
                
                # Llenar cubeta desde tanque
                elif not item.has_water and self.current_water >= 10:
                    self.current_water -= 10
                    item.fill(purity=self.purity)
                    self.update_image()
                    print(f"🪣 Cubeta llenada desde tanque ({self.current_water}/{self.capacity}L)")
                    return True

    def draw(self, screen, camera_x, camera_y):
        """Dibuja el tanque y su colisión (debug)"""
        screen_x = self.rect.x - camera_x
        screen_y = self.rect.y - camera_y

        # Dibuja la imagen del tanque (centrado correctamente)
        screen.blit(self.image, (screen_x, screen_y))

        # Dibuja barras si hay agua
        if self.current_water > 0:
            self.draw_status_bars(screen, screen_x, screen_y)

        # ✅ Dibuja colisión en rojo (debug)
        debug_rect = self.collision_rect.copy()
        debug_rect.x -= camera_x
        debug_rect.y -= camera_y
        pygame.draw.rect(screen, (255, 0, 0), debug_rect, 2)


    def draw_status_bars(self, screen, screen_x, screen_y):
        """Dibuja las barras de agua y pureza"""
        bar_width = self.size - 20
        bar_height = 8
        bar_margin = 5
        
        # Posición de las barras (arriba del tanque)
        bars_y = screen_y - 25
        
        # Barra de nivel de agua
        water_fill = self.current_water / self.capacity
        water_bar_bg = pygame.Rect(screen_x + 10, bars_y, bar_width, bar_height)
        water_bar_fill = pygame.Rect(screen_x + 10, bars_y, int(bar_width * water_fill), bar_height)
        
        # Barra de pureza
        purity_bar_bg = pygame.Rect(screen_x + 10, bars_y + bar_height + bar_margin, bar_width, bar_height)
        purity_bar_fill = pygame.Rect(screen_x + 10, bars_y + bar_height + bar_margin, 
                                    int(bar_width * self.purity), bar_height)
        
        # Dibujar barras
        pygame.draw.rect(screen, (50, 50, 50), water_bar_bg)  # Fondo agua
        pygame.draw.rect(screen, (0, 100, 255), water_bar_fill)  # Relleno agua
        
        pygame.draw.rect(screen, (50, 50, 50), purity_bar_bg)  # Fondo pureza
        purity_color = (0, 255, 100) if self.purity > 0.7 else (255, 200, 0) if self.purity > 0.3 else (255, 50, 0)
        pygame.draw.rect(screen, purity_color, purity_bar_fill)  # Relleno pureza
        
        # Etiquetas opcionales
        font = pygame.font.Font(None, 16)
        water_text = font.render(f"{int(water_fill * 100)}%", True, (255, 255, 255))
        purity_text = font.render(f"{int(self.purity * 100)}%", True, (255, 255, 255))
        
        screen.blit(water_text, (screen_x + 10, bars_y - 15))
        screen.blit(purity_text, (screen_x + 10, bars_y + bar_height + bar_margin - 15))

    def update(self, dt, world=None, player=None):
        """Actualización periódica (para evaporación, contaminación, etc.)"""
        # Pequeña evaporación
        if self.current_water > 0 and random.random() < 0.001:  # 0.1% de probabilidad por frame
            self.current_water = max(0, self.current_water - 1)
            if self.current_water == 0:
                self.update_image()
        
        # Pequeña pérdida de pureza con el tiempo
        if self.current_water > 0 and random.random() < 0.0005:  # 0.05% de probabilidad por frame
            self.purity = max(0.3, self.purity - 0.01)  # No baja del 30%