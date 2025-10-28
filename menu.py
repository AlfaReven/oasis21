import pygame

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.options = ["JUGAR", "MULTIJUGADOR", "CARGAR", "SALIR"]
        self.selected = 0
        
    def draw(self):
        # Fondo azul tipo agua
        self.screen.fill((30, 60, 90))
        
        # Título
        title = self.font_large.render("OASIS JAPAMI", True, (255, 255, 255))
        screen_width = self.screen.get_width()
        self.screen.blit(title, (screen_width//2 - title.get_width()//2, 100))
        
        # Opciones
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (200, 200, 255)
            text = self.font.render(option, True, color)
            x = screen_width//2 - text.get_width()//2
            y = 200 + i * 60
            self.screen.blit(text, (x, y))
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                return self.selected
        return None