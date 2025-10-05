# Python 3.13 + Ursina Engine - Super Mario 64: Enhanced 3D Edition
from ursina import *
from ursina.shaders import lit_with_shadows_shader
from math import sin, cos, radians, sqrt, atan2
import random

app = Ursina(title='Super Mario 64 - Enhanced 3D Castle Edition', borderless=False)

# Enable antialiasing and better rendering
window.fps_counter.enabled = True
window.fullscreen = False
window.vsync = True  # Added for smoother rendering

# Constants
WALK_SPEED = 5
RUN_SPEED = 10
JUMP_POWER = 12
GRAVITY = 25
STAR_REQUIREMENT = 8
CAMERA_SMOOTHNESS = 0.1  # Added for smoother camera

class Mario(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.rgb(255, 0, 0),
            scale=(1, 1.8, 1),
            collider='box',
            position=(0, 2, 0),
            shader=lit_with_shadows_shader,
            **kwargs
        )
        
        # Mario's components (optimized by reducing redundant shaders)
        self.hat = Entity(model='cube', color=color.rgb(200, 0, 0), scale=(1.2, 0.3, 1.2), 
                         parent=self, position=(0, 1, 0), shader=lit_with_shadows_shader)
        self.hat_brim = Entity(model='cube', color=color.rgb(180, 0, 0), scale=(1.4, 0.1, 1.4), 
                              parent=self.hat, position=(0, -0.1, 0), shader=lit_with_shadows_shader)
        self.face = Entity(model='cube', color=color.rgb(255, 220, 180), scale=(1, 0.8, 1), 
                         parent=self, position=(0, 0.5, 0), shader=lit_with_shadows_shader)
        self.mustache = Entity(model='cube', color=color.rgb(80, 40, 20), scale=(0.8, 0.2, 0.2), 
                              parent=self.face, position=(0, -0.1, 0.5), shader=lit_with_shadows_shader)
        self.nose = Entity(model='sphere', color=color.rgb(255, 180, 150), scale=(0.3, 0.25, 0.3), 
                          parent=self.face, position=(0, 0.1, 0.5), shader=lit_with_shadows_shader)
        
        # Eyes (optimized loop)
        for x_pos in [-0.25, 0.25]:
            eye_white = Entity(model='sphere', color=color.white, scale=0.2, 
                             parent=self.face, position=(x_pos, 0.2, 0.45), shader=lit_with_shadows_shader)
            Entity(model='sphere', color=color.rgb(0, 100, 200), scale=0.12, 
                   parent=eye_white, position=(0, 0, 0.5), shader=lit_with_shadows_shader)
        
        # Overalls and buttons
        self.overalls = Entity(model='cube', color=color.rgb(0, 50, 200), scale=(1.1, 0.8, 1.1), 
                             parent=self, position=(0, -0.2, 0), shader=lit_with_shadows_shader)
        for x_pos in [-0.3, 0.3]:
            Entity(model='sphere', color=color.yellow, scale=0.15, 
                   parent=self.overalls, position=(x_pos, 0.3, 0.55), shader=lit_with_shadows_shader)
        
        # Gloves and shoes
        for x_pos in [-0.7, 0.7]:
            Entity(model='cube', color=color.white, scale=(0.3, 0.3, 0.3), 
                   parent=self, position=(x_pos, -0.5, 0), shader=lit_with_shadows_shader)
        for x_pos in [-0.35, 0.35]:
            Entity(model='cube', color=color.rgb(139, 69, 19), scale=(0.4, 0.3, 0.6), 
                   parent=self, position=(x_pos, -0.95, 0.1), shader=lit_with_shadows_shader)
        
        self.vel = Vec3(0, 0, 0)
        self.on_ground = False
        self.jump_chain = 0
        self.coins = 0
        self.stars = 0
        self.current_course = "castle_grounds"
        self.bunnies_caught = 0
    
    def update(self):
        dt = time.dt
        keys = held_keys
        
        # Horizontal movement with smoother rotation
        move = Vec3(keys['d'] - keys['a'], 0, keys['w'] - keys['s'])
        if move.length() > 0:
            move = move.normalized()
            target_rotation = atan2(move.x, move.z) * 57.3
            self.rotation_y = lerp(self.rotation_y, target_rotation, CAMERA_SMOOTHNESS)
            speed = RUN_SPEED if keys['shift'] else WALK_SPEED
            self.position += move * speed * dt
            
            # Walking animation
            bob = sin(time.time() * 10) * 0.1
            self.y += bob * dt
        
        # Apply gravity
        self.vel.y -= GRAVITY * dt
        self.position += self.vel * dt
        
        # Ground collision with better detection
        hit_info = raycast(self.world_position + Vec3(0, 0.5, 0), Vec3(0, -1, 0), 
                          distance=1.5, ignore=(self,), traverse_target=scene)
        if hit_info.hit and hit_info.entity.collider:
            if self.vel.y <= 0:
                self.y = hit_info.world_point.y + 0.9
                self.vel.y = 0
                self.on_ground = True
                self.jump_chain = 0
        else:
            self.on_ground = False
        
        # Jump with double jump support
        if keys['space'] and self.on_ground and self.jump_chain < 2:
            self.vel.y = JUMP_POWER * (1.2 if self.jump_chain == 1 else 1.0)
            self.jump_chain += 1
            self.on_ground = False
            
        # Water/lava collision
        if self.y < -5 and self.current_course != "basement":
            self.position = (0, 10, 0)
            self.vel = Vec3(0, 0, 0)

