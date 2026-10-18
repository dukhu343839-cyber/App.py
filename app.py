
"""
HERA FIRE: BATTLE ARENA
An original top-down battle-royale-inspired Python/Pygame prototype.

Install:
    python -m pip install pygame
Run:
    python hera_fire.py

Controls:
    WASD / Arrow keys : Move
    Mouse             : Aim
    Left mouse button : Shoot
    R                 : Reload
    Space             : Dash
    Esc               : Pause / resume
"""

import math
import random
import sys
import pygame

pygame.init()
pygame.display.set_caption("HERA FIRE: BATTLE ARENA")

# ---------------------------- Configuration ----------------------------
W, H = 1280, 760
FPS = 60
WORLD_W, WORLD_H = 2200, 1600
screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
clock = pygame.time.Clock()

# Palette
BG = (13, 20, 29)
GROUND = (26, 42, 43)
GRID = (37, 59, 58)
CYAN = (65, 229, 238)
ORANGE = (255, 139, 70)
RED = (245, 75, 92)
WHITE = (239, 247, 250)
MUTED = (146, 166, 178)
GREEN = (80, 225, 150)
DARK = (8, 13, 20)

FONT = pygame.font.SysFont("arial", 20, bold=True)
SMALL = pygame.font.SysFont("arial", 15, bold=True)
MED = pygame.font.SysFont("arial", 28, bold=True)
BIG = pygame.font.SysFont("arial", 56, bold=True)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def vec_from_angle(angle):
    return pygame.Vector2(math.cos(angle), math.sin(angle))

def draw_text(surf, text, font, color, pos, anchor="topleft"):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, (int(pos[0]), int(pos[1])))
    surf.blit(image, rect)
    return rect

def panel(surf, rect, fill=(9, 16, 24, 220), border=(65, 229, 238), radius=12, width=1):
    layer = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=radius)
    surf.blit(layer, rect.topleft)
    pygame.draw.rect(surf, border, rect, width, border_radius=radius)

def glow_circle(surf, pos, radius, color, strength=90):
    r = max(1, int(radius * 2.8))
    layer = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(layer, (*color, strength), (r, r), int(radius * 1.7))
    pygame.draw.circle(layer, (*color, min(220, strength * 2)), (r, r), int(radius))
    surf.blit(layer, (int(pos[0] - r), int(pos[1] - r)), special_flags=pygame.BLEND_RGBA_ADD)

class Particle:
    def __init__(self, pos, color, velocity=None, life=None, size=None):
        self.pos = pygame.Vector2(pos)
        self.vel = velocity or pygame.Vector2(random.uniform(-180, 180), random.uniform(-180, 180))
        self.life = life or random.uniform(.18, .55)
        self.max_life = self.life
        self.size = size or random.uniform(2, 5)
        self.color = color

    def update(self, dt):
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= max(0, 1 - dt * 2.8)

    def draw(self, surf, camera):
        if self.life <= 0:
            return
        p = self.pos - camera
        alpha = clamp(self.life / self.max_life, 0, 1)
        r = max(1, int(self.size * alpha))
        pygame.draw.circle(surf, self.color, (int(p.x), int(p.y)), r)

class Bullet:
    def __init__(self, pos, velocity, owner, damage=18):
        self.pos = pygame.Vector2(pos)
        self.prev = self.pos.copy()
        self.vel = pygame.Vector2(velocity)
        self.owner = owner
        self.life = 1.2
        self.damage = damage

    def update(self, dt):
        self.prev = self.pos.copy()
        self.pos += self.vel * dt
        self.life -= dt

    def draw(self, surf, camera):
        p = self.pos - camera
        q = self.prev - camera
        pygame.draw.line(surf, (255, 206, 116), q, p, 3)
        pygame.draw.circle(surf, (255, 246, 210), (int(p.x), int(p.y)), 3)

