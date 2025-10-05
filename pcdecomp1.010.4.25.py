
# Python 3.13 + Ursina Engine - Super Mario 64: Peach's Castle Edition
from ursina import *
from math import sin, cos, radians, sqrt, atan2
import random

app = Ursina(title='Super Mario 64 - Peach\'s Castle Edition', borderless=False)

# Constants
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_POWER = 12
GRAVITY = 25
STAR_REQUIREMENT = 8  # Stars needed to unlock areas

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgb(255, 0, 0),
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
        # Mario's overalls
        self.overalls = Entity(
            model='cube',
            color=color.blue,
            scale=(1.1, 0.8, 1.1),
            parent=self,
            position=(0, -0.2, 0)
        )
        
        self.vel = Vec3(0, 0, 0)
        self.on_ground = False
        self.jump_chain = 0
        self.coins = 0
        self.stars = 0
        self.current_course = "castle_grounds"
    
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
            
        # Water/lava collision
        if self.y < -5:
            self.position = (0, 10, 0)
            self.vel = Vec3(0, 0, 0)

class MIPSBunny(Entity):
    """The famous yellow rabbit from Super Mario 64!"""
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.yellow,
            scale=(0.8, 1.2, 1.4),
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
        self.original_y = self.y
        
    def update(self):
        if not self.enabled:
            return
            
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
                random.uniform(-15, 15),
                self.original_y,
                random.uniform(-15, 15)
            )
        
        if self.move_target:
            direction = self.move_target - self.position
            if direction.length() > 0.5:
                direction = direction.normalized()
                self.position += direction * 2 * time.dt
                self.rotation_y = atan2(direction.x, direction.z) * 57.3
            else:
                self.move_target = None

class PaintingPortal(Entity):
    """Magic painting that warps Mario to courses"""
    def __init__(self, course_name, star_requirement=0, **kwargs):
        super().__init__(
            model='quad',
            scale=(3, 2),
            collider='box',
            **kwargs
        )
        self.course_name = course_name
        self.star_requirement = star_requirement
        self.rotation_x = 90
        
        # Different colors for different courses
        colors = {
            "bobomb_battlefield": color.orange,
            "whomp_fortress": color.gray,
            "cool_cool_mountain": color.cyan,
            "jolly_roger_bay": color.blue
        }
        self.color = colors.get(course_name, color.white)
        
        # Frame
        self.frame = Entity(
            model='cube',
            color=color.gold,
            scale=(3.2, 2.2, 0.2),
            position=self.position,
            rotation=self.rotation
        )

class Course(Entity):
    """Represents different Mario 64 courses"""
    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.coins = []
        self.stars = []
        self.platforms = []
        self.enemies = []

