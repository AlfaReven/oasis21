import pygame
import constants
from constants import *
import os

import pygame
import os
import constants

class InventoryItem:
    def __init__(self, name, image_path=None, quantity=1, fill_level=0, current_liters=0):
        self.name = name
        self.quantity = quantity
        self.fill_level = fill_level  # 0=vacío, 1=medio, 2=lleno
        self.current_liters = current_liters  # NUEVO: litros actuales
        self.max_liters = 20  # NUEVO: capacidad máxima de la cubeta
        self.image_path = image_path
        self.image = None
        self.dragging = False
        self.drag_offset = (0, 0)
        self.update_image()

    def update_image(self):
        """Actualiza la imagen basado en los litros actuales"""
        if "bucket" in self.name:
            # Calcular fill_level basado en litros actuales
            if self.current_liters <= 0:
                self.fill_level = 0
                filename = "bucket.png"
            elif self.current_liters < self.max_liters / 2:
                self.fill_level = 1
                filename = "bucket_half.png"
            else:
                self.fill_level = 2
                filename = "bucket_full.png"
                
            image_path = os.path.join("assets", "images", filename)
        else:
            image_path = self.image_path or os.path.join("assets", "images", f"{self.name}.png")

        # Cargar imagen...
        if os.path.exists(image_path):
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (SLOT_SIZE - 10, SLOT_SIZE - 10))
        else:
            surface = pygame.Surface((SLOT_SIZE - 10, SLOT_SIZE - 10), pygame.SRCALPHA)
            surface.fill((150, 150, 150, 200))
            self.image = surface

    def add_water(self, liters):
        """Añade agua a la cubeta"""
        space_available = self.max_liters - self.current_liters
        actual_liters = min(liters, space_available)
        self.current_liters += actual_liters
        self.update_image()
        return actual_liters

    def remove_water(self, liters=10):
        """Remueve agua de la cubeta (al beber)"""
        actual_liters = min(liters, self.current_liters)
        self.current_liters -= actual_liters
        self.update_image()
        return actual_liters

    def get_water_status(self):
        """Devuelve el estado del agua en texto"""
        return f"{self.current_liters}/{self.max_liters}L"

    # Mantén los métodos fill() y empty() para compatibilidad
    def fill(self):
        """Llena la cubeta completamente"""
        self.current_liters = self.max_liters
        self.update_image()

    def empty(self):
        """Vacía la cubeta completamente"""
        self.current_liters = 0
        self.update_image()
        

