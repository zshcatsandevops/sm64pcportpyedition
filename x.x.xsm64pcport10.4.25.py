"""
Super Mario 64 Python Recreation
Based on HackerSM64 PC Port architecture
Python 3.13 + Pygame + PyOpenGL
"""

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

# ==================== CONSTANTS ====================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FOV = 60
NEAR_CLIP = 0.1
FAR_CLIP = 1000.0

# Mario Physics Constants (from SM64 decomp)
GRAVITY = -4.0
TERMINAL_VELOCITY = -75.0
WALK_SPEED = 4.0
RUN_SPEED = 8.0
SWIM_SPEED = 3.0
JUMP_VELOCITY = 18.0
DOUBLE_JUMP_VELOCITY = 20.0
TRIPLE_JUMP_VELOCITY = 25.0
LONG_JUMP_VELOCITY = 15.0
WALL_KICK_VELOCITY = 22.0
GROUND_FRICTION = 0.92
AIR_FRICTION = 0.98
WALL_SLIDE_FRICTION = 0.7

# ==================== ENUMS ====================
class MarioAction(Enum):
    IDLE = 0
    WALKING = 1
    RUNNING = 2
    JUMPING = 3
    DOUBLE_JUMPING = 4
    TRIPLE_JUMPING = 5
    LONG_JUMPING = 6
    WALL_KICKING = 7
    GROUND_POUNDING = 8
    SWIMMING = 9
    DIVING = 10
    SLIDING = 11
    CROUCHING = 12

class TerrainType(Enum):
    NORMAL = 0
    SLIPPERY = 1
    WATER = 2
    LAVA = 3
    QUICKSAND = 4

# ==================== DATA STRUCTURES ====================
@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self):
        l = self.length()
        if l > 0:
            return Vector3(self.x/l, self.y/l, self.z/l)
        return Vector3(0, 0, 0)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def to_tuple(self):
        return (self.x, self.y, self.z)

@dataclass
class CollisionBox:
    min_pos: Vector3
    max_pos: Vector3

# ==================== CAMERA SYSTEM ====================
class LakituCamera:
    """SM64's camera system (Lakitu following Mario)"""
    def __init__(self):
        self.position = Vector3(0, 10, 20)
        self.target = Vector3(0, 0, 0)
        self.yaw = 0.0
        self.pitch = 20.0
        self.distance = 20.0
        self.height_offset = 5.0
        
    def update(self, mario_pos, mario_facing, mouse_rel):
        # Camera rotation from mouse
        self.yaw -= mouse_rel[0] * 0.1
        self.pitch = max(-80, min(80, self.pitch - mouse_rel[1] * 0.1))
        
        # Calculate camera position
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        
        offset_x = self.distance * math.cos(pitch_rad) * math.sin(yaw_rad)
        offset_y = self.distance * math.sin(pitch_rad) + self.height_offset
        offset_z = self.distance * math.cos(pitch_rad) * math.cos(yaw_rad)
        
        # Smooth camera movement
        target_pos = mario_pos + Vector3(offset_x, offset_y, offset_z)
        self.position.x += (target_pos.x - self.position.x) * 0.1
        self.position.y += (target_pos.y - self.position.y) * 0.1
        self.position.z += (target_pos.z - self.position.z) * 0.1
        
        self.target = mario_pos + Vector3(0, 3, 0)
    
    def apply(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, SCREEN_WIDTH/SCREEN_HEIGHT, NEAR_CLIP, FAR_CLIP)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.position.x, self.position.y, self.position.z,
            self.target.x, self.target.y, self.target.z,
            0, 1, 0
        )