def create_peach_castle():
    """Build Peach's Castle with interior and exterior"""
    castle_entities = []
    
    # === CASTLE GROUNDS ===
    # Main courtyard
    courtyard = Entity(
        model='plane',
        scale=(80, 1, 80),
        texture='grass',
        collider='box',
        texture_scale=(16, 16),
        color=color.rgb(80, 180, 80),
        position=(0, 0, 0)
    )
    castle_entities.append(courtyard)
    
    # Castle moat
    moat = Entity(
        model='cylinder',
        scale=(45, 1, 45),
        color=color.rgb(0, 100, 200),
        position=(0, -0.5, 0),
        collider='mesh'
    )
    castle_entities.append(moat)
    
    # Drawbridge
    drawbridge = Entity(
        model='cube',
        scale=(8, 0.5, 4),
        color=color.brown,
        position=(0, 0.25, -18),
        collider='box'
    )
    castle_entities.append(drawbridge)
    
    # === MAIN CASTLE STRUCTURE ===
    # Castle foundation
    castle_base = Entity(
        model='cube',
        scale=(25, 10, 25),
        color=color.rgb(200, 200, 200),
        position=(0, 5, -40),
        collider='box',
        texture='brick'
    )
    castle_entities.append(castle_base)
    
    # Main castle tower
    main_tower = Entity(
        model='cylinder',
        scale=(8, 20, 8),
        color=color.rgb(220, 220, 220),
        position=(0, 15, -40),
        collider='mesh'
    )
    castle_entities.append(main_tower)
    
    # Castle roof (cone)
    main_roof = Entity(
        model='cone',
        scale=(10, 8, 10),
        color=color.red,
        position=(0, 25, -40)
    )
    castle_entities.append(main_roof)
    
    # Side towers
    for i, pos in enumerate([(-12, -40), (12, -40), (-8, -25), (8, -25)]):
        side_tower = Entity(
            model='cylinder',
            scale=(3, 12, 3),
            color=color.rgb(200, 200, 200),
            position=(pos[0], 8, pos[1]),
            collider='mesh'
        )
        side_roof = Entity(
            model='cone',
            scale=(4, 4, 4),
            color=color.red,
            position=(pos[0], 14, pos[1])
        )
        castle_entities.extend([side_tower, side_roof])
    
    # === CASTLE INTERIOR ===
    # Main hall floor
    hall_floor = Entity(
        model='plane',
        scale=(15, 1, 15),
        color=color.rgb(150, 120, 80),
        position=(0, 0.1, -40),
        collider='box'
    )
    castle_entities.append(hall_floor)
    
    # Interior walls
    hall_walls = [
        (0, 5, -32, 15, 10, 1),    # Back wall
        (-7.5, 5, -40, 1, 10, 15), # Left wall
        (7.5, 5, -40, 1, 10, 15),  # Right wall
    ]
    
    for x, y, z, sx, sy, sz in hall_walls:
        wall = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=color.rgb(180, 180, 180),
            collider='box'
        )
        castle_entities.append(wall)
    
    # === STAIRCASES ===
    # Main staircase to second floor
    for i in range(10):
        stair = Entity(
            model='cube',
            position=(0, i * 0.6, -32 + i * 1.2),
            scale=(6, 0.3, 1.2),
            color=color.rgb(160, 140, 100),
            collider='box'
        )
        castle_entities.append(stair)
    
    # === BASEMENT ===
    basement_floor = Entity(
        model='plane',
        scale=(12, 1, 12),
        color=color.rgb(80, 80, 80),
        position=(0, -8, -40),
        collider='box'
    )
    castle_entities.append(basement_floor)
    
    basement_walls = [
        (0, -3, -34, 12, 5, 1),    # Back wall
        (-6, -3, -40, 1, 5, 12),   # Left wall
        (6, -3, -40, 1, 5, 12),    # Right wall
    ]
    
    for x, y, z, sx, sy, sz in basement_walls:
        wall = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=color.rgb(100, 100, 100),
            collider='box'
        )
        castle_entities.append(wall)
    
    # Basement entrance (hole in main hall floor)
    basement_entrance = Entity(
        model='plane',
        scale=(2, 1, 2),
        color=color.clear,
        position=(0, 0.2, -35),
        collider='box'
    )
    castle_entities.append(basement_entrance)
    
    return castle_entities

def create_bobomb_battlefield():
    """Create Bob-omb Battlefield course"""
    course_entities = []
    
    # Terrain
    terrain = Entity(
        model='plane',
        scale=(30, 1, 30),
        texture='grass',
        color=color.rgb(60, 160, 60),
        collider='box',
        position=(0, 0, 0)
    )
    course_entities.append(terrain)
    
    # Central mountain
    mountain = Entity(
        model='sphere',
        scale=(8, 4, 8),
        color=color.rgb(120, 80, 60),
        position=(0, 2, 0),
        collider='mesh'
    )
    course_entities.append(mountain)
    
    # Floating platforms
    platforms = [
        (0, 6, 0, 3, 0.5, 3, color.brown),
        (-8, 4, -8, 2, 0.5, 2, color.orange),
        (8, 4, -8, 2, 0.5, 2, color.orange),
        (0, 8, -5, 2, 0.5, 2, color.red),
    ]
    
    for x, y, z, sx, sy, sz, col in platforms:
        platform = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=col,
            collider='box'
        )
        course_entities.append(platform)
    
    # Bridge
    bridge = Entity(
        model='cube',
        scale=(6, 0.3, 1.5),
        color=color.brown,
        position=(0, 1, -12),
        collider='box'
    )
    course_entities.append(bridge)
    
    return course_entities