class MIPSBunny(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            model='cube',
            color=color.yellow,
            scale=(0.8, 1.2, 1.4),
            collider='box',
            shader=lit_with_shadows_shader,
            **kwargs
        )
        
        # Bunny components (optimized)
        self.head = Entity(model='sphere', color=color.rgb(255, 230, 100), scale=(0.7, 0.7, 0.7), 
                         parent=self, position=(0, 0.8, 0.2), shader=lit_with_shadows_shader)
        
        # Ears
        for side, angle in [(-0.3, -15), (0.3, 15)]:
            ear = Entity(model='cube', color=color.rgb(255, 230, 100), scale=(0.15, 0.8, 0.1), 
                        parent=self.head, position=(side, 0.6, 0), rotation=(0, 0, angle), 
                        shader=lit_with_shadows_shader)
            Entity(model='cube', color=color.rgb(255, 192, 203), scale=(0.08, 0.5, 0.05), 
                   parent=ear, position=(0, 0.1, 0.05), shader=lit_with_shadows_shader)
        
        # Eyes
        for x_pos in [-0.2, 0.2]:
            eye_white = Entity(model='sphere', color=color.white, scale=0.15, 
                             parent=self.head, position=(x_pos, 0.1, 0.3), shader=lit_with_shadows_shader)
            Entity(model='sphere', color=color.black, scale=0.08, 
                   parent=eye_white, position=(0, 0, 0.08), shader=lit_with_shadows_shader)
        
        # Nose and tail
        self.nose = Entity(model='sphere', color=color.rgb(255, 182, 193), scale=(0.1, 0.08, 0.1), 
                          parent=self.head, position=(0, 0, 0.35), shader=lit_with_shadows_shader)
        self.tail = Entity(model='sphere', color=color.white, scale=0.4, 
                         parent=self, position=(0, 0, -0.8), shader=lit_with_shadows_shader)
        
        # Whiskers and paws
        for side in [-1, 1]:
            for y_offset in [-0.02, 0, 0.02]:
                Entity(model='cube', color=color.rgb(150, 150, 150), scale=(0.3, 0.01, 0.01), 
                       parent=self.head, position=(side * 0.35, y_offset, 0.3), shader=lit_with_shadows_shader)
        for x_pos, z_pos in [(-0.3, 0.5), (0.3, 0.5), (-0.3, -0.5), (0.3, -0.5)]:
            Entity(model='sphere', color=color.rgb(255, 220, 100), scale=(0.2, 0.15, 0.25), 
                   parent=self, position=(x_pos, -0.6, z_pos), shader=lit_with_shadows_shader)
        
        self.hop_time = 0
        self.hop_speed = random.uniform(2, 4)
        self.move_target = None
        self.scared = False
        self.original_y = self.y
        
    def update(self):
        if not self.enabled:
            return
            
        # Optimized bunny animation
        self.hop_time += time.dt * self.hop_speed
        self.y = self.original_y + abs(sin(self.hop_time)) * 0.3
        
        # Ear and tail animations
        ear_wiggle = sin(self.hop_time * 2) * 5
        self.head.children[0].rotation_z = -15 + ear_wiggle  # Left ear
        self.head.children[1].rotation_z = 15 - ear_wiggle   # Right ear
        self.tail.rotation_y = sin(self.hop_time * 3) * 10
        
        # Improved bunny AI
        if not self.scared and random.random() < 0.01:
            self.move_target = Vec3(
                random.uniform(-15, 15),
                self.original_y,
                random.uniform(-15, 15)
            )
            # Ensure target is within bounds
            self.move_target.x = clamp(self.move_target.x, -30, 30)
            self.move_target.z = clamp(self.move_target.z, -30, 30)
        
        if self.move_target:
            direction = self.move_target - self.position
            if direction.length() > 0.5:
                direction = direction.normalized()
                self.position += direction * 2 * time.dt
                self.rotation_y = lerp(self.rotation_y, atan2(direction.x, direction.z) * 57.3, 0.1)
            else:
                self.move_target = None

