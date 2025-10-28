# multiplayer_manager.py
import pygame
from player import Player
from constants import *

class MultiplayerManager:
    def __init__(self):
        self.players = []
        self.active_players = 1
        
    def setup_players(self, num_players=1):
        self.players.clear()
        self.active_players = num_players
        
        # Jugador 1 con teclado
        player1 = Player(WIDTH // 2, HEIGHT // 2, player_id=0, control_type="keyboard")
        self.players.append(player1)
        
        # Jugador 2 si se solicita
        if num_players >= 2:
            joypads = pygame.joystick.get_count()
            if joypads > 0:
                player2 = Player(WIDTH // 2 + 100, HEIGHT // 2, player_id=1, control_type="joypad", joypad_id=0)
            else:
                player2 = Player(WIDTH // 2 + 100, HEIGHT // 2, player_id=1, control_type="keyboard")
            self.players.append(player2)
    
    def update(self, dt, obstacles):
        for player in self.players:
            player.update(dt, obstacles)
            player.update_animation(dt)  # NUEVO: Actualizar animaciones
    
    def draw(self, screen, camera_x, camera_y):
        for player in self.players:
            player.draw(screen, camera_x, camera_y)
    
    def get_players(self):
        return self.players
    
    def get_main_player(self):
        return self.players[0] if self.players else None