def create_whomp_fortress():
    """Create Whomp's Fortress course"""
    course_entities = []
    
    # Main fortress platform
    fortress_base = Entity(
        model='cube',
        scale=(15, 1, 15),
        color=color.rgb(150, 150, 150),
        position=(0, 5, 0),
        collider='box'
    )
    course_entities.append(fortress_base)
    
    # Tower
    tower = Entity(
        model='cylinder',
        scale=(3, 8, 3),
        color=color.rgb(120, 120, 120),
        position=(0, 9, 0),
        collider='mesh'
    )
    course_entities.append(tower)
    
    # Floating blocks
    for i in range(5):
        block = Entity(
            model='cube',
            scale=(2, 0.8, 2),
            color=color.rgb(200, 200, 200),
            position=(random.uniform(-10, 10), 3 + i * 2, random.uniform(-10, 10)),
            collider='box'
        )
        course_entities.append(block)
    
    return course_entities

# Create Mario
mario = Mario()

# Build all game areas
castle_entities = create_peach_castle()
bobomb_entities = create_bobomb_battlefield()
whomp_entities = create_whomp_fortress()

# Initially disable course entities
for entity in bobomb_entities + whomp_entities:
    entity.enabled = False

# Create painting portals
paintings = [
    PaintingPortal("bobomb_battlefield", 0, position=(-5, 8, -31.9)),
    PaintingPortal("whomp_fortress", 3, position=(5, 8, -31.9)),
    PaintingPortal("cool_cool_mountain", 1, position=(-3, 4, -31.9)),
    PaintingPortal("jolly_roger_bay", 2, position=(3, 4, -31.9)),
]

# Create MIPS bunnies
bunnies = []
for pos in [(0, -7, -35), (4, -7, -38), (-4, -7, -38)]:
    bunny = MIPSBunny(position=pos)
    bunny.original_y = pos[1]
    bunnies.append(bunny)

# Create coins throughout the castle
coins = []
coin_positions = [
    (0, 2, -20), (5, 2, -25), (-5, 2, -25),  # Courtyard
    (0, 1, -35), (4, 1, -37), (-4, 1, -37),  # Main hall
    (0, -6, -35), (3, -6, -38), (-3, -6, -38),  # Basement
    (0, 9, -32), (4, 9, -32), (-4, 9, -32),  # Second floor
]

for pos in coin_positions:
    coin = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.3,
        position=pos,
        collider='sphere'
    )
    coins.append(coin)

# Create power stars
stars = []
star_positions = [
    (0, 12, -40),  # Top of castle
    (0, -6, -35),  # Basement
    (0, 3, -15),   # Courtyard
]

for i, pos in enumerate(star_positions):
    star = Entity(
        model='sphere',
        color=color.gold,
        scale=0.5,
        position=pos,
        collider='sphere'
    )
    # Create star points
    for j in range(5):
        angle = j * 72
        point = Entity(
            model='cube',
            color=color.gold,
            scale=(0.15, 0.15, 0.6),
            parent=star,
            position=(cos(radians(angle)) * 0.8, 0, sin(radians(angle)) * 0.8),
            rotation=(0, -angle, 0)
        )
    stars.append(star)

# =============== CAMERA ===============
camera.parent = mario
camera.position = (0, 5, -12)
camera.rotation = (15, 0, 0)

# =============== UI ===============
title_text = Text(
    text='Super Mario 64 - Peach\'s Castle',
    position=(-0.8, 0.45),
    color=color.white,
    scale=1.5
)

coin_text = Text(
    text='Coins: 0',
    position=(-0.85, 0.40),
    color=color.yellow,
    scale=1.2
)

star_text = Text(
    text='Stars: 0/8',
    position=(-0.85, 0.35),
    color=color.gold,
    scale=1.2
)

bunny_text = Text(
    text='MIPS Caught: 0/3',
    position=(-0.85, 0.30),
    color=color.yellow,
    scale=1.2
)

location_text = Text(
    text='Location: Castle Grounds',
    position=(-0.85, 0.25),
    color=color.cyan,
    scale=1.1
)

mario.bunnies_caught = 0
mario.current_location = "Castle Grounds"

# Animations
for coin in coins:
    coin.animate('rotation_y', 360, duration=2, loop=True)

for star in stars:
    star.animate('rotation_y', 360, duration=3, loop=True)
    star.animate('y', star.y + 0.5, duration=1.5, loop=True)

for painting in paintings:
    painting.animate('rotation_y', 10, duration=2, loop=True)