# ==================== MARIO CHARACTER ====================
class Mario:
    """Mario with SM64 physics and movement"""
    def __init__(self, game):
        # Position and movement
        self.pos = Vector3(0, 10, 0)
        self.velocity = Vector3(0, 0, 0)
        self.facing_angle = 0.0
        self.forward_vel = 0.0
        
        # State
        self.action = MarioAction.IDLE
        self.health = 8
        self.air_timer = 0
        self.jump_counter = 0
        self.on_ground = False
        self.in_water = False
        
        # Collectibles
        self.coins = 0
        self.stars = 0
        self.lives = 4
        
        # Physics
        self.collision_box = CollisionBox(
            Vector3(-0.5, 0, -0.5),
            Vector3(0.5, 1.8, 0.5)
        )
        
        # Reference to game for camera access
        self.game = game
    
    def update(self, keys, dt, level):
        # Store previous action for animation
        prev_action = self.action
        
        # Input handling
        forward = keys[K_w] - keys[K_s]
        strafe = keys[K_d] - keys[K_a]
        
        # Calculate movement direction relative to camera
        camera_yaw = math.radians(self.game.camera.yaw)
        move_x = strafe * math.cos(camera_yaw) + forward * math.sin(camera_yaw)
        move_z = strafe * math.sin(camera_yaw) - forward * math.cos(camera_yaw)
        
        # Apply movement
        if self.on_ground:
            self.ground_movement(move_x, move_z, keys, dt)
        else:
            self.air_movement(move_x, move_z, keys, dt)
        
        # Apply gravity
        if not self.on_ground:
            self.velocity.y += GRAVITY * dt
            self.velocity.y = max(TERMINAL_VELOCITY, self.velocity.y)
        
        # Update position
        self.pos = self.pos + self.velocity * dt
        
        # Collision detection
        self.handle_collision(level)
        
        # Water check
        self.check_water_level(level)
        
        # Update timers
        if not self.on_ground:
            self.air_timer += dt
        else:
            self.air_timer = 0
            if self.velocity.y <= 0:
                if prev_action in [MarioAction.JUMPING, MarioAction.DOUBLE_JUMPING, 
                                   MarioAction.TRIPLE_JUMPING]:
                    self.jump_counter = min(2, self.jump_counter + 1)
    
    def ground_movement(self, move_x, move_z, keys, dt):
        # Crouching
        if keys[K_LSHIFT]:
            self.action = MarioAction.CROUCHING
            return
        
        # Calculate target velocity
        speed = RUN_SPEED if keys[K_LCTRL] else WALK_SPEED
        target_vel_x = move_x * speed
        target_vel_z = move_z * speed
        
        # Accelerate towards target velocity
        self.velocity.x += (target_vel_x - self.velocity.x) * 0.3
        self.velocity.z += (target_vel_z - self.velocity.z) * 0.3
        
        # Apply friction
        self.velocity.x *= GROUND_FRICTION
        self.velocity.z *= GROUND_FRICTION
        
        # Update facing angle
        if abs(move_x) > 0.1 or abs(move_z) > 0.1:
            self.facing_angle = math.degrees(math.atan2(move_x, -move_z))
            vel_2d = math.sqrt(self.velocity.x**2 + self.velocity.z**2)
            self.action = MarioAction.RUNNING if vel_2d > 6 else MarioAction.WALKING
        else:
            self.action = MarioAction.IDLE
        
        # Jumping
        if keys[K_SPACE]:
            self.jump()
        
        # Long jump (run + crouch + jump)
        if keys[K_SPACE] and keys[K_LSHIFT] and self.action == MarioAction.RUNNING:
            self.long_jump()
    
    def air_movement(self, move_x, move_z, keys, dt):
        # Air control
        self.velocity.x += move_x * 0.5 * dt
        self.velocity.z += move_z * 0.5 * dt
        
        # Air friction
        self.velocity.x *= AIR_FRICTION
        self.velocity.z *= AIR_FRICTION
        
        # Ground pound
        if keys[K_LSHIFT] and self.action not in [MarioAction.GROUND_POUNDING]:
            self.ground_pound()
    
    def jump(self):
        if self.jump_counter == 0:
            self.velocity.y = JUMP_VELOCITY
            self.action = MarioAction.JUMPING
        elif self.jump_counter == 1:
            self.velocity.y = DOUBLE_JUMP_VELOCITY
            self.action = MarioAction.DOUBLE_JUMPING
        elif self.jump_counter == 2:
            self.velocity.y = TRIPLE_JUMP_VELOCITY
            self.action = MarioAction.TRIPLE_JUMPING
            self.jump_counter = 0  # Reset after triple jump
        
        self.on_ground = False
    
    def long_jump(self):
        self.velocity.y = LONG_JUMP_VELOCITY
        # Add forward momentum
        angle_rad = math.radians(self.facing_angle)
        self.velocity.x += math.sin(angle_rad) * 10
        self.velocity.z += -math.cos(angle_rad) * 10
        self.action = MarioAction.LONG_JUMPING
        self.on_ground = False
    
    def ground_pound(self):
        self.velocity.y = -50.0  # Fast downward velocity
        self.action = MarioAction.GROUND_POUNDING
    
    def wall_kick(self, wall_normal):
        self.velocity.y = WALL_KICK_VELOCITY
        self.velocity.x = wall_normal.x * 15
        self.velocity.z = wall_normal.z * 15
        self.action = MarioAction.WALL_KICKING
    
    def handle_collision(self, level):
        # Simple ground collision
        if self.pos.y <= 0:
            self.pos.y = 0
            self.velocity.y = 0
            self.on_ground = True
            if self.action == MarioAction.GROUND_POUNDING:
                # Ground pound impact
                self.create_shockwave()
        else:
            self.on_ground = False
        
        # Platform collision
        for platform in level.platforms:
            if self.check_platform_collision(platform):
                self.on_ground = True
                self.velocity.y = 0
    
    def check_platform_collision(self, platform):
        # AABB collision
        return (self.pos.x > platform.min_pos.x and self.pos.x < platform.max_pos.x and
                self.pos.z > platform.min_pos.z and self.pos.z < platform.max_pos.z and
                self.pos.y < platform.max_pos.y and self.pos.y > platform.min_pos.y - 2)
    
    def check_water_level(self, level):
        if self.pos.y < level.water_level:
            self.in_water = True
            self.action = MarioAction.SWIMMING
        else:
            self.in_water = False
    
    def create_shockwave(self):
        # TODO: Add particle effect
        pass
    
    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.die()
    
    def die(self):
        self.lives -= 1
        self.health = 8
        self.pos = Vector3(0, 10, 0)
        self.velocity = Vector3(0, 0, 0)
    
    def collect_coin(self):
        self.coins += 1
        if self.coins >= 100:
            self.lives += 1
            self.coins = 0
    
    def collect_star(self):
        self.stars += 1
    
    def render(self):
        glPushMatrix()
        glTranslatef(self.pos.x, self.pos.y, self.pos.z)
        glRotatef(self.facing_angle, 0, 1, 0)
        
        # Mario body (simplified)
        # Head
        glColor3f(0.95, 0.7, 0.6)  # Skin color
        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        self.draw_sphere(0.35, 8, 8)
        glPopMatrix()
        
        # Body
        glColor3f(0.8, 0.1, 0.1)  # Red shirt
        glPushMatrix()
        glTranslatef(0, 0.9, 0)
        glScalef(0.5, 0.7, 0.3)
        self.draw_cube()
        glPopMatrix()
        
        # Legs (blue overalls)
        glColor3f(0.1, 0.1, 0.8)
        glPushMatrix()
        glTranslatef(-0.15, 0.3, 0)
        glScalef(0.15, 0.6, 0.15)
        self.draw_cube()
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.15, 0.3, 0)
        glScalef(0.15, 0.6, 0.15)
        self.draw_cube()
        glPopMatrix()
        
        # Cap
        glColor3f(0.8, 0.1, 0.1)
        glPushMatrix()
        glTranslatef(0, 1.7, 0)
        glScalef(0.4, 0.1, 0.4)
        self.draw_cube()
        glPopMatrix()
        
        glPopMatrix()
    
    @staticmethod
    def draw_cube():
        vertices = [
            (-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
            (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1)
        ]
        
        glBegin(GL_QUADS)
        # Front
        glVertex3fv(vertices[0]); glVertex3fv(vertices[1])
        glVertex3fv(vertices[2]); glVertex3fv(vertices[3])
        # Back
        glVertex3fv(vertices[4]); glVertex3fv(vertices[7])
        glVertex3fv(vertices[6]); glVertex3fv(vertices[5])
        # Left
        glVertex3fv(vertices[0]); glVertex3fv(vertices[3])
        glVertex3fv(vertices[7]); glVertex3fv(vertices[4])
        # Right
        glVertex3fv(vertices[1]); glVertex3fv(vertices[5])
        glVertex3fv(vertices[6]); glVertex3fv(vertices[2])
        # Top
        glVertex3fv(vertices[3]); glVertex3fv(vertices[2])
        glVertex3fv(vertices[6]); glVertex3fv(vertices[7])
        # Bottom
        glVertex3fv(vertices[0]); glVertex3fv(vertices[4])
        glVertex3fv(vertices[5]); glVertex3fv(vertices[1])
        glEnd()
    
    @staticmethod
    def draw_sphere(radius, slices, stacks):
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + i / stacks)
            z0 = radius * math.sin(lat0)
            zr0 = radius * math.cos(lat0)
            
            lat1 = math.pi * (-0.5 + (i + 1) / stacks)
            z1 = radius * math.sin(lat1)
            zr1 = radius * math.cos(lat1)
            
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lng = 2 * math.pi * j / slices
                x = math.cos(lng)
                y = math.sin(lng)
                
                glVertex3f(x * zr0, z0, y * zr0)
                glVertex3f(x * zr1, z1, y * zr1)
            glEnd()