class PaintingPortal(Entity):
    def __init__(self, course_name, star_requirement=0, **kwargs):
        super().__init__(
            model='quad',
            scale=(3, 2),
            collider='box',
            shader=lit_with_shadows_shader,
            **kwargs
        )
        self.course_name = course_name
        self.star_requirement = star_requirement
        self.colors_dict = {
            "bobomb_battlefield": color.rgb(255, 140, 0),
            "whomp_fortress": color.rgb(140, 140, 140),
            "cool_cool_mountain": color.rgb(150, 220, 255),
            "jolly_roger_bay": color.rgb(0, 120, 200)
        }
        self.color = self.colors_dict.get(course_name, color.white)
        
        # Optimized frame creation
        frame_thickness = 0.15
        frame_depth = 0.3
        frame_positions = [
            (0, 1.1, 0, 3.4, frame_thickness, frame_depth),  # Top
            (0, -1.1, 0, 3.4, frame_thickness, frame_depth), # Bottom
            (-1.65, 0, 0, frame_thickness, 2.3, frame_depth), # Left
            (1.65, 0, 0, frame_thickness, 2.3, frame_depth)   # Right
        ]
        
        for x, y, z, sx, sy, sz in frame_positions:
            Entity(
                model='cube',
                color=color.rgb(218, 165, 32),
                scale=(sx, sy, sz),
                position=self.position + Vec3(x, y, z),
                rotation=self.rotation,
                shader=lit_with_shadows_shader
            )
        
        # Corner ornaments
        for x, y in [(-1.5, 0.9), (1.5, 0.9), (-1.5, -0.9), (1.5, -0.9)]:
            Entity(
                model='sphere',
                color=color.rgb(255, 215, 0),
                scale=0.2,
                position=self.position + Vec3(x, y, 0.15),
                shader=lit_with_shadows_shader
            )

def create_detailed_castle_brick(x, y, z, scale_x, scale_y, scale_z):
    brick = Entity(
        model='cube',
        position=(x, y, z),
        scale=(scale_x, scale_y, scale_z),
        color=color.rgb(200, 200, 200),
        collider='box',
        shader=lit_with_shadows_shader
    )
    
    # Optimized mortar lines
    if scale_x > 2:
        for i in range(int(scale_x/2)):
            Entity(
                model='cube',
                color=color.rgb(180, 180, 180),
                scale=(0.1, scale_y * 1.01, scale_z * 1.01),
                position=(x - scale_x/4 + i, y, z),
                shader=lit_with_shadows_shader
            )
    
    return brick

