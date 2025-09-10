# sharper_night_explorer.py

import pygame
import random
import time

# --- Pygame Initialization ---
pygame.init()

# Initial screen size and reference size for scaling
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Indovina: quale attrezzo pesca cosa?")

INITIAL_SCREEN_WIDTH = 2400
INITIAL_SCREEN_HEIGHT = 1200

# --- Colors ---
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
SUBTITLE_COLOR = (200, 200, 200) # A lighter white for the subtitle
CARD_BACK_COLOR = (43, 108, 176)  # A nice blue
MATCHED_COLOR = (72, 187, 120)    # A green for matched cards
BUTTON_COLOR = (255, 165, 0)      # Orange for the button
BORDER_COLOR = (255, 255, 255)    # White border for visibility

# --- Background ---
BACKGROUND_IMAGE_PATH = "./placeholder/sfondo2.png"
background_image = None 
background_image_scaled = None # For the scaled image

# --- Card and Grid Settings ---
# These will be scaled dynamically
CARD_SIZE = 0
CARD_MARGIN = 0
GRID_ROWS = 2
GRID_COLS = 8
GRID_X = 0
GRID_Y = 0
border_width = 8
border_radius = 20

# --- Fonts ---
title_font = None
subtitle_font = None
status_font = None
card_font = None

# --- Game Icons (Paired images) ---
ICONS = [
    ("./placeholder/cogollo.png", "./placeholder/seppia.png"), 
    ("./placeholder/nassa.png", "./placeholder/canocchia.png"), 
    ("./placeholder/cestino.png", "./placeholder/lumachinedimare.png"), 
    ("./placeholder/imbrocco.png", "./placeholder/sogliola.png"), 
    ("./placeholder/tramaglio.png", "./placeholder/rombo.png"), 
    ("./placeholder/palangaro.png", "./placeholder/ricciola.png"), 
    ("./placeholder/dragaidraulica.png", "./placeholder/vongole.png"), 
    ("./placeholder/strascico.png", "./placeholder/pescemisto.png")
]

# --- Game State Variables ---
game_board = []
flipped_cards = []
matched_pairs = 0
game_score = 0
game_timer = 0
game_over = False
start_time = 0
can_flip = True
loaded_images = {} 

# --- Functions ---
def update_layout():
    """Recalculates positions, sizes, and fonts for all game elements on resize."""
    global GRID_X, GRID_Y, background_image_scaled, SCREEN_WIDTH, SCREEN_HEIGHT, CARD_SIZE, CARD_MARGIN, title_font, subtitle_font, status_font, card_font, border_width

    # Calculate scaling ratio based on the smaller dimension to maintain aspect ratio
    scale_ratio = min(SCREEN_WIDTH / INITIAL_SCREEN_WIDTH, SCREEN_HEIGHT / INITIAL_SCREEN_HEIGHT)
    
    # Recalculate dynamic sizes
    CARD_SIZE = int(250 * scale_ratio)
    CARD_MARGIN = int(40 * scale_ratio)
    border_width = int(8 * scale_ratio)
    
    # Recalculate fonts
    title_font = pygame.font.Font(None, int(100 * scale_ratio))
    subtitle_font = pygame.font.Font(None, int(90 * scale_ratio))
    status_font = pygame.font.Font(None, int(80 * scale_ratio))
    card_font = pygame.font.Font(None, int(140 * scale_ratio))
    
    # Recalculate grid position
    GRID_X = (SCREEN_WIDTH - (GRID_COLS * (CARD_SIZE + CARD_MARGIN))) / 2 + CARD_MARGIN / 2
    GRID_Y = SCREEN_HEIGHT * 0.25 # Position relative to height

    # Update background image size
    if background_image:
        background_image_scaled = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Re-scale loaded images for cards
    for gear_path, fish_path in ICONS:
        if gear_path in loaded_images:
            gear_image = loaded_images[gear_path]
            scaled_gear = pygame.transform.scale(gear_image, (CARD_SIZE - border_width*2, CARD_SIZE - border_width*2))
            loaded_images[gear_path] = scaled_gear
        
        if fish_path in loaded_images:
            fish_image = loaded_images[fish_path]
            scaled_fish = pygame.transform.scale(fish_image, (CARD_SIZE - border_width*2, CARD_SIZE - border_width*2))
            loaded_images[fish_path] = scaled_fish

    # Recalculate card positions on the board
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            card_data = game_board[i][j]
            card_data['rect'] = pygame.Rect(
                GRID_X + j * (CARD_SIZE + CARD_MARGIN),
                GRID_Y + i * (CARD_SIZE + CARD_MARGIN),
                CARD_SIZE,
                CARD_SIZE
            )

