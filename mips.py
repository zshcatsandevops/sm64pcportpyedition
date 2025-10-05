# Python 3.13 + Ursina Engine - Super Mario 64 with MIPS Bunny
from ursina import *
from math import sin, cos, radians, sqrt, atan2
import random

app = Ursina(title='Super Mario 64 - MIPS Bunny Edition')

# Constants
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_POWER = 10
GRAVITY = 20

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgb(255, 0, 0),  # Red for Mario
            scale=(1, 1.8, 1),
            collider='box',
            position=(0, 2, 0),
            **kwargs
        )
        # Mario's hat
        self.hat = Entity(
            model='cube',
            color=color.rgb(200, 0, 0),
            scale=(1.2, 0.3, 1.2),
            parent=self,
            position=(0, 1, 0)
        )
        self.vel = Vec3(0, 0, 0)
        self.on_ground = False
        self.jump_chain = 0
        self.coins = 0
        self.stars = 0
    
    def update(self):
        dt = time.dt
        keys = held_keys
        
        # Horizontal movement
        move = Vec3(keys['d'] - keys['a'], 0, keys['w'] - keys['s'])
        if move.length() > 0:
            move = move.normalized()
            self.rotation_y = atan2(move.x, move.z) * 57.3
            speed = RUN_SPEED if keys['shift'] else WALK_SPEED
            self.position += move * speed * dt
        
        # Apply gravity
        self.vel.y -= GRAVITY * dt
        self.position += self.vel * dt
        
        # Ground collision
        hit_info = raycast(self.world_position, Vec3(0, -1, 0), distance=1.1, ignore=(self,))
        if hit_info.hit:
            if self.vel.y < 0:
                self.y = hit_info.world_point.y + 0.9
                self.vel.y = 0
                self.on_ground = True
                self.jump_chain = 0
        else:
            self.on_ground = False
        
        # Jump
        if keys['space'] and self.on_ground:
            self.vel.y = JUMP_POWER
            self.jump_chain += 1
            self.on_ground = False


class MIPSBunny(Entity):
    """The famous yellow rabbit from Super Mario 64!"""
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.yellow,
            scale=(0.8, 1.2, 1.4),  # Bunny body
            collider='box',
            **kwargs
        )
        
        # Bunny head
        self.head = Entity(
            model='sphere',
            color=color.yellow,
            scale=(0.7, 0.7, 0.7),
            parent=self,
            position=(0, 0.8, 0.2)
        )
        
        # Long ears
        self.left_ear = Entity(
            model='cube',
            color=color.yellow,
            scale=(0.15, 0.8, 0.1),
            parent=self.head,
            position=(-0.3, 0.6, 0),
            rotation=(0, 0, -15)
        )
        self.right_ear = Entity(
            model='cube',
            color=color.yellow,
            scale=(0.15, 0.8, 0.1),
            parent=self.head,
            position=(0.3, 0.6, 0),
            rotation=(0, 0, 15)
        )
        
        # Pink inner ears
        Entity(
            model='cube',
            color=color.pink,
            scale=(0.08, 0.5, 0.05),
            parent=self.left_ear,
            position=(0, 0.1, 0.05)
        )
        Entity(
            model='cube',
            color=color.pink,
            scale=(0.08, 0.5, 0.05),
            parent=self.right_ear,
            position=(0, 0.1, 0.05)
        )
        
        # Eyes
        self.left_eye = Entity(
            model='sphere',
            color=color.black,
            scale=0.15,
            parent=self.head,
            position=(-0.2, 0.1, 0.3)
        )
        self.right_eye = Entity(
            model='sphere',
            color=color.black,
            scale=0.15,
            parent=self.head,
            position=(0.2, 0.1, 0.3)
        )
        
        # Nose
        self.nose = Entity(
            model='sphere',
            color=color.pink,
            scale=(0.1, 0.08, 0.1),
            parent=self.head,
            position=(0, 0, 0.35)
        )
        
        # Cotton tail
        self.tail = Entity(
            model='sphere',
            color=color.white,
            scale=0.4,
            parent=self,
            position=(0, 0, -0.8)
        )
        
        # Animation properties
        self.hop_time = 0
        self.hop_speed = random.uniform(2, 4)
        self.move_target = None
        self.scared = False
        
    def update(self):
        # Animate bunny hopping
        self.hop_time += time.dt * self.hop_speed
        hop = abs(sin(self.hop_time)) * 0.3
        self.y = self.original_y + hop
        
        # Wiggle ears
        ear_wiggle = sin(self.hop_time * 2) * 5
        self.left_ear.rotation_z = -15 + ear_wiggle
        self.right_ear.rotation_z = 15 - ear_wiggle
        
        # Random hopping movement
        if not self.scared and random.random() < 0.01:
            self.move_target = Vec3(
                random.uniform(-20, 20),
                self.y,
                random.uniform(-20, 20)
            )
        
        if self.move_target:
            direction = self.move_target - self.position
            if direction.length() > 0.5:
                direction = direction.normalized()
                self.position += direction * 2 * time.dt
                self.look_at(self.move_target)
            else:
                self.move_target = None


