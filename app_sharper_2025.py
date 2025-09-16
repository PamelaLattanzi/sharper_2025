import pygame
import random
import time
import json
import os

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
SUBTITLE_COLOR = (200, 200, 200)  # A lighter white for the subtitle
CARD_BACK_COLOR = (43, 108, 176)  # A nice blue
MATCHED_COLOR = (72, 187, 120)    # A green for matched cards
BUTTON_COLOR = (255, 165, 0)      # Orange for the button
BORDER_COLOR = (255, 255, 255)    # White border for visibility
ATTEMPT_COLOR = (255, 0, 0) # Red for low attempts

# --- Background ---
BACKGROUND_IMAGE_PATH = "./placeholder/sfondo2.png"
background_image = None
background_image_scaled = None # For the scaled image

# --- Card and Grid Settings ---
# These will be scaled dynamically
CARD_SIZE = 0
CARD_MARGIN = 0
GRID_ROWS = 2
GRID_COLS = 6
GRID_X = 0
GRID_Y_TOP = 0
GRID_Y_BOTTOM = 0
border_width = 8
border_radius = 20

# --- Fonts ---
title_font = None
subtitle_font = None
status_font = None
card_font = None
label_font = None

# --- Game Icons (Paired images) ---
# Separating the icons into two lists for easier row management.
# The index of the item in each list corresponds to its pair.
GEAR_ICONS = [
    "./placeholder/cogollo.png",
    "./placeholder/nassa.png",
    "./placeholder/cestino.png",
    "./placeholder/imbrocco.png",
    "./placeholder/tramaglio.png",
    "./placeholder/palangaro.png",
]

