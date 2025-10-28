# weather_system.py
import pygame
import random

class WeatherSystem:
    def __init__(self):
        self.raining = False
        self.rain_timer = random.uniform(30, 90)
        self.rain_duration = 0
        self.rain_drops = []
        self.max_rain_drops = 300  # Aumentar gotas para pantalla completa
        
    def update(self, dt):
        if not self.raining:
            self.rain_timer -= dt
            if self.rain_timer <= 0:
                self.start_rain()
        else:
            self.rain_duration -= dt
            if self.rain_duration <= 0:
                self.stop_rain()
                
        if self.raining:
            self.update_rain_drops()
    
    def start_rain(self):
        self.raining = True
        self.rain_duration = random.uniform(10, 25)
        self.rain_drops = []
        print("🌧️ ¡Empieza a llover! - Ciclo del agua en acción")
        
    def stop_rain(self):
        self.raining = False
        self.rain_timer = random.uniform(45, 120)
        self.rain_drops = []
        print("☀️ Deja de llover")
    
    def update_rain_drops(self):
        # Crear nuevas gotas en toda el área visible + margen
        screen_width = 800  # Ajusta según tu WIDTH
        screen_height = 600  # Ajusta según tu HEIGHT
        
        while len(self.rain_drops) < self.max_rain_drops:
            self.rain_drops.append({
                'x': random.randint(-50, screen_width + 50),  # Margen extra
                'y': random.randint(-100, 0),  # Empezar arriba de la pantalla
                'speed': random.uniform(8, 15),  # Más rápido
                'length': random.uniform(8, 15)  # Longitud variable
            })
        
        # Mover gotas existentes
        for drop in self.rain_drops[:]:
            drop['y'] += drop['speed']
            # Eliminar solo si sale muy abajo de la pantalla
            if drop['y'] > screen_height + 100:
                self.rain_drops.remove(drop)
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """
        Dibuja la lluvia en coordenadas de pantalla
        camera_x, camera_y: para que la lluvia sea independiente del movimiento
        """
        if self.raining:
            for drop in self.rain_drops:
                # Dibujar en posición absoluta de pantalla (sin afectar por cámara)
                screen_x = drop['x']
                screen_y = drop['y']
                
                # Verificar si está en el área visible
                if -20 <= screen_x <= 820 and -20 <= screen_y <= 620:
                    pygame.draw.line(screen, (150, 150, 255), 
                                   (screen_x, screen_y), 
                                   (screen_x, screen_y + drop['length']), 2)