# =============== GAME LOGIC ===============
def warp_to_course(course_name):
    """Warp Mario to a different course"""
    mario.current_course = course_name
    mario.position = (0, 5, 0)
    mario.vel = Vec3(0, 0, 0)
    
    # Enable/disable appropriate entities
    if course_name == "castle_grounds":
        for entity in castle_entities:
            entity.enabled = True
        for entity in bobomb_entities + whomp_entities:
            entity.enabled = False
        location_text.text = "Location: Castle Grounds"
        
    elif course_name == "bobomb_battlefield":
        for entity in bobomb_entities:
            entity.enabled = True
        for entity in castle_entities + whomp_entities:
            entity.enabled = False
        location_text.text = "Location: Bob-omb Battlefield"
        
    elif course_name == "whomp_fortress":
        for entity in whomp_entities:
            entity.enabled = True
        for entity in castle_entities + bobomb_entities:
            entity.enabled = False
        location_text.text = "Location: Whomp's Fortress"

def update():
    mario.update()
    
    # Bunny AI
    for bunny in bunnies:
        if bunny.enabled:
            bunny.update()
            
            # Check if Mario is near bunny
            dist = distance(mario.position, bunny.position)
            if dist < 6:
                bunny.scared = True
                # Run away from Mario
                escape_dir = (bunny.position - mario.position).normalized()
                bunny.position += escape_dir * 4 * time.dt
                bunny.rotation_y = atan2(escape_dir.x, escape_dir.z) * 57.3
            else:
                bunny.scared = False
            
            # Catch bunny
            if dist < 1.5:
                bunny.enabled = False
                mario.bunnies_caught += 1
                bunny_text.text = f'MIPS Caught: {mario.bunnies_caught}/3'
                print(f"You caught MIPS! Total: {mario.bunnies_caught}/3")
    
    # Coin collection
    for coin in coins:
        if coin.enabled and distance(mario.position, coin.position) < 1.2:
            coin.enabled = False
            mario.coins += 1
            coin_text.text = f'Coins: {mario.coins}'
    
    # Star collection
    for star in stars:
        if star.enabled and distance(mario.position, star.position) < 1.8:
            star.enabled = False
            mario.stars += 1
            star_text.text = f'Stars: {mario.stars}/8'
            print(f"⭐ STAR GET! Total: {mario.stars}/8")
    
    # Painting portal interaction
    for painting in paintings:
        if distance(mario.position, painting.position) < 2.5:
            if mario.stars >= painting.star_requirement:
                if held_keys['e']:
                    warp_to_course(painting.course_name)
                    print(f"Warping to {painting.course_name}!")
    
    # Basement access
    if mario.position.y < -5 and mario.current_course == "castle_grounds":
        mario.position = (0, -7, -35)  # Teleport to basement
        print("Entered basement!")
    
    # Return from basement
    if mario.position.y < -10:
        mario.position = (0, 1, -35)  # Return to main hall
        print("Returned to main hall!")
    
    # Smooth camera follow
    camera.look_at(mario)
    
    # Win condition
    if mario.stars >= 8 and not hasattr(mario, 'won'):
        mario.won = True
        win_text = Text(
            text='🎉 YOU WIN! PRINCESS PEACH IS SAVED! 🎉',
            position=(-0.5, 0),
            scale=2,
            color=color.gold
        )
        print("CONGRATULATIONS! You saved Princess Peach!")

# =============== CONTROLS HELP ===============
help_text = Text(
    text='Controls: WASD-Move, SHIFT-Run, SPACE-Jump, E-Enter Painting',
    position=(-0.8, -0.45),
    color=color.white,
    scale=1.0
)

# =============== SKY & LIGHTING ===============
Sky(color=color.rgb(135, 206, 235))

# Add directional lighting
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))

print("=" * 60)
print("🎮 SUPER MARIO 64 - PEACH'S CASTLE EDITION 🏰")
print("=" * 60)
print("Controls:")
print("  WASD - Move Mario")
print("  SHIFT - Run")
print("  SPACE - Jump")
print("  E - Enter painting (when close)")
print("\nObjectives:")
print("  • Collect 8 power stars")
print("  • Catch all 3 MIPS bunnies in the basement")
print("  • Explore Peach's Castle and its courses")
print("  • Unlock new areas with more stars")
print("=" * 60)
print("Good luck! Princess Peach is counting on you!")

