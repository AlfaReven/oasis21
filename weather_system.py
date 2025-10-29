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

    
    def start_rain(self, intensity=1.0):
        self.raining = True
        self.intensity = intensity
        self.rain_duration = random.uniform(15, 40)
        self.max_rain_drops = int(300 * intensity)
        self.wind_speed = random.uniform(-1.2, 1.2)
        self.rain_drops.clear()

        
    def stop_rain(self):
        self.raining = False
        self.rain_timer = random.uniform(45, 120)
        self.rain_drops.clear()


    
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

    
    def draw(self, screen, camera_x=0, camera_y=0):
        if not self.raining:
            return

        for drop in self.rain_drops:
            screen_x = drop['x'] - camera_x
            screen_y = drop['y'] - camera_y
            if -20 <= screen_x <= self.screen_width + 20 and -20 <= screen_y <= self.screen_height + 20:
                pygame.draw.line(screen, (150, 150, 255),
                                (screen_x, screen_y),
                                (screen_x + self.wind_speed * 2, screen_y + drop['length']),
                                2)