def create_peach_castle():
    castle_entities = []
    
    # Optimized castle creation
    courtyard = Entity(model='plane', scale=(80, 1, 80), color=color.rgb(80, 180, 80), 
                     collider='box', position=(0, 0, 0), shader=lit_with_shadows_shader)
    castle_entities.append(courtyard)
    
    # Reduced grass patches for performance
    for _ in range(15):
        grass_patch = Entity(
            model='cube',
            scale=(random.uniform(0.5, 1.5), 0.05, random.uniform(0.5, 1.5)),
            color=color.rgb(random.randint(60, 100), random.randint(150, 190), random.randint(60, 100)),
            position=(random.uniform(-35, 35), 0.05, random.uniform(-35, 35)),
            shader=lit_with_shadows_shader
        )
        castle_entities.append(grass_patch)
    
    moat = Entity(model='cylinder', scale=(45, 1.5, 45), color=color.rgb(30, 100, 180), 
                 position=(0, -0.75, 0), collider='mesh', shader=lit_with_shadows_shader)
    castle_entities.append(moat)
    
    drawbridge = Entity(model='cube', scale=(8, 0.5, 4), color=color.rgb(139, 90, 43), 
                       position=(0, 0.25, -18), collider='box', shader=lit_with_shadows_shader)
    castle_entities.append(drawbridge)
    
    # Simplified drawbridge planks
    for i in range(4):
        Entity(model='cube', scale=(1.8, 0.51, 4), color=color.rgb(120, 80, 40), 
               position=(-3.5 + i*2, 0.25, -18), shader=lit_with_shadows_shader)
    
    castle_base = create_detailed_castle_brick(0, 5, -40, 25, 10, 25)
    castle_entities.append(castle_base)
    
    # Optimized windows
    for x in [-8, 0, 8]:
        for y in [3, 7]:
            window = Entity(model='cube', scale=(1.5, 2, 0.2), color=color.rgb(50, 50, 80), 
                           position=(x, y, -27.4), shader=lit_with_shadows_shader)
            Entity(model='cube', scale=(1.3, 1.8, 0.1), color=color.rgb(255, 240, 150), 
                   position=(x, y, -27.3), shader=lit_with_shadows_shader)
            castle_entities.append(window)
    
    # Main tower and roof
    main_tower = Entity(model='cylinder', scale=(8, 20, 8), color=color.rgb(220, 220, 220), 
                       position=(0, 15, -40), collider='mesh', shader=lit_with_shadows_shader)
    main_roof = Entity(model='cone', scale=(10, 8, 10), color=color.rgb(180, 0, 0), 
                      position=(0, 25, -40), shader=lit_with_shadows_shader)
    castle_entities.extend([main_tower, main_roof])
    
    # Simplified tower details
    for i in range(5):
        Entity(model='cylinder', scale=(8.1, 1, 8.1), color=color.rgb(200, 200, 200), 
               position=(0, 5 + i*4, -40), shader=lit_with_shadows_shader)
    
    flag_pole = Entity(model='cylinder', scale=(0.1, 5, 0.1), color=color.rgb(139, 69, 19), 
                      position=(0, 31, -40), shader=lit_with_shadows_shader)
    flag = Entity(model='cube', scale=(2, 1.5, 0.1), color=color.rgb(255, 0, 0), 
                 position=(1, 32, -40), shader=lit_with_shadows_shader)
    Entity(model='sphere', scale=0.5, color=color.rgb(255, 192, 203), 
           position=(1, 32, -39.9), shader=lit_with_shadows_shader)
    castle_entities.extend([flag_pole, flag])
    
    # Simplified side towers
    for pos in [(-12, -40), (12, -40)]:
        side_tower = Entity(model='cylinder', scale=(3, 12, 3), color=color.rgb(200, 200, 200), 
                           position=(pos[0], 8, pos[1]), collider='mesh', shader=lit_with_shadows_shader)
        side_roof = Entity(model='cone', scale=(4, 4, 4), color=color.rgb(180, 0, 0), 
                          position=(pos[0], 14, pos[1]), shader=lit_with_shadows_shader)
        castle_entities.extend([side_tower, side_roof])
    
    # Interior
    hall_floor = Entity(model='plane', scale=(15, 1, 15), color=color.rgb(180, 150, 120), 
                      position=(0, 0.1, -40), collider='box', shader=lit_with_shadows_shader)
    castle_entities.append(hall_floor)
    
    hall_walls = [
        (0, 5, -32, 15, 10, 1),
        (-7.5, 5, -40, 1, 10, 15),
        (7.5, 5, -40, 1, 10, 15),
    ]
    
    for x, y, z, sx, sy, sz in hall_walls:
        wall = Entity(model='cube', position=(x, y, z), scale=(sx, sy, sz), 
                     color=color.rgb(180, 180, 180), collider='box', shader=lit_with_shadows_shader)
        castle_entities.append(wall)
    
    # Simplified staircase
    for i in range(5):
        stair = Entity(model='cube', position=(0, i * 0.6, -32 + i * 1.2), 
                      scale=(6, 0.3, 1.2), color=color.rgb(160, 140, 100), 
                      collider='box', shader=lit_with_shadows_shader)
        Entity(model='cube', position=(0, i * 0.6 + 0.16, -32 + i * 1.2), 
               scale=(3, 0.01, 1.2), color=color.rgb(180, 0, 0), shader=lit_with_shadows_shader)
        castle_entities.append(stair)
    
    # Basement
    basement_floor = Entity(model='plane', scale=(12, 1, 12), color=color.rgb(60, 60, 60), 
                          position=(0, -8, -40), collider='box', shader=lit_with_shadows_shader)
    castle_entities.append(basement_floor)
    
    basement_walls = [
        (0, -3, -34, 12, 5, 1),
        (-6, -3, -40, 1, 5, 12),
        (6, -3, -40, 1, 5, 12),
    ]
    
    for x, y, z, sx, sy, sz in basement_walls:
        wall = Entity(model='cube', position=(x, y, z), scale=(sx, sy, sz), 
                     color=color.rgb(80, 80, 80), collider='box', shader=lit_with_shadows_shader)
        castle_entities.append(wall)
    
    return castle_entities