# ==================== LEVEL/WORLD ====================
class Platform:
    def __init__(self, min_pos, max_pos, terrain_type=TerrainType.NORMAL):
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.terrain_type = terrain_type
    
    def render(self):
        glPushMatrix()
        center = Vector3(
            (self.min_pos.x + self.max_pos.x) / 2,
            (self.min_pos.y + self.max_pos.y) / 2,
            (self.min_pos.z + self.max_pos.z) / 2
        )
        size = Vector3(
            self.max_pos.x - self.min_pos.x,
            self.max_pos.y - self.min_pos.y,
            self.max_pos.z - self.min_pos.z
        )
        
        glTranslatef(center.x, center.y, center.z)
        glScalef(size.x/2, size.y/2, size.z/2)
        
        # Color based on terrain type
        if self.terrain_type == TerrainType.NORMAL:
            glColor3f(0.4, 0.3, 0.2)
        elif self.terrain_type == TerrainType.SLIPPERY:
            glColor3f(0.7, 0.9, 1.0)
        
        Mario.draw_cube()
        glPopMatrix()

class Coin:
    def __init__(self, pos):
        self.pos = pos
        self.collected = False
        self.rotation = 0
    
    def update(self, dt):
        self.rotation += 90 * dt
    
    def render(self):
        if not self.collected:
            glPushMatrix()
            glTranslatef(self.pos.x, self.pos.y, self.pos.z)
            glRotatef(self.rotation, 0, 1, 0)
            glColor3f(1.0, 0.84, 0.0)  # Gold
            glScalef(0.3, 0.3, 0.05)
            Mario.draw_cube()
            glPopMatrix()

