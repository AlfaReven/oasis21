import pygame
from constants import *
from entities import Entities
import random
from inventory import Inventory
import os
from world import *
from placeable import CraftingTable
from minigame_well import *


class Player(Entities):
    def __init__(self, x, y, player_id=0, control_type="keyboard", joypad_id=0):
        super().__init__(x, y, "Player.png")  
        
        # NUEVO: Atributos para multijugador
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
        
        # APARTADO PARA ATRIBUTOS DEL INVENTARIO DE EDUARDO
        self.inventory = Inventory()
        self._give_starter_items()
        
        self.show_inventory = False
        self.item_images = {
            "wood": self.load_item_image("woods.png"),
            "stone": self.load_item_image("small_stone.png")
        }
        
        # ATRIBUTOS DE EDUARDO
        self.energy = MAX_ENERGY
        self.food = MAX_FOOD
        self.thirst = MAX_THIRST
        self.stamina = MAX_STAMINA
        
        self.font = pygame.font.Font(None, 24)
        
        # ANIMACIONES DE HERRAMIENTAS
        self.action_sprite_sheet = pygame.image.load(os.path.join('assets', 'images', 'Player_Actions.png')).convert_alpha()

        # Propiedades para animaciones especiales
        self.special_animation = False  
        self.animation_type = None      
        self.special_animation_frame = 0
        self.special_animation_timer = 0
        self.special_animation_delay = AXE_ANIMATION_DELAY
        self.tool_animations = self.load_tool_animations()
        
        # NUEVO: Color diferente para cada jugador
        if player_id == 0:
            # Jugador 1 - Azul
            color_filter = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            color_filter.fill((0, 0, 255, 50))  # Azul semi-transparente
            self.image.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            # Jugador 2 - Rojo/Naranja
            color_filter = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            color_filter.fill((255, 100, 0, 50))  # Naranja semi-transparente
            self.image.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            
    #ESTO LO PONGO POR CUESTRIONES DE DESARROLLO YA DESPUES LO QUITARE
    # --- KIT DE DESARROLLO INICIAL ---
        



    def _give_starter_items(self):
        """Provee materiales iniciales al jugador (solo para pruebas)."""
        print("🧰 Cargando kit de inicio para pruebas...")

        starter_items = {
            'wood': 20,
            'stone': 15,
            'mineral_iron': 10,
            'ingot_iron': 5,
            'axe': 1,
            'work_bench': 1,
            'furnace': 1,
            'pala': 1,
            'ingot_copper': 5,
            'mineral_copper': 5,
            'bucket': 1,
            'pump':1,
        }

        for item_name, qty in starter_items.items():
            if item_name in self.inventory.item_images:
                self.inventory.add_item(item_name, qty)
            else:
                print(f"⚠️ Item '{item_name}' no tiene imagen definida en inventory.")

    
    def load_item_image(self, filename):
        path = os.path.join('assets', 'images', filename)
        image = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(image, (40, 40))
    
    def load_tool_animations(self):
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
                
                animations[tool_name][direction] = frames
        
        return animations
    
    def start_axe_animation(self):
        """Inicia la animación del hacha"""
        self.special_animation = True
        self.animation_type = 'axe'
        self.special_animation_frame = 0
        self.special_animation_timer = pygame.time.get_ticks()
        self.moving = False
    
    def update_special_animation(self, dt):
        #metodo que actualiza laas animaciones especiales, herramientas, etc
        if not self.special_animation:
            return
            
        current_time = pygame.time.get_ticks()
        
        if current_time - self.special_animation_timer > self.special_animation_delay:
            self.special_animation_timer = current_time
            self.special_animation_frame += 1
            
            # Si llegamos al final de la animación, terminarla
            if self.special_animation_frame >= AXE_FRAMES:
                self.special_animation = False
                self.animation_type = None
                self.special_animation_frame = 0
    
    def get_special_animation_frame(self):
        if not self.special_animation or self.animation_type not in self.tool_animations:
            return None
            
        # PARA SABER QUE FRAME DEL PLAYER ACTIONS USAR
        if self.current_state in [IDLE_RIGHT, WALK_RIGHT]:
            direction = 'right'
        elif self.current_state in [IDLE_DOWN, WALK_DOWN]:
            direction = 'down'
        elif self.current_state in [IDLE_UP, WALK_UP]:
            direction = 'up'
        else:
            direction = 'right'  #SI NO POS POR DEFFAUL MIRA A LA DERECHA
            
        #BUSCAR EL FRAME EN LA VARIBLE CON EL DICCIONARIO
        if direction in self.tool_animations[self.animation_type]:
            frame = self.tool_animations[self.animation_type][direction][self.special_animation_frame]
            
            #SI ESTA MIRANDO A LA IZQUIERDA LO GIRAMOS 
            if self.facing_left and direction == 'right':
                frame = pygame.transform.flip(frame, True, False)
                
            return frame
        
        return None
    
    def update_animation(self, dt):
        """Actualiza las animaciones de eduardo
        porque tiene animaciones especiales para el uso de herramientas y pistolas"""
        #primero usamos las animaciones especiales y ya despues usamos el metodo de la clase entities para las demas animaciones
        if self.special_animation:
            self.update_special_animation(dt)
            special_frame = self.get_special_animation_frame()
            if special_frame:
                self.image = special_frame
                self.rect = self.image.get_rect(center=(self.x, self.y))
            return
        super().update_animation(dt)
    
    def draw(self, screen, camera_x, camera_y):
        #lo primero es dibujar a eduardo pero centrado en chunnk
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        current_image = self.image
        
        if not self.special_animation and self.facing_left:
            current_image = pygame.transform.flip(current_image, True, False)
        
        screen.blit(current_image, (screen_x, screen_y))
        
        # NUEVO: Dibujar identificador del jugador
        if hasattr(self, 'player_id'):
            player_text = self.font.render(f"P{self.player_id + 1}", True, (255, 255, 255))
            screen.blit(player_text, (screen_x, screen_y - 20))
    
    def update(self, dt, obstacles):
        if self.special_animation:
            self.moving = False
            return
            
        # NUEVO: Control diferente según tipo de control
        if self.control_type == "keyboard":
            self.handle_keyboard_input(dt, obstacles)
        else:
            self.handle_joypad_input(dt, obstacles)
    
    def handle_keyboard_input(self, dt, obstacles):
        """Maneja entrada de teclado para ambos jugadores"""
        keys = pygame.key.get_pressed()
        
        # PARA SABER SI EDUARDO ANDA CORRIENDO 
        if self.player_id == 0:
            # Jugador 1: Shift para correr
            self.is_running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        else:
            # Jugador 2: Ctrl derecho para correr
            self.is_running = keys[pygame.K_RCTRL]
        
        current_speed = self.speed * 2 if self.is_running else self.speed

        dx, dy = 0, 0
        
        # Jugador 1 usa WASD, Jugador 2 usa Flechas
        if self.player_id == 0:
            if keys[pygame.K_w]:
                dy = -5
            if keys[pygame.K_s]:
                dy = 5
            if keys[pygame.K_a]:
                dx = -5
            if keys[pygame.K_d]:
                dx = 5
        else:
            # Jugador 2 usa flechas
            if keys[pygame.K_UP]:
                dy = -5
            if keys[pygame.K_DOWN]:
                dy = 5
            if keys[pygame.K_LEFT]:
                dx = -5
            if keys[pygame.K_RIGHT]:
                dx = 5
        
        # Movimiento diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        if dx != 0 or dy != 0:
            self.move(dx * current_speed, dy * current_speed, obstacles)
        else:
            self.moving = False
            if self.current_state == WALK_DOWN:
                self.current_state = IDLE_DOWN
            elif self.current_state == WALK_UP:
                self.current_state = IDLE_UP
            elif self.current_state == WALK_RIGHT:
                self.current_state = IDLE_RIGHT
    
    """Esta cosa lo que hace es saber si eduardo esta interactuando con el mundo"""
    def interact(self, world):
        #si esta en medio de una animacion especial es decir talando o usando herramientas
        if self.special_animation:
            return
            
        #para añadir tierras de cultivo
        keys = pygame.key.get_pressed()
        if keys[pygame.K_t]:
            world.add_farmland(self.x, self.y) 
            return
        
        #aqui llamamos al metodo is near para que no tale todos los arboles del chunk de golpe
        for tree in world.trees:
            if self.is_near(tree):
                has_item = self.inventory.has_item_equipped()
                if has_item:
                    self.start_axe_animation()
                if tree.chop(with_axe=has_item):
                    cantidad = 2 if has_item else 1
                    self.inventory.add_item('wood', cantidad)
                return
                
        for stone in world.small_stones:
            if self.is_near(stone):
                if stone.collect():
                    self.inventory.add_item('stone')
                return
        
        for iron in world.iron_minerals: 
            if self.is_near(iron):
                if iron.collect():
                    self.inventory.add_item('mineral_iron')
                return
        for copper in world.copper_minerals:
            if self.is_near(copper):
                if copper.collect():
                    self.inventory.add_item('mineral_copper')
                return

        
        for well in world.wells:
            if self.is_near(well):
                # Verificar que tiene cubeta en alguna mano
                has_bucket = (
                    (self.inventory.left_hand and self.inventory.left_hand.name == "bucket")
                    or (self.inventory.right_hand and self.inventory.right_hand.name == "bucket")
                )
                
                if not has_bucket:
                    print("🪣 Necesitas tener una cubeta equipada para sacar agua.")
                    return
                
                # Si tiene cubeta, iniciar el minijuego
                start_well_minigame(self, well)
                return


    # Los demás métodos se mantienen igual...
    def draw_inventory(self, screen, show_inventory=False):
        self.inventory.draw(screen, show_inventory)
        
        if show_inventory:
            font = pygame.font.Font(None, 24)
            close_inventory_text = font.render("Press 'I' for close inventory", True, WHITE)
            screen.blit(close_inventory_text, (WIDTH // 2 - close_inventory_text.get_width() // 2,
                                               HEIGHT - 40))
    
    def update_energy(self, amount):
        self.energy = max(0, min(self.energy + amount, MAX_ENERGY))
    
    def update_food(self, amount):
        self.food = max(0, min(self.food + amount, MAX_FOOD))
        
    def update_thirst(self, amount):
        """Actualiza la sed de Eduardo (0–MAX_THIRST)."""
        self.thirst = max(0, min(self.thirst + amount, MAX_THIRST))

    def drink_water(self):
        """Eduardo bebe agua de una cubeta si tiene."""
        for item in self.inventory.all_items():
            if "bucket" in item.name and getattr(item, "fill_level", 0) > 0:
                item.empty()
                self.update_thirst(+20)
                print("🥤 Eduardo bebió agua de su cubeta.")
                break
        else:
            print("🚫 No tienes cubetas con agua.")

        
    def update_stamina(self, amount):
        self.stamina = max(0, min(self.stamina + amount, MAX_STAMINA))
    
    def update_health(self, amount):
        self.stats['health'] = max(0, min(self.stats['health'] + amount, MAX_HEALTH))
        
    def draw_status_bars(self, screen):
        bar_width = 100
        bar_height = 10
        x_offset = 10
        y_offset = 50 + (self.player_id * 80)  # NUEVO: Offset diferente por jugador
        
        # NUEVO: Etiqueta del jugador
        player_label = self.font.render(f"Jugador {self.player_id + 1}", True, 
                                      (0, 100, 255) if self.player_id == 0 else (255, 100, 0))
        screen.blit(player_label, (x_offset, y_offset - 20))

        # Energía
        pygame.draw.rect(screen, BAR_BACKGROUND, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(screen, ENERGY_COLOR, (x_offset, y_offset, bar_width * (self.energy / MAX_ENERGY), bar_height))

        # Comida
        y_offset += 15
        pygame.draw.rect(screen, BAR_BACKGROUND, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(screen, FOOD_COLOR, (x_offset, y_offset, bar_width * (self.food / MAX_FOOD), bar_height))
        
        # Sed
        y_offset += 15
        pygame.draw.rect(screen, BAR_BACKGROUND, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(screen, THIRST_COLOR, (x_offset, y_offset, bar_width * (self.thirst / MAX_THIRST), bar_height))   
        
        # Stamina
        y_offset += 15
        pygame.draw.rect(screen, BAR_BACKGROUND, (x_offset, y_offset, bar_width, bar_height))
        pygame.draw.rect(screen, STAMINA_COLOR, (x_offset, y_offset, bar_width * (self.stamina / MAX_STAMINA), bar_height))
        
    def update_status(self):
        # Aplicar multiplicadores si está corriendo
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
    
    def attack(self, enemies):
        for enemy in enemies:
            if self.is_near(enemy):
                damage = self.take_damage(enemy, 'ranged')
                return damage
        return 0
    
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
        print(f"¡Nivel up! Jugador {self.player_id + 1} ahora es nivel {self.stats['level']}")
    

    def place_object(self, world):
        """Metodo para hacer que eduardo ponga obejtos en el mapa y se tomen como parte del mundo pero solo si el item esta en la 
        lista de obejtos colocables"""
        if hasattr(self, 'special_animation') and self.special_animation:
            return False
            
        # Verificar si tiene objeto en las manos
        if not (self.inventory.right_hand or self.inventory.left_hand):
            return False

        item_to_place = None
        hand_used = None
        
        if self.inventory.right_hand:
            item_to_place = self.inventory.right_hand.name
            hand_used = 'right'
        elif self.inventory.left_hand:
            item_to_place = self.inventory.left_hand.name
            hand_used = 'left'
        
        
        #Determinar donde pondra el obejto y en que direccion 
        place_distance = 60
        if self.current_state in [IDLE_RIGHT, WALK_RIGHT]:
            if self.facing_left:
                place_x = self.x - place_distance
                place_y = self.y
            else:
                place_x = self.x + place_distance
                place_y = self.y
        elif self.current_state in [IDLE_DOWN, WALK_DOWN]:
            place_x = self.x
            place_y = self.y + place_distance
        elif self.current_state in [IDLE_UP, WALK_UP]:
            place_x = self.x
            place_y = self.y - place_distance
        else:
            place_x = self.x + place_distance
            place_y = self.y
        
        #considerando los metodos de world trata de ponerlo si es que no hay anda que se ocupe ese clugar
        if hasattr(world, 'add_placeable'):
            success = world.add_placeable(item_to_place, place_x, place_y)
            
            if success:
                if hand_used == 'right':
                    self.inventory.right_hand = None
                else:
                    self.inventory.left_hand = None
            else:
                return success
        else:
            return False

    def interact_with_objects(self, world):
        """Interactúa con objetos cercanos cuando se presiona E"""
        if hasattr(self, 'special_animation') and self.special_animation:
            return False
            
        # Buscar objetos colocables cercanos
        if hasattr(world, 'get_nearby_placeable'):
            nearby_object = world.get_nearby_placeable(self)
            if nearby_object and hasattr(nearby_object, 'interact'):
                return nearby_object.interact(self)

        for tree in world.trees:
            if self.is_near(tree):
                has_axe = self.inventory.has_item_equipped()
                if has_axe:
                    self.start_axe_animation()

                
                if tree.chop(with_axe=has_axe):
                    self.inventory.add_item('wood')
                return True
                
        for stone in world.small_stones:
            if self.is_near(stone):
                if stone.collect():
                    self.inventory.add_item('stone')
                return True
        
        for iron in world.iron_minerals:
            if self.is_near(iron):
                if iron.collect():
                    self.inventory.add_item('mineral_iron')
                return True
        
        return False
    
    def pick_placeable(self, world):
        """Permite recoger un objeto colocado cercano."""
        for obj in world.placeable_objects:
            if self.is_near(obj):
                if len(self.inventory.hotbar) < len(world.placeable_objects):
                    item_name = obj.__class__.__name__.lower()
                    self.inventory.add_item(item_name, 1)
                    world.placeable_objects.remove(obj)
                    print(f"♻️ Has recogido {item_name}.")
                    return True
        return False