def create_bobomb_battlefield():
    course_entities = []
    
    terrain = Entity(model='plane', scale=(30, 1, 30), color=color.rgb(60, 160, 60), 
                    collider='box', position=(0, 0, 0), shader=lit_with_shadows_shader)
    course_entities.append(terrain)
    
    # Reduced grass patches
    for _ in range(20):
        Entity(model='cube', scale=(random.uniform(0.3, 0.8), 0.3, random.uniform(0.3, 0.8)), 
               color=color.rgb(random.randint(40, 80), random.randint(140, 180), random.randint(40, 80)), 
               position=(random.uniform(-14, 14), 0.15, random.uniform(-14, 14)), 
               shader=lit_with_shadows_shader)
    
    mountain = Entity(model='sphere', scale=(8, 4, 8), color=color.rgb(120, 80, 60), 
                     position=(0, 2, 0), collider='mesh', shader=lit_with_shadows_shader)
    course_entities.append(mountain)
    
    platforms = [
        (0, 6, 0, 3, 0.5, 3, color.rgb(139, 90, 43)),
        (-8, 4, -8, 2, 0.5, 2, color.rgb(255, 140, 0)),
        (8, 4, -8, 2, 0.5, 2, color.rgb(255, 140, 0)),
    ]
    
    for x, y, z, sx, sy, sz, col in platforms:
        platform = Entity(model='cube', position=(x, y, z), scale=(sx, sy, sz), 
                        color=col, collider='box', shader=lit_with_shadows_shader)
        course_entities.append(platform)
    
    bridge = Entity(model='cube', scale=(6, 0.3, 1.5), color=color.rgb(139, 90, 43), 
                   position=(0, 1, -12), collider='box', shader=lit_with_shadows_shader)
    course_entities.append(bridge)
    
    return course_entities

def create_whomp_fortress():
    course_entities = []
    
    fortress_base = Entity(model='cube', scale=(15, 1, 15), color=color.rgb(150, 150, 150), 
                         position=(0, 5, 0), collider='box', shader=lit_with_shadows_shader)
    course_entities.append(fortress_base)
    
    tower = Entity(model='cylinder', scale=(3, 8, 3), color=color.rgb(120, 120, 120), 
                  position=(0, 9, 0), collider='mesh', shader=lit_with_shadows_shader)
    course_entities.append(tower)
    
    for i in range(3):
        block = Entity(model='cube', scale=(2, 0.8, 2), color=color.rgb(200, 200, 200), 
                      position=(random.uniform(-10, 10), 3 + i * 2, random.uniform(-10, 10)), 
                      collider='box', shader=lit_with_shadows_shader)
        course_entities.append(block)
    
    return course_entities

# Create game objects
mario = Mario()
castle_entities = create_peach_castle()
bobomb_entities = create_bobomb_battlefield()
whomp_entities = create_whomp_fortress()

for entity in bobomb_entities + whomp_entities:
    entity.enabled = False

paintings = [
    PaintingPortal("bobomb_battlefield", 0, position=(-5, 8, -31.9), rotation_x=90),
    PaintingPortal("whomp_fortress", 3, position=(5, 8, -31.9), rotation_x=90),
]

bunnies = [MIPSBunny(position=pos, original_y=pos[1]) for pos in [(0, -7, -35), (4, -7, -38)]]
coins = [Entity(model='cylinder', color=color.rgb(255, 215, 0), scale=(0.4, 0.1, 0.4), 
               position=pos, collider='sphere', shader=lit_with_shadows_shader) 
         for pos in [(0, 2, -20), (5, 2, -25), (-5, 2, -25)]]
