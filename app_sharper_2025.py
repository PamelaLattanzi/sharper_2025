import pygame
import random
import time
import json
import os
import math # Added for particle rotation

# Run from the script's folder so relative asset paths (./placeholder, leaderboard.json) always resolve
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- Pygame Initialization ---
pygame.init()

# Initial screen size and reference size for scaling
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Indovina: quale attrezzo pesca cosa?")

# CHANGED: Reduced the reference resolution for better scaling on modern screens.
# This makes all UI elements (fonts, cards) appear larger relative to the window size.
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
LABEL_BAR_COLOR = (40, 40, 40, 220) 

# REMOVED: BUBBLE_COLORS as fish images are now used

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
GRID_WIDTH = 0 # New variable to store the total width of the card grid
border_width = 8
border_radius = 20

# --- Fonts ---
title_font = None
subtitle_font = None
status_font = None
card_font = None
label_font = None
leaderboard_font = None # New font for the leaderboard
message_font = None # New font for final message

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
current_username = "" # Global variable to store the username
FISH_PARTICLES = [] # List to hold active fish particles for the win effect
PARTICLE_IMAGES = {} # NEW: Dictionary to hold small scaled particle images

# --- Leaderboard Variables ---
LEADERBOARD_FILE = 'leaderboard.json'
leaderboard = []

# --- Custom Events ---
REVEAL_END_EVENT = pygame.USEREVENT + 1


# --- Classes for Fish Particle Effect (Updated for image-based particle) ---
class FishParticle:
    """A fish image particle for the win effect."""
    def __init__(self, x, y):
        # Select a random fish image for this particle
        self.image_path = random.choice(FISH_ICONS)
        self.image = PARTICLE_IMAGES.get(self.image_path)
        
        # Fallback for safety
        if self.image is None:
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            self.image.fill((255, 0, 0, 100))
        
        self.rect = self.image.get_rect(center=(x, y))

        # Initial position (using float for precision)
        self.x = float(x)
        self.y = float(y)

        # Increased speed for a dramatic burst (bigger fish, more motion)
        # Random burst direction (vx and vy)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(8, 18) # Increased speed
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        
        self.drift_vx = random.uniform(-0.5, 0.5)
        self.drift_vy = random.uniform(-0.5, 0.5)

        self.lifetime = 120 # Frames (2 seconds)
        self.gravity = 0.4 # Slight downward pull for a falling/swimming effect

    def update(self):
        """Updates particle position and velocity."""
        # Apply gravity and slight velocity decay
        self.vy += self.gravity
        self.vx *= 0.98 # Drag
        self.vy *= 0.98 # Drag
        
        # Update position
        self.x += self.vx + self.drift_vx
        self.y += self.vy + self.drift_vy
        self.rect.center = (int(self.x), int(self.y))
        self.lifetime -= 1
        
    def draw(self, surface):
        """Draws the fish particle image with rotation."""
        if self.lifetime > 0:
            # Calculate rotation angle based on movement direction
            if self.vx != 0 or self.vy != 0:
                # Angle in radians, then convert to degrees and adjust rotation
                angle = math.atan2(self.vy, self.vx) * (180 / math.pi)
                # Rotate the image
                rotated_image = pygame.transform.rotate(self.image, -angle) 
                rotated_rect = rotated_image.get_rect(center=self.rect.center)
                surface.blit(rotated_image, rotated_rect)
            else:
                # Draw image without rotation if stationary
                surface.blit(self.image, self.rect)


def launch_win_effect(center_x, center_y, count=800): # Increased count for "a lot"
    """Generates a burst of fish particles."""
    global FISH_PARTICLES
    # Clear existing particles before a new launch
    FISH_PARTICLES.clear() 
    for _ in range(count):
        # Create a tight source around the center
        x_start = center_x + random.uniform(-20, 20)
        y_start = center_y + random.uniform(-20, 20)
        particle = FishParticle(x_start, y_start)
        FISH_PARTICLES.append(particle)

# --- Functions ---
def initialize_fonts():
    """Initializes all font objects. This must be called once at the start."""
    global title_font, subtitle_font, status_font, card_font, label_font, leaderboard_font, message_font

    # Calculate scale ratio based on the updated screen dimensions
    scale_ratio = min(SCREEN_WIDTH / INITIAL_SCREEN_WIDTH, SCREEN_HEIGHT / INITIAL_SCREEN_HEIGHT)
    
    title_font = pygame.font.Font(None, int(100 * scale_ratio))
    subtitle_font = pygame.font.Font(None, int(90 * scale_ratio))
    status_font = pygame.font.Font(None, int(80 * scale_ratio))
    card_font = pygame.font.Font(None, int(140 * scale_ratio))
    label_font = pygame.font.Font(None, int(50 * scale_ratio)) 
    leaderboard_font = pygame.font.Font(None, int(50 * scale_ratio)) 
    message_font = pygame.font.Font(None, int(60 * scale_ratio)) 