def setup_game():
    """Sets up the game board with shuffled pairs."""
    global game_board, game_over, matched_pairs, game_score, start_time, can_flip, loaded_images, background_image, SCREEN_WIDTH, SCREEN_HEIGHT
    
    game_over = False
    matched_pairs = 0
    game_score = 0
    flipped_cards.clear()
    
    # Load the background image once at the start
    try:
        background_image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    except pygame.error as e:
        print(f"Error loading background image: {BACKGROUND_IMAGE_PATH} - {e}")
        background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background_image.fill(BLACK)
    
    # Load all card images once
    for gear_path, fish_path in ICONS:
        try:
            gear_image = pygame.image.load(gear_path).convert_alpha()
            loaded_images[gear_path] = gear_image
        except pygame.error as e:
            print(f"Error loading image: {gear_path} - {e}")
            loaded_images[gear_path] = pygame.Surface((250, 250))
            loaded_images[gear_path].fill(BLACK)

        try:
            fish_image = pygame.image.load(fish_path).convert_alpha()
            loaded_images[fish_path] = fish_image
        except pygame.error as e:
            print(f"Error loading image: {fish_path} - {e}")
            loaded_images[fish_path] = pygame.Surface((250, 250))
            loaded_images[fish_path].fill(BLACK)
    
    all_cards = []
    for pair_id, (gear_path, fish_path) in enumerate(ICONS):
        all_cards.append({'icon': gear_path, 'pair_id': pair_id, 'is_flipped': False, 'is_matched': False})
        all_cards.append({'icon': fish_path, 'pair_id': pair_id, 'is_flipped': False, 'is_matched': False})
    
    random.shuffle(all_cards)

    game_board = []
    for i in range(GRID_ROWS):
        row = []
        for j in range(GRID_COLS):
            card_data = all_cards.pop()
            row.append(card_data)
        game_board.append(row)
    
    update_layout()
    start_time = time.time()
    can_flip = True


def draw_game_board():
    """Draws the cards on the screen based on their state."""
    for row in game_board:
        for card in row:
            if card['is_flipped'] or card['is_matched']:
                pygame.draw.rect(screen, BLACK, card['rect'], border_radius=border_radius)
                pygame.draw.rect(screen, BORDER_COLOR, card['rect'], border_width, border_radius)
                
                image_to_draw = loaded_images[card['icon']]
                image_rect = image_to_draw.get_rect(center=card['rect'].center)
                screen.blit(image_to_draw, image_rect)

            else:
                pygame.draw.rect(screen, CARD_BACK_COLOR, card['rect'], border_radius=border_radius)
                pygame.draw.rect(screen, BORDER_COLOR, card['rect'], border_width, border_radius)
                question_mark = card_font.render("?", True, WHITE)
                q_rect = question_mark.get_rect(center=card['rect'].center)
                screen.blit(question_mark, q_rect)


def draw_text(text, font, color, x, y):
    """A helper function to draw text on the screen."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)


def handle_click(pos):
    """Handles a mouse click to flip a card."""
    global flipped_cards, game_score, matched_pairs, game_over, can_flip

    if not can_flip or game_over:
        return

    for row in game_board:
        for card in row:
            if card['rect'].collidepoint(pos) and not card['is_flipped'] and not card['is_matched']:
                card['is_flipped'] = True
                flipped_cards.append(card)
                
                if len(flipped_cards) == 2:
                    can_flip = False
                    pygame.time.set_timer(pygame.USEREVENT, 1000) 


# --- Main Game Loop ---
def main():
    global game_score, game_over, game_timer, can_flip, matched_pairs, SCREEN_WIDTH, SCREEN_HEIGHT, screen

    setup_game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                update_layout()
            
            if event.type == pygame.USEREVENT:
                card1, card2 = flipped_cards
                if card1['pair_id'] == card2['pair_id']:
                    card1['is_matched'] = True
                    card2['is_matched'] = True
                    game_score += 1
                    matched_pairs += 1
                
                card1['is_flipped'] = False
                card2['is_flipped'] = False
                flipped_cards.clear()
                can_flip = True
                pygame.time.set_timer(pygame.USEREVENT, 0)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game_over:
                    handle_click(event.pos)
                else:
                    BUTTON_WIDTH = 400
                    BUTTON_HEIGHT = 100
                    play_again_rect = pygame.Rect(
                        (SCREEN_WIDTH - BUTTON_WIDTH) / 2, 
                        (SCREEN_HEIGHT // 2) + 200,
                        BUTTON_WIDTH, 
                        BUTTON_HEIGHT
                    )
                    if play_again_rect.collidepoint(event.pos):
                        setup_game()

        # --- Game Logic Updates ---
        if not game_over:
            game_timer = int(time.time() - start_time)

        if matched_pairs == len(ICONS):
            game_over = True

        # --- Drawing to the Screen ---
        screen.blit(background_image_scaled, (0, 0))

        draw_text("Indovina: quale attrezzo pesca cosa?", title_font, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1)
        draw_text("SHARPER Night 2025", subtitle_font, SUBTITLE_COLOR, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.17)
        
        draw_text(f"Punteggio: {game_score}", status_font, WHITE, SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2)
        draw_text(f"Tempo: {game_timer}s", status_font, WHITE, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2)

        if not game_over:
            draw_game_board()

        if game_over:
            buffer_rect = pygame.Rect(0, 0, SCREEN_WIDTH * 0.4, SCREEN_HEIGHT * 0.3)
            buffer_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150)
            pygame.draw.rect(screen, WHITE, buffer_rect, border_radius=20)
            
            win_message = f"Hai vinto! Tempo: {game_timer}s"
            draw_text(win_message, title_font, BLACK, buffer_rect.centerx, buffer_rect.centery - 50)
            
            BUTTON_WIDTH = int(SCREEN_WIDTH * 0.2)
            BUTTON_HEIGHT = int(SCREEN_HEIGHT * 0.08)
            play_again_rect = pygame.Rect(
                (buffer_rect.centerx - BUTTON_WIDTH / 2),
                (buffer_rect.centery + 20),
                BUTTON_WIDTH,
                BUTTON_HEIGHT
            )
            pygame.draw.rect(screen, BUTTON_COLOR, play_again_rect, border_radius=10)
            draw_text("Gioca ancora", status_font, BLACK, play_again_rect.centerx, play_again_rect.centery)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
