import random
import time
from pygame.rect import Rect

# Configurações do jogo
WIDTH = 500
HEIGHT = 600
GRAVITY = 0.4
JUMP_VELOCITY = -10
MOVE_SPEED = 3
PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 10

# Estados do jogo
MENU = 'menu'
GAME = 'game'
GAME_OVER = 'game_over'

# Variáveis globais
game_state = MENU
music_on = True

# Sistema de perguntas matemáticas
math_question_active = False
math_question = ""
math_options = []
correct_answer = None
last_math_time = time.time()
math_interval = 30  # Pergunta a cada 30 segundos

# Sistema de bolas
ball_spawn_timer = 0
ball_spawn_interval = 2 * 60  # Nova bola a cada 2 segundos (60 frames = 1 segundo)
max_balls = 10  # Número máximo de bolas na tela

def play_music():
    """Controla a reprodução da música de fundo"""
    if music_on:
        music.play('background')
    else:
        music.stop()

class Button:
    """Classe para botões interativos"""
    def __init__(self, text, x, y, w, h):
        self.rect = Rect((x, y), (w, h))
        self.text = text

    def draw(self):
        """Desenha o botão na tela"""
        screen.draw.filled_rect(self.rect, (200, 200, 200))
        screen.draw.text(self.text, center=self.rect.center, color="black")

class Player:
    """Classe que representa o personagem do jogador"""
    def __init__(self):
        self.actor = Actor('alien')
        self.actor.pos = WIDTH // 2, HEIGHT - 100
        self.vy = 0
        self.on_ground = False

    def move(self):
        """Movimentação horizontal e aplicação da gravidade"""
        if keyboard.left:
            self.actor.x -= MOVE_SPEED
        if keyboard.right:
            self.actor.x += MOVE_SPEED

        self.vy += GRAVITY
        self.actor.y += self.vy

        # Teleporte entre as bordas da tela
        if self.actor.x > WIDTH: 
            self.actor.x = 0
        if self.actor.x < 0: 
            self.actor.x = WIDTH

    def jump(self):
        """Realiza o pulo se estiver no chão"""
        if self.on_ground:
            self.vy = JUMP_VELOCITY

    def check_collision(self, platforms):
        """Detecta colisão com plataformas"""
        self.on_ground = False
        for plat in platforms:
            if self.actor.colliderect(plat.rect) and self.vy >= 0:
                self.actor.y = plat.rect.top - self.actor.height / 2
                self.vy = 0
                self.on_ground = True

class Platform:
    """Classe para as plataformas do jogo"""
    def __init__(self, x, y):
        self.rect = Rect((x, y), (PLATFORM_WIDTH, PLATFORM_HEIGHT))

    def draw(self, camera_y):
        """Desenha a plataforma com ajuste de câmera"""
        r = Rect(self.rect.x, self.rect.y - camera_y, self.rect.width, PLATFORM_HEIGHT)
        screen.draw.filled_rect(r, (139, 69, 19))  # Cor marrom

class Ball:
    """Classe para os obstáculos (bolas vermelhas)"""
    def __init__(self, y_pos=None):
        self.x = random.randint(20, WIDTH - 20)
        # Se y_pos não for fornecido, começa acima da tela
        self.y = y_pos if y_pos is not None else -20
        self.radius = 10
        self.speed = random.uniform(2, 4)

    def update(self):
        """Atualiza a posição da bola"""
        self.y += self.speed

    def draw(self, camera_y):
        """Desenha a bola com ajuste de câmera"""
        py = self.y - camera_y
        screen.draw.filled_circle((self.x, py), self.radius, (255, 0, 0))

    def get_rect(self):
        """Retorna o retângulo de colisão"""
        return Rect(self.x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)