def update_layout():
    """Recalculates positions, sizes, and fonts for all game elements on resize."""
    global GRID_X, GRID_Y_TOP, GRID_Y_BOTTOM, GRID_WIDTH, background_image_scaled, SCREEN_WIDTH, SCREEN_HEIGHT, CARD_SIZE, CARD_MARGIN, border_width, PARTICLE_IMAGES
    
    # Calculate scaling ratio based on the smaller dimension to maintain aspect ratio
    scale_ratio = min(SCREEN_WIDTH / INITIAL_SCREEN_WIDTH, SCREEN_HEIGHT / INITIAL_SCREEN_HEIGHT)
    
    # Recalculate dynamic sizes
    CARD_SIZE = int(350 * scale_ratio) 
    CARD_MARGIN = int(50 * scale_ratio) 
    border_width = int(8 * scale_ratio)

    # Calculate total grid width (6 cards + 5 margins + 1 margin for centering)
    GRID_WIDTH = GRID_COLS * CARD_SIZE + (GRID_COLS - 1) * CARD_MARGIN 

    # Recalculate grid positions
    # Grid X position centered horizontally
    GRID_X = (SCREEN_WIDTH - GRID_WIDTH) / 2
    
    # Grid Y positions adjusted slightly to accommodate the labels above
    GRID_Y_TOP = SCREEN_HEIGHT * 0.35 
    GRID_Y_BOTTOM = GRID_Y_TOP + CARD_SIZE + CARD_MARGIN + int(40 * scale_ratio) 

    # Update background image size
    if background_image:
        background_image_scaled = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Re-scale loaded images for cards using smoothscale for quality
    for path in loaded_images:
        # Use smoothscale for higher quality image downscaling
        # IMPORTANT: We use the original loaded image (which is stored in loaded_images)
        original_image = loaded_images[path] 
        scaled_image = pygame.transform.smoothscale(original_image, (CARD_SIZE - border_width*2, CARD_SIZE - border_width*2))
        loaded_images[path] = scaled_image

    # NEW: Recalculate particle size and scale particle images ("bigger" fish)
    particle_size = int(CARD_SIZE * 0.3) # 30% of card size
    for path in FISH_ICONS:
        try:
            # Re-load original image for scaling consistency
            original_image = pygame.image.load(path).convert_alpha()
            scaled_image = pygame.transform.smoothscale(original_image, (particle_size, particle_size))
            PARTICLE_IMAGES[path] = scaled_image
        except pygame.error:
            # Fallback
            PARTICLE_IMAGES[path] = pygame.Surface((30, 30), pygame.SRCALPHA)
            PARTICLE_IMAGES[path].fill((255, 0, 0, 100)) # Red semi-transparent square
    

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
    global game_board, game_over, matched_pairs, game_score, start_time, can_flip, loaded_images, background_image, SCREEN_WIDTH, SCREEN_HEIGHT, is_revealing_cards, leaderboard, PARTICLE_IMAGES
    
    game_over = False
    matched_pairs = 0
    game_score = 0
    flipped_cards.clear()
    FISH_PARTICLES.clear() # Clear fish particles for new game
    PARTICLE_IMAGES.clear() # Clear particle images, they will be recreated/scaled in update_layout
    
    # Load the leaderboard
    leaderboard = load_leaderboard()

    # Set state for initial card reveal
    is_revealing_cards = True
    can_flip = False # Prevent flipping while cards are being revealed
    pygame.time.set_timer(REVEAL_END_EVENT, 15000) # 8-second timer for the reveal

    # Load the background image once at the start
    try:
        background_image = pygame.image.load(BACKGROUND_IMAGE_PATH).convert()
    except pygame.error as e:
        print(f"Error loading background image: {BACKGROUND_IMAGE_PATH} - {e}")
        background_image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        background_image.fill(BLACK)
    
    # Load all card images once (we load the originals here, scaling happens in update_layout)
    all_icons = GEAR_ICONS + FISH_ICONS
    for path in all_icons:
        try:
            # Load the original image once
            image = pygame.image.load(path).convert_alpha()
            # Store the original image to be scaled later in update_layout
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
    
    update_layout() # Initial layout calculation (and particle image scaling)
    start_time = time.time()
    can_flip = True

def load_leaderboard():
    """Loads the leaderboard data from a local file."""
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r') as f:
                data = json.load(f)
                # Cleanup old entries that might not have the 'time' key
                cleaned_data = []
                for entry in data:
                    if 'time' not in entry:
                        # Estimate time based on score for sorting/display robustness
                        # Score = 1000000 - time, so time = 1000000 - score
                        entry['time'] = 1000000 - entry.get('final_score', 0) 
                    cleaned_data.append(entry)
                return cleaned_data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading leaderboard file: {e}")
            return []
    return []