app.run()# Python 3.13 + Ursina Engine - Super Mario 64: Peach's Castle Edition
from ursina import *
from math import sin, cos, radians, sqrt, atan2
import random

app = Ursina(title='Super Mario 64 - Peach\'s Castle Edition', borderless=False)

# Constants
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_POWER = 12
GRAVITY = 25
STAR_REQUIREMENT = 8  # Stars needed to unlock areas

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgb(255, 0, 0),
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
        # Mario's overalls
        self.overalls = Entity(
            model='cube',
            color=color.blue,
            scale=(1.1, 0.8, 1.1),
            parent=self,
            position=(0, -0.2, 0)
        )
        
        self.vel = Vec3(0, 0, 0)
        self.on_ground = False
        self.jump_chain = 0
        self.coins = 0
        self.stars = 0
        self.current_course = "castle_grounds"
    
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
            
        # Water/lava collision
        if self.y < -5:
            self.position = (0, 10, 0)
            self.vel = Vec3(0, 0, 0)

class MIPSBunny(Entity):
    """The famous yellow rabbit from Super Mario 64!"""
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.yellow,
            scale=(0.8, 1.2, 1.4),
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
        self.original_y = self.y
        
    def update(self):
        if not self.enabled:
            return
            
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
                random.uniform(-15, 15),
                self.original_y,
                random.uniform(-15, 15)
            )
        
        if self.move_target:
            direction = self.move_target - self.position
            if direction.length() > 0.5:
                direction = direction.normalized()
                self.position += direction * 2 * time.dt
                self.rotation_y = atan2(direction.x, direction.z) * 57.3
            else:
                self.move_target = None

class PaintingPortal(Entity):
    """Magic painting that warps Mario to courses"""
    def __init__(self, course_name, star_requirement=0, **kwargs):
        super().__init__(
            model='quad',
            scale=(3, 2),
            collider='box',
            **kwargs
        )
        self.course_name = course_name
        self.star_requirement = star_requirement
        self.rotation_x = 90
        
        # Different colors for different courses
        colors = {
            "bobomb_battlefield": color.orange,
            "whomp_fortress": color.gray,
            "cool_cool_mountain": color.cyan,
            "jolly_roger_bay": color.blue
        }
        self.color = colors.get(course_name, color.white)
        
        # Frame
        self.frame = Entity(
            model='cube',
            color=color.gold,
            scale=(3.2, 2.2, 0.2),
            position=self.position,
            rotation=self.rotation
        )

class Course(Entity):
    """Represents different Mario 64 courses"""
    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.coins = []
        self.stars = []
        self.platforms = []
        self.enemies = []