class Inventory:
    def __init__(self):
        self.hotbar = [None] * constants.HOTBAR_SLOTS
        self.inventory = [[None for _ in range(constants.INVENTORY_COLS)] for _ in range(constants.INVENTORY_ROWS)]
        self.crafting_grid = [[None for _ in range(constants.CRAFTING_GRID_SIZE)] for _ in range(constants.CRAFTING_GRID_SIZE)]
        self.crafting_result = None 
        self.dragged_item = None
        self.font = pygame.font.Font(None, 24)
        self.table_crafting_open = False
        self.table_crafting_grid = [[None for _ in range(3)] for _ in range(3)]
        self.table_crafting_result = None
                
        
        
        self.left_hand = None   
        self.right_hand = None
        
        
        self.item_images = {
            'wood': os.path.join('assets', 'images', 'woods.png'),
            'stone': os.path.join('assets', 'images', 'small_stone.png'),
            'axe': os.path.join('assets', 'images', 'axe.png'),
            'mineral_iron': os.path.join('assets', 'images', 'iron_mineral.png'),
            'mineral_copper': os.path.join('assets', 'images', 'mineral_copper.png'),
            'work_bench': os.path.join('assets', 'images', 'work_bench.png'),
            'furnace': os.path.join('assets', 'images', 'furnace.png'),
            'pala': os.path.join('assets', 'images', 'pala.png'),
            'ingot_iron': os.path.join('assets', 'images', 'ingot_iron.png'),
            'ingot_copper': os.path.join('assets', 'images', 'ingot_copper.png'),
            'bucket': os.path.join('assets', 'images', 'bucket.png'),
            'bucket_half': os.path.join('assets', 'images', 'bucket_half.png'),
            'bucket_full': os.path.join('assets', 'images', 'bucket_full.png'),
            'pump': os.path.join('assets', 'images', 'pump.png'),
            'water_tank': os.path.join('assets', 'images', 'water_tank.png'),
            'waste_tank': os.path.join('assets', 'images', 'waste_tank.png'),
            'empty_tank': os.path.join('assets', 'images', 'empty_tank.png')
        }
        
        
        self.stackable_items = {
            'wood': 21,
            'stone': 21,
            'mineral_iron': 21,
            'ingot_iron': 21,
            'mineral_copper':21,
            'ingot_iron': 21,
        }
        
        """RECETAS PARA LA CREACION DE ITEMS QUE NECESITARA EDUARDO PARA CONTINUARCON 
        CON LOS MINIJUEGOS DE RECOLECCION"""
        self.recipes = {
            
            'axe': {
                'pattern': [
                    ['wood', 'stone'],
                    [None, None]
                ],
                'result': 'axe',
                'result_quantity': 1,
                'requires_table': False  
            },

            'work_bench': {
                'pattern': [
                    ['wood', 'wood'],
                    ['wood', 'wood']
                ],
                'result': 'work_bench',
                'result_quantity': 1,
                'requires_table': False
            },

            
            'iron_axe': {
                'pattern': [
                    ['iron', 'iron', None],
                    ['iron', 'wood', None],
                    [None, 'wood', None]
                ],
                'result': 'axe',
                'result_quantity': 1,
                'requires_table': True  
            },

            'furnace': {
                'pattern': [
                    ['stone', 'stone', 'stone'],
                    ['stone', None, 'stone'],
                    ['stone', 'stone', 'stone']
                ],
                'result': 'furnace',
                'result_quantity': 1,
                'requires_table': True
            },
            'pala': {
                'pattern': [
                    [None, 'stone', None],
                    [None, 'wood', None],
                    [None, 'wood', None]
                ],
                'result': 'pala',
                'result_quantity': 1,
                'requires_table': True
            },
            'bucket': {
                'pattern': [
                    ['ingot_iron', None, 'ingot_iron'],
                    ['ingot_iron', None, 'ingot_iron'],
                    [None, 'ingot_iron', None]
                ],
                'result': 'bucket',
                'result_quantity': 1,
                'requires_table': True
            },
            'pump': {
                'pattern': [
                    ['ingot_iron', 'ingot_iron', 'copper'],
                    ['ingot_iron', 'ingot_iron', 'copper'],
                    ['wood', 'wood', 'wood']
                ],
                'result': 'pump',
                'result_quantity': 1,
                'requires_table': True
            },
            'empty_tank': {
                'pattern': [
                    ['ingot_iron', None, 'ingot_iron'],
                    ['ingot_iron', None, 'ingot_iron'],
                    ['ingot_iron', 'ingot_iron', 'ingot_iron']
                ],
                'result': 'empty_tank',
                'result_quantity': 1,
                'requires_table': True
            },
        }

        
        self.equippable_items = {'axe', 'work_bench', 'furnace', 'water_tank', 
                                 'farm_plot', 'pickaxe', 'bucket', 'bucket_half',
                                 'bucket_full', 'pump', 'empty_tank', 'waste_tank'}

    def add_item(self, item_name, quantity=1):

        if item_name in self.stackable_items:
            max_stack = self.stackable_items[item_name]
            remaining_quantity = quantity
            

            for i, slot in enumerate(self.hotbar):
                if slot and slot.name == item_name and slot.quantity < max_stack:
                    space_available = max_stack - slot.quantity
                    amount_to_add = min(remaining_quantity, space_available)
                    slot.quantity += amount_to_add
                    remaining_quantity -= amount_to_add
                    
                    if remaining_quantity <= 0:
                        return True
     
            for row in range(constants.INVENTORY_ROWS):
                for col in range(constants.INVENTORY_COLS):
                    slot = self.inventory[row][col]
                    if slot and slot.name == item_name and slot.quantity < max_stack:
                        space_available = max_stack - slot.quantity
                        amount_to_add = min(remaining_quantity, space_available)
                        slot.quantity += amount_to_add
                        remaining_quantity -= amount_to_add
                        
                        if remaining_quantity <= 0:
                            return True
  
            while remaining_quantity > 0:
                added = False
                for i, slot in enumerate(self.hotbar):
                    if slot is None:
                        amount_to_add = min(remaining_quantity, max_stack)
                        self.hotbar[i] = InventoryItem(item_name, self.item_images[item_name], amount_to_add)
                        remaining_quantity -= amount_to_add
                        added = True
                        break
                
                if remaining_quantity <= 0:
                    break
                    
                if not added:
                    for row in range(constants.INVENTORY_ROWS):
                        for col in range(constants.INVENTORY_COLS):
                            if self.inventory[row][col] is None:
                                amount_to_add = min(remaining_quantity, max_stack)
                                self.inventory[row][col] = InventoryItem(item_name, self.item_images[item_name], amount_to_add)
                                remaining_quantity -= amount_to_add
                                added = True
                                break
                        if added:
                            break
                
           
                if not added:
                    return False
            
            return True
        
        else:
      
            return self._add_non_stackable_item(item_name, quantity)

    def _add_non_stackable_item(self, item_name, quantity=1):
        for i, slot in enumerate(self.hotbar):
            if slot is None:
                self.hotbar[i] = InventoryItem(item_name, self.item_images[item_name], quantity)
                return True
            
        for row in range(constants.INVENTORY_ROWS):
            for col in range(constants.INVENTORY_COLS):
                if self.inventory[row][col] is None:
                    self.inventory[row][col] = InventoryItem(item_name, self.item_images[item_name], quantity)
                    return True
        return False

    def has_items_for_recipe(self, recipe_pattern):
        grid_size = constants.CRAFTING_GRID_SIZE

        for row in range(len(recipe_pattern)):
            for col in range(len(recipe_pattern[row])):
                expected = recipe_pattern[row][col]
                if expected is None:
                    continue

                if row >= grid_size or col >= grid_size:
                    return False

                cell = self.crafting_grid[row][col]
                if not cell or cell.name != expected:
                    return False

        return True


    def _count_all_items(self):
        item_counts = {}
        

        for slot in self.hotbar:
            if slot:
                item_counts[slot.name] = item_counts.get(slot.name, 0) + slot.quantity
        
        for row in range(constants.INVENTORY_ROWS):
            for col in range(constants.INVENTORY_COLS):
                slot = self.inventory[row][col]
                if slot:
                    item_counts[slot.name] = item_counts.get(slot.name, 0) + slot.quantity
        
        return item_counts

    def consume_items_for_recipe(self, recipe_pattern):
        grid_size = constants.CRAFTING_GRID_SIZE

        for row in range(grid_size):
            for col in range(grid_size):
                expected = None
                if row < len(recipe_pattern) and col < len(recipe_pattern[row]):
                    expected = recipe_pattern[row][col]

                cell = self.crafting_grid[row][col]

                if expected and cell and cell.name == expected:
                    cell.quantity -= 1
                    if cell.quantity <= 0:
                        self.crafting_grid[row][col] = None

    def draw(self, screen, show_inventory=False):

        self._draw_hotbar(screen)
        
        self._draw_hand_slots (screen)
        
        if show_inventory:
            background = pygame.Surface((constants.WIDTH, constants.HEIGHT), pygame.SRCALPHA)
            background.fill((0, 0, 0, 128))
            screen.blit(background, (0, 0))
            
            self._draw_main_inventory(screen)
            self._draw_crafting_grid(screen)
            
        if self.dragged_item:
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(self.dragged_item.image,
                        (mouse_pos[0] - self.dragged_item.drag_offset[0],
                         mouse_pos[1] - self.dragged_item.drag_offset[1]))
            if self.dragged_item.quantity > 1:
                text = self.font.render(str(self.dragged_item.quantity), True, constants.WHITE)
                text_rect = text.get_rect()
                text_rect.bottomright = (mouse_pos[0] + self.dragged_item.image.get_width() // 2 - 5, 
                                         mouse_pos[1] + self.dragged_item.image.get_height() // 2 - 5)
                screen.blit(text, text_rect)
                
    def _draw_hotbar(self, screen):

        for i in range(constants.HOTBAR_SLOTS):
            x = constants.HOTBAR_X + (i * constants.SLOT_SIZE)
            y = constants.HOTBAR_Y
            
    
            pygame.draw.rect(screen, constants.SLOT_BORDER, 
                             (x, y, constants.SLOT_SIZE, constants.SLOT_SIZE))
            pygame.draw.rect(screen, constants.SLOT_COLOR,
                             (x + 2, y + 2, constants.SLOT_SIZE - 4, constants.SLOT_SIZE - 4))
    
            if self.hotbar[i]:
                self._draw_item(screen, self.hotbar[i], x, y)
        
    def _draw_main_inventory(self, screen):
        for row in range(constants.INVENTORY_ROWS):
            for col in range(constants.INVENTORY_COLS):
                x = constants.INVENTORY_X + (col * constants.SLOT_SIZE)
                y = constants.INVENTORY_Y + (row * constants.SLOT_SIZE)
                
          
                pygame.draw.rect(screen, constants.SLOT_BORDER, 
                             (x, y, constants.SLOT_SIZE, constants.SLOT_SIZE))
                pygame.draw.rect(screen, constants.SLOT_COLOR,
                             (x + 2, y + 2, constants.SLOT_SIZE - 4, constants.SLOT_SIZE - 4))

                if self.inventory[row][col]:
                    self._draw_item(screen, self.inventory[row][col], x, y)       
                    
    def _draw_item(self, screen, item, x, y):

        item_x = x + (constants.SLOT_SIZE - item.image.get_width()) // 2
        item_y = y + (constants.SLOT_SIZE - item.image.get_height()) // 2
        screen.blit(item.image, (item_x, item_y))
        
        if item.quantity > 0:
            text = self.font.render(str(item.quantity), True, constants.WHITE)
            text_rect = text.get_rect()
            text_rect.bottomright = (x + constants.SLOT_SIZE - 5, y + constants.SLOT_SIZE - 5)
            screen.blit(text, text_rect)
    
    def _draw_hand_slots(self, screen):
        
        pygame.draw.rect(screen, SLOT_BORDER,
                         (LEFT_HAND_SLOT_X, LEFT_HAND_SLOT_Y,
                          SLOT_SIZE, SLOT_SIZE))
        
        pygame.draw.rect(screen, SLOT_COLOR,
                         (LEFT_HAND_SLOT_X + 2, LEFT_HAND_SLOT_Y + 2,
                          SLOT_SIZE - 4, SLOT_SIZE-4))
        
        if self.left_hand:
            self._draw_item(screen, self.left_hand, LEFT_HAND_SLOT_X, LEFT_HAND_SLOT_Y)
            
        
        
        pygame.draw.rect(screen, SLOT_BORDER,
                         (RIGHT_HAND_SLOT_X, RIGHT_HAND_SLOT_Y,
                          SLOT_SIZE, SLOT_SIZE))
        
        pygame.draw.rect(screen, SLOT_COLOR,
                         (RIGHT_HAND_SLOT_X + 2, RIGHT_HAND_SLOT_Y + 2,
                          SLOT_SIZE - 4, SLOT_SIZE - 4))

        
        if self.right_hand:
            self._draw_item(screen, self.right_hand, RIGHT_HAND_SLOT_X, RIGHT_HAND_SLOT_Y)

    def handle_click(self, pos, button, show_inventory=False):
        """Maneja los clicks en el inventario"""
        mouse_x, mouse_y = pos
        
        
        if HOTBAR_Y <= mouse_y <= HOTBAR_Y + SLOT_SIZE:
            if (LEFT_HAND_SLOT_X <= mouse_x <= LEFT_HAND_SLOT_X + SLOT_SIZE):
                self._handle_hand_slot_click(button, 'left')
                return True
            
            elif (RIGHT_HAND_SLOT_X <= mouse_x <= RIGHT_HAND_SLOT_X + SLOT_SIZE):
                self._handle_hand_slot_click(button, 'right')
                return True

            
        
        if constants.HOTBAR_Y <= mouse_y <= constants.HOTBAR_Y + constants.SLOT_SIZE:
            slot_index = (mouse_x - constants.HOTBAR_X) // constants.SLOT_SIZE
            if 0 <= slot_index < constants.HOTBAR_SLOTS:
                self._handle_slot_click(button, self.hotbar, slot_index,
                                        constants.HOTBAR_X + (slot_index * constants.SLOT_SIZE),
                                        constants.HOTBAR_Y)
                self._check_recipe()  
                return True
            
        if show_inventory:
            if constants.INVENTORY_Y <= mouse_y <= constants.INVENTORY_Y + (
                    constants.INVENTORY_ROWS * constants.SLOT_SIZE):
                row = (mouse_y - constants.INVENTORY_Y) // constants.SLOT_SIZE
                col = (mouse_x - constants.INVENTORY_X) // constants.SLOT_SIZE
                if (0 <= row < constants.INVENTORY_ROWS and 0 <= col < constants.INVENTORY_COLS):
                    self._handle_grid_slot_click(button, row, col,
                                                constants.INVENTORY_X + (col * constants.SLOT_SIZE),
                                                constants.INVENTORY_Y + (row * constants.SLOT_SIZE))
                    self._check_recipe()  
                    return True
            
            
            if constants.CRAFTING_GRID_Y <= mouse_y <= constants.CRAFTING_GRID_Y + (
                constants.CRAFTING_GRID_SIZE * constants.SLOT_SIZE):
                row = (mouse_y - constants.CRAFTING_GRID_Y) // constants.SLOT_SIZE
                col = (mouse_x - constants.CRAFTING_GRID_X) // constants.SLOT_SIZE
                if (0 <= row < constants.CRAFTING_GRID_SIZE and 0 <= col < constants.CRAFTING_GRID_SIZE):
                    self._handle_crafting_grid_click(button, row, col)
                    
                    return True
            
            
            if (constants.CRAFTING_RESULT_SLOT_X <= mouse_x <= constants.CRAFTING_RESULT_SLOT_X + constants.SLOT_SIZE and
                constants.CRAFTING_RESULT_SLOT_Y <= mouse_y <= constants.CRAFTING_RESULT_SLOT_Y + constants.SLOT_SIZE):
                self._handle_crafting_result_click(button)
                return True
                
        
        if self.dragged_item and button == 1:
            self._return_dragged_item()
            self._check_recipe()  
        return False

    def _handle_slot_click(self, button, slot_list, index, slot_x, slot_y):
        """Maneja clicks en slots de la hotbar"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, mouse_y = mouse_pos
        
        if button == 1: 
            if self.dragged_item:
                if slot_list[index] is None:
                    slot_list[index] = self.dragged_item
                else:
                    slot_list[index], self.dragged_item = self.dragged_item, slot_list[index]
                    return
                self.dragged_item = None
            elif slot_list[index]:

                self.dragged_item = slot_list[index]
                slot_list[index] = None
                item_rect = self.dragged_item.image.get_rect()
                item_rect.x = slot_x
                item_rect.y = slot_y
                self.dragged_item.drag_offset = (mouse_x - item_rect.centerx, mouse_y - item_rect.centery)
                
        elif button == 3:  
            self._handle_right_click(slot_list, index, slot_x, slot_y)
                
    def _handle_grid_slot_click(self, button, row, col, slot_x, slot_y):
        """Maneja clicks en slots del inventario principal"""
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, mouse_y = mouse_pos
        
        if button == 1: 
            if self.dragged_item:
                if self.inventory[row][col] is None:
                    self.inventory[row][col] = self.dragged_item
                else:
                    self.inventory[row][col], self.dragged_item = self.dragged_item, self.inventory[row][col]
                    return
                self.dragged_item = None
            elif self.inventory[row][col]:
                self.dragged_item = self.inventory[row][col]
                self.inventory[row][col] = None
                item_rect = self.dragged_item.image.get_rect()
                item_rect.x = slot_x
                item_rect.y = slot_y
                self.dragged_item.drag_offset = (mouse_x - item_rect.centerx, mouse_y - item_rect.centery)
                
        elif button == 3: 
            self._handle_right_click_grid(row, col, slot_x, slot_y)

    def _handle_crafting_grid_click(self, button, row, col):
        """Maneja clicks en la cuadrícula de crafteo"""
        if button == 1:  
            if self.dragged_item:
                if self.crafting_grid[row][col] is None:
                    self.crafting_grid[row][col] = self.dragged_item
                    self.dragged_item = None
                else:
                    self.crafting_grid[row][col], self.dragged_item = self.dragged_item, self.crafting_grid[row][col]
            elif self.crafting_grid[row][col]:
                self.dragged_item = self.crafting_grid[row][col]
                self.crafting_grid[row][col] = None
                
        elif button == 3:
            self._handle_right_click_crafting(row, col)
                
        self._check_recipe()

    def _handle_right_click(self, slot_list, index, slot_x, slot_y):

        if self.dragged_item:
            if slot_list[index] is None:
                if self.dragged_item.quantity > 1:
                    slot_list[index] = InventoryItem(
                        self.dragged_item.name, 
                        self.item_images[self.dragged_item.name], 
                        1
                    )
                    self.dragged_item.quantity -= 1
                else:
                    slot_list[index] = self.dragged_item
                    self.dragged_item = None
            elif slot_list[index].name == self.dragged_item.name:
                max_stack = self.stackable_items.get(slot_list[index].name, 1)
                if slot_list[index].quantity < max_stack:
                    slot_list[index].quantity += 1
                    self.dragged_item.quantity -= 1
                    if self.dragged_item.quantity <= 0:
                        self.dragged_item = None
        elif slot_list[index] and slot_list[index].quantity > 1:
            half = slot_list[index].quantity // 2
            if half > 0:
                self.dragged_item = InventoryItem(
                    slot_list[index].name,
                    self.item_images[slot_list[index].name],
                    half
                )
                slot_list[index].quantity -= half

    def _handle_right_click_grid(self, row, col, slot_x, slot_y):
        if self.dragged_item:
            if self.inventory[row][col] is None:
                if self.dragged_item.quantity > 1:
                    self.inventory[row][col] = InventoryItem(
                        self.dragged_item.name, 
                        self.item_images[self.dragged_item.name], 
                        1
                    )
                    self.dragged_item.quantity -= 1
                else:
                    self.inventory[row][col] = self.dragged_item
                    self.dragged_item = None
            elif self.inventory[row][col].name == self.dragged_item.name:
                max_stack = self.stackable_items.get(self.inventory[row][col].name, 1)
                if self.inventory[row][col].quantity < max_stack:
                    self.inventory[row][col].quantity += 1
                    self.dragged_item.quantity -= 1
                    if self.dragged_item.quantity <= 0:
                        self.dragged_item = None
        elif self.inventory[row][col] and self.inventory[row][col].quantity > 1:
            half = self.inventory[row][col].quantity // 2
            if half > 0:
                self.dragged_item = InventoryItem(
                    self.inventory[row][col].name,
                    self.item_images[self.inventory[row][col].name],
                    half
                )
                self.inventory[row][col].quantity -= half

    def _handle_right_click_crafting(self, row, col):
        if self.dragged_item:
            if self.crafting_grid[row][col] is None:
                if self.dragged_item.quantity > 1:
                    self.crafting_grid[row][col] = InventoryItem(
                        self.dragged_item.name, 
                        self.item_images[self.dragged_item.name], 
                        1
                    )
                    self.dragged_item.quantity -= 1
                else:
                    self.crafting_grid[row][col] = self.dragged_item
                    self.dragged_item = None
            elif self.crafting_grid[row][col].name == self.dragged_item.name:
                max_stack = self.stackable_items.get(self.crafting_grid[row][col].name, 1)
                if self.crafting_grid[row][col].quantity < max_stack:
                    self.crafting_grid[row][col].quantity += 1
                    self.dragged_item.quantity -= 1
                    if self.dragged_item.quantity <= 0:
                        self.dragged_item = None
        elif self.crafting_grid[row][col] and self.crafting_grid[row][col].quantity > 1:
            half = self.crafting_grid[row][col].quantity // 2
            if half > 0:
                self.dragged_item = InventoryItem(
                    self.crafting_grid[row][col].name,
                    self.item_images[self.crafting_grid[row][col].name],
                    half
                )
                self.crafting_grid[row][col].quantity -= half
                
    def _handle_hand_slot_click(self, button, hand):
        if button == 1:
            if hand == 'left':
                if self.dragged_item:
                    if self.dragged_item.name in self.equippable_items:
                        self.left_hand, self.dragged_item = self.dragged_item, self.left_hand
                elif self.left_hand:
                    self.dragged_item = self.left_hand
                    self.left_hand = None
            else:
                if self.dragged_item:
                    if self.dragged_item.name in self.equippable_items:
                        self.right_hand, self.dragged_item = self.dragged_item, self.right_hand
                elif self.right_hand:
                    self.dragged_item = self.right_hand
                    self.right_hand = None
                        
    def has_item_equipped(self, item_name=None):
        if item_name is None:
            return (
                (self.left_hand and self.left_hand.name in self.equippable_items) or
                (self.right_hand and self.right_hand.name in self.equippable_items)
            )
        return(
            (self.left_hand and self.left_hand.name == item_name) or 
            (self.right_hand and self.right_hand.name == item_name)
        )
    
    def has_axe_equipped(self):
        """Verifica específicamente si tiene un hacha equipada"""
        return (self.right_hand and self.right_hand.name == 'axe') or \
            (self.left_hand and self.left_hand.name == 'axe')


    def _return_dragged_item(self):
        for i, slot in enumerate(self.hotbar):
            if slot is None:
                self.hotbar[i] = self.dragged_item
                self.dragged_item = None
                return

        for row in range(constants.INVENTORY_ROWS):
            for col in range(constants.INVENTORY_COLS):
                if self.inventory[row][col] is None:
                    self.inventory[row][col] = self.dragged_item
                    self.dragged_item = None
                    return
                
    def _draw_crafting_grid(self, screen):
        for row in range(constants.CRAFTING_GRID_SIZE):
            for col in range(constants.CRAFTING_GRID_SIZE):
                x = constants.CRAFTING_GRID_X + (col * constants.SLOT_SIZE)
                y = constants.CRAFTING_GRID_Y + (row * constants.SLOT_SIZE)
                
                
                pygame.draw.rect(screen, constants.SLOT_BORDER, 
                                 (x, y, constants.SLOT_SIZE, constants.SLOT_SIZE))
                pygame.draw.rect(screen, constants.SLOT_COLOR, 
                                 (x + 2, y + 2, constants.SLOT_SIZE - 4, constants.SLOT_SIZE - 4))
        
                
                if self.crafting_grid[row][col]:
                    self._draw_item(screen, self.crafting_grid[row][col], x, y)
    
        
        
        pygame.draw.rect(screen, constants.SLOT_BORDER, 
                        (constants.CRAFTING_RESULT_SLOT_X, constants.CRAFTING_RESULT_SLOT_Y, 
                         constants.SLOT_SIZE, constants.SLOT_SIZE))
        pygame.draw.rect(screen, constants.SLOT_COLOR, 
                        (constants.CRAFTING_RESULT_SLOT_X + 2, constants.CRAFTING_RESULT_SLOT_Y + 2, 
                         constants.SLOT_SIZE - 4, constants.SLOT_SIZE - 4))
        
        
        if self.crafting_result:
            self._draw_item(screen, self.crafting_result,
                            constants.CRAFTING_RESULT_SLOT_X,
                            constants.CRAFTING_RESULT_SLOT_Y)
            

    
    def _check_recipe(self):
        current_pattern = []
        for row in range(constants.CRAFTING_GRID_SIZE):
            pattern_row = []
            for col in range(constants.CRAFTING_GRID_SIZE):
                item = self.crafting_grid[row][col]
                pattern_row.append(item.name if item else None)
            current_pattern.append(pattern_row)
        
        
        print(f"receta actual en grid: {current_pattern}") 
        
        
        for recipe_name, recipe in self.recipes.items():
            recipe_pattern = recipe['pattern']
            print(f"Comparando con receta {recipe_name}: {recipe_pattern}")  
            
            
            pattern_matches = True
            for row in range(len(recipe_pattern)):
                for col in range(len(recipe_pattern[row])):
                    expected = recipe_pattern[row][col]
                    actual = current_pattern[row][col] if (row < len(current_pattern) and col < len(current_pattern[row])) else None
                    
                    if expected != actual:
                        pattern_matches = False
                        break
                if not pattern_matches:
                    break
            
            print(f"¿Coincide {recipe_name}? {pattern_matches}")  
            

            if pattern_matches:
                has_items = self.has_items_for_recipe(recipe_pattern)
                print(f"¿Tenemos items para {recipe_name}? {has_items}")  
                
                if has_items:
                    self.crafting_result = InventoryItem(
                        recipe['result'], 
                        self.item_images[recipe['result']],
                        recipe.get('result_quantity', 1)
                    )
                    print(f"¡Receta {recipe_name} completada!")  
                    return
        

        self.crafting_result = None
        print("No hay recetas que coincidan")  
    
    
    def _pattern_matches(self, recipe_pattern):
        grid_size = constants.CRAFTING_GRID_SIZE
        current_pattern = [
            [self.crafting_grid[r][c].name if self.crafting_grid[r][c] else None for c in range(grid_size)]
            for r in range(grid_size)
        ]

        recipe_rows = len(recipe_pattern)
        recipe_cols = len(recipe_pattern[0])

        for offset_y in range(grid_size - recipe_rows + 1):
            for offset_x in range(grid_size - recipe_cols + 1):
                match = True
                for ry in range(recipe_rows):
                    for rx in range(recipe_cols):
                        expected = recipe_pattern[ry][rx]
                        actual = current_pattern[offset_y + ry][offset_x + rx]
                        if expected != actual:
                            match = False
                            break
                    if not match:
                        break
                if match:
                    return True
        return False



    def _handle_crafting_result_click(self, button):
        if button == 1 and self.crafting_result:

            current_pattern = []
            for row in range(constants.CRAFTING_GRID_SIZE):
                pattern_row = []
                for col in range(constants.CRAFTING_GRID_SIZE):
                    item = self.crafting_grid[row][col]
                    pattern_row.append(item.name if item else None)
                current_pattern.append(pattern_row)
            
            matched_recipe = None
            for recipe_name, recipe in self.recipes.items():
                recipe_pattern = recipe['pattern']
                if self._pattern_matches(recipe_pattern):
                    matched_recipe = recipe
                    break

            if matched_recipe:

                if not self.dragged_item:
                    self.dragged_item = self.crafting_result
                    self.crafting_result = None
                    self.consume_items_for_recipe(matched_recipe['pattern'])

                    
  
                    for row in range(constants.CRAFTING_GRID_SIZE):
                        for col in range(constants.CRAFTING_GRID_SIZE):
                            if self.crafting_grid[row][col]:
                                if self.crafting_grid[row][col].quantity <= 0:
                                    self.crafting_grid[row][col] = None
                    

                    self._check_recipe()

    def get_selected_item(self):
        return None

    def remove_item(self, item_name, quantity=1):
        remaining = quantity
        
        for i, slot in enumerate(self.hotbar):
            if slot and slot.name == item_name:
                if slot.quantity <= remaining:
                    remaining -= slot.quantity
                    self.hotbar[i] = None
                else:
                    slot.quantity -= remaining
                    remaining = 0
                
                if remaining <= 0:
                    return True
        

        for row in range(constants.INVENTORY_ROWS):
            for col in range(constants.INVENTORY_COLS):
                if remaining <= 0:
                    return True
                    
                slot = self.inventory[row][col]
                if slot and slot.name == item_name:
                    if slot.quantity <= remaining:
                        remaining -= slot.quantity
                        self.inventory[row][col] = None
                    else:
                        slot.quantity -= remaining
                        remaining = 0
        
        return remaining <= 0
    
    def get_placeable_item_in_hand(self):
        """Obtiene el objeto colocable que tiene en las manos"""
        placeable_items = ['work_bench', 'furnace', 'water_tank', 'farm_plot']
        
        if self.right_hand and self.right_hand.name in placeable_items:
            return self.right_hand.name
        elif self.left_hand and self.left_hand.name in placeable_items:
            return self.left_hand.name
        return None

    def _pattern_matches_grid(self, recipe_pattern, grid_pattern):
        for r in range(len(recipe_pattern)):
            for c in range(len(recipe_pattern[r])):
                expected = recipe_pattern[r][c]
                actual = grid_pattern[r][c] if r < len(grid_pattern) and c < len(grid_pattern[r]) else None
                if expected != actual:
                    return False
        return True

    
    
    
    def check_table_recipe(self):
        """Verifica recetas avanzadas en la mesa"""
        current_pattern = [[self.table_crafting_grid[r][c].name if self.table_crafting_grid[r][c] else None
                            for c in range(3)] for r in range(3)]
        self.table_crafting_result = None

        for name, recipe in self.recipes.items():
            if not recipe.get('requires_table'):
                continue
            if self._pattern_matches_grid(recipe['pattern'], current_pattern):
                print(f"✅ Receta {name} detectada en la mesa")
                self.table_crafting_result = InventoryItem(recipe['result'],
                                                           self.item_images[recipe['result']],
                                                           recipe['result_quantity'])
                return

    def handle_table_crafting_click(self, pos, button):
        """Maneja clicks dentro de la interfaz combinada: inventario + mesa de crafteo"""
        mouse_x, mouse_y = pos

        
        inv_start_x = WIDTH // 2 - 350
        inv_start_y = HEIGHT // 2 - (INVENTORY_ROWS * SLOT_SIZE // 2)

        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                x = inv_start_x + (col * SLOT_SIZE)
                y = inv_start_y + (row * SLOT_SIZE)
                if x <= mouse_x <= x + SLOT_SIZE and y <= mouse_y <= y + SLOT_SIZE:
                    if button == 1:  
                        if self.dragged_item:
                            if self.inventory[row][col] is None:
                                self.inventory[row][col] = self.dragged_item
                                self.dragged_item = None
                            else:
                                self.inventory[row][col], self.dragged_item = self.dragged_item, self.inventory[row][col]
                        elif self.inventory[row][col]:
                            self.dragged_item = self.inventory[row][col]
                            self.inventory[row][col] = None
                    elif button == 3:  
                        if self.dragged_item:
                            if self.inventory[row][col] is None and self.dragged_item.quantity > 1:
                                self.inventory[row][col] = InventoryItem(
                                    self.dragged_item.name,
                                    self.item_images[self.dragged_item.name],
                                    1
                                )
                                self.dragged_item.quantity -= 1
                            else:
                                self.inventory[row][col], self.dragged_item = self.dragged_item, self.inventory[row][col]
                        elif self.inventory[row][col] and self.inventory[row][col].quantity > 1:
                            half = self.inventory[row][col].quantity // 2
                            self.dragged_item = InventoryItem(
                                self.inventory[row][col].name,
                                self.item_images[self.inventory[row][col].name],
                                half
                            )
                            self.inventory[row][col].quantity -= half
                    return
             
        hotbar_start_x = HOTBAR_X
        hotbar_start_y = HOTBAR_Y

        for i in range(HOTBAR_SLOTS):
            x = hotbar_start_x + i * SLOT_SIZE
            y = hotbar_start_y
            if x <= mouse_x <= x + SLOT_SIZE and y <= mouse_y <= y + SLOT_SIZE:
                if button == 1: 
                    if self.dragged_item:
                        if self.hotbar[i] is None:
                            self.hotbar[i] = self.dragged_item
                            self.dragged_item = None
                        else:
                            self.hotbar[i], self.dragged_item = self.dragged_item, self.hotbar[i]
                    elif self.hotbar[i]:
                        self.dragged_item = self.hotbar[i]
                        self.hotbar[i] = None

                elif button == 3:  
                    if self.dragged_item:
                        if self.hotbar[i] is None and self.dragged_item.quantity > 1:
                            self.hotbar[i] = InventoryItem(
                                self.dragged_item.name,
                                self.item_images[self.dragged_item.name],
                                1
                            )
                            self.dragged_item.quantity -= 1
                        else:
                            self.hotbar[i], self.dragged_item = self.dragged_item, self.hotbar[i]
                    elif self.hotbar[i] and self.hotbar[i].quantity > 1:
                        half = self.hotbar[i].quantity // 2
                        self.dragged_item = InventoryItem(
                            self.hotbar[i].name,
                            self.item_images[self.hotbar[i].name],
                            half
                        )
                        self.hotbar[i].quantity -= half
                return


        
        table_start_x = WIDTH // 2 + 100
        table_start_y = HEIGHT // 2 - (3 * SLOT_SIZE // 2)

        for row in range(3):
            for col in range(3):
                x = table_start_x + col * (SLOT_SIZE + 10)
                y = table_start_y + row * (SLOT_SIZE + 10)
                if x <= mouse_x <= x + SLOT_SIZE and y <= mouse_y <= y + SLOT_SIZE:
                    if button == 1:  
                        if self.dragged_item:
                            if self.table_crafting_grid[row][col] is None:
                                self.table_crafting_grid[row][col] = self.dragged_item
                                self.dragged_item = None
                            else:
                                self.table_crafting_grid[row][col], self.dragged_item = self.dragged_item, self.table_crafting_grid[row][col]
                        elif self.table_crafting_grid[row][col]:
                            self.dragged_item = self.table_crafting_grid[row][col]
                            self.table_crafting_grid[row][col] = None
                    elif button == 3:  
                        if self.dragged_item:
                            if self.table_crafting_grid[row][col] is None and self.dragged_item.quantity > 1:
                                self.table_crafting_grid[row][col] = InventoryItem(
                                    self.dragged_item.name,
                                    self.item_images[self.dragged_item.name],
                                    1
                                )
                                self.dragged_item.quantity -= 1
                            else:
                                self.table_crafting_grid[row][col], self.dragged_item = self.dragged_item, self.table_crafting_grid[row][col]
                        elif self.table_crafting_grid[row][col] and self.table_crafting_grid[row][col].quantity > 1:
                            half = self.table_crafting_grid[row][col].quantity // 2
                            self.dragged_item = InventoryItem(
                                self.table_crafting_grid[row][col].name,
                                self.item_images[self.table_crafting_grid[row][col].name],
                                half
                            )
                            self.table_crafting_grid[row][col].quantity -= half
                    self.check_table_recipe()
                    return

        
        result_x = table_start_x + 3 * (SLOT_SIZE + 20)
        result_y = table_start_y + SLOT_SIZE

        if result_x <= mouse_x <= result_x + SLOT_SIZE and result_y <= mouse_y <= result_y + SLOT_SIZE:
            if button == 1 and self.table_crafting_result:
                if not self.dragged_item:
                    self.dragged_item = self.table_crafting_result
                    self.table_crafting_result = None
                    
                    for r in range(3):
                        for c in range(3):
                            if self.table_crafting_grid[r][c]:
                                self.table_crafting_grid[r][c].quantity -= 1
                                if self.table_crafting_grid[r][c].quantity <= 0:
                                    self.table_crafting_grid[r][c] = None
                    self.check_table_recipe()
            return


    def draw_crafting_table(self, screen):
        """Dibuja la interfaz completa de la mesa + inventario + hotbar"""
        background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        background.fill((0, 0, 0, 180))
        screen.blit(background, (0, 0))

        
        inv_start_x = WIDTH // 2 - 350
        inv_start_y = HEIGHT // 2 - (INVENTORY_ROWS * SLOT_SIZE // 2)

        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                x = inv_start_x + (col * SLOT_SIZE)
                y = inv_start_y + (row * SLOT_SIZE)
                pygame.draw.rect(screen, SLOT_BORDER, (x, y, SLOT_SIZE, SLOT_SIZE))
                pygame.draw.rect(screen, SLOT_COLOR, (x + 2, y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
                if self.inventory[row][col]:
                    self._draw_item(screen, self.inventory[row][col], x, y)
        

        inv_title = self.font.render("Inventario", True, WHITE)
        screen.blit(inv_title, (inv_start_x, inv_start_y - 35))

        
        table_start_x = WIDTH // 2 + 100
        table_start_y = HEIGHT // 2 - (3 * SLOT_SIZE // 2)

        for row in range(3):
            for col in range(3):
                x = table_start_x + col * (SLOT_SIZE + 10)
                y = table_start_y + row * (SLOT_SIZE + 10)
                pygame.draw.rect(screen, SLOT_BORDER, (x, y, SLOT_SIZE, SLOT_SIZE))
                pygame.draw.rect(screen, SLOT_COLOR, (x + 2, y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
                if self.table_crafting_grid[row][col]:
                    self._draw_item(screen, self.table_crafting_grid[row][col], x, y)

        
        result_x = table_start_x + 3 * (SLOT_SIZE + 20)
        result_y = table_start_y + SLOT_SIZE
        pygame.draw.rect(screen, SLOT_BORDER, (result_x, result_y, SLOT_SIZE, SLOT_SIZE))
        pygame.draw.rect(screen, SLOT_COLOR, (result_x + 2, result_y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
        if self.table_crafting_result:
            self._draw_item(screen, self.table_crafting_result, result_x, result_y)

        table_title = self.font.render("Mesa de Crafteo", True, WHITE)
        screen.blit(table_title, (table_start_x, table_start_y - 35))

        
        self._draw_hotbar(screen)
        self._draw_hand_slots(screen)
        
        if self.dragged_item:
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(self.dragged_item.image,
                        (mouse_pos[0] - self.dragged_item.drag_offset[0],
                         mouse_pos[1] - self.dragged_item.drag_offset[1]))
            
            if self.dragged_item.quantity > 1:
                text = self.font.render(str(self.dragged_item.quantity), True, constants.WHITE)
                text_rect = text.get_rect()
                text_rect.bottomright = (mouse_pos[0] + self.dragged_item.image.get_width() // 2 - 5,
                                         mouse_pos[1] + self.dragged_item.image.get_height() // 2 - 5)
                screen.blit(text, text_rect)



    """funciones que nada mas para cambiar de estados, digamos que son como auxiliares"""
    def open_table_crafting(self):
        self.table_crafting_open = True
        print("🪵 Mesa de crafteo abierta")

    def close_table_crafting(self):
        self.table_crafting_open = False
        print("🪵 Mesa de crafteo cerrada")


# ------------------------------
# 🔥 HORNO - VERSIÓN CORREGIDA
# ------------------------------

    def open_furnace(self, furnace_obj):
        """Activa la interfaz del horno."""
        self.active_furnace = furnace_obj
        self.furnace_open = True
        print("🔥 Horno abierto.")

    def close_furnace(self):
        self.furnace_open = False
        self.active_furnace = None
        print("❌ Horno cerrado.")

    def handle_furnace_click(self, pos, button):
        """Maneja clicks dentro de la interfaz combinada: inventario + horno + hotbar - MISMOS QUE MESA"""
        if not hasattr(self, 'furnace_open') or not self.furnace_open:
            return
        if not hasattr(self, 'active_furnace') or not self.active_furnace:
            return

        mouse_x, mouse_y = pos
        furnace = self.active_furnace

        # === 1️⃣ INVENTARIO (MISMA LÓGICA QUE MESA) ===
        inv_start_x = WIDTH // 2 - 350
        inv_start_y = HEIGHT // 2 - (INVENTORY_ROWS * SLOT_SIZE // 2)

        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                x = inv_start_x + (col * SLOT_SIZE)
                y = inv_start_y + (row * SLOT_SIZE)
                if x <= mouse_x <= x + SLOT_SIZE and y <= mouse_y <= y + SLOT_SIZE:
                    if button == 1:  # Click izquierdo
                        if self.dragged_item:
                            if self.inventory[row][col] is None:
                                self.inventory[row][col] = self.dragged_item
                                self.dragged_item = None
                            else:
                                # Intercambiar
                                self.inventory[row][col], self.dragged_item = self.dragged_item, self.inventory[row][col]
                        elif self.inventory[row][col]:
                            # Agarrar item
                            self.dragged_item = self.inventory[row][col]
                            self.inventory[row][col] = None
                    elif button == 3:  # Click derecho
                        self._handle_right_click_grid(row, col, x, y)
                    return

        # === 2️⃣ HOTBAR (MISMA LÓGICA QUE MESA) ===
        hotbar_start_x = HOTBAR_X
        hotbar_start_y = HOTBAR_Y

        for i in range(HOTBAR_SLOTS):
            x = hotbar_start_x + i * SLOT_SIZE
            y = hotbar_start_y
            if x <= mouse_x <= x + SLOT_SIZE and y <= mouse_y <= y + SLOT_SIZE:
                if button == 1:  # Click izquierdo
                    if self.dragged_item:
                        if self.hotbar[i] is None:
                            self.hotbar[i] = self.dragged_item
                            self.dragged_item = None
                        else:
                            # Intercambiar
                            self.hotbar[i], self.dragged_item = self.dragged_item, self.hotbar[i]
                    elif self.hotbar[i]:
                        # Agarrar item
                        self.dragged_item = self.hotbar[i]
                        self.hotbar[i] = None
                elif button == 3:  # Click derecho
                    self._handle_right_click(self.hotbar, i, x, y)
                return

        # === 3️⃣ SLOTS DEL HORNO ===
        furnace_start_x = WIDTH // 2 + 100
        furnace_start_y = HEIGHT // 2 - (SLOT_SIZE // 2)

        # Definir áreas de los slots del horno
        input_rect = pygame.Rect(furnace_start_x, furnace_start_y, SLOT_SIZE, SLOT_SIZE)
        fuel_rect = pygame.Rect(furnace_start_x + SLOT_SIZE + 40, furnace_start_y, SLOT_SIZE, SLOT_SIZE)
        output_rect = pygame.Rect(furnace_start_x + 2 * (SLOT_SIZE + 40), furnace_start_y, SLOT_SIZE, SLOT_SIZE)

        # --- SLOT DE ENTRADA (INPUT) ---
        if input_rect.collidepoint(mouse_x, mouse_y):
            if button == 1:  # Click izquierdo
                if self.dragged_item:
                    if furnace.input_slot is None:
                        furnace.input_slot = self.dragged_item
                        self.dragged_item = None
                    else:
                        # Intercambiar
                        furnace.input_slot, self.dragged_item = self.dragged_item, furnace.input_slot
                elif furnace.input_slot:
                    # Agarrar item
                    self.dragged_item = furnace.input_slot
                    furnace.input_slot = None
            elif button == 3:  # Click derecho
                self._handle_right_click_furnace_slot('input')
            return

        # --- SLOT DE COMBUSTIBLE (FUEL) ---
        if fuel_rect.collidepoint(mouse_x, mouse_y):
            if button == 1:  # Click izquierdo
                if self.dragged_item:
                    # Si es madera, colocarla en el slot de combustible
                    if self.dragged_item.name == "wood":
                        if furnace.fuel_slot is None:
                            furnace.fuel_slot = self.dragged_item
                            self.dragged_item = None
                            print(f"🪵 Madera colocada como combustible: {furnace.fuel_slot.quantity} unidades")
                        else:
                            # Si ya hay madera, intercambiar
                            furnace.fuel_slot, self.dragged_item = self.dragged_item, furnace.fuel_slot
                    else:
                        print(f"❌ {self.dragged_item.name} no es combustible válido (solo madera)")
                elif furnace.fuel_slot:
                    # Agarrar combustible
                    self.dragged_item = furnace.fuel_slot
                    furnace.fuel_slot = None
                    print("🪵 Combustible removido")
            elif button == 3:  # Click derecho
                self._handle_right_click_furnace_slot('fuel')
            return

        # === 4️⃣ MANOS (LEFT/RIGHT HAND) ===
        if LEFT_HAND_SLOT_X <= mouse_x <= LEFT_HAND_SLOT_X + SLOT_SIZE and HOTBAR_Y <= mouse_y <= HOTBAR_Y + SLOT_SIZE:
            self._handle_hand_slot_click(button, 'left')
            return
        
        if RIGHT_HAND_SLOT_X <= mouse_x <= RIGHT_HAND_SLOT_X + SLOT_SIZE and HOTBAR_Y <= mouse_y <= HOTBAR_Y + SLOT_SIZE:
            self._handle_hand_slot_click(button, 'right')
            return

        # === 5️⃣ CLICK FUERA → DEVOLVER ITEM ARRASTRADO ===
        if self.dragged_item and button == 1:
            self._return_dragged_item()
            
        # --- SLOT DE SALIDA (OUTPUT) ---
        if output_rect.collidepoint(mouse_x, mouse_y):
            if button == 1:  # Click izquierdo
                if furnace.output_slot and not self.dragged_item:
                    # Agarrar el resultado si no tenemos nada arrastrado
                    self.dragged_item = furnace.output_slot
                    furnace.output_slot = None
                    print("✅ Resultado tomado del horno")
                elif furnace.output_slot and self.dragged_item:
                    # Si hay resultado y tenemos item arrastrado, intercambiar
                    furnace.output_slot, self.dragged_item = self.dragged_item, furnace.output_slot
                    print("🔄 Resultado intercambiado")
            elif button == 3 and furnace.output_slot:  # Click derecho
                # Dividir stack del resultado
                if furnace.output_slot.quantity > 1:
                    half = furnace.output_slot.quantity // 2
                    self.dragged_item = InventoryItem(
                        furnace.output_slot.name,
                        self.item_images[furnace.output_slot.name],
                        half
                    )
                    furnace.output_slot.quantity -= half
                    print(f"➗ Resultado dividido: {half} unidades")
            return

    def _handle_right_click_furnace_slot(self, slot_type):
        """Maneja click derecho en slots del horno (dividir stacks)"""
        furnace = self.active_furnace
        if not furnace:
            return

        if slot_type == 'input':
            slot = furnace.input_slot
        elif slot_type == 'fuel':
            slot = furnace.fuel_slot
        else:
            return

        if self.dragged_item:
            # Si hay item arrastrado, intentar colocar 1 unidad
            if slot is None and self.dragged_item.quantity > 1:
                # Crear nuevo item con 1 unidad
                new_item = InventoryItem(
                    self.dragged_item.name,
                    self.item_images[self.dragged_item.name],
                    1
                )
                if slot_type == 'input':
                    furnace.input_slot = new_item
                else:
                    furnace.fuel_slot = new_item
                self.dragged_item.quantity -= 1
            elif slot and slot.name == self.dragged_item.name:
                # Si son del mismo tipo, agregar 1 unidad
                max_stack = self.stackable_items.get(slot.name, 1)
                if slot.quantity < max_stack:
                    slot.quantity += 1
                    self.dragged_item.quantity -= 1
                    if self.dragged_item.quantity <= 0:
                        self.dragged_item = None
        elif slot and slot.quantity > 1:
            # Dividir stack a la mitad
            half = slot.quantity // 2
            if half > 0:
                self.dragged_item = InventoryItem(
                    slot.name,
                    self.item_images[slot.name],
                    half
                )
                slot.quantity -= half

    def draw_furnace(self, screen):
        """Dibuja la interfaz completa del horno + inventario + hotbar."""
        if not hasattr(self, "furnace_open") or not self.furnace_open:
            return
        if not hasattr(self, "active_furnace") or not self.active_furnace:
            return

        furnace = self.active_furnace

        # Fondo translúcido
        background = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        background.fill((0, 0, 0, 180))
        screen.blit(background, (0, 0))

        # === INVENTARIO ===
        inv_start_x = WIDTH // 2 - 350
        inv_start_y = HEIGHT // 2 - (INVENTORY_ROWS * SLOT_SIZE // 2)

        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):
                x = inv_start_x + (col * SLOT_SIZE)
                y = inv_start_y + (row * SLOT_SIZE)
                pygame.draw.rect(screen, SLOT_BORDER, (x, y, SLOT_SIZE, SLOT_SIZE))
                pygame.draw.rect(screen, SLOT_COLOR, (x + 2, y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
                if self.inventory[row][col]:
                    self._draw_item(screen, self.inventory[row][col], x, y)

        inv_title = self.font.render("Inventario", True, WHITE)
        screen.blit(inv_title, (inv_start_x, inv_start_y - 35))

        # === HORNO ===
        furnace_start_x = WIDTH // 2 + 100
        furnace_start_y = HEIGHT // 2 - (SLOT_SIZE // 2)

        # Título del horno
        furnace_title = self.font.render("Horno", True, WHITE)
        screen.blit(furnace_title, (furnace_start_x, furnace_start_y - 60))

        # Slot de Entrada (Input) - MINERAL
        input_rect = pygame.Rect(furnace_start_x, furnace_start_y, SLOT_SIZE, SLOT_SIZE)
        pygame.draw.rect(screen, SLOT_BORDER, input_rect)
        pygame.draw.rect(screen, SLOT_COLOR, (input_rect.x + 2, input_rect.y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
        if furnace.input_slot:
            self._draw_item(screen, furnace.input_slot, input_rect.x, input_rect.y)
        
        # Etiqueta "Mineral"
        mineral_label = self.font.render("Mineral", True, WHITE)
        mineral_label_rect = mineral_label.get_rect(center=(furnace_start_x + SLOT_SIZE//2, furnace_start_y + SLOT_SIZE + 15))
        screen.blit(mineral_label, mineral_label_rect)

        # Flecha de proceso
        arrow_x = furnace_start_x + SLOT_SIZE + 15
        arrow_y = furnace_start_y + SLOT_SIZE // 2 - 10
        pygame.draw.polygon(screen, WHITE, [
            (arrow_x, arrow_y),
            (arrow_x + 20, arrow_y),
            (arrow_x + 10, arrow_y + 10)
        ])

        # Slot de Combustible (Fuel) - MADERA
        fuel_rect = pygame.Rect(furnace_start_x + SLOT_SIZE + 40, furnace_start_y, SLOT_SIZE, SLOT_SIZE)
        pygame.draw.rect(screen, SLOT_BORDER, fuel_rect)
        pygame.draw.rect(screen, (100, 80, 40), (fuel_rect.x + 2, fuel_rect.y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
        if furnace.fuel_slot:
            self._draw_item(screen, furnace.fuel_slot, fuel_rect.x, fuel_rect.y)
        
        # Etiqueta "Combustible"
        fuel_label = self.font.render("Combustible", True, WHITE)
        fuel_label_rect = fuel_label.get_rect(center=(furnace_start_x + SLOT_SIZE + 40 + SLOT_SIZE//2, furnace_start_y + SLOT_SIZE + 15))
        screen.blit(fuel_label, fuel_label_rect)

        # BARRA DE PROGRESO DE FUNDICIÓN
        progress_bar_width = 80
        progress_bar_height = 10
        progress_bar_x = furnace_start_x + SLOT_SIZE + 45
        progress_bar_y = furnace_start_y - 25
        
        # Fondo de la barra
        pygame.draw.rect(screen, (50, 50, 50), (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height))
        
        # Progreso actual (si está fundiendo)
        if furnace.burning and furnace.input_slot and furnace.timer > 0:
            progress_ratio = min(furnace.timer / 3000, 1.0)  # 3000ms = 3 segundos
            progress_width = int(progress_bar_width * progress_ratio)
            pygame.draw.rect(screen, (255, 165, 0), (progress_bar_x, progress_bar_y, progress_width, progress_bar_height))
        
        # Borde de la barra
        pygame.draw.rect(screen, WHITE, (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height), 1)
        
        # Texto de progreso
        progress_text = self.font.render("Fundición", True, WHITE)
        screen.blit(progress_text, (progress_bar_x, progress_bar_y - 20))

        # Flecha hacia output
        arrow2_x = furnace_start_x + 2 * SLOT_SIZE + 55
        arrow2_y = furnace_start_y + SLOT_SIZE // 2 - 10
        pygame.draw.polygon(screen, WHITE, [
            (arrow2_x, arrow2_y),
            (arrow2_x + 20, arrow2_y),
            (arrow2_x + 10, arrow2_y + 10)
        ])

        # Slot de Salida (Output) - RESULTADO
        output_rect = pygame.Rect(furnace_start_x + 2 * (SLOT_SIZE + 40), furnace_start_y, SLOT_SIZE, SLOT_SIZE)
        pygame.draw.rect(screen, SLOT_BORDER, output_rect)
        pygame.draw.rect(screen, SLOT_COLOR, (output_rect.x + 2, output_rect.y + 2, SLOT_SIZE - 4, SLOT_SIZE - 4))
        if furnace.output_slot:
            self._draw_item(screen, furnace.output_slot, output_rect.x, output_rect.y)
        
        # Etiqueta "Resultado"
        output_label = self.font.render("Resultado", True, WHITE)
        output_label_rect = output_label.get_rect(center=(furnace_start_x + 2 * (SLOT_SIZE + 40) + SLOT_SIZE//2, furnace_start_y + SLOT_SIZE + 15))
        screen.blit(output_label, output_label_rect)

        # === HOTBAR Y MANOS ===
        self._draw_hotbar(screen)
        self._draw_hand_slots(screen)

        # === ITEM ARRASTRADO ===
        if self.dragged_item:
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(self.dragged_item.image,
                        (mouse_pos[0] - self.dragged_item.drag_offset[0],
                        mouse_pos[1] - self.dragged_item.drag_offset[1]))
            
            if self.dragged_item.quantity > 1:
                text = self.font.render(str(self.dragged_item.quantity), True, WHITE)
                text_rect = text.get_rect()
                text_rect.bottomright = (mouse_pos[0] + self.dragged_item.image.get_width() // 2 - 5,
                                        mouse_pos[1] + self.dragged_item.image.get_height() // 2 - 5)
                screen.blit(text, text_rect)
                
    def all_items(self):
        """
        Devuelve una lista con todos los ítems del inventario:
        incluye hotbar, inventario principal y manos.
        """
        items = []

        # Inventario principal (2D list)
        if hasattr(self, "inventory"):
            for row in self.inventory:
                for slot in row:
                    if slot:
                        items.append(slot)

        # Hotbar
        if hasattr(self, "hotbar"):
            for slot in self.hotbar:
                if slot:
                    items.append(slot)

        # Manos
        if hasattr(self, "left_hand") and self.left_hand:
            items.append(self.left_hand)
        if hasattr(self, "right_hand") and self.right_hand:
            items.append(self.right_hand)

        return items