def save_leaderboard():
    """Saves the current leaderboard to a local file."""
    try:
        # Sort by final score descending (higher score = faster time)
        leaderboard.sort(key=lambda x: x['final_score'], reverse=True) 
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f, indent=4)
    except IOError as e:
        print(f"Error saving leaderboard file: {e}")

def get_username():
    """Draws a simple input box to get the user's name."""
    # Fixed size input box for better aesthetics
    input_box_width = int(SCREEN_WIDTH * 0.2)
    input_box_height = int(SCREEN_HEIGHT * 0.05)
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - input_box_width // 2, SCREEN_HEIGHT // 2, input_box_width, input_box_height)
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
        # Use a fixed width for the text surface to prevent it from growing
        text_rect = txt_surface.get_rect(center=input_box.center)
        screen.blit(txt_surface, text_rect)
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
    """Draws a long webbing bar with the text labels above each row."""
    
    # Define the height of the webbing bar
    BAR_HEIGHT = label_font.get_height() + 30 
    
    # --- Attrezzi Label (Top Row) ---
    
    # Define the rectangle for the webbing bar
    bar_rect_1 = pygame.Rect(
        GRID_X, # Start aligned with the first card
        GRID_Y_TOP - BAR_HEIGHT, # Position the bar to end right at the start of the cards
        GRID_WIDTH, # Span the entire width of the card grid
        BAR_HEIGHT
    )

    # Draw the semi-transparent bar
    s1 = pygame.Surface((bar_rect_1.width, bar_rect_1.height), pygame.SRCALPHA)
    s1.fill(LABEL_BAR_COLOR)
    screen.blit(s1, (bar_rect_1.x, bar_rect_1.y))
    
    # Draw text centered horizontally and vertically in the bar
    draw_text(
        "Attrezzi:", 
        label_font, 
        WHITE, 
        bar_rect_1.centerx, 
        bar_rect_1.centery, 
        align="center"
    )

    # --- Specie Label (Bottom Row) ---
    
    # Define the rectangle for the webbing bar
    bar_rect_2 = pygame.Rect(
        GRID_X, # Start aligned with the first card
        GRID_Y_BOTTOM - BAR_HEIGHT, # Position the bar to end right at the start of the cards
        GRID_WIDTH, # Span the entire width of the card grid
        BAR_HEIGHT
    )
    
    # Draw the semi-transparent bar
    s2 = pygame.Surface((bar_rect_2.width, bar_rect_2.height), pygame.SRCALPHA)
    s2.fill(LABEL_BAR_COLOR)
    screen.blit(s2, (bar_rect_2.x, bar_rect_2.y))

    # Draw text centered horizontally and vertically in the bar
    draw_text(
        "Specie:", 
        label_font, 
        WHITE, 
        bar_rect_2.centerx, 
        bar_rect_2.centery, 
        align="center"
    )