FISH_ICONS = [
    "./placeholder/seppia.png",
    "./placeholder/canocchia.png",
    "./placeholder/lumachinedimare.png",
    "./placeholder/sogliola.png",
    "./placeholder/rombo.png",
    "./placeholder/ricciola.png",
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
is_revealing_cards = False
game_attempts = 0
MAX_ATTEMPTS = 6
current_username = "" # Global variable to store the username

# --- Leaderboard Variables ---
LEADERBOARD_FILE = 'leaderboard.json'
leaderboard = []

# --- Custom Events ---
REVEAL_END_EVENT = pygame.USEREVENT + 1

# --- Functions ---
def initialize_fonts():
    """Initializes all font objects. This must be called once at the start."""
    global title_font, subtitle_font, status_font, card_font, label_font

    scale_ratio = min(SCREEN_WIDTH / INITIAL_SCREEN_WIDTH, SCREEN_HEIGHT / INITIAL_SCREEN_HEIGHT)
    
    title_font = pygame.font.Font(None, int(100 * scale_ratio))
    subtitle_font = pygame.font.Font(None, int(90 * scale_ratio))
    status_font = pygame.font.Font(None, int(80 * scale_ratio))
    card_font = pygame.font.Font(None, int(140 * scale_ratio))
    label_font = pygame.font.Font(None, int(60 * scale_ratio))

def update_layout():
    """Recalculates positions, sizes, and fonts for all game elements on resize."""
    global GRID_X, GRID_Y_TOP, GRID_Y_BOTTOM, background_image_scaled, SCREEN_WIDTH, SCREEN_HEIGHT, CARD_SIZE, CARD_MARGIN, border_width
    
    # Calculate scaling ratio based on the smaller dimension to maintain aspect ratio
    scale_ratio = min(SCREEN_WIDTH / INITIAL_SCREEN_WIDTH, SCREEN_HEIGHT / INITIAL_SCREEN_HEIGHT)
    
    # Recalculate dynamic sizes
    CARD_SIZE = int(250 * scale_ratio)
    CARD_MARGIN = int(40 * scale_ratio)
    border_width = int(8 * scale_ratio)

    # Recalculate grid positions
    GRID_X = (SCREEN_WIDTH - (GRID_COLS * (CARD_SIZE + CARD_MARGIN))) / 2 + CARD_MARGIN / 2
    GRID_Y_TOP = SCREEN_HEIGHT * 0.35 # Position of the top row (Attrezzi)
    GRID_Y_BOTTOM = GRID_Y_TOP + CARD_SIZE + CARD_MARGIN + int(40 * scale_ratio) # Position of the bottom row (Specie)

    # Update background image size
    if background_image:
        background_image_scaled = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Re-scale loaded images for cards
    for path in loaded_images:
        image = loaded_images[path]
        scaled_image = pygame.transform.scale(image, (CARD_SIZE - border_width*2, CARD_SIZE - border_width*2))
        loaded_images[path] = scaled_image

    # Recalculate card positions on the board
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            card_data = game_board[i][j]
            card_data['rect'] = pygame.Rect(
                GRID_X + j * (CARD_SIZE + CARD_MARGIN),
                (GRID_Y_TOP if i == 0 else GRID_Y_BOTTOM),
                CARD_SIZE,
                CARD_SIZE
            )

def setup_game():
    """Sets up the game board with shuffled pairs."""
    global game_board, game_over, matched_pairs, game_score, start_time, can_flip, loaded_images, background_image, SCREEN_WIDTH, SCREEN_HEIGHT, is_revealing_cards, game_attempts, leaderboard
    
    game_over = False
    matched_pairs = 0
    game_score = 0
    game_attempts = 0 # Reset attempts
    flipped_cards.clear()
    
    # Load the leaderboard
    leaderboard = load_leaderboard()

    # Set state for initial card reveal
    is_revealing_cards = True
    can_flip = False # Prevent flipping while cards are being revealed
    pygame.time.set_timer(REVEAL_END_EVENT, 8000) # 8-second timer for the reveal

    # Load the background image once at the start
    try:
        background_image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    except pygame.error as e:
        print(f"Error loading background image: {BACKGROUND_IMAGE_PATH} - {e}")
        background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background_image.fill(BLACK)
    
    # Load all card images once
    all_icons = GEAR_ICONS + FISH_ICONS
    for path in all_icons:
        try:
            image = pygame.image.load(path).convert_alpha()
            loaded_images[path] = image
        except pygame.error as e:
            print(f"Error loading image: {path} - {e}")
            loaded_images[path] = pygame.Surface((250, 250))
            loaded_images[path].fill(BLACK)

    # Create two separate lists of card data
    gear_cards = []
    for pair_id, path in enumerate(GEAR_ICONS):
        gear_cards.append({'icon': path, 'pair_id': pair_id, 'is_flipped': False, 'is_matched': False})
    
    fish_cards = []
    for pair_id, path in enumerate(FISH_ICONS):
        fish_cards.append({'icon': path, 'pair_id': pair_id, 'is_flipped': False, 'is_matched': False})
    
    # Shuffle each list independently
    random.shuffle(gear_cards)
    random.shuffle(fish_cards)

    # Build the game board with two distinct rows
    game_board = [gear_cards, fish_cards]
    
    update_layout()
    start_time = time.time()
    can_flip = True

def load_leaderboard():
    """Loads the leaderboard data from a local file."""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading leaderboard file: {e}")
            return []
    return []

def save_leaderboard():
    """Saves the current leaderboard to a local file."""
    try:
        # Sort by final score descending before saving
        leaderboard.sort(key=lambda x: x['final_score'], reverse=True)
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f, indent=4)
    except IOError as e:
        print(f"Error saving leaderboard file: {e}")

def get_username():
    """Draws a simple input box to get the user's name."""
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2, 400, 50)
    color_active = pygame.Color('dodgerblue2')
    color_inactive = pygame.Color('lightskyblue3')
    color = color_inactive
    active = False
    text = ''
    done = False
    
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
        
        screen.fill(BLACK)
        draw_text("Enter your username:", status_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        
        txt_surface = status_font.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)
        
        pygame.display.flip()
    
    return text if text.strip() else "Guest"

def draw_game_board():
    """Draws the cards on the screen based on their state."""
    for row in game_board:
        for card in row:
            # New logic: Check if we are in the initial reveal phase
            if is_revealing_cards or card['is_flipped'] or card['is_matched']:
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