class Actor:
    def __init__(self, x, y, player=False):
        self.pos = pygame.Vector2(x, y)
        self.player = player
        self.radius = 17 if player else 15
        self.hp = 100
        self.max_hp = 100
        self.speed = 245 if player else random.uniform(105, 145)
        self.angle = 0
        self.cooldown = 0
        self.alive = True
        self.color = CYAN if player else random.choice([(255, 117, 100), (255, 176, 77), (186, 122, 255)])
        self.ammo = 24 if player else 999
        self.reserve = 120
        self.reload_timer = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.ai_timer = random.random()
        self.ai_dir = pygame.Vector2(1, 0)
        self.kills = 0

    def hurt(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def reload(self):
        if self.player and self.reload_timer <= 0 and self.ammo < 24 and self.reserve > 0:
            self.reload_timer = 1.05

    def update(self, dt, game):
        if not self.alive:
            return
        self.cooldown = max(0, self.cooldown - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)

        if self.player:
            keys = pygame.key.get_pressed()
            move = pygame.Vector2(
                (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
                (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            )
            if move.length_squared():
                move = move.normalize()
                self.pos += move * self.speed * dt
            mouse_world = pygame.Vector2(pygame.mouse.get_pos()) + game.camera
            delta = mouse_world - self.pos
            if delta.length_squared() > 0:
                self.angle = math.atan2(delta.y, delta.x)
            if pygame.mouse.get_pressed()[0]:
                self.shoot(game)
        else:
            player = game.player
            if player.alive:
                to_player = player.pos - self.pos
                distance = to_player.length()
                if distance > 0:
                    self.angle = math.atan2(to_player.y, to_player.x)
                self.ai_timer -= dt
                if self.ai_timer <= 0:
                    self.ai_timer = random.uniform(.35, .8)
                    if distance > 300:
                        self.ai_dir = to_player.normalize()
                    elif distance < 170:
                        self.ai_dir = -to_player.normalize()
                    else:
                        self.ai_dir = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                        if self.ai_dir.length_squared():
                            self.ai_dir = self.ai_dir.normalize()
                self.pos += self.ai_dir * self.speed * dt
                if distance < 500 and random.random() < dt * 1.1:
                    self.shoot(game, enemy=True)

        self.pos.x = clamp(self.pos.x, 25, WORLD_W - 25)
        self.pos.y = clamp(self.pos.y, 25, WORLD_H - 25)

        if self.player and self.reload_timer > 0:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                needed = 24 - self.ammo
                take = min(needed, self.reserve)
                self.ammo += take
                self.reserve -= take

    def shoot(self, game, enemy=False):
        if self.cooldown > 0:
            return
        if self.player:
            if self.reload_timer > 0:
                return
            if self.ammo <= 0:
                self.reload()
                return
            self.ammo -= 1
            self.cooldown = .13
            damage = 34
            speed = 880
        else:
            self.cooldown = random.uniform(.45, .75)
            damage = 8
            speed = 560
        direction = vec_from_angle(self.angle)
        muzzle = self.pos + direction * (self.radius + 11)
        spread = 0 if self.player else random.uniform(-.10, .10)
        direction = vec_from_angle(self.angle + spread)
        game.bullets.append(Bullet(muzzle, direction * speed, self, damage))
        for _ in range(5 if self.player else 3):
            game.particles.append(Particle(muzzle, ORANGE, direction * random.uniform(30, 190), .18, random.uniform(2, 4)))
        game.shake = max(game.shake, 2.0 if self.player else .5)

    def draw(self, surf, camera):
        if not self.alive:
            return
        p = self.pos - camera
        x, y = int(p.x), int(p.y)
        if -50 < x < surf.get_width()+50 and -50 < y < surf.get_height()+50:
            glow_circle(surf, (x, y), self.radius, self.color, 24)
            # shadow
            pygame.draw.ellipse(surf, (7, 12, 17), (x-self.radius, y-self.radius//2+7, self.radius*2, self.radius))
            pygame.draw.circle(surf, self.color, (x, y), self.radius)
            pygame.draw.circle(surf, (235, 250, 250), (x, y), self.radius, 2)
            direction = vec_from_angle(self.angle)
            gun_end = pygame.Vector2(x, y) + direction * (self.radius + 18)
            pygame.draw.line(surf, (28, 35, 43), (x, y), gun_end, 8)
            pygame.draw.line(surf, CYAN if self.player else ORANGE, (x, y), gun_end, 3)
            # small visor
            pygame.draw.circle(surf, (8, 19, 27), (int(x + direction.x*5), int(y + direction.y*5)), 6)
            if not self.player:
                bar_w = 34
                pygame.draw.rect(surf, (54, 26, 33), (x-bar_w//2, y-self.radius-13, bar_w, 5), border_radius=3)
                pygame.draw.rect(surf, RED, (x-bar_w//2, y-self.radius-13, int(bar_w*self.hp/self.max_hp), 5), border_radius=3)

class Loot:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.kind = random.choice(["ammo", "med"])
        self.phase = random.random() * 6

    def draw(self, surf, camera, t):
        p = self.pos - camera
        bob = math.sin(t*3 + self.phase) * 3
        x, y = int(p.x), int(p.y + bob)
        color = GREEN if self.kind == "med" else ORANGE
        glow_circle(surf, (x, y), 9, color, 28)
        pygame.draw.rect(surf, color, (x-9, y-9, 18, 18), border_radius=4)
        pygame.draw.rect(surf, (245, 250, 250), (x-4, y-2, 8, 4))
        if self.kind == "med":
            pygame.draw.rect(surf, (245, 250, 250), (x-2, y-6, 4, 12))

class Game:
    def __init__(self):
        self.reset()
        self.state = "menu"
        self.elapsed = 0

    def reset(self):
        self.player = Actor(WORLD_W/2, WORLD_H/2, True)
        self.enemies = []
        for _ in range(15):
            while True:
                x, y = random.randint(100, WORLD_W-100), random.randint(100, WORLD_H-100)
                if pygame.Vector2(x, y).distance_to(self.player.pos) > 350:
                    break
            self.enemies.append(Actor(x, y))
        self.bullets = []
        self.particles = []
        self.loot = [Loot(random.randint(100, WORLD_W-100), random.randint(100, WORLD_H-100)) for _ in range(24)]
        self.camera = pygame.Vector2(0, 0)
        self.safe_center = pygame.Vector2(WORLD_W/2, WORLD_H/2)
        self.safe_radius = 1000
        self.safe_min = 190
        self.match_time = 0
        self.shake = 0
        self.elapsed = 0
        self.state = "playing"

    def update(self, dt):
        if self.state != "playing":
            return
        self.elapsed += dt
        self.match_time += dt
        self.safe_radius = max(self.safe_min, 1000 - self.match_time * 4.1)
        self.player.update(dt, self)
        for enemy in self.enemies:
            enemy.update(dt, self)
        for bullet in self.bullets[:]:
            bullet.update(dt)
            if bullet.life <= 0 or not (0 <= bullet.pos.x <= WORLD_W and 0 <= bullet.pos.y <= WORLD_H):
                self.bullets.remove(bullet)
                continue
            targets = self.enemies if bullet.owner is self.player else ([self.player] if self.player.alive else [])
            hit = False
            for target in targets:
                if target.alive and bullet.pos.distance_to(target.pos) < target.radius + 5:
                    target.hurt(bullet.damage)
                    hit = True
                    for _ in range(10):
                        self.particles.append(Particle(bullet.pos, RED if not target.player else CYAN))
                    if not target.alive and bullet.owner is self.player:
                        self.player.kills += 1
                        self.loot.append(Loot(target.pos.x, target.pos.y))
                    break
            if hit:
                self.bullets.remove(bullet)

        # Zone damage
        for actor in [self.player] + self.enemies:
            if actor.alive and actor.pos.distance_to(self.safe_center) > self.safe_radius:
                actor.hurt(7 * dt)
                if random.random() < dt * 10:
                    self.particles.append(Particle(actor.pos, (170, 90, 255), size=3))

        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)

        for loot in self.loot[:]:
            if self.player.pos.distance_to(loot.pos) < 34:
                if loot.kind == "med":
                    self.player.hp = min(100, self.player.hp + 30)
                else:
                    self.player.reserve += 30
                self.loot.remove(loot)

        self.enemies = [e for e in self.enemies if e.alive]
        target_camera = self.player.pos - pygame.Vector2(screen.get_width()/2, screen.get_height()/2)
        self.camera.x += (target_camera.x - self.camera.x) * min(1, dt*7)
        self.camera.y += (target_camera.y - self.camera.y) * min(1, dt*7)
        self.camera.x = clamp(self.camera.x, 0, WORLD_W-screen.get_width())
        self.camera.y = clamp(self.camera.y, 0, WORLD_H-screen.get_height())
        self.shake = max(0, self.shake - dt*12)

        if not self.player.alive:
            self.state = "over"
        elif len(self.enemies) == 0:
            self.state = "win"

    def draw_world(self, surf):
        surf.fill(GROUND)
        cam = self.camera.copy()
        if self.shake > 0:
            cam.x += random.uniform(-self.shake, self.shake)
            cam.y += random.uniform(-self.shake, self.shake)
        ox, oy = int(-cam.x) % 64, int(-cam.y) % 64
        for x in range(ox, surf.get_width(), 64):
            pygame.draw.line(surf, GRID, (x, 0), (x, surf.get_height()), 1)
        for y in range(oy, surf.get_height(), 64):
            pygame.draw.line(surf, GRID, (0, y), (surf.get_width(), y), 1)

        # Random fixed map structures, deterministic from seed
        random.seed(19)
        for _ in range(48):
            wx, wy = random.randint(50, WORLD_W-120), random.randint(50, WORLD_H-120)
            rect = pygame.Rect(int(wx-cam.x), int(wy-cam.y), random.randint(42, 90), random.randint(36, 78))
            if rect.right < 0 or rect.left > surf.get_width() or rect.bottom < 0 or rect.top > surf.get_height():
                continue
            pygame.draw.rect(surf, (18, 31, 36), rect.inflate(8, 8), border_radius=7)
            pygame.draw.rect(surf, (43, 61, 66), rect, border_radius=5)
            pygame.draw.rect(surf, (63, 91, 94), rect, 2, border_radius=5)
            pygame.draw.line(surf, (25, 43, 47), rect.topleft, rect.bottomright, 2)
        random.seed()

        # Safe zone boundary and outside tint
        center = self.safe_center - cam
        pygame.draw.circle(surf, (135, 74, 255), (int(center.x), int(center.y)), int(self.safe_radius), 2)
        pygame.draw.circle(surf, (135, 74, 255), (int(center.x), int(center.y)), int(self.safe_radius), 1)
        for loot in self.loot:
            loot.draw(surf, cam, self.elapsed)
        for bullet in self.bullets:
            bullet.draw(surf, cam)
        for enemy in self.enemies:
            enemy.draw(surf, cam)
        self.player.draw(surf, cam)
        for particle in self.particles:
            particle.draw(surf, cam)

        # screen vignette / bottom fade
        shade = pygame.Surface((surf.get_width(), 95), pygame.SRCALPHA)
        shade.fill((2, 8, 14, 100))
        surf.blit(shade, (0, surf.get_height()-95))

    def draw_hud(self, surf):
        sw, sh = surf.get_size()
        # top header
        panel(surf, pygame.Rect(18, 16, 310, 68), fill=(6, 13, 20, 225))
        draw_text(surf, "HERA", MED, CYAN, (34, 24))
        draw_text(surf, "FIRE  /  BATTLE ARENA", SMALL, WHITE, (121, 37))
        draw_text(surf, "SURVIVE • LOOT • ELIMINATE", SMALL, MUTED, (35, 61))

        panel(surf, pygame.Rect(sw-250, 16, 232, 68), fill=(6, 13, 20, 225), border=ORANGE)
        draw_text(surf, f"ALIVE  {len(self.enemies)+1}", MED, WHITE, (sw-230, 25))
        draw_text(surf, f"ELIMS  {self.player.kills:02d}", SMALL, ORANGE, (sw-228, 57))

        # health / armor-style status
        panel(surf, pygame.Rect(18, sh-87, 335, 68), fill=(6, 13, 20, 225))
        draw_text(surf, "HP", SMALL, WHITE, (32, sh-74))
        pygame.draw.rect(surf, (48, 35, 43), (72, sh-71, 220, 14), border_radius=6)
        hpw = int(220 * self.player.hp / self.player.max_hp)
        pygame.draw.rect(surf, GREEN if self.player.hp > 35 else RED, (72, sh-71, hpw, 14), border_radius=6)
        draw_text(surf, f"{int(self.player.hp)} / 100", SMALL, WHITE, (300, sh-75), "topright")
        draw_text(surf, "WASD MOVE  •  MOUSE AIM  •  CLICK FIRE  •  SPACE DASH", SMALL, MUTED, (32, sh-48))

        panel(surf, pygame.Rect(sw-260, sh-100, 242, 81), fill=(6, 13, 20, 225), border=ORANGE)
        draw_text(surf, "ASSAULT RIFLE", SMALL, MUTED, (sw-240, sh-88))
        draw_text(surf, f"{self.player.ammo:02d}", BIG, WHITE, (sw-240, sh-67))
        draw_text(surf, f"/ {self.player.reserve:03d}", FONT, ORANGE, (sw-158, sh-48))

        # compact minimap
        mw, mh = 150, 110
        mx, my = sw-mw-22, 105
        panel(surf, pygame.Rect(mx, my, mw, mh), fill=(6, 13, 20, 220), border=(66, 103, 112), radius=8)
        scale_x, scale_y = (mw-12)/WORLD_W, (mh-12)/WORLD_H
        for e in self.enemies:
            ex, ey = mx+6+e.pos.x*scale_x, my+6+e.pos.y*scale_y
            pygame.draw.circle(surf, RED, (int(ex), int(ey)), 2)
        px, py = mx+6+self.player.pos.x*scale_x, my+6+self.player.pos.y*scale_y
        pygame.draw.circle(surf, CYAN, (int(px), int(py)), 4)
        cx, cy = mx+6+self.safe_center.x*scale_x, my+6+self.safe_center.y*scale_y
        pygame.draw.circle(surf, (165, 108, 255), (int(cx), int(cy)), max(2, int(self.safe_radius*scale_x)), 1)
        draw_text(surf, "MINIMAP", SMALL, MUTED, (mx+8, my+mh+5))

        # zone alert
        if self.player.pos.distance_to(self.safe_center) > self.safe_radius:
            draw_text(surf, "WARNING: RETURN TO SAFE ZONE!", FONT, (190, 120, 255), (sw//2, 28), "midtop")
        else:
            draw_text(surf, f"ZONE SHRINK  {max(0, int(1000-self.match_time*4.1))}m", SMALL, (190, 150, 255), (sw//2, 28), "midtop")

    def draw_overlay(self, surf, title, subtitle, hint):
        sw, sh = surf.get_size()
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((3, 8, 15, 190))
        surf.blit(veil, (0, 0))
        panel(surf, pygame.Rect(sw//2-310, sh//2-170, 620, 340), fill=(7, 16, 25, 242), border=CYAN, radius=22, width=2)
        draw_text(surf, "HERA FIRE", BIG, CYAN, (sw//2, sh//2-120), "midtop")
        draw_text(surf, title, MED, WHITE, (sw//2, sh//2-45), "midtop")
        draw_text(surf, subtitle, FONT, MUTED, (sw//2, sh//2+2), "midtop")
        pygame.draw.rect(surf, ORANGE, (sw//2-115, sh//2+55, 230, 48), border_radius=12)
        draw_text(surf, hint, FONT, DARK, (sw//2, sh//2+79), "center")
        draw_text(surf, "WASD / ARROWS MOVE   •   MOUSE AIM   •   CLICK SHOOT   •   R RELOAD   •   SPACE DASH", SMALL, WHITE, (sw//2, sh//2+125), "midtop")

    def draw(self, surf):
        self.draw_world(surf)
        if self.state == "playing":
            self.draw_hud(surf)
        elif self.state == "menu":
            self.draw_overlay(surf, "BATTLE ARENA", "Enter the arena. Be the last survivor.", "PRESS ENTER TO DEPLOY")
        elif self.state == "paused":
            self.draw_overlay(surf, "PAUSED", "Take a breath, then return to the fight.", "PRESS ESC TO RESUME")
        elif self.state == "over":
            self.draw_overlay(surf, "MISSION FAILED", f"Eliminations: {self.player.kills}  •  Try a new drop.", "PRESS ENTER TO RETRY")
        elif self.state == "win":
            self.draw_overlay(surf, "VICTORY ROYALE!", f"Champion! Eliminations: {self.player.kills}", "PRESS ENTER TO PLAY AGAIN")

game = Game()
game.state = "menu"
running = True

while running:
    dt = min(clock.tick(FPS) / 1000.0, 0.033)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            W, H = max(800, event.w), max(520, event.h)
            screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game.state == "playing":
                    game.state = "paused"
                elif game.state == "paused":
                    game.state = "playing"
            if event.key == pygame.K_RETURN and game.state in ("menu", "over", "win"):
                game.reset()
            if event.key == pygame.K_r and game.state == "playing":
                game.player.reload()
            if event.key == pygame.K_SPACE and game.state == "playing":
                p = game.player
                if p.dash_cooldown <= 0:
                    keys = pygame.key.get_pressed()
                    d = pygame.Vector2(
                        (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
                        (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
                    )
                    if d.length_squared() == 0:
                        d = vec_from_angle(p.angle)
                    else:
                        d = d.normalize()
                    p.pos += d * 115
                    p.dash_cooldown = 2.2
                    for _ in range(18):
                        game.particles.append(Particle(p.pos, CYAN, -d*random.uniform(40, 220), .3, random.uniform(2, 5)))
                    game.shake = 5
    game.update(dt)
    game.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