def draw_text(text, font, color, x, y, align="center"):
    """A helper function to draw text with alignment on the screen."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "center":
        text_rect.center = (x, y)
    elif align == "left":
        text_rect.left = x
        text_rect.centery = y
        
    screen.blit(text_surface, text_rect)

def draw_leaderboard():
    """Draws the top 5 scores from the leaderboard at the bottom left."""
    # New positioning: Bottom-left corner
    PADDING = 20
    buffer_width = SCREEN_WIDTH * 0.3
    buffer_height = SCREEN_HEIGHT * 0.35
    leaderboard_buffer = pygame.Rect(
        PADDING,
        SCREEN_HEIGHT - buffer_height - PADDING,
        buffer_width,
        buffer_height
    )
    pygame.draw.rect(screen, (0, 0, 0, 100), leaderboard_buffer, border_radius=20) # Use a semi-transparent black
    pygame.draw.rect(screen, BORDER_COLOR, leaderboard_buffer, 2, border_radius=20)

    draw_text("Classifica:", status_font, WHITE, leaderboard_buffer.centerx, leaderboard_buffer.top + 30)

    # Sort leaderboard by final score (descending), which means fastest time is ranked highest
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x.get('final_score', 0), reverse=True)

    y_offset = leaderboard_buffer.top + 80
    for i, entry in enumerate(sorted_leaderboard[:5]):
        # Use .get() to safely retrieve 'time', defaulting to N/A if missing (for old entries)
        time_display = entry.get('time', 'N/A')
        text = f"{i+1}. {entry['username']} - Tempo: {time_display}s"
        draw_text(text, leaderboard_font, WHITE, leaderboard_buffer.left + PADDING, y_offset, align="left")
        y_offset += 40

def draw_final_message_and_ranking(win_state, player_rank):
    """Draws the final win/lose message and ranking at the bottom left."""
    PADDING = 20
    buffer_width = SCREEN_WIDTH * 0.3
    buffer_height = SCREEN_HEIGHT * 0.1
    # Position the message buffer just above the leaderboard
    message_buffer = pygame.Rect(
        PADDING,
        SCREEN_HEIGHT - (SCREEN_HEIGHT * 0.35) - PADDING - buffer_height - 10,
        buffer_width,
        buffer_height
    )
    
    pygame.draw.rect(screen, (0, 0, 0, 100), message_buffer, border_radius=20)
    pygame.draw.rect(screen, BORDER_COLOR, message_buffer, 2, border_radius=20)

    # We assume a win since the game only ends on matched_pairs == 6
    message = f"Hai vinto! Tempo: {game_timer}s"
    message_color = WHITE
    
    # Ensure player_rank is not None before trying to use it
    if player_rank is not None:
        message += f" Classifica: #{player_rank}"
    
    draw_text(message, message_font, message_color, message_buffer.centerx, message_buffer.centery)


def draw_game_over_screen():
    """Draws the main elements of the game over screen (e.g., the button)."""
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
    
    return play_again_rect

def handle_click(pos):
    """Handles a mouse click to flip a card."""
    global flipped_cards, game_score, matched_pairs, game_over, can_flip, is_revealing_cards

    # Game only stops when completed
    if not can_flip or game_over or is_revealing_cards:
        return

    for row in game_board:
        for card in row:
            if card['rect'].collidepoint(pos) and not card['is_flipped'] and not card['is_matched']:
                card['is_flipped'] = True
                flipped_cards.append(card)
                
                if len(flipped_cards) == 2:
                    can_flip = False
                    pygame.time.set_timer(pygame.USEREVENT, 1500) 

def get_player_rank(leaderboard, username):
    """Finds the rank of the current player in the sorted leaderboard."""
    # Re-sort leaderboard by final score (descending) to get the rank
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x.get('final_score', 0), reverse=True)
    for i, entry in enumerate(sorted_leaderboard):
        if entry['username'] == username:
            return i + 1
    return None
    
def draw_title_and_status():
    """Draws the title and game status text on the screen."""
    draw_text("Indovina: quale attrezzo pesca cosa?", title_font, WHITE, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.1)
    draw_text("SHARPER Night 2025", subtitle_font, SUBTITLE_COLOR, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.17)
    
    # Only display the time status
    draw_text(f"Tempo: {game_timer}s", status_font, WHITE, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.2)


# --- Main Game Loop ---
def main():
    global game_score, game_over, game_timer, can_flip, matched_pairs, SCREEN_WIDTH, SCREEN_HEIGHT, screen, is_revealing_cards, leaderboard, current_username, FISH_PARTICLES

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
                    # No penalty for wrong guess, just flip back
                    pass
                
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
                    play_again_rect = draw_game_over_screen()
                    if play_again_rect.collidepoint(event.pos):
                        # Prompt for a new username before starting a new game
                        new_username = get_username()
                        if new_username:
                            current_username = new_username
                            setup_game()
                            displaying_game_over = False
                            FISH_PARTICLES.clear() # Clear particles for the new game
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
            # UPDATED: Launch fish/bubble effect when the game is won
            launch_win_effect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            
            # Calculate final score: Maximize score by minimizing time.
            # We use a base large number (1,000,000) minus time. Higher score = lower time.
            final_score = 1000000 - game_timer
            
            # Add new score to leaderboard and save
            new_entry = {
                'username': current_username, 
                'final_score': final_score, # For sorting
                'time': game_timer          # For display
            }
            # Remove old entry if username already exists before appending
            leaderboard = [entry for entry in leaderboard if entry['username'] != current_username]
            leaderboard.append(new_entry)
            save_leaderboard()
            
            # Get the player's rank from the newly updated and sorted leaderboard
            player_rank = get_player_rank(leaderboard, current_username)
            displaying_game_over = True

        # --- Drawing to the Screen ---
        screen.blit(background_image_scaled, (0, 0))
        draw_title_and_status()

        if not displaying_game_over:
            draw_game_board()
            draw_labels() # Call the new function to draw the labels

        if displaying_game_over:
            # We assume a win since the game only ends on matched_pairs == 6
            draw_final_message_and_ranking(True, player_rank) 
            draw_leaderboard()
            draw_game_over_screen()
            
        # UPDATED: Update and draw fish particles
        for particle in FISH_PARTICLES:
            particle.update()
            particle.draw(screen)
        # Remove dead particles
        FISH_PARTICLES = [p for p in FISH_PARTICLES if p.lifetime > 0]
            
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