def create_peach_castle():
    """Build Peach's Castle with interior and exterior"""
    castle_entities = []
    
    # === CASTLE GROUNDS ===
    # Main courtyard
    courtyard = Entity(
        model='plane',
        scale=(80, 1, 80),
        texture='grass',
        collider='box',
        texture_scale=(16, 16),
        color=color.rgb(80, 180, 80),
        position=(0, 0, 0)
    )
    castle_entities.append(courtyard)
    
    # Castle moat
    moat = Entity(
        model='cylinder',
        scale=(45, 1, 45),
        color=color.rgb(0, 100, 200),
        position=(0, -0.5, 0),
        collider='mesh'
    )
    castle_entities.append(moat)
    
    # Drawbridge
    drawbridge = Entity(
        model='cube',
        scale=(8, 0.5, 4),
        color=color.brown,
        position=(0, 0.25, -18),
        collider='box'
    )
    castle_entities.append(drawbridge)
    
    # === MAIN CASTLE STRUCTURE ===
    # Castle foundation
    castle_base = Entity(
        model='cube',
        scale=(25, 10, 25),
        color=color.rgb(200, 200, 200),
        position=(0, 5, -40),
        collider='box',
        texture='brick'
    )
    castle_entities.append(castle_base)
    
    # Main castle tower
    main_tower = Entity(
        model='cylinder',
        scale=(8, 20, 8),
        color=color.rgb(220, 220, 220),
        position=(0, 15, -40),
        collider='mesh'
    )
    castle_entities.append(main_tower)
    
    # Castle roof (cone)
    main_roof = Entity(
        model='cone',
        scale=(10, 8, 10),
        color=color.red,
        position=(0, 25, -40)
    )
    castle_entities.append(main_roof)
    
    # Side towers
    for i, pos in enumerate([(-12, -40), (12, -40), (-8, -25), (8, -25)]):
        side_tower = Entity(
            model='cylinder',
            scale=(3, 12, 3),
            color=color.rgb(200, 200, 200),
            position=(pos[0], 8, pos[1]),
            collider='mesh'
        )
        side_roof = Entity(
            model='cone',
            scale=(4, 4, 4),
            color=color.red,
            position=(pos[0], 14, pos[1])
        )
        castle_entities.extend([side_tower, side_roof])
    
    # === CASTLE INTERIOR ===
    # Main hall floor
    hall_floor = Entity(
        model='plane',
        scale=(15, 1, 15),
        color=color.rgb(150, 120, 80),
        position=(0, 0.1, -40),
        collider='box'
    )
    castle_entities.append(hall_floor)
    
    # Interior walls
    hall_walls = [
        (0, 5, -32, 15, 10, 1),    # Back wall
        (-7.5, 5, -40, 1, 10, 15), # Left wall
        (7.5, 5, -40, 1, 10, 15),  # Right wall
    ]
    
    for x, y, z, sx, sy, sz in hall_walls:
        wall = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=color.rgb(180, 180, 180),
            collider='box'
        )
        castle_entities.append(wall)
    
    # === STAIRCASES ===
    # Main staircase to second floor
    for i in range(10):
        stair = Entity(
            model='cube',
            position=(0, i * 0.6, -32 + i * 1.2),
            scale=(6, 0.3, 1.2),
            color=color.rgb(160, 140, 100),
            collider='box'
        )
        castle_entities.append(stair)
    
    # === BASEMENT ===
    basement_floor = Entity(
        model='plane',
        scale=(12, 1, 12),
        color=color.rgb(80, 80, 80),
        position=(0, -8, -40),
        collider='box'
    )
    castle_entities.append(basement_floor)
    
    basement_walls = [
        (0, -3, -34, 12, 5, 1),    # Back wall
        (-6, -3, -40, 1, 5, 12),   # Left wall
        (6, -3, -40, 1, 5, 12),    # Right wall
    ]
    
    for x, y, z, sx, sy, sz in basement_walls:
        wall = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=color.rgb(100, 100, 100),
            collider='box'
        )
        castle_entities.append(wall)
    
    # Basement entrance (hole in main hall floor)
    basement_entrance = Entity(
        model='plane',
        scale=(2, 1, 2),
        color=color.clear,
        position=(0, 0.2, -35),
        collider='box'
    )
    castle_entities.append(basement_entrance)
    
    return castle_entities

def create_bobomb_battlefield():
    """Create Bob-omb Battlefield course"""
    course_entities = []
    
    # Terrain
    terrain = Entity(
        model='plane',
        scale=(30, 1, 30),
        texture='grass',
        color=color.rgb(60, 160, 60),
        collider='box',
        position=(0, 0, 0)
    )
    course_entities.append(terrain)
    
    # Central mountain
    mountain = Entity(
        model='sphere',
        scale=(8, 4, 8),
        color=color.rgb(120, 80, 60),
        position=(0, 2, 0),
        collider='mesh'
    )
    course_entities.append(mountain)
    
    # Floating platforms
    platforms = [
        (0, 6, 0, 3, 0.5, 3, color.brown),
        (-8, 4, -8, 2, 0.5, 2, color.orange),
        (8, 4, -8, 2, 0.5, 2, color.orange),
        (0, 8, -5, 2, 0.5, 2, color.red),
    ]
    
    for x, y, z, sx, sy, sz, col in platforms:
        platform = Entity(
            model='cube',
            position=(x, y, z),
            scale=(sx, sy, sz),
            color=col,
            collider='box'
        )
        course_entities.append(platform)
    
    # Bridge
    bridge = Entity(
        model='cube',
        scale=(6, 0.3, 1.5),
        color=color.brown,
        position=(0, 1, -12),
        collider='box'
    )
    course_entities.append(bridge)
    
    return course_entities

