import pygame
import constants
from constants import *
from elements import Tree, Smallstone, FarmLand, Water, MineralIron, Well, MineralCopper
import random
import os
from pygame import Surface
from enemy import Enemy, RangedEnemy  
from placeable import *
from pytmx.util_pygame import load_pygame

class WorldChunk: 
    def __init__(self, x, y, width, height, world_reference=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.world = world_reference
        self.farmland_tiles = {}
        self.water_tiles = {}
        self.iron_minerals = []
        self.copper_minerals = []
        self.wells = []
        self.trees = []
        self.small_stones = []
        self.enemies = []
        
        # CHUNK INICIAL (0,0) - USAR TMX Y NO GENERAR NADA
        if x == 0 and y == 0:
            self.width = 1536
            self.height = 1024
        else:
            self._generate_chunk_content()
        
    def _generate_chunk_content(self):
        """Genera el contenido para chunks normales (no el inicial)"""
        chunk_seed = hash(f"{self.x},{self.y}")
        old_state = random.getstate()
        random.seed(chunk_seed)
        
        # Generar árboles y piedras
        self.trees = [
            Tree(self.x + random.randint(50, self.width - constants.TREE - 50), 
                self.y + random.randint(50, self.height - constants.TREE - 50)
                ) for _ in range(5)
        ]
        
        self.small_stones = [
            Smallstone(self.x + random.randint(50, self.width - constants.SMALL_STONE - 50),
                       self.y + random.randint(50, self.height - constants.SMALL_STONE - 50)
                       ) for _ in range(10)
        ]
        
        # Generar recursos
        self.generate_surface_resource(MineralIron, self.iron_minerals, MINERAL_IRON, MINERAL_IRON_PROBABILITY)
        self.generate_surface_resource(MineralCopper, self.copper_minerals, MINERAL_COPPER, MINERAL_COPPER_PROBABILITY)

        # Generar agua
        self._generate_water()
        
        # Generar pozos
        self._generate_wells()
        
        # Generar enemigos
        self._generate_enemies()
        
        random.setstate(old_state)
    
    def _generate_water(self):
        """Genera cuerpos de agua en el chunk"""
        if random.random() < WATER_GENERATION_PROBABILITY:
            center_x = self.x + random.randint(0, self.width)
            center_y = self.y + random.randint(0, self.height)
            radius = random.randint(3, 5) * GRASS
            
            for y_offset in range(-int(radius), int(radius) + 1, GRASS):
                for x_offset in range(-int(radius), int(radius) + 1, GRASS):
                    tile_x = center_x + x_offset
                    tile_y = center_y + y_offset
                    
                    if ((x_offset ** 2 + y_offset ** 2) < radius ** 2 and
                        self.x <= tile_x < self.x + self.width and
                        self.y <= tile_y < self.y + self.height):
                        
                        grid_x = (tile_x // GRASS) * GRASS
                        grid_y = (tile_y // GRASS) * GRASS
                        
                        tile_key = (grid_x, grid_y)
                        self.water_tiles[tile_key] = Water(grid_x, grid_y)
    
    def _generate_wells(self):
        """Genera pozos en el chunk"""
        if random.random() < WELL_GENERATION_PROBABILITY:
            well_x = self.x + random.randint(0, self.width)
            well_y = self.y + random.randint(0, self.height)
            
            # Evita ponerlo sobre árboles o agua
            if all(not pygame.Rect(well_x, well_y, GRASS, GRASS).colliderect(obj.rect)
                for obj in (self.trees + self.small_stones + list(self.water_tiles.values()))):
                self.wells.append(Well(well_x, well_y))
    
    def _generate_enemies(self):
        """Genera enemigos en el chunk"""
        for _ in range(5):
            enemy_x = self.x + random.randint(50, self.width - ENTITY - 50)
            enemy_y = self.y + random.randint(50, self.height - ENTITY - 50)
            
            # 70% enemigos básicos, 30% a distancia
            if random.random() < 0.3:
                self.enemies.append(RangedEnemy(enemy_x, enemy_y, "ranged"))
            else:
                self.enemies.append(Enemy(enemy_x, enemy_y, "basic"))

    def generate_surface_resource(self, resource_class, resource_list, size, probability):
        """Genera minerales o recursos superficiales de forma genérica."""
        for _ in range(20):
            rx = self.x + random.randint(0, self.width - size)
            ry = self.y + random.randint(0, self.height - size)

            if self.is_valid_resource_position(rx, ry, size, resource_list):
                if random.random() < probability:
                    resource_list.append(resource_class(rx, ry))

    def is_valid_resource_position(self, x, y, size, existing_list):
        """Verifica que un recurso no colisione con obstáculos."""
        test_rect = pygame.Rect(x, y, size, size)

        # Verificar colisiones con todos los obstáculos
        obstacles = (self.trees + self.small_stones + 
                    list(self.water_tiles.values()) + existing_list)
        
        for obj in obstacles:
            if hasattr(obj, 'rect') and test_rect.colliderect(obj.rect):
                return False

        return True
        
    def update(self, player, dt, bullets_group, current_time):
        """Actualiza el estado del chunk"""
        # Actualizar enemigos
        for enemy in self.enemies[:]:
            if hasattr(enemy, 'update_with_bullets'):
                enemy.update_with_bullets(dt, player, [], bullets_group, current_time)
            elif hasattr(enemy, 'update_ranged'):
                enemy.update_ranged(dt, player, [], bullets_group, current_time)
            else:
                enemy.update(dt, player, [])
                
            if enemy.is_dead():
                self.enemies.remove(enemy)
        
        # Limpiar elementos agotados
        self._cleanup_depleted_elements()
    
    def _cleanup_depleted_elements(self):
        """Remueve elementos agotados del chunk"""
        self.trees = [tree for tree in self.trees if not tree.is_depleted()]
        self.small_stones = [stone for stone in self.small_stones if not stone.is_depleted()]
        self.iron_minerals = [iron for iron in self.iron_minerals if not iron.is_depleted()]
        self.copper_minerals = [copper for copper in self.copper_minerals if not copper.is_depleted()]
        self.wells = [well for well in self.wells if not well.is_depleted()]
        self.enemies = [enemy for enemy in self.enemies if not enemy.is_dead()]
    
    def draw_normal_chunk(self, screen, grass_image, camera_x, camera_y, bullets_group=None, current_time=0):
        """Dibujar chunks normales (no el inicial)"""
        # Dibujar tiles base
        self._draw_base_tiles(screen, grass_image, camera_x, camera_y)
        
        # Dibujar elementos
        self._draw_elements(screen, camera_x, camera_y)
    
    def _draw_base_tiles(self, screen, grass_image, camera_x, camera_y):
        """Dibuja los tiles base del chunk"""
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
    
    def _draw_elements(self, screen, camera_x, camera_y):
        """Dibuja todos los elementos del chunk"""
        # Piedras
        for stone in self.small_stones:
            stone.draw(screen, camera_x, camera_y)
                
        # Árboles
        for tree in self.trees:
            tree.draw(screen, camera_x, camera_y)
            
        # Minerales
        for iron in self.iron_minerals:
            iron.draw(screen, camera_x, camera_y)
        
        for copper in self.copper_minerals:
            copper.draw(screen, camera_x, camera_y)

        # Agua
        for water in self.water_tiles.values():
            water.draw(screen, camera_x, camera_y)
        
        # Pozos
        for well in self.wells:
            well.draw(screen, camera_x, camera_y)

        # Enemigos
        for enemy in self.enemies:
            enemy_screen_x = enemy.x - camera_x
            enemy_screen_y = enemy.y - camera_y
            if (enemy_screen_x + enemy.size >= 0 and enemy_screen_x <= constants.WIDTH and
                enemy_screen_y + enemy.size >= 0 and enemy_screen_y <= constants.HEIGHT):
                enemy.draw(screen, camera_x, camera_y)
    
    def update_water(self, dt):
        """Actualiza el estado del agua"""
        for water in self.water_tiles.values():
            water.update(dt)


class World:
    def __init__(self, width, height):
        self.chunk_width = CHUNK_WIDTH
        self.chunk_height = CHUNK_HEIGHT
        self.active_chunks = {}  
        self.inactive_chunks = {}
        self.placeable_objects = []
        
        self.view_width = width
        self.view_height = height
        
        # Cargar recursos
        self._load_resources()
        
        # Generar chunks iniciales
        self._generate_initial_chunks()
    
    def _load_resources(self):
        """Carga todos los recursos del mundo"""
        # Cargar TMX
        self.tmx_map = None
        self.load_tmx_map()

        # Cargar imagen de grass
        grass_path = os.path.join('assets', 'images', 'grass.png')
        self.grass_image = pygame.image.load(grass_path).convert()
        self.grass_image = pygame.transform.scale(self.grass_image, (constants.GRASS, constants.GRASS))
        
        # Configurar ciclo día/noche
        self.current_time = constants.MORNING_TIME
        self.day_overlay = Surface((self.view_width, self.view_height))
        self.day_overlay.fill(constants.DAY_COLOR)
        self.day_overlay.set_alpha(0)
    
    def load_tmx_map(self):
        """Cargar el archivo TMX del asentamiento"""
        try:
            tmx_path = os.path.join('assets', 'tilesets', 'nonito.tmx')
            self.tmx_map = load_pygame(tmx_path)
        except Exception as e:
            print(f"Error cargando TMX: {e}")
            self.tmx_map = None
    
    def _generate_initial_chunks(self):
        """Genera los chunks iniciales alrededor del origen"""
        self.generate_chunk(0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                self.generate_chunk(dx, dy)
    
    def get_chunk_key(self, x, y):
        """Obtiene la clave del chunk para coordenadas dadas"""
        chunk_x = x // CHUNK_WIDTH
        chunk_y = y // CHUNK_HEIGHT
        return (chunk_x, chunk_y)
    
    def generate_chunk(self, chunk_x, chunk_y):
        """Genera o reactiva un chunk"""
        key = (chunk_x, chunk_y)
        if key not in self.active_chunks:
            if key in self.inactive_chunks:
                self.active_chunks[key] = self.inactive_chunks[key]
                del self.inactive_chunks[key]
            else:
                x = chunk_x * self.chunk_width
                y = chunk_y * self.chunk_height
                self.active_chunks[key] = WorldChunk(x, y, self.chunk_width, self.chunk_height, self)
    
    def update_chunks(self, player_x, player_y):
        """Actualiza los chunks activos basado en la posición del jugador"""
        current_chunk = self.get_chunk_key(player_x, player_y)
        
        # Activar chunks cercanos
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                chunk_x = current_chunk[0] + dx
                chunk_y = current_chunk[1] + dy    
                self.generate_chunk(chunk_x, chunk_y)     
        
        # Desactivar chunks lejanos
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
        
        # Guardar referencia a los jugadores para verificación de colisiones
        self.players = [player]  # Puedes expandir esto para multijugador
        
        for chunk in self.active_chunks.values():  
            chunk.update(player, dt, bullets_group, current_time)
    
        self.update_time(dt)
        self.update_placeables(dt, player)
    
    def update_time(self, dt):
        """Actualizar el ciclo día/noche"""
        self.current_time = (self.current_time + dt) % constants.DAY_LENGTH
        alpha = 0
        
        # Calcular intensidad de la iluminación basado en la hora
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
        
        # Actualizar agua en todos los chunks
        for chunk in self.active_chunks.values():
            chunk.update_water(dt)
    
    def draw(self, screen, camera_x, camera_y, bullets_group=None, current_time=0):
        """Dibujar el mundo completo"""
        # Dibujar TMX primero
        if self.tmx_map:
            self.draw_tmx_map_full(screen, camera_x, camera_y)
        
        # Dibujar chunks normales
        for chunk in self.active_chunks.values():  
            if not (chunk.x == 0 and chunk.y == 0):
                chunk.draw_normal_chunk(screen, self.grass_image, camera_x, camera_y, bullets_group, current_time)
        
        # Dibujar objetos colocables
        self.draw_placeables(screen, camera_x, camera_y)
        
        # Overlay de día/noche
        screen.blit(self.day_overlay, (0, 0))

    def draw_tmx_map_full(self, screen, camera_x, camera_y):
        """Render exacto del mapa TMX"""
        if not self.tmx_map:
            return

        tile_w = self.tmx_map.tilewidth
        tile_h = self.tmx_map.tileheight
        scr_w, scr_h = screen.get_size()

        # Calcular rango visible
        start_x = int(camera_x // tile_w)
        start_y = int(camera_y // tile_h)
        end_x = int((camera_x + scr_w) // tile_w) + 1
        end_y = int((camera_y + scr_h) // tile_h) + 1

        # Limitar al tamaño del mapa
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(self.tmx_map.width, end_x)
        end_y = min(self.tmx_map.height, end_y)

        for layer_index, layer in enumerate(self.tmx_map.visible_layers):
            if not hasattr(layer, "data"):
                continue

            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    image = self.tmx_map.get_tile_image(x, y, layer_index)
                    if image:
                        px = round(x * tile_w - camera_x)
                        py = round(y * tile_h - camera_y)
                        screen.blit(image, (px, py))

    # === MÉTODOS PARA OBJETOS COLOCABLES ===
    
    def add_placeable(self, item_name, x, y):
        """Agrega objetos colocables al mundo si el espacio está libre."""
        # Determinar el tamaño base del objeto
        default_size = 96

        # Crear un objeto temporal solo para obtener su tamaño
        temp_obj = None
        if item_name == 'work_bench':
            temp_obj = CraftingTable(x, y)
        elif item_name == 'furnace':
            temp_obj = Furnace(x, y)
        elif item_name == 'pump':
            temp_obj = WaterPump(x, y)
        elif item_name == 'empty_tank':
            temp_obj = WaterTank(x, y)
        
        # Si no es un objeto conocido, salir
        if not temp_obj:
            return False
        
        size = getattr(temp_obj, "size", default_size)
        test_rect = pygame.Rect(x, y, size, size)

        # Para objetos grandes como Water Tank, usar una verificación más estricta
        if item_name == 'empty_tank':
            return self._place_large_object(item_name, x, y, size)
        else:
            return self._place_standard_object(item_name, x, y, size, test_rect)

    def _create_placeable_temp(self, item_name, x, y):
        """Crea un objeto temporal para verificación"""
        placeables = {
            'work_bench': CraftingTable,
            'furnace': Furnace,
            'pump': WaterPump,
            'empty_tank': WaterTank
        }
        return placeables.get(item_name, lambda x, y: None)(x, y)

    def _create_placeable(self, item_name, x, y):
        """Crea el objeto colocable definitivo"""
        placeables = {
            'work_bench': CraftingTable,
            'furnace': Furnace,
            'pump': WaterPump,
            'empty_tank': WaterTank
        }
        constructor = placeables.get(item_name)
        return constructor(x, y) if constructor else None

    def _find_valid_placeable_position(self, x, y, size, test_rect):
        """Encuentra una posición válida para colocar un objeto"""
        # Verificar posición inicial
        if not self._is_placeable_collision(test_rect):
            return x, y
        
        # Buscar posición alternativa
        offsets = [(size, 0), (-size, 0), (0, size), (0, -size)]
        for dx, dy in offsets:
            new_x, new_y = x + dx, y + dy
            new_rect = pygame.Rect(new_x, new_y, size, size)
            if not self._is_placeable_collision(new_rect):
                return new_x, new_y
        
        return None, None

    def _is_placeable_collision(self, rect):
        """Verifica colisiones para objetos colocables"""
        all_obstacles = (self.trees + self.small_stones + 
                        self.placeable_objects + self.wells +
                        self.iron_minerals + self.copper_minerals)
        
        for obj in all_obstacles:
            if hasattr(obj, "rect") and rect.colliderect(obj.rect):
                return True
        return False

    def get_nearby_placeable(self, player):
        """Devuelve el objeto colocable más cercano al jugador"""
        for obj in self.placeable_objects:
            if obj.is_near(player):
                return obj
        return None

    def draw_placeables(self, screen, camera_x, camera_y):
        """Dibuja todos los objetos colocables"""
        for obj in self.placeable_objects:
            obj.draw(screen, camera_x, camera_y)
            
    def _place_large_object(self, item_name, x, y, size):
        """Coloca objetos grandes con verificación de espacio extendida"""
        positions_to_try = [
            (x, y),  # posición original
            (x + size, y), (x - size, y), (x, y + size), (x, y - size),
            (x + size, y + size), (x - size, y - size),
            (x + size, y - size), (x - size, y + size)
        ]
        
        for pos_x, pos_y in positions_to_try:
            test_rect = pygame.Rect(pos_x - size // 2, pos_y - size // 2, size, size)
            
            # ✅ Llamada corregida (solo un argumento)
            if not self._is_placeable_collision(test_rect):
                return self._create_placeable_at_position(item_name, pos_x, pos_y)

        print("🚫 No hay espacio suficiente para colocar el objeto grande.")
        return False


    def _place_standard_object(self, item_name, x, y, size, test_rect):
        """Coloca objetos estándar con verificación normal"""
        # Evita colocar encima de árboles, piedras, pozos u otros objetos
        if not self._is_placeable_collision(test_rect, size):
            return self._create_placeable_at_position(item_name, x, y)
        
        # Buscar posición libre cercana
        offsets = [(size, 0), (-size, 0), (0, size), (0, -size)]
        for dx, dy in offsets:
            new_x, new_y = x + dx, y + dy
            new_rect = pygame.Rect(new_x, new_y, size, size)
            if not self._is_placeable_collision(new_rect, size):
                return self._create_placeable_at_position(item_name, new_x, new_y)
        
        return False

    def _create_placeable_at_position(self, item_name, x, y):
        """Crea el objeto colocable en la posición especificada"""
        if item_name == 'work_bench':
            new_obj = CraftingTable(x, y)
        elif item_name == 'furnace':
            new_obj = Furnace(x, y)
        elif item_name == 'pump':
            new_obj = WaterPump(x, y)
        elif item_name == 'empty_tank':
            new_obj = WaterTank(x, y)
        else:
            return False

        self.placeable_objects.append(new_obj)
        return True

    def _is_placeable_collision(self, rect, size=None):
        """Verifica colisiones para objetos colocables (con o sin tamaño específico)."""
        # Expandir ligeramente para evitar que queden pegados
        expanded_rect = rect.inflate(10, 10)
        
        all_obstacles = (self.trees + self.small_stones + 
                        self.placeable_objects + self.wells +
                        self.iron_minerals + self.copper_minerals)
        
        for obj in all_obstacles:
            if hasattr(obj, "rect") and expanded_rect.colliderect(obj.rect):
                return True
        
        # Verificar colisión con jugadores
        for player in getattr(self, 'players', []):
            if hasattr(player, 'rect') and expanded_rect.colliderect(player.rect):
                return True
        
        return False


    def update_placeables(self, dt, player):
        """Actualiza objetos colocables"""
        for obj in self.placeable_objects:
            if hasattr(obj, 'update'):
                try:
                    obj.update(dt, self, player)
                except TypeError:
                    obj.update(dt)

    # === PROPIEDADES PARA ACCEDER A ELEMENTOS DE CHUNKS ===
    
    def _get_chunk_elements(self, element_name):
        """Obtiene elementos de todos los chunks activos"""
        all_elements = []
        for chunk in self.active_chunks.values():  
            all_elements.extend(getattr(chunk, element_name, []))
        return all_elements
    
    def _get_chunk_dict_elements(self, element_name):
        """Obtiene elementos de diccionario de todos los chunks activos"""
        all_elements = {}
        for chunk in self.active_chunks.values():
            all_elements.update(getattr(chunk, element_name, {}))
        return all_elements
    
    @property
    def trees(self):
        return self._get_chunk_elements('trees')
        
    @property
    def small_stones(self):
        return self._get_chunk_elements('small_stones')
    
    @property
    def water_tiles(self):
        return self._get_chunk_dict_elements('water_tiles')
    
    @property
    def iron_minerals(self):
        return self._get_chunk_elements('iron_minerals')
    
    @property
    def copper_minerals(self):
        return self._get_chunk_elements('copper_minerals')
    
    @property
    def enemies(self):
        return self._get_chunk_elements('enemies')
    
    @property
    def wells(self):
        return self._get_chunk_elements('wells')

    # === MÉTODOS PARA INTERACCIÓN CON EL MUNDO ===
    
    def add_farmland(self, x, y):
        """Agrega terreno de cultivo en la posición especificada"""
        chunk_key = self.get_chunk_key(x, y)
        chunk = self.active_chunks.get(chunk_key)
        
        if not chunk:
            return False
            
        grid_x = (x // GRASS) * GRASS
        grid_y = (y // GRASS) * GRASS
        
        # Verificar colisiones
        if self._is_farmland_collision(chunk, grid_x, grid_y):
            return False
        
        # Agregar farmland
        tile_key = (grid_x, grid_y)
        if tile_key not in chunk.farmland_tiles:
            chunk.farmland_tiles[tile_key] = FarmLand(grid_x, grid_y)
            return True
        return False

    def _is_farmland_collision(self, chunk, grid_x, grid_y):
        """Verifica colisiones para farmland"""
        farmland_rect = pygame.Rect(grid_x, grid_y, GRASS, GRASS)
        
        # Verificar todos los obstáculos posibles
        obstacles = (chunk.trees + chunk.small_stones + chunk.iron_minerals + 
                    chunk.copper_minerals + list(chunk.water_tiles.values()))
        
        for obj in obstacles:
            if hasattr(obj, 'rect') and farmland_rect.colliderect(obj.rect):
                return True
        return False

    def is_water_at(self, x, y):
        """Verifica si hay agua en la posición especificada"""
        chunk_key = self.get_chunk_key(x, y)
        chunk = self.active_chunks.get(chunk_key)
        
        if chunk:
            grid_x = (x // GRASS) * GRASS
            grid_y = (y // GRASS) * GRASS
            tile_key = (grid_x, grid_y)
            return tile_key in chunk.water_tiles
        return False

    def draw_inventory(self, screen, character):
        """Dibujar interfaz de inventario"""
        font = pygame.font.Font(None, 24)
        instruction_text = font.render("Press 'I' to open inventory", True, constants.WHITE)
        screen.blit(instruction_text, (10, 10))