# Create Mario
mario = Mario()

# =============== BUILD THE COURSE ===============

# Main ground
ground = Entity(
    model='plane',
    scale=100,
    texture='grass',
    collider='box',
    texture_scale=(20, 20),
    color=color.rgb(100, 200, 100)
)

# Castle walls (Peach's Castle courtyard)
castle_wall_positions = [
    (0, 0, -30, 40, 10, 2),     # Back wall
    (-20, 0, -10, 2, 10, 40),   # Left wall
    (20, 0, -10, 2, 10, 40),    # Right wall
]

walls = []
for x, y, z, sx, sy, sz in castle_wall_positions:
    wall = Entity(
        model='cube',
        position=(x, y + sy/2, z),
        scale=(sx, sy, sz),
        color=color.rgb(150, 150, 150),
        collider='box',
        texture='brick'
    )
    walls.append(wall)

# Green pipes (warp pipes)
pipe_positions = [
    (-15, 0, 10),
    (15, 0, 10),
    (0, 0, 15)
]

pipes = []
for x, y, z in pipe_positions:
    # Pipe body (using cube instead of cylinder)
    pipe = Entity(
        model='cube',
        position=(x, y + 2, z),
        scale=(1.5, 4, 1.5),
        color=color.rgb(0, 180, 0),
        collider='box'
    )
    # Pipe rim
    pipe_rim = Entity(
        model='cube',
        position=(x, y + 4.2, z),
        scale=(1.8, 0.5, 1.8),
        color=color.rgb(0, 200, 0),
        collider='box'
    )
    pipes.append(pipe)

# Floating platforms (classic SM64 style)
platforms = []
platform_configs = [
    # (x, y, z, scale_x, scale_z, color)
    (0, 3, 0, 4, 4, color.brown),           # Center platform
    (-8, 5, -8, 3, 3, color.orange),        # Left-back
    (8, 5, -8, 3, 3, color.orange),         # Right-back
    (-12, 7, 0, 2.5, 2.5, color.red),       # High left
    (12, 7, 0, 2.5, 2.5, color.red),        # High right
    (0, 9, -5, 3, 3, color.violet),         # Top center
]

for x, y, z, sx, sz, col in platform_configs:
    p = Entity(
        model='cube',
        color=col,
        scale=(sx, 0.5, sz),
        position=(x, y, z),
        collider='box'
    )
    platforms.append(p)

# Staircase to castle
stairs = []
for i in range(8):
    stair = Entity(
        model='cube',
        position=(0, i * 0.5, -25 + i * 0.8),
        scale=(6, 0.5 + i * 0.1, 1),
        color=color.rgb(200, 200, 220),
        collider='box'
    )
    stairs.append(stair)

# Bob-omb Battlefield style hills
hills = []
for i in range(6):
    angle = i * 60
    x = cos(radians(angle)) * 25
    z = sin(radians(angle)) * 25
    hill = Entity(
        model='sphere',
        position=(x, -2, z),
        scale=(8, 6, 8),
        color=color.rgb(80, 160, 80),
        collider='mesh'
    )
    hills.append(hill)

# Red coins (8 red coins challenge)
red_coins = []
for i in range(8):
    angle = i * 45
    x = cos(radians(angle)) * 12
    z = sin(radians(angle)) * 12
    coin = Entity(
        model='sphere',
        color=color.red,
        scale=0.6,
        position=(x, 3 + sin(radians(angle * 2)) * 2, z)
    )
    red_coins.append(coin)

# Yellow coins
yellow_coins = []
for i in range(20):
    x = random.uniform(-18, 18)
    z = random.uniform(-18, 18)
    coin = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.4,
        position=(x, 1.5, z)
    )
    yellow_coins.append(coin)