def create_whomp_fortress():
    """Create Whomp's Fortress course"""
    course_entities = []
    
    # Main fortress platform
    fortress_base = Entity(
        model='cube',
        scale=(15, 1, 15),
        color=color.rgb(150, 150, 150),
        position=(0, 5, 0),
        collider='box'
    )
    course_entities.append(fortress_base)
    
    # Tower
    tower = Entity(
        model='cylinder',
        scale=(3, 8, 3),
        color=color.rgb(120, 120, 120),
        position=(0, 9, 0),
        collider='mesh'
    )
    course_entities.append(tower)
    
    # Floating blocks
    for i in range(5):
        block = Entity(
            model='cube',
            scale=(2, 0.8, 2),
            color=color.rgb(200, 200, 200),
            position=(random.uniform(-10, 10), 3 + i * 2, random.uniform(-10, 10)),
            collider='box'
        )
        course_entities.append(block)
    
    return course_entities

# Create Mario
mario = Mario()

# Build all game areas
castle_entities = create_peach_castle()
bobomb_entities = create_bobomb_battlefield()
whomp_entities = create_whomp_fortress()

# Initially disable course entities
for entity in bobomb_entities + whomp_entities:
    entity.enabled = False

# Create painting portals
paintings = [
    PaintingPortal("bobomb_battlefield", 0, position=(-5, 8, -31.9)),
    PaintingPortal("whomp_fortress", 3, position=(5, 8, -31.9)),
    PaintingPortal("cool_cool_mountain", 1, position=(-3, 4, -31.9)),
    PaintingPortal("jolly_roger_bay", 2, position=(3, 4, -31.9)),
]

# Create MIPS bunnies
bunnies = []
for pos in [(0, -7, -35), (4, -7, -38), (-4, -7, -38)]:
    bunny = MIPSBunny(position=pos)
    bunny.original_y = pos[1]
    bunnies.append(bunny)

# Create coins throughout the castle
coins = []
coin_positions = [
    (0, 2, -20), (5, 2, -25), (-5, 2, -25),  # Courtyard
    (0, 1, -35), (4, 1, -37), (-4, 1, -37),  # Main hall
    (0, -6, -35), (3, -6, -38), (-3, -6, -38),  # Basement
    (0, 9, -32), (4, 9, -32), (-4, 9, -32),  # Second floor
]

for pos in coin_positions:
    coin = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.3,
        position=pos,
        collider='sphere'
    )
    coins.append(coin)

# Create power stars
stars = []
star_positions = [
    (0, 12, -40),  # Top of castle
    (0, -6, -35),  # Basement
    (0, 3, -15),   # Courtyard
]

for i, pos in enumerate(star_positions):
    star = Entity(
        model='sphere',
        color=color.gold,
        scale=0.5,
        position=pos,
        collider='sphere'
    )
    # Create star points
    for j in range(5):
        angle = j * 72
        point = Entity(
            model='cube',
            color=color.gold,
            scale=(0.15, 0.15, 0.6),
            parent=star,
            position=(cos(radians(angle)) * 0.8, 0, sin(radians(angle)) * 0.8),
            rotation=(0, -angle, 0)
        )
    stars.append(star)

# =============== CAMERA ===============
camera.parent = mario
camera.position = (0, 5, -12)
camera.rotation = (15, 0, 0)

# =============== UI ===============
title_text = Text(
    text='Super Mario 64 - Peach\'s Castle',
    position=(-0.8, 0.45),
    color=color.white,
    scale=1.5
)

coin_text = Text(
    text='Coins: 0',
    position=(-0.85, 0.40),
    color=color.yellow,
    scale=1.2
)

star_text = Text(
    text='Stars: 0/8',
    position=(-0.85, 0.35),
    color=color.gold,
    scale=1.2
)

bunny_text = Text(
    text='MIPS Caught: 0/3',
    position=(-0.85, 0.30),
    color=color.yellow,
    scale=1.2
)

location_text = Text(
    text='Location: Castle Grounds',
    position=(-0.85, 0.25),
    color=color.cyan,
    scale=1.1
)

mario.bunnies_caught = 0
mario.current_location = "Castle Grounds"

# Animations
for coin in coins:
    coin.animate('rotation_y', 360, duration=2, loop=True)

for star in stars:
    star.animate('rotation_y', 360, duration=3, loop=True)
    star.animate('y', star.y + 0.5, duration=1.5, loop=True)

for painting in paintings:
    painting.animate('rotation_y', 10, duration=2, loop=True)