def draw_labels():
    """Draws text labels for each row."""
    # Label for the first row (Attrezzi)
    label_text_1 = label_font.render("Attrezzi", True, WHITE)
    label_rect_1 = label_text_1.get_rect()
    label_rect_1.right = GRID_X - CARD_MARGIN
    label_rect_1.centery = GRID_Y_TOP + CARD_SIZE / 2
    screen.blit(label_text_1, label_rect_1)

    # Label for the second row (Specie)
    label_text_2 = label_font.render("Specie", True, WHITE)
    label_rect_2 = label_text_2.get_rect()
    label_rect_2.right = GRID_X - CARD_MARGIN
    label_rect_2.centery = GRID_Y_BOTTOM + CARD_SIZE / 2
    screen.blit(label_text_2, label_rect_2)


def draw_text(text, font, color, x, y):
    """A helper function to draw text on the screen."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def draw_leaderboard():
    """Draws the top 5 scores from the leaderboard."""
    leaderboard_buffer = pygame.Rect(0, 0, SCREEN_WIDTH * 0.4, SCREEN_HEIGHT * 0.4)
    leaderboard_buffer.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pygame.draw.rect(screen, BLACK, leaderboard_buffer, border_radius=20)
    pygame.draw.rect(screen, BORDER_COLOR, leaderboard_buffer, 2, border_radius=20)

    draw_text("Leaderboard", status_font, WHITE, leaderboard_buffer.centerx, leaderboard_buffer.top + 30)

    # Sort leaderboard by final score (descending)
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['final_score'], reverse=True)

    y_offset = leaderboard_buffer.top + 80
    for i, entry in enumerate(sorted_leaderboard[:5]):
        text = f"{i+1}. {entry['username']} - Score: {entry['final_score']}"
        draw_text(text, status_font, WHITE, leaderboard_buffer.centerx, y_offset)
        y_offset += 50

def draw_game_over_screen(win_state, player_rank=None):
    """Draws the game over screen with a win or lose message and the leaderboard."""
    
    if win_state:
        win_message = f"Hai vinto! Tempo: {game_timer}s"
        message_color = BLACK
        # Add the rank if the player won
        if player_rank:
            win_message += f" - Classifica: #{player_rank}"
    else:
        win_message = "Hai perso! Tentativi esauriti."
        message_color = ATTEMPT_COLOR
    
    # Draw game over message
    buffer_rect = pygame.Rect(0, 0, SCREEN_WIDTH * 0.4, SCREEN_HEIGHT * 0.15)
    buffer_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200)
    pygame.draw.rect(screen, WHITE, buffer_rect, border_radius=20)
    draw_text(win_message, title_font, message_color, buffer_rect.centerx, buffer_rect.centery)
    
    # Draw play again button
    BUTTON_WIDTH = int(SCREEN_WIDTH * 0.2)
    BUTTON_HEIGHT = int(SCREEN_HEIGHT * 0.08)
    play_again_rect = pygame.Rect(
        (SCREEN_WIDTH / 2 - BUTTON_WIDTH / 2),
        (SCREEN_HEIGHT - 100),
        BUTTON_WIDTH,
        BUTTON_HEIGHT
    )
    pygame.draw.rect(screen, BUTTON_COLOR, play_again_rect, border_radius=10)
    draw_text("Gioca ancora", status_font, BLACK, play_again_rect.centerx, play_again_rect.centery)
    
    # Draw the leaderboard on the same screen
    draw_leaderboard()
    
    return play_again_rect

def handle_click(pos):
    """Handles a mouse click to flip a card."""
    global flipped_cards, game_score, matched_pairs, game_over, can_flip, is_revealing_cards

    if not can_flip or game_over or is_revealing_cards:
        return

    for row in game_board:
        for card in row:
            if card['rect'].collidepoint(pos) and not card['is_flipped'] and not card['is_matched']:
                card['is_flipped'] = True
                flipped_cards.append(card)
                
                if len(flipped_cards) == 2:
                    can_flip = False
                    pygame.time.set_timer(pygame.USEREVENT, 1000) 

def get_player_rank(leaderboard, username):
    """Finds the rank of the current player in the sorted leaderboard."""
    for i, entry in enumerate(leaderboard):
        if entry['username'] == username:
            return i + 1
    return None

# --- Main Game Loop ---
def main():
    global game_score, game_over, game_timer, can_flip, matched_pairs, SCREEN_WIDTH, SCREEN_HEIGHT, screen, is_revealing_cards, game_attempts, leaderboard, current_username

    # Initialize fonts once at the start
    initialize_fonts()
    
    # Prompt for username at the very beginning of the first game
    current_username = get_username()
    if not current_username:
        return # Quit if no username is entered

    setup_game()
    running = True
    displaying_game_over = False
    player_rank = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.size
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                # Recalculate layout and fonts on resize
                initialize_fonts()
                update_layout()
            
            if event.type == pygame.USEREVENT:
                card1, card2 = flipped_cards
                if card1['pair_id'] == card2['pair_id']:
                    card1['is_matched'] = True
                    card2['is_matched'] = True
                    matched_pairs += 1
                else:
                    game_attempts += 1 # Increment attempts on a failed match
                    if game_attempts >= MAX_ATTEMPTS:
                        game_over = True
                
                card1['is_flipped'] = False
                card2['is_flipped'] = False
                flipped_cards.clear()
                can_flip = True
                pygame.time.set_timer(pygame.USEREVENT, 0)

            # Handle the new reveal timer event
            if event.type == REVEAL_END_EVENT:
                is_revealing_cards = False
                can_flip = True # Allow clicking after the reveal
                start_time = time.time() # Start the game timer now
                pygame.time.set_timer(REVEAL_END_EVENT, 0) # Stop the reveal timer

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game_over and not is_revealing_cards:
                    handle_click(event.pos)
                elif displaying_game_over:
                    # Check for play again button on game over screen
                    play_again_rect = draw_game_over_screen(matched_pairs == len(GEAR_ICONS), player_rank)
                    if play_again_rect.collidepoint(event.pos):
                        # Prompt for a new username before starting a new game
                        new_username = get_username()
                        if new_username:
                            current_username = new_username
                            setup_game()
                            displaying_game_over = False
                        else:
                            running = False # Quit if user cancels username prompt


        # --- Game Logic Updates ---
        if not game_over:
            # Only update timer after the initial reveal is over
            if not is_revealing_cards:
                game_timer = int(time.time() - start_time)

        if matched_pairs == len(GEAR_ICONS):
            game_over = True

        if game_over and not displaying_game_over:
            # Calculate final score
            final_score = (matched_pairs * 1000) - (game_timer * 10) - (game_attempts * 50)
            final_score = max(0, final_score)
            
            # Add new score to leaderboard and save
            new_entry = {'username': current_username, 'final_score': final_score}
            leaderboard.append(new_entry)
            save_leaderboard()
            
            # Get the player's rank from the newly updated and sorted leaderboard
            player_rank = get_player_rank(leaderboard, current_username)
            displaying_game_over = True

        # --- Drawing to the Screen ---
        screen.blit(background_image_scaled, (0, 0))

        draw_text("Indovina: quale attrezzo pesca cosa?", title_font, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1)
        draw_text("SHARPER Night 2025", subtitle_font, SUBTITLE_COLOR, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.17)
        
        # New attempt counter display
        attempts_color = WHITE if game_attempts < MAX_ATTEMPTS - 1 else ATTEMPT_COLOR
        draw_text(f"Tentativi: {game_attempts}/{MAX_ATTEMPTS}", status_font, attempts_color, SCREEN_WIDTH * 0.1, SCREEN_HEIGHT * 0.2)
        draw_text(f"Tempo: {game_timer}s", status_font, WHITE, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2)

        if not displaying_game_over:
            draw_game_board()
            draw_labels() # Call the new function to draw the labels

        if displaying_game_over:
            draw_game_over_screen(matched_pairs == len(GEAR_ICONS), player_rank)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()