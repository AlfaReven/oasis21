import pygame
import constants
from constants import *
from elements import Tree, Smallstone, FarmLand, Water, MineralIron
import random
import os
from pygame import Surface
from enemy import Enemy, RangedEnemy  
from placeable import *

class WorldChunk: 
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.farmland_tiles = {}
        self.water_tiles = {}
        self.iron_minerals = []
        
        
        
        chunk_seed = hash(f"{x},{y}")
        old_state = random.getstate()
        random.seed(chunk_seed)
        
        self.trees = [
            Tree(self.x + random.randint(50, width - constants.TREE - 50), 
                self.y + random.randint(50, height - constants.TREE - 50)
                ) for _ in range(5)
        ]
        self.small_stones = [
            Smallstone(self.x + random.randint(50, width - constants.SMALL_STONE - 50),
                       self.y + random.randint(50, height - constants.SMALL_STONE - 50)
                       ) for _ in range(10)
        ]
        
        self.generate_surface_iron()
        
        #generar el agua de los lagos
        if random.random() < WATER_GENERATION_PROBABILITY:
            center_x = self.x + random.randint(0, width)
            center_y = self.y + random.randint(0, height)
            radius = random.randint(3, 5) * GRASS
            
            for y_offset in range(-int(radius), int(radius) + 1, GRASS):
                for x_offset in range(-int(radius), int(radius) + 1, GRASS):
                    tile_x = center_x + x_offset
                    tile_y = center_y + y_offset
                    
                    if ((x_offset ** 2 + y_offset ** 2) < radius ** 2 and
                        self.x <= tile_x < self.x + width and
                        self.y <= tile_y < self.y + height):
                        
                        grid_x = (tile_x // GRASS) * GRASS
                        grid_y = (tile_y // GRASS) * GRASS
                        
                        tile_key = (grid_x, grid_y)
                        self.water_tiles[tile_key] = Water(grid_x, grid_y)
        
        # Mezclar tipos de enemigos
        self.enemies = []
        for _ in range(5):
            enemy_x = self.x + random.randint(50, width - ENTITY - 50)
            enemy_y = self.y + random.randint(50, height - ENTITY - 50)
            
            # 70% enemigos básicos, 30% a distancia
            if random.random() < 0.3:
                self.enemies.append(RangedEnemy(enemy_x, enemy_y, "ranged"))
            else:
                self.enemies.append(Enemy(enemy_x, enemy_y, "basic"))
        
        random.setstate(old_state)
        
    def generate_surface_iron(self):
        for _ in range(20):  
            iron_x = self.x + random.randint(0, self.width - MINERAL_IRON)
            iron_y = self.y + random.randint(0, self.height - MINERAL_IRON)
            
            #verifica que se pueda poner es decir que no choque con arboles o algo
            if self.is_valid_iron_position(iron_x, iron_y):
                # Aplicar probabilidad
                if random.random() < MINERAL_IRON_PROBABILITY:
                    self.iron_minerals.append(MineralIron(iron_x, iron_y))
    
    def is_valid_iron_position(self, x, y):
        iron_rect = pygame.Rect(x, y, MINERAL_IRON, MINERAL_IRON)
        

        for tree in self.trees:
            tree_rect = pygame.Rect(tree.x, tree.y, tree.size, tree.size)
            if iron_rect.colliderect(tree_rect):
                return False
        

        for stone in self.small_stones:
            stone_rect = pygame.Rect(stone.x, stone.y, stone.size, stone.size)
            if iron_rect.colliderect(stone_rect):
                return False
        

        for water_pos in self.water_tiles.keys():
            water_rect = pygame.Rect(water_pos[0], water_pos[1], constants.GRASS, constants.GRASS)
            if iron_rect.colliderect(water_rect):
                return False
        
        for iron in self.iron_minerals:
            existing_iron_rect = pygame.Rect(iron.x, iron.y, iron.size, iron.size)
            if iron_rect.colliderect(existing_iron_rect):
                return False
        
        return True
        
    def update(self, player, dt, bullets_group, current_time):

        for enemy in self.enemies[:]:
            if hasattr(enemy, 'update_with_bullets'):
                enemy.update_with_bullets(dt, player, [], bullets_group, current_time)
            elif hasattr(enemy, 'update_ranged'):
                enemy.update_ranged(dt, player, [], bullets_group, current_time)
            else:
                enemy.update(dt, player, [])
                
                
            if enemy.is_dead():
                self.enemies.remove(enemy)
        
    def draw(self, screen, grass_image, camera_x, camera_y, player=None, dt=0, bullets_group=None, current_time=0):
       
        chunk_screen_x = self.x - camera_x
        chunk_screen_y = self.y - camera_y
        
        # CALCULAR EL RANGO DE LOS TILES
        start_x = max(0, (camera_x - self.x - constants.GRASS) // constants.GRASS)
        end_x = min(self.width // constants.GRASS + 1, 
                    (camera_x + constants.WIDTH - self.x + constants.GRASS) // constants.GRASS + 1)
        start_y = max(0, (camera_y - self.y - constants.GRASS) // constants.GRASS)
        end_y = min(self.height // constants.GRASS + 1, 
                    (camera_y + constants.HEIGHT - self.y + constants.GRASS) // constants.GRASS + 1)
        
        for y in range(int(start_y), int(end_y)):
            for x in range(int(start_x), int(end_x)):
                tile_x = self.x + x * GRASS
                tile_y = self.y + y * GRASS
                screen_x = tile_x - camera_x
                screen_y = tile_y - camera_y
                
                tile_key = (tile_x, tile_y)
                
                if tile_key not in self.water_tiles:
                    if tile_key in self.farmland_tiles:
                        self.farmland_tiles[tile_key].draw(screen, camera_x, camera_y)
                    else:
                        screen.blit(grass_image, (screen_x, screen_y))
                
        # REMOVER ELEMENTOS AGOTADOS
        self.trees = [tree for tree in self.trees if not tree.is_depleted()]
        self.small_stones = [stone for stone in self.small_stones if not stone.is_depleted()]
        self.iron_minerals = [iron for iron in self.iron_minerals if not iron.is_depleted()]
        
        #REMOVER ENEMGIOS VENCIDOS
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_dead()]
        
        # DIBUJAR PIEDRAS
        for stone in self.small_stones:
            stone.draw(screen, camera_x, camera_y)
                
        # DIBUJAR ÁRBOLES
        for tree in self.trees:
            tree.draw(screen, camera_x, camera_y)
            
        #DIBUJAR EL HIERRO ENCIMA 
        for iron in self.iron_minerals:
            iron.draw(screen, camera_x, camera_y)
            
        #DIBUJAR EL AGUA ENCIMA DEL PASTO Y DE LAS PIEDRAS
        for tile_key, water in self.water_tiles.items():
            water.draw(screen, camera_x, camera_y)
        
        
            
            
        # DIBUJAR ENEMIGOS
        for enemy in self.enemies:
            enemy_screen_x = enemy.x - camera_x
            enemy_screen_y = enemy.y - camera_y
            if (enemy_screen_x + enemy.size >= 0 and enemy_screen_x <= constants.WIDTH and
                enemy_screen_y + enemy.size >= 0 and enemy_screen_y <= constants.HEIGHT):
                enemy.draw(screen, camera_x, camera_y)
    
    def update_water(self, dt):
        for water in self.water_tiles.values():
            water.update(dt)       
                
        

class World:
    def __init__(self, width, height):
        self.chunk_size = constants.CHUNK_SIZE
        self.active_chunks = {}  
        self.inactive_chunks = {}
        #nuevo atributo para items que se pueden colocar
        self.placeable_objects = []
        
        
        self.view_width = width
        self.view_height = height
        
        grass_path = os.path.join('assets', 'images', 'grass.png')
        self.grass_image = pygame.image.load(grass_path).convert()
        self.grass_image = pygame.transform.scale(self.grass_image, (constants.GRASS, constants.GRASS))
        
        # Parámetros de día y noche 
        self.current_time = constants.MORNING_TIME
        self.day_overlay = Surface((width, height))
        self.day_overlay.fill(constants.DAY_COLOR)
        self.day_overlay.set_alpha(0)
        
        # Generar chunks iniciales
        self.generate_chunk(0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                self.generate_chunk(dx, dy)
    
    def get_chunk_key(self, x, y):

        chunk_x = x // self.chunk_size
        chunk_y = y // self.chunk_size
        return (chunk_x, chunk_y)
    
    def generate_chunk(self, chunk_x, chunk_y):
        key = (chunk_x, chunk_y)
        if key not in self.active_chunks:
            if key in self.inactive_chunks:
                self.active_chunks[key] = self.inactive_chunks[key]
                del self.inactive_chunks[key]
            else:
                x = chunk_x * self.chunk_size
                y = chunk_y * self.chunk_size
                self.active_chunks[key] = WorldChunk(x, y, self.chunk_size, self.chunk_size)
    
    def update_chunks(self, player_x, player_y):
        current_chunk = self.get_chunk_key(player_x, player_y)
        
   
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                chunk_x = current_chunk[0] + dx
                chunk_y = current_chunk[1] + dy    
                self.generate_chunk(chunk_x, chunk_y)     
        

        chunks_to_move = []
        for chunk_key in self.active_chunks:  
            distance_x = abs(chunk_key[0] - current_chunk[0])
            distance_y = abs(chunk_key[1] - current_chunk[1]) 
            if distance_x > 2 or distance_y > 2:
                chunks_to_move.append(chunk_key)
                
        for chunk_key in chunks_to_move:
            self.inactive_chunks[chunk_key] = self.active_chunks[chunk_key]
            del self.active_chunks[chunk_key]  
    
    def update(self, player, dt, bullets_group, current_time):
        self.update_chunks(player.x, player.y)
        
 
        for chunk in self.active_chunks.values():  
            chunk.update(player, dt, bullets_group, current_time)
   
        self.update_time(dt)
    
    def update_time(self, dt):
        """Actualizar el ciclo día/noche"""
        self.current_time = (self.current_time + dt) % constants.DAY_LENGTH
        alpha = 0
        
        # CALCULAR EL COLOR Y LA INTENSIDAD BASADO EN LA HORA DEL DIA
        if constants.MORNING_TIME <= self.current_time <= constants.DUSK_TIME:
            self.day_overlay.fill(constants.DAY_COLOR)
            alpha = 0
            
        elif constants.DAWN_TIME <= self.current_time <= constants.MORNING_TIME:
            self.day_overlay.fill(constants.NINGHT_COLOR)
            morning_progress = (self.current_time - constants.DAWN_TIME) / (
                                constants.MORNING_TIME - constants.DAWN_TIME)
            alpha = int(constants.MAX_DARKNESS * (1 - morning_progress))  
        elif constants.DUSK_TIME <= self.current_time <= constants.MIDNIGHT:
            self.day_overlay.fill(constants.NINGHT_COLOR)
            night_progress = (self.current_time - constants.DUSK_TIME) / (
                constants.MIDNIGHT - constants.DUSK_TIME)
            alpha = int(constants.MAX_DARKNESS * night_progress)
        else:
            self.day_overlay.fill(constants.NINGHT_COLOR)
            alpha = constants.MAX_DARKNESS
             
        self.day_overlay.set_alpha(alpha)
        
        for chunk in self.active_chunks.values():
            chunk.update_water(dt)
    
    def draw(self, screen, camera_x, camera_y, bullets_group=None, current_time=0):
        """Dibujar el mundo"""
        for chunk in self.active_chunks.values():  
            chunk.draw(screen, self.grass_image, camera_x, camera_y, 
                      bullets_group=bullets_group, current_time=current_time)
        screen.blit(self.day_overlay, (0, 0))

    def draw_inventory(self, screen, character):
        """Dibujar interfaz de inventario"""
        font = pygame.font.Font(None, 24)
        instruction_text = font.render("Press 'I' to open inventory", True, constants.WHITE)
        screen.blit(instruction_text, (10, 10))
        
            
    def add_placeable(self, object_type, x, y):
        """Agrega un objeto colocable verificando colisiones"""
        from placeable import CraftingTable  # Import aquí para evitar circular
        
        # Mapeo de tipos de items a clases Placeable
        placeable_map = {
            'work_bench': CraftingTable,
            # Agregar más después: 'furnace': Furnace, etc.
        }
        
        if object_type not in placeable_map:
            print(f"❌ {object_type} no es un objeto colocable")
            return False
        
        # Crear objeto temporal para verificar colisiones
        temp_obj = placeable_map[object_type](x, y)
        
        # Verificar colisiones con obstáculos existentes
        if self._check_placeable_collision(temp_obj):
            print(f"❌ Colisión detectada al colocar {object_type}")
            return False
            
        # Verificar colisiones con otros objetos colocables
        for existing_obj in self.placeable_objects:
            if self._objects_collide(temp_obj, existing_obj):
                print(f"❌ Demasiado cerca de otro objeto")
                return False
        
        # Si no hay colisiones, agregar el objeto real
        obj = placeable_map[object_type](x, y)
        self.placeable_objects.append(obj)
        print(f"✅ {object_type} colocado en ({x:.1f}, {y:.1f})")
        return True

    def _check_placeable_collision(self, placeable_obj):
        """Verifica colisiones con obstáculos del mundo"""
        temp_rect = pygame.Rect(
            placeable_obj.x - placeable_obj.size//2, 
            placeable_obj.y - placeable_obj.size//2, 
            placeable_obj.size * 0.75, 
            placeable_obj.size * 0.75
        )
        
        # Verificar colisiones con árboles
        for tree in self.trees:
            if temp_rect.colliderect(tree.rect):
                return True
                
        # Verificar colisiones con piedras
        for stone in self.small_stones:
            if temp_rect.colliderect(stone.rect):
                return True
                
        # Verificar colisiones con minerales
        for mineral in self.iron_minerals:
            if temp_rect.colliderect(mineral.rect):
                return True
                
        return False

    def _objects_collide(self, obj1, obj2):
        """Verifica si dos objetos están muy cerca"""
        return (abs(obj1.x - obj2.x) < obj1.size and 
                abs(obj1.y - obj2.y) < obj1.size)

    def get_nearby_placeable(self, player):
        """Encuentra objetos colocables cercanos usando is_near"""
        for obj in self.placeable_objects:
            if obj.is_near(player):
                return obj
        return None

    def draw_placeables(self, screen, camera_x, camera_y):
        """Dibuja todos los objetos colocables"""
        for obj in self.placeable_objects:
            obj.draw(screen, camera_x, camera_y)

    def update_placeables(self, dt):
        """Actualiza objetos colocables (si tienen animaciones o lógica propia)"""
        for obj in self.placeable_objects:
            if hasattr(obj, 'update'):
                obj.update(dt)

            
    # Propiedades para obtener todos los elementos de los chunks activos
    @property
    def trees(self):
        all_trees = []
        for chunk in self.active_chunks.values():  
            all_trees.extend(chunk.trees)
        return all_trees
        
    @property
    def small_stones(self):
        all_stones = []
        for chunk in self.active_chunks.values():  
            all_stones.extend(chunk.small_stones)
        return all_stones
    
    @property
    def water_tiles(self):
        all_water = {}
        for chunk in self.active_chunks.values():
            all_water.update(chunk.water_tiles)
        return all_water
    
    @property
    def iron_minerals(self):
        all_iron = []
        for chunk in self.active_chunks.values():  
            all_iron.extend(chunk.iron_minerals)
        return all_iron
    
    
    def add_farmland(self, x, y):
        chunk_key = self.get_chunk_key(x, y)
        chunk = self.active_chunks.get(chunk_key)
        
        if chunk:
            grid_x = (x // GRASS) * GRASS
            grid_y = (y // GRASS) * GRASS
            
            for tree in chunk.trees:
                if(grid_x < tree.x + tree.size and grid_x + GRASS > tree.x and
                   grid_y < tree.y + tree.size and grid_y + GRASS > tree.y):
                    return False
            
            for stone in chunk.small_stones:
                if(grid_x < stone.x + stone.size and grid_x + GRASS > stone.x and
                   grid_y < stone.y + stone.size and grid_y + GRASS > stone.y):
                    return False
            
            for iron in chunk.iron_minerals:
                if(grid_x < iron.x + iron.size and grid_x + GRASS > iron.x and
                grid_y < iron.y + iron.size and grid_y + GRASS > iron.y):
                    return False
                
                
            tile_key = (grid_x, grid_y)
            if tile_key in chunk.water_tiles:
                return False
            
            if tile_key not in chunk.farmland_tiles:
                chunk.farmland_tiles[tile_key] = FarmLand(grid_x, grid_y)
                return True
        return False
    
    def is_water_at(self, x, y):
        chunk_key = self.get_chunk_key(x, y)
        chunk = self.active_chunks.get(chunk_key)
        
        if chunk:
            grid_x = (x // GRASS) * GRASS
            grid_y = (y // GRASS) * GRASS
            
            tile_key = (grid_x, grid_y)
            return tile_key in chunk.water_tiles
        return False
                
    @property
    def enemies(self):
        all_enemies = []
        for chunk in self.active_chunks.values():  
            all_enemies.extend(chunk.enemies)
        return all_enemies