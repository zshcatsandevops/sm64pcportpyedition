from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController  # For basic movement, but customized for Mario feel
import random

app = Ursina()

# Global vars
stars_collected = 0
total_stars = 151  # Nod to Shining Stars - but we start with 5 for demo
goal_reached = False

# Simple Mario-like player (orange cube for now - mod in a model later!)
player = FirstPersonController(model='cube', color=color.orange, scale=(0.6, 1.8, 0.6), speed=8, jump_height=3)
player.position = Vec3(0, 5, 0)

# Third-person camera toggle
third_person = False
def toggle_camera():
    global third_person
    third_person = not third_person
    if third_person:
        camera.parent = player
        camera.position = Vec3(0, 4, -10)
        camera.rotation_x = 10
    else:
        camera.parent = None
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)

# Hub World Ground & Platforms
ground = Entity(model='plane', scale=50, texture='grass', collider='box', color=color.green)
platform1 = Entity(model='cube', scale=(10, 1, 10), position=(15, 2, 0), color=color.brown, collider='box')
platform2 = Entity(model='cube', scale=(8, 1, 8), position=(0, 5, -15), color=color.brown, collider='box')
pitfall = Entity(model='cube', scale=(5, 0.1, 5), position=(25, -1, 0), color=color.red, collider='box')  # Deadly pit

# Simple Course - Floating Islands for Star Hunt
for i in range(3):
    x = random.uniform(-20, 20)
    z = random.uniform(-20, 20)
    y = random.uniform(3, 8)
    Entity(model='cube', scale=(6, 1, 6), position=(x, y, z), color=color.gray, collider='box')

# Stars to Collect (Yellow Spheres - Shine like in SM64!)
stars = []
for i in range(5):  # Demo count - expand to 151 for full chaos
    star = Entity(model='sphere', color=color.yellow, scale=0.5, position=Vec3(random.uniform(-25, 25), random.uniform(5, 15), random.uniform(-25, 25)))
    star.collider = 'sphere'
    stars.append(star)

# Bowser Tease (Hidden Boss Entity - Appears after 5 stars)
bowser = Entity(model='cube', color=color.red, scale=(3, 4, 2), position=(0, 10, 30), visible=False)
bowser_text = Text('Bowser: "Muahaha! The Grand Shining Star is MINE!"', position=(-0.5, 0.4), scale=2, visible=False)

# UI - Star Counter (Mario Font Vibes)
star_text = Text(f'Stars: {stars_collected}/{total_stars}', position=(-0.8, 0.45), scale=2, color=color.yellow)
instruction_text = Text('WASD: Move | Space: Jump | C: Toggle Camera | I: Infinite Jump Cheat', position=(-0.8, -0.45), scale=1.5)

# Sounds (Ursina Built-ins - Add WAVs for full mod)
def collect_sound():
    Audio('coin', autoplay=True, volume=0.5)  # Placeholder - mod in SM64 star jingle

def victory_sound():
    Audio('crowd_cheer', autoplay=True, volume=0.7)

# Input Handling
def input(key):
    if key == 'c':
        toggle_camera()
    if key == 'i':
        player.gravity = 0 if player.gravity == 0 else -20  # Cheat: Toggle gravity off
        print('Infinite Jump Activated!' if player.gravity == 0 else 'Gravity Restored!')

# Update Loop - Movement, Collisions, Star Logic
def update():
    global stars_collected, goal_reached
    
    # Basic Mario Physics (Ursina handles gravity/jump)
    player.rotation_y += (mouse.velocity[0] * 150) * time.dt  # Mouse look
    
    # Star Collection
    hit_info = raycast(player.world_position, player.down, distance=2)
    for star in stars[:]:  # Copy list to avoid mod during iter
        if distance(player, star) < 1.5:
            destroy(star)
            stars.remove(star)
            stars_collected += 1
            collect_sound()
            star_text.text = f'Stars: {stars_collected}/{total_stars}'
            
            # Bowser Unlock at 5 Stars
            if stars_collected == 5 and not goal_reached:
                bowser.visible = True
                bowser_text.visible = True
                victory_sound()
                goal_reached = True
                print('Shining Stars Mini-Run Complete! Time to mod more levels...')
    
    # Pitfall Death (Respawn)
    if held_keys['shift'] and distance(player, pitfall) < 3:  # Simulate fall
        player.position = Vec3(0, 5, 0)
        print('Oof! Respawning at Hub - Keep Collecting!')

# Lighting for that N64 Glow
directional_light = DirectionalLight()
directional_light.rotation = (45, 45, 45)

# Run the Mod!
app.run()
