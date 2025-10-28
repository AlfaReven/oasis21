# ESTA SCRIPT ES PARA LA CLASE PADRE DE TODAS LAS ENTIDADES VIVAS EN EL JUEGO
import pygame
import os
from constants import *
import random

class Entities:
    def __init__(self, x, y, filename):
        # PARA OBTENER SUS COORDENADAS EN x,y
        self.x = x
        self.y = y
        self.speed = BASE_SPEED
        self.size = ENTITY
        
        # PARA CARGAR LOS SPRITES DE CADA COSA QUE SE CONSIDERE VIVA
        image_path = os.path.join('assets', 'images', filename)
        self.sprite_sheet = pygame.image.load(image_path).convert_alpha()
        
        # PROPIEDADES DE LA ANIMACION
        self.frame_size = FRAME_SIZE
        self.animation_frame = 0
        self.animation_timer = 0
        self.animation_delay = ANIMATION_DELAY
        self.current_state = IDLE_DOWN
        self.moving = False
        self.facing_left = False
        self.is_running = False

        # CARGAR TODOS LOS FRAMES DE CADA COSA VIVA
        self.animation = self.load_animations()
        self.image = self.animation[self.current_state][0]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        
        # PROPIEDADES PARA EL ATAQUE DE LOS ENEMIGOS
        self.melee_attack = MELEE_ATTACK_DISTANCE
        self.ranged_attack = RANGED_ATTACK_DISTANCE
        
        """DICCIONARIO CON LAS ESTADISTICAS CON LAS QUE CUENTA CADA COSA VIVA"""
        self.stats = {
            'force': BASE_FORCE,
            'health': MAX_HEALTH,
            'max_health': MAX_HEALTH,
            'weapon_skill': BASE_WEAPON_SKILL,
            'armor': BASE_ARMOR,
            'critical_damage': BASE_CRITICAL_DAMAGE,
            'magic_resistence': BASE_MAGIC_RESISTENCE
        }
    
    # METODO PARA EXTRAER LOS SPRITES DE LAS SPRITESHEETS (NUEVA VERSIÓN)
    def load_animations(self):
        animations = {}
        for state in range(6):
            frames = []
            for frame in range(BASIC_FRAMES):
                frame_surface = self.process_frame(state, frame)  # 🔹 Hook extensible
                frames.append(frame_surface)
            animations[state] = frames
        return animations

    def process_frame(self, state, frame):
        """Método base que genera un frame estándar."""
        surface = pygame.Surface((self.frame_size, self.frame_size), pygame.SRCALPHA)
        surface.blit(
            self.sprite_sheet,
            (0, 0),
            (
                frame * self.frame_size,
                state * self.frame_size,
                self.frame_size,
                self.frame_size,
            ),
        )
        if ENTITY != self.frame_size:
            surface = pygame.transform.scale(surface, (ENTITY, ENTITY))
        return surface

    
    # METODO PARA ITERAR EN LOS SPRITES (ACTUALIZADO)
    def update_animation(self, dt):
        # Si esta entidad tiene una animación especial activa, no procesar animación normal
        if hasattr(self, 'special_animation') and self.special_animation:
            return
        if self.moving:
            self.animation_timer += dt
            # VAMOS A AJUSTAR LA VELOCIDAD DE LA ANIMACION SI EDUARDO ANDA CORRIENDO
            animation_speed = RUNNING_ANIMATION_DELAY if self.is_running else ANIMATION_DELAY
            if self.animation_timer >= animation_speed:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % len(self.animation[self.current_state])
        else:
            # Para estados idle, usar el primer frame (frame 0)
            self.animation_frame = 0
        
        self.image = self.animation[self.current_state][self.animation_frame]
        self.rect = self.image.get_rect(center=(self.x, self.y))
    
    # METODO PARA DIBUJAR A LAS COSAS VIVAS EN LA PANTALLA CON
    # UNA POSICION RELATIVA A LA CAMARA DEL JUGADOR
    def draw(self, screen, camera_x, camera_y):
        # DIBUJAR EL ENEMIGO EN SU POSICIÓN RELATIVA A LA CÁMARA
        
        current_frame = self.animation[self.current_state][self.animation_frame]
        
        # Aplicar flip si está mirando hacia la izquierda
        if self.facing_left:
            current_frame = pygame.transform.flip(current_frame, True, False)
        
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        if (screen_x + self.size >= 0 and screen_x <= WIDTH and
            screen_y + self.size >= 0 and screen_y <= HEIGHT):
            screen.blit(current_frame, (screen_x, screen_y))
        
    def check_collision(self, x, y, obj):
        return (x < obj.x + obj.size*.75 and x + ENTITY*.75 > obj.x
                and y < obj.y + obj.size*.75 and y + ENTITY*.75 > obj.y)
        
    def is_near(self, obj):
        return (abs(self.x - obj.x) <= max(ENTITY, obj.size) + 5 and
                abs(self.y - obj.y) <= max(ENTITY, obj.size) + 5)
        
    def take_damage(self, source, attack_type):
        base_damage = 0
        
        # CASES PARA CETERMINAR EL TIPO DE ATAQUE Y COMO ES QUE SE COMPORTA EL DAÑO
        if attack_type == 'melee':
            base_damage = source.stats['force']
        elif attack_type == 'ranged':
            base_damage = source.stats['weapon_skill']
            
        # APLICAR LA DEFENSA COMO UN PARAMETRO UTIL EN COMBATE
        if attack_type in ('melee', 'ranged'):
            base_damage -= self.stats['armor']
        # por el momento lo pondre pero quiza luego lo use
        if attack_type == 'magic':
            base_damage -= self.stats['magic_resistence']
        
        # Aplicar daño crítico
        damage = base_damage
        if random.random() < (source.stats['critical_damage'] / 100):
            damage *= 2
            
        # validacion para evitar el daño negativo
        damage = max(damage, 1)  # Mínimo 1 de daño
        
        # para que se le reste la vida a la entidad viva
        self.stats['health'] -= damage
        
        # para revisar si la salud llega a 0 o menos llamar al metodo is_dead
        if self.stats['health'] <= 0:
            self.stats['health'] = 0
        
        # para futuras mejoras return el daño para imprimirlo en pantalla
        return damage      
        
    def is_dead(self):
        return self.stats['health'] <= 0
    
    def move(self, dx, dy, obstacles):
        # Si está en medio de una accion
        if hasattr(self, 'is_chopping') and self.is_chopping:
            return False
            
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed
        
        # Verificar colisiones con los obejtos de world
        can_move = True
        temp_rect = pygame.Rect(new_x - self.size//2, new_y - self.size//2, 
                            self.size * 0.75, self.size * 0.75)
        
        for obstacle in obstacles:
            if temp_rect.colliderect(obstacle.rect):
                can_move = False
                break
        
        #SI NO HAY COLISIONES ENOCES MOVER ES TRUE
        if can_move:
            self.x = new_x
            self.y = new_y
            self.moving = True
            
            if dx > 0:
                self.current_state = WALK_RIGHT
                self.facing_left = False
            elif dx < 0:
                self.current_state = WALK_RIGHT
                self.facing_left = True
            elif dy > 0:
                self.current_state = WALK_DOWN
                self.facing_left = False
            elif dy < 0:
                self.current_state = WALK_UP
                self.facing_left = False
        else:
            self.moving = False
            # Cambiar a estado idle correspondiente
            if self.current_state == WALK_DOWN:
                self.current_state = IDLE_DOWN
            elif self.current_state == WALK_UP:
                self.current_state = IDLE_UP
            elif self.current_state == WALK_RIGHT:
                self.current_state = IDLE_RIGHT
                
        return can_move