class Star:
    def __init__(self, pos):
        self.pos = pos
        self.collected = False
        self.bob_offset = 0
    
    def update(self, dt):
        self.bob_offset += dt * 2
    
    def render(self):
        if not self.collected:
            glPushMatrix()
            y_offset = math.sin(self.bob_offset) * 0.5
            glTranslatef(self.pos.x, self.pos.y + y_offset, self.pos.z)
            glColor3f(1.0, 1.0, 0.3)  # Yellow
            glScalef(0.5, 0.5, 0.5)
            Mario.draw_sphere(1, 8, 8)
            glPopMatrix()

class Level:
    """SM64 Level with platforms, collectibles, and obstacles"""
    def __init__(self):
        self.platforms = []
        self.coins = []
        self.stars = []
        self.water_level = -10.0
        self.name = "Bob-omb Battlefield"
        
        self.create_test_level()
    
    def create_test_level(self):
        # Ground
        self.platforms.append(Platform(
            Vector3(-50, -1, -50),
            Vector3(50, 0, 50)
        ))
        
        # Platforms
        for i in range(5):
            x = math.sin(i * math.pi / 2.5) * 20
            z = math.cos(i * math.pi / 2.5) * 20
            y = i * 3 + 2
            self.platforms.append(Platform(
                Vector3(x-3, y, z-3),
                Vector3(x+3, y+1, z+3)
            ))
        
        # Coins
        for i in range(20):
            angle = i * math.pi / 10
            x = math.sin(angle) * 15
            z = math.cos(angle) * 15
            self.coins.append(Coin(Vector3(x, 2, z)))
        
        # Stars
        self.stars.append(Star(Vector3(0, 15, 0)))
        self.stars.append(Star(Vector3(20, 8, 20)))
    
    def update(self, mario, dt):
        # Update collectibles
        for coin in self.coins:
            coin.update(dt)
            if not coin.collected:
                dist = math.sqrt((mario.pos.x - coin.pos.x)**2 + 
                                (mario.pos.y - coin.pos.y)**2 +
                                (mario.pos.z - coin.pos.z)**2)
                if dist < 1.5:
                    coin.collected = True
                    mario.collect_coin()
        
        for star in self.stars:
            star.update(dt)
            if not star.collected:
                dist = math.sqrt((mario.pos.x - star.pos.x)**2 + 
                                (mario.pos.y - star.pos.y)**2 +
                                (mario.pos.z - star.pos.z)**2)
                if dist < 2.0:
                    star.collected = True
                    mario.collect_star()
    
    def render(self):
        # Ground
        glColor3f(0.2, 0.6, 0.2)
        glBegin(GL_QUADS)
        glVertex3f(-100, 0, -100)
        glVertex3f(100, 0, -100)
        glVertex3f(100, 0, 100)
        glVertex3f(-100, 0, 100)
        glEnd()
        
        # Sky (simplified)
        glColor3f(0.5, 0.7, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(-100, 100, -100)
        glVertex3f(100, 100, -100)
        glVertex3f(100, 100, 100)
        glVertex3f(-100, 100, 100)
        glEnd()
        
        # Platforms
        for platform in self.platforms:
            platform.render()
        
        # Coins
        for coin in self.coins:
            coin.render()
        
        # Stars
        for star in self.stars:
            star.render()

# ==================== HUD ====================
class HUD:
    def __init__(self):
        self.font = None
        # Initialize a simple font for text rendering
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
    
    def render(self, mario):
        # Switch to 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # Health (power meter)
        self.draw_health_bar(mario.health, 20, 20)
        
        # Coins
        self.draw_text(f"x {mario.coins}", SCREEN_WIDTH - 120, 20, (255, 215, 0))
        
        # Stars
        self.draw_text(f"★ x {mario.stars}", SCREEN_WIDTH - 120, 50, (255, 255, 77))
        
        # Lives
        self.draw_text(f"Lives: {mario.lives}", 20, SCREEN_HEIGHT - 40, (255, 255, 255))
        
        # Action
        self.draw_text(f"{mario.action.name}", SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT - 40, (128, 255, 128))
        
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        
        # Restore projection
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def draw_health_bar(self, health, x, y):
        # Power meter segments (like SM64)
        for i in range(8):
            if i < health:
                glColor3f(1, 0, 0)
            else:
                glColor3f(0.3, 0.3, 0.3)
            
            glBegin(GL_QUADS)
            glVertex2f(x + i * 15, y)
            glVertex2f(x + i * 15 + 12, y)
            glVertex2f(x + i * 15 + 12, y + 20)
            glVertex2f(x + i * 15, y + 20)
            glEnd()
    
    def draw_text(self, text, x, y, color=(255, 255, 255)):
        # Use pygame font for text rendering
        text_surface = self.font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        glRasterPos2f(x, y)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)