class Game:
    """Classe principal que controla a lógica do jogo"""
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reinicia o estado do jogo"""
        self.player = Player()
        self.platforms = []
        self.camera_y = 0
        self.score = 0
        self.balls = []
        
        # Configuração das bolas
        self.ball_spawn_timer = 0
        self.ball_speed_increase = 0.5
        
        self.generate_initial_platforms()
        
        # Começa com algumas bolas
        for _ in range(3):
            self.spawn_ball()

    def spawn_ball(self, y_pos=None):
        """Cria uma nova bola em uma posição aleatória"""
        if len(self.balls) < max_balls:
            self.balls.append(Ball(y_pos))

    def generate_initial_platforms(self):
        """Cria as plataformas iniciais"""
        # Cria o chão
        floor = Platform(0, HEIGHT - PLATFORM_HEIGHT)
        floor.rect.width = WIDTH
        self.platforms.append(floor)
        
        # Cria plataformas aleatórias
        y = HEIGHT - 20
        while y > -1000:
            x = random.randint(0, WIDTH - PLATFORM_WIDTH)
            self.platforms.append(Platform(x, y))
            y -= random.randint(80, 120)

    def generate_new_platforms(self):
        """Gera novas plataformas conforme o jogador sobe"""
        if not self.platforms:
            return
            
        highest = min(p.rect.y for p in self.platforms)
        while highest > self.camera_y - HEIGHT:
            x = random.randint(0, WIDTH - PLATFORM_WIDTH)
            y = highest - random.randint(80, 120)
            self.platforms.append(Platform(x, y))
            highest = y

    def update_balls(self):
        """Atualiza o estado das bolas obstáculos"""
        self.ball_spawn_timer += 1
        
        # Spawn de novas bolas em intervalos regulares
        if self.ball_spawn_timer >= ball_spawn_interval:
            self.ball_spawn_timer = 0
            
            # Chance de spawnar bola no topo ou em plataformas
            if random.random() < 0.7:  # 70% de chance de spawn no topo
                self.spawn_ball()
            else:  # 30% de chance de spawn em plataformas
                if self.platforms:
                    platform = random.choice(self.platforms)
                    self.spawn_ball(platform.rect.top - 20)
        
        # Atualiza posição das bolas existentes
        for ball in self.balls:
            ball.update()
        
        # Remove bolas que saíram da tela
        self.balls = [b for b in self.balls if b.y - self.camera_y < HEIGHT + 50]

    def update(self):
        """Atualiza o estado do jogo a cada frame"""
        global game_state, math_question_active, last_math_time
        
        if math_question_active:
            return  # Pausa o jogo durante perguntas
            
        self.player.move()
        self.player.check_collision(self.platforms)
        
        # Controle da câmera e pontuação
        if self.player.on_ground and (self.player.actor.y - self.camera_y < HEIGHT // 3):
            self.camera_y = self.player.actor.y - HEIGHT // 3
            self.score += 1
        
        # Gerenciamento de plataformas
        self.generate_new_platforms()
        self.platforms = [p for p in self.platforms if p.rect.y - self.camera_y < HEIGHT]
        
        # Atualização das bolas
        self.update_balls()
        
        # Verificação de colisão com bolas
        player_rect = Rect(
            self.player.actor.x - self.player.actor.width // 2,
            self.player.actor.y - self.player.actor.height // 2,
            self.player.actor.width,
            self.player.actor.height
        )
        
        # Corrigido: verificação de colisão com as bolas
        if any(ball.get_rect().colliderect(player_rect) for ball in self.balls):
            game_state = GAME_OVER
        
        if self.player.actor.y - self.camera_y > HEIGHT:
            game_state = GAME_OVER
        
        # Verifica se é hora de mostrar uma pergunta matemática
        current_time = time.time()
        if current_time - last_math_time > math_interval:
            generate_math_question()
            math_question_active = True
            last_math_time = current_time

    def draw(self):
        """Renderiza todos os elementos do jogo"""
        screen.clear()
        screen.fill((135, 206, 235))  # Fundo azul claro
        
        # Desenha plataformas
        for plat in self.platforms:
            plat.draw(self.camera_y)
            
        # Desenha bolas
        for ball in self.balls:
            ball.draw(self.camera_y)
        
        # Desenha jogador
        px = self.player.actor.x
        py = self.player.actor.y - self.camera_y
        screen.blit('alien', (px - self.player.actor.width // 2, py - self.player.actor.height // 2))
        
        # Mostra pontuação
        screen.draw.text(f"Pontos: {self.score}", topleft=(10, 10), fontsize=30, color="black")

def generate_math_question():
    """Gera uma nova pergunta matemática com opções de resposta"""
    global math_question, math_options, correct_answer
    
    # Gera números e operação aleatória
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    operation = random.choice(['+', '-', '*'])
    
    # Calcula a resposta correta
    if operation == '+':
        correct_answer = a + b
    elif operation == '-':
        correct_answer = a - b
    else:  # '*'
        correct_answer = a * b
    
    # Gera opções de resposta
    math_options = [correct_answer]
    while len(math_options) < 2:
        # Gera respostas erradas próximas da correta
        wrong_answer = correct_answer + random.choice([-3, -2, -1, 1, 2, 3])
        if wrong_answer != correct_answer and wrong_answer > 0:
            math_options.append(wrong_answer)
    
    random.shuffle(math_options)
    math_question = f"{a} {operation} {b} = ?"

def check_math_answer(answer):
    """Verifica a resposta do jogador e aplica penalidade se errado"""
    global math_question_active
    
    if answer != correct_answer:
        # Aumenta o tamanho das bolas como penalidade
        for ball in game.balls:
            ball.radius = min(30, ball.radius + 3)  # Limita o tamanho máximo
    
    math_question_active = False

# Inicialização do jogo e elementos de interface
game = Game()

# Botões do menu principal
start_button = Button("Começar Jogo", WIDTH//2 - 80, 200, 160, 50)
music_button = Button("Música: ON", WIDTH//2 - 80, 270, 160, 50)
exit_button = Button("Sair", WIDTH//2 - 80, 340, 160, 50)

# Botões da tela de game over
restart_button = Button("Voltar ao Menu", WIDTH//2 - 80, 300, 160, 50)

# Botões para as perguntas matemáticas
math_button1 = Button("", WIDTH//2 - 110, HEIGHT//2, 100, 50)
math_button2 = Button("", WIDTH//2 + 10, HEIGHT//2, 100, 50)

# Inicia a música
play_music()

def update():
    """Função chamada a cada frame para atualizar a lógica do jogo"""
    if game_state == GAME:
        game.update()

def draw():
    """Função chamada a cada frame para renderizar a tela"""
    if game_state == MENU:
        # Tela de menu
        screen.clear()
        screen.draw.text("MENU PRINCIPAL", center=(WIDTH//2, 100), fontsize=40, color="black")
        start_button.draw()
        music_button.draw()
        exit_button.draw()
        
    elif game_state == GAME:
        # Tela do jogo
        game.draw()
        
        # Mostra pergunta matemática se ativa
        if math_question_active:
            # Fundo semi-transparente
            screen.draw.filled_rect(Rect(0, 0, WIDTH, HEIGHT), (0, 0, 0, 180))
            screen.draw.text("RESPONDA CORRETAMENTE!", center=(WIDTH//2, 100), fontsize=30, color="white")
            screen.draw.text(math_question, center=(WIDTH//2, 180), fontsize=40, color="yellow")
            
            # Atualiza e mostra os botões de resposta
            math_button1.text = str(math_options[0])
            math_button2.text = str(math_options[1])
            math_button1.draw()
            math_button2.draw()
            
    elif game_state == GAME_OVER:
        # Tela de game over
        screen.clear()
        screen.draw.text("GAME OVER!", center=(WIDTH//2, 150), fontsize=60, color="red")
        screen.draw.text(f"Pontuação: {game.score}", center=(WIDTH//2, 220), fontsize=40, color="black")
        restart_button.draw()

def on_mouse_down(pos):
    """Lida com cliques do mouse"""
    global game_state, music_on, math_question_active
    
    if math_question_active:
        # Verifica clique nas respostas matemáticas
        if math_button1.rect.collidepoint(pos):
            check_math_answer(math_options[0])
        elif math_button2.rect.collidepoint(pos):
            check_math_answer(math_options[1])
            
    elif game_state == MENU:
        # Cliques no menu principal
        if start_button.rect.collidepoint(pos):
            game.reset()
            game_state = GAME
        elif music_button.rect.collidepoint(pos):
            music_on = not music_on
            music_button.text = "Música: ON" if music_on else "Música: OFF"
            play_music()
        elif exit_button.rect.collidepoint(pos):
            quit()
            
    elif game_state == GAME_OVER:
        # Clique no botão de reinício
        if restart_button.rect.collidepoint(pos):
            game_state = MENU

def on_key_down(key):
    """Lida com pressionamento de teclas"""
    if game_state == GAME and not math_question_active and key == keys.SPACE:
        game.player.jump()