# =============== GAME LOGIC ===============
def warp_to_course(course_name):
    """Warp Mario to a different course"""
    mario.current_course = course_name
    mario.position = (0, 5, 0)
    mario.vel = Vec3(0, 0, 0)
    
    # Enable/disable appropriate entities
    if course_name == "castle_grounds":
        for entity in castle_entities:
            entity.enabled = True
        for entity in bobomb_entities + whomp_entities:
            entity.enabled = False
        location_text.text = "Location: Castle Grounds"
        
    elif course_name == "bobomb_battlefield":
        for entity in bobomb_entities:
            entity.enabled = True
        for entity in castle_entities + whomp_entities:
            entity.enabled = False
        location_text.text = "Location: Bob-omb Battlefield"
        
    elif course_name == "whomp_fortress":
        for entity in whomp_entities:
            entity.enabled = True
        for entity in castle_entities + bobomb_entities:
            entity.enabled = False
        location_text.text = "Location: Whomp's Fortress"

def update():
    mario.update()
    
    # Bunny AI
    for bunny in bunnies:
        if bunny.enabled:
            bunny.update()
            
            # Check if Mario is near bunny
            dist = distance(mario.position, bunny.position)
            if dist < 6:
                bunny.scared = True
                # Run away from Mario
                escape_dir = (bunny.position - mario.position).normalized()
                bunny.position += escape_dir * 4 * time.dt
                bunny.rotation_y = atan2(escape_dir.x, escape_dir.z) * 57.3
            else:
                bunny.scared = False
            
            # Catch bunny
            if dist < 1.5:
                bunny.enabled = False
                mario.bunnies_caught += 1
                bunny_text.text = f'MIPS Caught: {mario.bunnies_caught}/3'
                print(f"You caught MIPS! Total: {mario.bunnies_caught}/3")
    
    # Coin collection
    for coin in coins:
        if coin.enabled and distance(mario.position, coin.position) < 1.2:
            coin.enabled = False
            mario.coins += 1
            coin_text.text = f'Coins: {mario.coins}'
    
    # Star collection
    for star in stars:
        if star.enabled and distance(mario.position, star.position) < 1.8:
            star.enabled = False
            mario.stars += 1
            star_text.text = f'Stars: {mario.stars}/8'
            print(f"⭐ STAR GET! Total: {mario.stars}/8")
    
    # Painting portal interaction
    for painting in paintings:
        if distance(mario.position, painting.position) < 2.5:
            if mario.stars >= painting.star_requirement:
                if held_keys['e']:
                    warp_to_course(painting.course_name)
                    print(f"Warping to {painting.course_name}!")
    
    # Basement access
    if mario.position.y < -5 and mario.current_course == "castle_grounds":
        mario.position = (0, -7, -35)  # Teleport to basement
        print("Entered basement!")
    
    # Return from basement
    if mario.position.y < -10:
        mario.position = (0, 1, -35)  # Return to main hall
        print("Returned to main hall!")
    
    # Smooth camera follow
    camera.look_at(mario)
    
    # Win condition
    if mario.stars >= 8 and not hasattr(mario, 'won'):
        mario.won = True
        win_text = Text(
            text='🎉 YOU WIN! PRINCESS PEACH IS SAVED! 🎉',
            position=(-0.5, 0),
            scale=2,
            color=color.gold
        )
        print("CONGRATULATIONS! You saved Princess Peach!")

# =============== CONTROLS HELP ===============
help_text = Text(
    text='Controls: WASD-Move, SHIFT-Run, SPACE-Jump, E-Enter Painting',
    position=(-0.8, -0.45),
    color=color.white,
    scale=1.0
)

# =============== SKY & LIGHTING ===============
Sky(color=color.rgb(135, 206, 235))

# Add directional lighting
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))

print("=" * 60)
print("🎮 SUPER MARIO 64 - PEACH'S CASTLE EDITION 🏰")
print("=" * 60)
print("Controls:")
print("  WASD - Move Mario")
print("  SHIFT - Run")
print("  SPACE - Jump")
print("  E - Enter painting (when close)")
print("\nObjectives:")
print("  • Collect 8 power stars")
print("  • Catch all 3 MIPS bunnies in the basement")
print("  • Explore Peach's Castle and its courses")
print("  • Unlock new areas with more stars")
print("=" * 60)
print("Good luck! Princess Peach is counting on you!")

app.run()