# ==================== GAME CLASS ====================
class SM64Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Super Mario 64 - Python Port")
        
        # OpenGL setup
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        glLight(GL_LIGHT0, GL_POSITION, (0, 100, 0, 1))
        glLight(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1))
        glLight(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
        
        # Game objects
        self.camera = LakituCamera()
        self.mario = Mario(self)  # Pass game reference to Mario
        self.level = Level()
        self.hud = HUD()
        
        # Game state
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        
        # Mouse setup
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
    
    def handle_events(self):
        mouse_rel = (0, 0)
        
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_p:
                    self.paused = not self.paused
            elif event.type == MOUSEMOTION:
                mouse_rel = event.rel
        
        return mouse_rel
    
    def update(self, dt, keys, mouse_rel):
        if not self.paused:
            self.mario.update(keys, dt, self.level)
            self.level.update(self.mario, dt)
            self.camera.update(self.mario.pos, self.mario.facing_angle, mouse_rel)
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.5, 0.7, 1.0, 1)
        
        # Apply camera
        self.camera.apply()
        
        # Render scene
        self.level.render()
        self.mario.render()
        
        # Render HUD
        self.hud.render(self.mario)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds, locked to 60 FPS
            
            mouse_rel = self.handle_events()
            keys = pygame.key.get_pressed()
            
            self.update(dt, keys, mouse_rel)
            self.render()
        
        pygame.quit()

# ==================== MAIN ====================
if __name__ == "__main__":
    game = SM64Game()
    game.run()
