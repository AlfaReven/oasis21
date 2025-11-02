import pygame
from constants import *
from entities import Entities
import random
from inventory import Inventory
import os
from world import *
from placeable import CraftingTable, WaterPump, WaterTank
from minigame_well import *

class Player(Entities):
    def __init__(self, x, y, player_id=0, control_type="keyboard", joypad_id=0):
        super().__init__(x, y, "Player.png")  
        
        # Atributos para multijugador
        self.player_id = player_id
        self.control_type = control_type
        self.joypad_id = joypad_id
        
        self.stats.update({
            'force': BASE_FORCE * 10,  
            'health': MAX_HEALTH,
            'max_health': MAX_HEALTH,
            'coins': 0,
            'experience': 0,
            'level': 1
        })
        
        # Sistema de inventario
        self.inventory = Inventory()
        self._give_starter_items()
        
        self.show_inventory = False
        
        # Atributos de supervivencia
        self.energy = MAX_ENERGY
        self.food = MAX_FOOD
        self.thirst = MAX_THIRST
        self.stamina = MAX_STAMINA
        
        self.font = pygame.font.Font(None, 24)
        
        # Animaciones de herramientas
        self.action_sprite_sheet = pygame.image.load(os.path.join('assets', 'images', 'Player_Actions.png')).convert_alpha()

        # Propiedades para animaciones especiales
        self.special_animation = False  
        self.animation_type = None      
        self.special_animation_frame = 0
        self.special_animation_timer = 0
        self.special_animation_delay = AXE_ANIMATION_DELAY
        self.tool_animations = self.load_tool_animations()
        
        # Color diferente para cada jugador
        self._apply_player_color()
    
    def _apply_player_color(self):
        """Aplica color distintivo para cada jugador"""
        color_filter = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
        if self.player_id == 0:
            color_filter.fill((0, 0, 255, 50))
        else:
            color_filter.fill((255, 100, 0, 50))
        self.image.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _give_starter_items(self):
        """Provee materiales iniciales al jugador"""
        starter_items = {
            'wood': 5,
            'stone': 5,
            'mineral_iron': 3,
            'bucket': 1,
            'pump': 1,
            'empty_tank': 1,
        }

        for item_name, qty in starter_items.items():
            self.inventory.add_item(item_name, qty)
    
    # === SISTEMA DE ANIMACIONES ===
    def load_tool_animations(self):
        """Carga las animaciones de herramientas"""
        animations = {}
        tool_rows = {
            'axe': {
                'right': 3,
                'down': 4,  
                'up': 5     
            }
        }
        
        for tool_name, directions in tool_rows.items():
            animations[tool_name] = {}
            for direction, row in directions.items():
                animations[tool_name][direction] = self._load_tool_frames(row)
        
        return animations

    def _load_tool_frames(self, row):
        """Carga los frames de animación para una herramienta"""
        frames = []
        for frame in range(AXE_FRAMES):
            temp_surface = pygame.Surface((ACTION_FRAME_SIZE, ACTION_FRAME_SIZE), pygame.SRCALPHA)
            x = (frame % AXE_COLS) * ACTION_FRAME_SIZE
            frame_rect = pygame.Rect(x, row * ACTION_FRAME_SIZE, ACTION_FRAME_SIZE, ACTION_FRAME_SIZE)
            temp_surface.blit(self.action_sprite_sheet, (0, 0), frame_rect)
        
            entity_scale = ENTITY / FRAME_SIZE  
            action_size = int(ACTION_FRAME_SIZE * entity_scale) 
            scaled_temp = pygame.transform.scale(temp_surface, (action_size, action_size))
            surface = pygame.Surface((ENTITY, ENTITY), pygame.SRCALPHA)
            
            offset_x = (ENTITY - action_size) // 2
            offset_y = (ENTITY - action_size) // 2
            
            surface.blit(scaled_temp, (offset_x, offset_y))
            frames.append(surface)
        
        return frames

    def start_axe_animation(self):
        """Inicia la animación del hacha"""
        self.special_animation = True
        self.animation_type = 'axe'
        self.special_animation_frame = 0
        self.special_animation_timer = pygame.time.get_ticks()
        self.moving = False
    
    def update_special_animation(self, dt):
        """Actualiza animaciones especiales"""
        if not self.special_animation:
            return
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.special_animation_timer > self.special_animation_delay:
            self.special_animation_timer = current_time
            self.special_animation_frame += 1
            
            if self.special_animation_frame >= AXE_FRAMES:
                self.special_animation = False
                self.animation_type = None
                self.special_animation_frame = 0

    def get_special_animation_frame(self):
        """Obtiene el frame actual de animación especial"""
        if not self.special_animation or self.animation_type not in self.tool_animations:
            return None
            
        direction = self._get_animation_direction()
        if direction in self.tool_animations[self.animation_type]:
            frame = self.tool_animations[self.animation_type][direction][self.special_animation_frame]
            
            if self.facing_left and direction == 'right':
                frame = pygame.transform.flip(frame, True, False)
                
            return frame
        
        return None

    def _get_animation_direction(self):
        """Determina la dirección para la animación"""
        if self.current_state in [IDLE_RIGHT, WALK_RIGHT]:
            return 'right'
        elif self.current_state in [IDLE_DOWN, WALK_DOWN]:
            return 'down'
        elif self.current_state in [IDLE_UP, WALK_UP]:
            return 'up'
        else:
            return 'right'

    def update_animation(self, dt):
        """Actualiza las animaciones"""
        if self.special_animation:
            self.update_special_animation(dt)
            special_frame = self.get_special_animation_frame()
            if special_frame:
                self.image = special_frame
                self.rect = self.image.get_rect(center=(self.x, self.y))
            return
        super().update_animation(dt)
    
    # === SISTEMA DE RENDERIZADO ===
    def draw(self, screen, camera_x, camera_y):
        """Dibuja al jugador en pantalla"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        current_image = self.image
        
        if not self.special_animation and self.facing_left:
            current_image = pygame.transform.flip(current_image, True, False)
        
        screen.blit(current_image, (screen_x, screen_y))
        self._draw_player_label(screen, screen_x, screen_y)

    def _draw_player_label(self, screen, screen_x, screen_y):
        """Dibuja la etiqueta del jugador"""
        player_text = self.font.render(f"P{self.player_id + 1}", True, (255, 255, 255))
        screen.blit(player_text, (screen_x, screen_y - 20))
    
    # === SISTEMA DE MOVIMIENTO ===
    def update(self, dt, obstacles):
        """Actualiza el estado del jugador"""
        if self.special_animation:
            self.moving = False
            return
            
        if self.control_type == "keyboard":
            self.handle_keyboard_input(dt, obstacles)
        else:
            self.handle_joypad_input(dt, obstacles)

    def handle_keyboard_input(self, dt, obstacles):
        """Maneja entrada de teclado"""
        keys = pygame.key.get_pressed()
        
        self.is_running = self._get_run_state(keys)
        current_speed = self.speed * 2 if self.is_running else self.speed

        dx, dy = self._get_movement_direction(keys)
        
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        if dx != 0 or dy != 0:
            self.move(dx * current_speed, dy * current_speed, obstacles)
        else:
            self._set_idle_state()

    def _get_run_state(self, keys):
        """Determina si el jugador está corriendo"""
        if self.player_id == 0:
            return keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        else:
            return keys[pygame.K_RCTRL]

    def _get_movement_direction(self, keys):
        """Obtiene la dirección del movimiento desde el teclado"""
        dx, dy = 0, 0
        
        if self.player_id == 0:
            if keys[pygame.K_w]: dy = -5
            if keys[pygame.K_s]: dy = 5
            if keys[pygame.K_a]: dx = -5
            if keys[pygame.K_d]: dx = 5
        else:
            if keys[pygame.K_UP]: dy = -5
            if keys[pygame.K_DOWN]: dy = 5
            if keys[pygame.K_LEFT]: dx = -5
            if keys[pygame.K_RIGHT]: dx = 5
        
        return dx, dy

    def _set_idle_state(self):
        """Establece el estado de reposo del jugador"""
        self.moving = False
        if self.current_state == WALK_DOWN:
            self.current_state = IDLE_DOWN
        elif self.current_state == WALK_UP:
            self.current_state = IDLE_UP
        elif self.current_state == WALK_RIGHT:
            self.current_state = IDLE_RIGHT

    # === SISTEMA DE INTERACCIÓN ===
    def interact(self, world):
        """Interacción básica con el mundo"""
        if self.special_animation:
            return
            
        if pygame.key.get_pressed()[pygame.K_t]:
            world.add_farmland(self.x, self.y) 
            return
        
        return self._interact_with_resources(world)

    def _interact_with_resources(self, world):
        """Interactúa con recursos del mundo"""
        interactions = [
            (world.trees, 'wood', True),
            (world.small_stones, 'stone', False),
            (world.iron_minerals, 'mineral_iron', False),
            (world.copper_minerals, 'mineral_copper', False)
        ]
        
        for resource_list, item_name, requires_axe in interactions:
            for resource in resource_list:
                if self.is_near(resource):
                    return self._handle_resource_interaction(resource, item_name, requires_axe)
        
        # Interacción con pozos
        for well in world.wells:
            if self.is_near(well):
                return self._handle_well_interaction(well, world)
        
        return False

    def _handle_resource_interaction(self, resource, item_name, requires_axe):
        """Maneja la interacción con un recurso específico"""
        if requires_axe:
            has_tool = self.inventory.has_axe_equipped()
            if has_tool:
                self.start_axe_animation()
            if resource.chop(with_axe=has_tool):
                cantidad = 2 if has_tool else 1
                self.inventory.add_item(item_name, cantidad)
                return True
        else:
            if resource.collect():
                self.inventory.add_item(item_name)
                return True
        return False

    def _handle_well_interaction(self, well, world):
        """Maneja la interacción con pozos"""
        if self.inventory.has_item_equipped("pump"):
            return self._handle_pump_placement(well, world)
        
        bucket = self._get_equipped_bucket()
        if bucket:
            start_well_minigame(self, well, bucket)
            return True
        
        # Mostrar información del pozo
        status, percentage = well.get_water_status()
        return True

    def _handle_pump_placement(self, well, world):
        """Coloca bomba en el pozo"""
        # Verificar si ya hay bomba en este pozo
        for obj in world.placeable_objects:
            if hasattr(obj, 'object_type') and obj.object_type == 'pump':
                dx = abs(obj.x - well.x)
                dy = abs(obj.y - well.y)
                if dx < 50 and dy < 50:
                    return False
        
        # Colocar bomba
        if world.add_placeable("pump", well.x, well.y):
            self.inventory.remove_item("pump", 1)
            return True
        return False

    def _get_equipped_bucket(self):
        """Obtiene la cubeta equipada en las manos"""
        if self.inventory.right_hand and "bucket" in self.inventory.right_hand.name:
            return self.inventory.right_hand
        elif self.inventory.left_hand and "bucket" in self.inventory.left_hand.name:
            return self.inventory.left_hand
        return None

    def interact_with_objects(self, world):
        """Interactúa con objetos cercanos"""
        if self.special_animation:
            return False

        # Buscar objetos colocables
        for obj in world.placeable_objects:
            if self._is_object_in_range(obj, 150) and hasattr(obj, 'interact'):
                if obj.interact(self):
                    return True

        # Buscar pozos
        for well in world.wells:
            if self._is_object_in_range(well, 150):
                return self._handle_well_interaction(well, world)

        return False

    def _is_object_in_range(self, obj, range_distance):
        """Verifica si un objeto está dentro del rango de interacción"""
        distance = ((self.x - obj.x) ** 2 + (self.y - obj.y) ** 2) ** 0.5
        return distance <= range_distance

    def use_bucket(self, world):
        """Usar cubeta para recoger agua o interactuar con tanques"""
        bucket = self._get_equipped_bucket()
        if not bucket:
            return False
        
        # Llenar cubeta de agua del suelo
        if world.is_water_at(self.x, self.y):
            if not getattr(bucket, 'has_water', False):
                bucket.fill()
                return True
        
        # Interactuar con tanques cercanos
        nearby_tank = world.get_nearby_placeable(self)
        if nearby_tank and hasattr(nearby_tank, 'water_tank'):
            return nearby_tank.interact(self)
        
        return False

    def drink_water(self):
        """Permite beber agua desde cubetas con agua, ya sea equipadas o en el inventario."""
        # 1️⃣ Primero buscar si tiene cubeta equipada
        bucket = self._get_equipped_bucket()
        if bucket and getattr(bucket, "has_water", False):
            self.update_thirst(+30)
            bucket.empty()
            print("💧 Bebiendo agua desde cubeta equipada.")
            return True

        # 2️⃣ Si no hay cubeta equipada, buscar en hotbar e inventario
        for slot in self.inventory.hotbar + [s for row in self.inventory.inventory for s in row]:
            if slot and "bucket" in slot.name and getattr(slot, "has_water", False):
                self.update_thirst(+30)
                slot.empty()
                print("💧 Bebiendo agua desde cubeta en inventario.")
                return True

        # 3️⃣ Si no hay cubeta con agua en ningún lado
        print("⚠️ No tienes cubeta con agua.")
        return False


    # === SISTEMA DE COLOCACIÓN Y RECOGIDA ===
    def place_object(self, world):
        """Coloca objetos en el mundo - MEJORADO para objetos grandes"""
        if self.special_animation:
            return False
            
        item_to_place = self._get_item_to_place()
        if not item_to_place:
            return False

        # Para objetos grandes, aumentar la distancia de colocación
        place_distance = 96 if item_to_place == 'water_tank' else 60
        
        place_x, place_y = self._get_placement_position(place_distance)
        
        if hasattr(world, 'add_placeable'):
            success = world.add_placeable(item_to_place, place_x, place_y)
            if success:
                self._remove_equipped_item()
                return True
                
        return False

    def _get_placement_position(self, place_distance):
        """Calcula la posición de colocación basada en la dirección"""
        if self.current_state in [IDLE_RIGHT, WALK_RIGHT]:
            if self.facing_left:
                return self.x - place_distance, self.y
            else:
                return self.x + place_distance, self.y
        elif self.current_state in [IDLE_DOWN, WALK_DOWN]:
            return self.x, self.y + place_distance
        elif self.current_state in [IDLE_UP, WALK_UP]:
            return self.x, self.y - place_distance
        else:
            return self.x + place_distance, self.y
            return False

    def _get_item_to_place(self):
        """Obtiene el item a colocar de las manos equipadas"""
        if self.inventory.right_hand:
            return self.inventory.right_hand.name
        elif self.inventory.left_hand:
            return self.inventory.left_hand.name
        return None

    def _remove_equipped_item(self):
        """Remueve el item equipado después de colocarlo"""
        if self.inventory.right_hand:
            self.inventory.right_hand = None
        else:
            self.inventory.left_hand = None

    def pick_placeable(self, world):
        """Recoge un objeto colocado cercano"""
        for obj in world.placeable_objects[:]:
            if self._is_object_in_range(obj, 64):
                item_name = self._get_placeable_item_name(obj)
                if self._can_add_to_inventory(item_name):
                    self.inventory.add_item(item_name, 1)
                    world.placeable_objects.remove(obj)
                    return True
        return False

    def _get_placeable_item_name(self, obj):
        """Obtiene el nombre del item basado en el objeto colocable"""
        if hasattr(obj, 'object_type'):
            item_name = obj.object_type
        else:
            item_name = obj.__class__.__name__.lower()
        
        item_mapping = {
            'pump': 'pump',
            'water_tank': 'water_tank', 
            'work_bench': 'work_bench',
            'furnace': 'furnace'
        }
        
        return item_mapping.get(item_name, item_name)

    def _can_add_to_inventory(self, item_name):
        """Verifica si se puede añadir el item al inventario"""
        if item_name in self.inventory.stackable_items:
            return self._has_stack_space(item_name) or self._has_empty_slots()
        else:
            return self._has_empty_slots()

    def _has_stack_space(self, item_name):
        """Verifica si hay espacio en stacks existentes"""
        max_stack = self.inventory.stackable_items[item_name]
        
        # Buscar en hotbar
        for slot in self.inventory.hotbar:
            if slot and slot.name == item_name and slot.quantity < max_stack:
                return True
                
        # Buscar en inventario principal
        for row in self.inventory.inventory:
            for slot in row:
                if slot and slot.name == item_name and slot.quantity < max_stack:
                    return True
        return False

    def _has_empty_slots(self):
        """Verifica si hay slots vacíos"""
        hotbar_empty = any(slot is None for slot in self.inventory.hotbar)
        inventory_empty = any(slot is None for row in self.inventory.inventory for slot in row)
        return hotbar_empty or inventory_empty

    # === SISTEMA DE SUPERVIVENCIA ===
    def update_energy(self, amount):
        self.energy = max(0, min(self.energy + amount, MAX_ENERGY))
    
    def update_food(self, amount):
        self.food = max(0, min(self.food + amount, MAX_FOOD))
        
    def update_thirst(self, amount):
        self.thirst = max(0, min(self.thirst + amount, MAX_THIRST))

    def update_stamina(self, amount):
        self.stamina = max(0, min(self.stamina + amount, MAX_STAMINA))
    
    def update_health(self, amount):
        self.stats['health'] = max(0, min(self.stats['health'] + amount, MAX_HEALTH))
        
    def draw_status_bars(self, screen):
        """Dibuja las barras de estado del jugador"""
        bar_width = 100
        bar_height = 10
        x_offset = 10
        y_offset = 50 + (self.player_id * 80)
        
        self._draw_player_label_status(screen, x_offset, y_offset)
        self._draw_status_bar(screen, x_offset, y_offset, bar_width, bar_height, 
                             self.energy / MAX_ENERGY, ENERGY_COLOR, "Energía")
        self._draw_status_bar(screen, x_offset, y_offset + 15, bar_width, bar_height,
                             self.food / MAX_FOOD, FOOD_COLOR, "Comida")
        self._draw_status_bar(screen, x_offset, y_offset + 30, bar_width, bar_height,
                             self.thirst / MAX_THIRST, THIRST_COLOR, "Sed")
        self._draw_status_bar(screen, x_offset, y_offset + 45, bar_width, bar_height,
                             self.stamina / MAX_STAMINA, STAMINA_COLOR, "Stamina")

    def _draw_player_label_status(self, screen, x, y):
        """Dibuja la etiqueta del jugador para el HUD"""
        player_label = self.font.render(f"Jugador {self.player_id + 1}", True, 
                                      (0, 100, 255) if self.player_id == 0 else (255, 100, 0))
        screen.blit(player_label, (x, y - 20))

    def _draw_status_bar(self, screen, x, y, width, height, ratio, color, label):
        """Dibuja una barra de estado individual"""
        pygame.draw.rect(screen, BAR_BACKGROUND, (x, y, width, height))
        pygame.draw.rect(screen, color, (x, y, width * ratio, height))
        
    def update_status(self):
        """Actualiza el estado de supervivencia del jugador"""
        food_rate = FOOD_DECREASE_RATE * (RUN_FOOD_DECREASE_MULTIPLER if self.is_running else 1)
        thirst_rate = THIRST_DECREASE_RATE * (RUN_THIRST_DECREASE_MULTIPLER if self.is_running else 1)
            
        self.update_food(-food_rate)
        self.update_thirst(-thirst_rate)
                 
        if self.food < MAX_FOOD * 0.2 or self.thirst < MAX_THIRST * 0.2:
            self.update_energy(-ENERGY_DECREASE_RATE)
        else:
            self.update_energy(ENERGY_INCREASE_RATE)
            
        if not self.is_running:
            self.update_stamina(STAMINA_INCREASE_RATE)

    # === SISTEMA DE EXPERIENCIA ===
    def add_experience(self, exp):
        self.stats['experience'] += exp
        if self.stats['experience'] >= self.stats['level'] * 100:
            self.level_up()
    
    def level_up(self):
        self.stats['level'] += 1
        self.stats['experience'] = 0
        self.stats['max_health'] += 10
        self.stats['health'] = self.stats['max_health']
        self.stats['force'] += 2