# Power stars
stars = []
star_positions = [(0, 11, -5), (15, 8, 0), (-15, 8, 0)]
for x, y, z in star_positions:
    star = Entity(
        model='sphere',
        color=color.gold,
        scale=0.8,
        position=(x, y, z)
    )
    # Star points (simplified)
    for j in range(5):
        angle = j * 72
        sx = cos(radians(angle)) * 0.5
        sz = sin(radians(angle)) * 0.5
        Entity(
            model='cube',
            color=color.gold,
            scale=(0.2, 0.2, 0.2),
            parent=star,
            position=(sx, 0, sz)
        )
    stars.append(star)

# MIPS BUNNIES!
bunnies = []
bunny_positions = [
    (5, 1, 5),
    (-8, 1, 8),
    (10, 1, -5)
]

for x, y, z in bunny_positions:
    bunny = MIPSBunny(position=(x, y, z))
    bunny.original_y = y
    bunnies.append(bunny)

# =============== CAMERA ===============
camera.parent = mario
camera.position = (0, 5, -12)
camera.rotation = (15, 0, 0)

# =============== UI ===============
title_text = Text(
    text='Super Mario 64 - MIPS Bunny Edition',
    position=(-.85, .47),
    color=color.white,
    scale=1.2
)
coin_text = Text(
    text='Coins: 0',
    position=(-.85, .42),
    color=color.yellow
)
star_text = Text(
    text='Stars: 0/3',
    position=(-.85, .37),
    color=color.gold
)
bunny_text = Text(
    text='MIPS Caught: 0/3',
    position=(-.85, .32),
    color=color.yellow
)

mario.bunnies_caught = 0

# Coin spin animation
for coin in yellow_coins + red_coins:
    coin.rotation_y = random.uniform(0, 360)
    coin.animate('rotation_y', coin.rotation_y + 360, duration=2, loop=True)

# Star spin animation
for star in stars:
    star.animate('rotation_y', 360, duration=3, loop=True)
    star.animate('y', star.y + 0.5, duration=1.5, loop=True)

# =============== GAME LOGIC ===============
def update():
    mario.update()
    
    # Bunny AI
    for bunny in bunnies:
        if bunny.enabled:
            bunny.update()
            
            # Check if Mario is near bunny
            dist = distance(mario.position, bunny.position)
            if dist < 8:
                bunny.scared = True
                # Run away from Mario
                escape_dir = (bunny.position - mario.position).normalized()
                bunny.position += escape_dir * 3 * time.dt
                bunny.look_at(mario)
                bunny.rotation_y += 180
            else:
                bunny.scared = False
            
            # Catch bunny
            if dist < 1.5:
                bunny.enabled = False
                mario.bunnies_caught += 1
                bunny_text.text = f'MIPS Caught: {mario.bunnies_caught}/3'
                print(f"You caught MIPS! Total: {mario.bunnies_caught}/3")
    
    # Yellow coin pickup
    for coin in yellow_coins:
        if coin.enabled and distance(mario.position, coin.position) < 1:
            coin.enabled = False
            mario.coins += 1
            coin_text.text = f'Coins: {mario.coins}'
    
    # Red coin pickup
    for coin in red_coins:
        if coin.enabled and distance(mario.position, coin.position) < 1:
            coin.enabled = False
            mario.coins += 2
            coin_text.text = f'Coins: {mario.coins}'
            print("Red Coin! +2")
    
    # Star collection
    for i, star in enumerate(stars):
        if star.enabled and distance(mario.position, star.position) < 1.5:
            star.enabled = False
            mario.stars += 1
            star_text.text = f'Stars: {mario.stars}/3'
            print(f"⭐ STAR GET! Total: {mario.stars}/3")
    
    # Smooth camera follow
    camera.look_at(mario)
    
    # Win condition
    if mario.stars >= 3:
        if not hasattr(mario, 'won'):
            mario.won = True
            Text(
                text='🎉 YOU WIN! ALL STARS COLLECTED! 🎉',
                position=(-.4, 0),
                scale=2,
                color=color.gold
            )
            print("CONGRATULATIONS! You collected all the stars!")

# =============== SKY ===============
Sky(color=color.rgb(135, 206, 235))

print("=" * 50)
print("🎮 SUPER MARIO 64 - MIPS BUNNY EDITION 🐰")
print("=" * 50)
print("Controls:")
print("  WASD - Move")
print("  SHIFT - Run")
print("  SPACE - Jump")
print("\nObjectives:")
print("  • Catch all 3 MIPS bunnies")
print("  • Collect coins")
print("  • Get all 3 power stars")
print("=" * 50)

app.run()