stars = [Entity(model='sphere', color=color.rgb(255, 215, 0), scale=0.5, 
               position=pos, collider='sphere', shader=lit_with_shadows_shader) 
         for pos in [(0, 12, -40), (0, -6, -35)]]

# Camera setup
camera.parent = None  # Independent camera for better control
camera.position = mario.position + Vec3(0, 6, -15)
camera.rotation = (20, 0, 0)

# UI
title_text = Text(text='Super Mario 64 - Enhanced', position=(-0.85, 0.47), 
                 color=color.white, scale=1.8)
coin_text = Text(text='Coins: 0', position=(-0.85, 0.40), 
                color=color.rgb(255, 215, 0), scale=1.3)
star_text = Text(text='⭐ Stars: 0/8', position=(-0.85, 0.35), 
                color=color.rgb(255, 215, 0), scale=1.3)
bunny_text = Text(text='🐰 MIPS: 0/2', position=(-0.85, 0.30), 
                 color=color.rgb(255, 230, 100), scale=1.3)
location_text = Text(text='📍 Castle Grounds', position=(-0.85, 0.25), 
                   color=color.rgb(150, 220, 255), scale=1.2)

# Animations
for coin in coins:
    coin.animate('rotation_y', 360, duration=2, loop=True)
for star in stars:
    star.animate('rotation_y', 360, duration=3, loop=True)

def warp_to_course(course_name):
    mario.current_course = course_name
    mario.position = (0, 5, 0)
    mario.vel = Vec3(0, 0, 0)
    
    # Enable/disable entities based on course
    entity_groups = {
        "castle_grounds": castle_entities,
        "bobomb_battlefield": bobomb_entities,
        "whomp_fortress": whomp_entities
    }
    
    for name, entities in entity_groups.items():
        for entity in entities:
            entity.enabled = (name == course_name)
    
    location_text.text = f"📍 {course_name.replace('_', ' ').title()}"

def update():
    mario.update()
    
    # Smooth camera following
    target_pos = mario.position + Vec3(0, 6, -15)
    camera.position = lerp(camera.position, target_pos, CAMERA_SMOOTHNESS)
    camera.look_at(mario.position + Vec3(0, 1, 0))
    
    # Bunny AI
    for bunny in bunnies:
        if bunny.enabled:
            bunny.update()
            dist = distance(mario.position, bunny.position)
            if dist < 6:
                bunny.scared = True
                escape_dir = (bunny.position - mario.position).normalized()
                bunny.position += escape_dir * 4 * time.dt
                bunny.rotation_y = lerp(bunny.rotation_y, 
                                      atan2(escape_dir.x, escape_dir.z) * 57.3, 
                                      0.1)
            else:
                bunny.scared = False
            
            if dist < 1.5 and bunny.enabled:
                bunny.enabled = False
                mario.bunnies_caught += 1
                bunny_text.text = f'🐰 MIPS: {mario.bunnies_caught}/2'
    
    # Coin and star collection
    for coin in coins:
        if coin.enabled and distance(mario.position, coin.position) < 1.2:
            coin.enabled = False
            mario.coins += 1
            coin_text.text = f'Coins: {mario.coins}'
    
    for star in stars:
        if star.enabled and distance(mario.position, star.position) < 1.8:
            star.enabled = False
            mario.stars += 1
            star_text.text = f'⭐ Stars: {mario.stars}/8'
    
    # Painting portal interaction with better collision
    for painting in paintings:
        if painting.enabled and distance(mario.position, painting.position) < 2.5:
            if mario.stars >= painting.star_requirement and held_keys['e']:
                warp_to_course(painting.course_name)
    
    # Win condition
    if mario.stars >= STAR_REQUIREMENT and not hasattr(mario, 'won'):
        mario.won = True
        Text(text='🎉 YOU WIN! PRINCESS PEACH IS SAVED! 🎉', 
            position=(-0.5, 0), scale=2.5, color=color.rgb(255, 215, 0))

# Sky and lighting
sky = Sky(color=color.rgb(120, 180, 255))
scene.fog_density = (0, 80)
sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
AmbientLight(color=color.rgb(0.5, 0.5, 0.6), parent=scene)

print("🎮 SUPER MARIO 64 - ENHANCED 3D CASTLE EDITION 🏰")
print("Controls: WASD - Move | SHIFT - Run | SPACE - Jump | E - Enter Painting")
print("Objectives: Collect 8 stars ⭐ and catch 2 MIPS bunnies 🐰")
app.run()
