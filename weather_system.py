# weather_system.py
import pygame
import random

class WeatherSystem:
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.raining = False
        self.rain_timer = random.uniform(30, 90)
        self.rain_duration = 0
        self.rain_drops = []
        self.max_rain_drops = 300
        self.wind_speed = random.uniform(-1.0, 1.0)
        self.intensity = 1.0
        
        # Referencia al mundo para llenar tanques (se asignará después)
        self.world = None

    def set_world_reference(self, world):
        """Establece referencia al mundo para acceder a los tanques"""
        self.world = world
        
    def update(self, dt, camera_x=0, camera_y=0):
        """Actualiza temporizadores de lluvia y genera gotas según la cámara."""
        if not self.raining:
            self.rain_timer -= dt
            if self.rain_timer <= 0:
                self.start_rain()
        else:
            self.rain_duration -= dt
            if self.rain_duration <= 0:
                self.stop_rain()

        # Generar y mover gotas sólo si está lloviendo
        if self.raining:
            self.update_rain_drops(camera_x, camera_y)
            
            # Llenar tanques de agua con agua de lluvia (cada 2 segundos aprox)
            if random.random() < dt * 0.5:  # 50% de probabilidad por segundo
                self._fill_water_tanks()

    
    def start_rain(self, intensity=1.0):
        self.raining = True
        self.intensity = intensity
        self.rain_duration = random.uniform(15, 40)
        self.max_rain_drops = int(300 * intensity)
        self.wind_speed = random.uniform(-1.2, 1.2)
        self.rain_drops.clear()
        print("🌧️ ¡Ha comenzado a llover!")

        
    def stop_rain(self):
        self.raining = False
        self.rain_timer = random.uniform(45, 120)
        self.rain_drops.clear()
        print("☀️ La lluvia ha parado")

    
    def update_rain_drops(self, camera_x=0, camera_y=0):
        # Generar gotas sobre el área visible + margen
        while len(self.rain_drops) < self.max_rain_drops:
            self.rain_drops.append({
                'x': random.uniform(camera_x - 50, camera_x + self.screen_width + 50),
                'y': random.uniform(camera_y - 100, camera_y),
                'speed_y': random.uniform(400, 700),
                'speed_x': self.wind_speed * random.uniform(0.5, 1.5),
                'length': random.uniform(10, 20)
            })

        # Actualizar movimiento
        for drop in self.rain_drops[:]:
            drop['x'] += drop['speed_x'] * 0.016  # dt aproximado
            drop['y'] += drop['speed_y'] * 0.016
            if drop['y'] > camera_y + self.screen_height + 100:
                self.rain_drops.remove(drop)

    def _fill_water_tanks(self):
        """Llena los tanques de agua cercanos con agua de lluvia"""
        if not self.world or not hasattr(self.world, 'placeable_objects'):
            return
            
        tanks_filled = 0
        for obj in self.world.placeable_objects:
            # Buscar tanques de agua (vacíos, medios o llenos)
            if hasattr(obj, 'object_type') and obj.object_type in ('empty_tank', 'tank_half', 'water_tank'):
                # Calcular cantidad de agua basada en intensidad de lluvia
                rain_water = random.uniform(1, 3) * self.intensity
                water_collected = obj.collect_rainwater(rain_water)
                if water_collected > 0:
                    tanks_filled += 1
        
        # Debug opcional (evita spam)
        if tanks_filled > 0 and random.random() < 0.1:
            print(f"💧 La lluvia está llenando {tanks_filled} tanque(s)")


    
    def draw(self, screen, camera_x=0, camera_y=0):
        if not self.raining:
            return

        # Dibujar gotas de lluvia
        for drop in self.rain_drops:
            screen_x = drop['x'] - camera_x
            screen_y = drop['y'] - camera_y
            if -20 <= screen_x <= self.screen_width + 20 and -20 <= screen_y <= self.screen_height + 20:
                # Color basado en intensidad
                alpha = int(150 * self.intensity)
                color = (150, 150, 255, alpha)
                
                pygame.draw.line(screen, color,
                                (screen_x, screen_y),
                                (screen_x + self.wind_speed * 2, screen_y + drop['length']),
                                2)

        # Opcional: Dibujar overlay de lluvia suave
        if self.intensity > 0.7:
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay_alpha = min(30, int(40 * (self.intensity - 0.7)))
            overlay.fill((100, 100, 150, overlay_alpha))
            screen.blit(overlay, (0, 0))

    def get_weather_status(self):
        """Devuelve el estado actual del clima"""
        if self.raining:
            intensity_desc = "Suave" if self.intensity < 0.5 else "Moderada" if self.intensity < 0.8 else "Fuerte"
            return f"🌧️ Lluvia {intensity_desc} - {self.rain_duration:.1f}s restantes"
        else:
            return f"☀️ Soleado - Lluvia en {self.rain_timer:.1f}s"