from tkinter import *
import time
import random
import math
import pygame
pygame.mixer.init() # [System] Audio Mixer Initialization


# =============================================================================
# [Manager] Sound Manager
# - BGM 및 SFX 리소스 로드 및 재생 관리
# - 싱글톤 패턴과 유사하게 전역 인스턴스(sound_mgr)로 운용
# =============================================================================
class SoundManager:
    def __init__(self):
        self.current_bgm = None
        
    def play_bgm(self, filename):
        """
        BGM 재생 (Loop)
        - 중복 요청 시 무시하여 끊김 방지
        """
        if not pygame: return
        if self.current_bgm == filename: return 
            
        self.current_bgm = filename
        try:
            pygame.mixer.music.load(f"sound/{filename}")
            pygame.mixer.music.play(-1) # Infinite Loop
        except: 
            print(f"[Err] BGM Load Failed: {filename}")

    def play_sfx(self, filename):
        """
        SFX 재생 (One-shot)
        - 효과음은 중첩 재생 허용
        """
        if not pygame: return
        try:
            sound = pygame.mixer.Sound(f"sound/{filename}")
            sound.play()
        except: pass

sound_mgr = SoundManager()


# =============================================================================
# [Utils] Resource Loader & Rendering Helpers
# - 퍼포먼스 최적화를 위한 GIF 프레임 캐싱 및 텍스트 렌더링 유틸리티
# =============================================================================
_gif_cache = {} 

def load_gif_frames(path, frame_count, scale=1):
    """
    GIF Frame Loader with Caching
    - 동일한 리소스 요청 시 캐시된 프레임 반환 (메모리 최적화)
    - scale 인자를 통해 로드 시 리사이징 수행
    """
    cache_key = (path, frame_count, scale)
    if cache_key in _gif_cache: return _gif_cache[cache_key]

    frames = []
    try:
        for i in range(frame_count):
            photo = PhotoImage(file=path, format=f"gif -index {i}")
            if scale > 1: photo = photo.subsample(scale) 
            frames.append(photo)
        _gif_cache[cache_key] = frames
    except Exception as e:
        print(f"[Err] Asset Load Failed: {path}")
        return [None] 
    return frames

def draw_outlined_text(canvas, x, y, text, font, fill_color, outline_color="black", **kwargs):
    """
    Text Rendering with Outline
    - 가독성 확보를 위해 8방향 오프셋으로 외곽선을 먼저 렌더링 후 본문 렌더링
    """
    offset = 2
    directions = [(-offset, -offset), (-offset, 0), (-offset, offset), 
                  (0, -offset),                     (0, offset), 
                  (offset, -offset),  (offset, 0),  (offset, offset)]
    
    for dx, dy in directions:
        canvas.create_text(x + dx, y + dy, text=text, font=font, fill=outline_color, **kwargs)
    return canvas.create_text(x, y, text=text, font=font, fill=fill_color, **kwargs)


# =============================================================================
# [Scene 0] Main Menu
# - 게임 진입점 및 관리자(Debug) 모드 진입 로직 포함
# =============================================================================
class MenuScene:
    def __init__(self, window, manager):
        self.window = window
        self.manager = manager
        self.canvas = Canvas(self.window, bg="white", width=1280, height=720)
        
        # [Easter Egg] Konami Code Logic (↑↑↓↓←→←→BA)
        self.input_log = []
        self.konami_code = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65]

        # Dynamic Background Setup
        self.bg_id = None 
        try:
            self.rand_bga_int = random.randint(1, 38)
            self.bg_img = PhotoImage(file=f"image/bga{self.rand_bga_int}.png")
            self.bg_id = self.canvas.create_image(640, 360, image=self.bg_img)
        except: pass
        
        # UI: Instruction Text
        draw_outlined_text(self.canvas, 1260, 700, 
                           text="이동: ← →   점프: Space   발사: A    대화 넘기기 : Enter", 
                           font=("KOTRA_BOLD", 15), fill_color="#DDDDDD", outline_color="black", anchor="se")

    def update_background(self):
        """Randomize Menu Background"""
        try:
            self.rand_bga_int = random.randint(1, 38)
            self.bg_img = PhotoImage(file=f"image/bga{self.rand_bga_int}.png")
            if self.bg_id:
                self.canvas.itemconfig(self.bg_id, image=self.bg_img)
        except Exception as e:
            print(f"[Err] BG Update Failed: {e}")

    def pack(self): 
        self.canvas.pack(expand=True, fill=BOTH) 
        
    def unpack(self): 
        self.canvas.pack_forget()
    
    def keyReleaseHandler(self, event):
        # [Input] Command Buffer Update
        self.input_log.append(event.keycode)
        if len(self.input_log) > 10:
            self.input_log.pop(0)
        
        # [Debug] Check Hidden Command
        if self.input_log == self.konami_code:
            sound_mgr.play_sfx("sfx_clear.wav")
            self.open_admin_tool() 
            self.input_log = []

        if event.keycode == 83: return 0  # Key 'S': Game Start
        if event.keycode == 82: self.update_background() # Key 'R': Refresh BG
        return -1

    def open_admin_tool(self):
        """
        [Debug] Admin Tool Window
        - 특정 스테이지로 즉시 이동하는 워프 기능 제공
        """
        admin_win = Toplevel(self.window)
        admin_win.title("관리자 도구 (Admin Tool)")
        admin_win.geometry("300x400")
        
        Label(admin_win, text="[ 스테이지 워프 ]", font=("Arial", 15, "bold")).pack(pady=10)

        def warp_to(scene_idx, bgm_name):
            admin_win.destroy()
            self.manager.change_scene(scene_idx)
            sound_mgr.play_bgm(bgm_name)

        Button(admin_win, text="1. 스테이지 1", width=20, command=lambda: warp_to(2, "bgm_stage1.mp3")).pack(pady=5)
        Button(admin_win, text="2. 스테이지 2", width=20, command=lambda: warp_to(3, "bgm_stage2.mp3")).pack(pady=5)
        Button(admin_win, text="3. 중간 보스 (대화)", width=20, command=lambda: warp_to(4, "bgm_stage2.mp3")).pack(pady=5)
        Button(admin_win, text="4. 중간 보스 (전투)", width=20, command=lambda: warp_to(5, "bgm_midboss.mp3")).pack(pady=5)
        Button(admin_win, text="5. 스테이지 3", width=20, command=lambda: warp_to(6, "bgm_stage3.mp3")).pack(pady=5)
        Button(admin_win, text="6. 최종 보스", width=20, command=lambda: warp_to(7, "bgm_boss.mp3")).pack(pady=5)


# =============================================================================
# [Scene] Dialogue / Cutscene
# - 순차적 이미지 렌더링을 통한 스토리텔링 씬
# =============================================================================
class DialogueScene:
    def __init__(self, window, image_files, bg_file=None):
        self.window = window
        self.canvas = Canvas(self.window, bg="black", width=1280, height=720)
        self.image_files = image_files 
        self.images = []                
        self.current_idx = 0             
        self.bg_img = None
        try:
            if bg_file: self.bg_img = PhotoImage(file=f"image/{bg_file}")
            for file in self.image_files:
                self.images.append(PhotoImage(file=f"image/{file}"))
        except: pass
        self.draw_scene()

    def pack(self): self.canvas.pack(expand=True, fill=BOTH)
    def unpack(self): self.canvas.pack_forget()
    def display(self): pass 
    def keyPressHandler(self, event): pass

    def draw_scene(self):
        self.canvas.delete("all")
        if self.bg_img: self.canvas.create_image(640, 360, image=self.bg_img)
        if self.current_idx < len(self.images):
            self.canvas.create_image(640, 360, image=self.images[self.current_idx])

    def keyReleaseHandler(self, event):
        if event.keycode == 13: # Key: Enter
            sound_mgr.play_sfx("sfx_dialogue.wav")
            self.current_idx += 1
            if self.current_idx >= len(self.image_files): return "NEXT" 
            self.draw_scene()
        return -1


# =============================================================================
# [Scene] Boss Encounter & Branching Logic
# - 대화 모드 -> 선택 모드(Choice)로 전환
# - 플레이어의 선택에 따라 엔딩 또는 히든 루트 분기 처리
# =============================================================================
class BossScene:
    def __init__(self, window):
        self.window = window
        self.canvas = Canvas(self.window, bg="black", width=1280, height=720)
        self.image_files = [f"boss_text{i}.png" for i in range(1, 36)]
        self.images = []
        try:
            for file in self.image_files:
                self.images.append(PhotoImage(file=f"image/{file}"))
            self.bg_img1 = PhotoImage(file="image/story2.png")
            self.bg_img2 = PhotoImage(file="image/story3.png")
        except: pass
        self.current_idx = 0
        self.state = "dialogue" 
        self.draw_scene()

    def pack(self): self.canvas.pack(expand=True, fill=BOTH)
    def unpack(self): self.canvas.pack_forget()
    def display(self): pass 
    def keyPressHandler(self, event): pass

    def draw_scene(self):
        self.canvas.delete("all")
        if self.state == "dialogue":
            current_bg = self.bg_img1 if self.current_idx < 2 else self.bg_img2
            if current_bg: self.canvas.create_image(640, 360, image=current_bg)
            if self.current_idx < len(self.images):
                self.canvas.create_image(640, 360, image=self.images[self.current_idx])
        elif self.state == "choice":
            self.canvas.create_rectangle(0, 0, 1280, 720, fill="#110000") 
            draw_outlined_text(self.canvas, 640, 200, text="진실을 마주한 당신, 무엇을 선택하겠습니까?", font=("KOTRA_BOLD", 30, "bold"), fill_color="white")
            draw_outlined_text(self.canvas, 640, 400, text="1. 연구소장을 죽이고 자결한다.", font=("KOTRA_BOLD", 20), fill_color="#FF6666")
            draw_outlined_text(self.canvas, 640, 500, text="2. 연구소장을 죽이고 연구소를 불태운다. ", font=("KOTRA_BOLD", 20), fill_color="#6666FF")
            # [Note] Option 3 is hidden (Triggered by key '3')
            self.canvas.create_text(640, 650, text="[1], [2]을 눌러 선택", font=("KOTRA_BOLD", 15), fill="gray")

    def keyReleaseHandler(self, event):
        if self.state == "dialogue":
            if event.keycode == 13: 
                sound_mgr.play_sfx("sfx_dialogue.wav")
                self.current_idx += 1
                if self.current_idx >= len(self.image_files): self.state = "choice"
                self.draw_scene()
        elif self.state == "choice":
            if event.char == '1': return "ENDING_1"
            elif event.char == '2': return "ENDING_2"
            elif event.char == '3': return "HIDDEN_BOSS" # [Secret] True Ending Route
        return -1


# =============================================================================
# [Scene] Ending & Game Over
# =============================================================================
class EndingScene:
    def __init__(self, window, ending_type):
        self.window = window
        self.canvas = Canvas(self.window, bg="black", width=1280, height=720)
        self.ending_type = ending_type 
        try:
            filename = f"image/ending{ending_type}.png"
            self.bg_img = PhotoImage(file=filename)
            self.canvas.create_image(640, 360, image=self.bg_img)
        except: pass
        self.canvas.create_text(60, 700, text="ESC: 종료", font=("KOTRA_BOLD", 15), fill="white", anchor="w")

    def pack(self): self.canvas.pack(expand=True, fill=BOTH)
    def unpack(self): self.canvas.pack_forget()
    def display(self): pass 
    def keyPressHandler(self, event): pass
    def keyReleaseHandler(self, event):
        if event.keycode == 27: self.window.destroy()
        return -1

class GameOverScene:
    def __init__(self, window):
        self.window = window
        self.canvas = Canvas(self.window, bg="black", width=1280, height=720)
        draw_outlined_text(self.canvas, 640, 300, text="GAME OVER", font=("KOTRA_BOLD", 70, "bold"), fill_color="red", outline_color="white")
        draw_outlined_text(self.canvas, 640, 500, text="[ Enter ] 메인 메뉴로 돌아가기", font=("KOTRA_BOLD", 20), fill_color="white", outline_color="black")

    def pack(self): self.canvas.pack(expand=True, fill=BOTH)
    def unpack(self): self.canvas.pack_forget()
    def display(self): pass 
    def keyPressHandler(self, event): pass
    def keyReleaseHandler(self, event):
        if event.keycode == 13: 
            return "GO_TO_MENU"
        return -1


# =============================================================================
# [Entities] Map Objects
# - Wall: 모든 방향 충돌 (Solid)
# - Glass: 플레이어는 막힘, 총알은 관통
# - Platform: 상향 점프 통과 가능 (One-way collision)
# =============================================================================
class MapObject:
    def __init__(self, canvas, x, y, w, h, color):
        self.canvas = canvas
        self.world_x = x; self.y = y; self.w = w; self.h = h; self.color = color
        self.id = self.canvas.create_rectangle(0, 0, 0, 0, fill=self.color, outline="black")
    def draw(self, scroll_x):
        screen_x = self.world_x - scroll_x
        self.canvas.coords(self.id, screen_x, self.y, screen_x + self.w, self.y + self.h)
    def get_rect(self): return (self.world_x, self.y, self.world_x + self.w, self.y + self.h)

class Wall(MapObject): 
    def __init__(self, canvas, x, y, w, h, color="gray"): super().__init__(canvas, x, y, w, h, color); self.type = "wall"
class Glass(MapObject): 
    def __init__(self, canvas, x, y, w, h):
        super().__init__(canvas, x, y, w, h, color="#87CEFA"); self.canvas.itemconfigure(self.id, stipple="gray50"); self.type = "glass" 
class Platform(MapObject): 
    def __init__(self, canvas, x, y, w, h, color="#8B4513"): super().__init__(canvas, x, y, w, h, color); self.type = "platform" 


# =============================================================================
# [Entities] Player
# - 물리 연산(중력, 점프), 애니메이션 상태 머신, 충돌 박스 관리
# =============================================================================
class Player:
    def __init__(self, canvas, x, y):
        self.canvas = canvas; self.x = x; self.y = y 
        self.speed = 15; self.dy = 0; self.gravity = 2.5; self.jump_power = -38; self.on_ground = False 
        self.facing = 1; self.state = "idle" 
        scale_factor = 6 
        
        self.anim = { "idle_R": [], "idle_L": [], "walk_R": [], "walk_L": [] }
        try:
            self.anim["walk_R"] = load_gif_frames("image/char/player/walk_R.gif", 8, scale_factor)
            self.anim["walk_L"] = load_gif_frames("image/char/player/walk_L.gif", 8, scale_factor)
            idle_r = PhotoImage(file="image/char/player/idle_0.png").subsample(scale_factor)
            idle_l = PhotoImage(file="image/char/player/idle_0_L.png").subsample(scale_factor)
            self.anim["idle_R"] = [idle_r]; self.anim["idle_L"] = [idle_l]
        except: print("[Warning] Player sprite load failed, using fallback.")

        self.frame_index = 0; self.last_anim_time = time.time()
        
        current_frame = self.anim["idle_R"][0] if self.anim["idle_R"] else None
        if current_frame:
            self.obj = self.canvas.create_image(self.x, self.y, image=current_frame)
            self.half_h = current_frame.height() // 2 
        else:
            self.obj = self.canvas.create_rectangle(x-20, y-40, x+20, y+40, fill="blue")
            self.half_h = 40

    def get_move_dir(self, pressed_keys):
        """Input Processing for Movement"""
        direction = 0; is_moving = False
        if 37 in pressed_keys: self.facing = -1; direction = -1; is_moving = True
        if 39 in pressed_keys: self.facing = 1; direction = 1; is_moving = True
        if is_moving: self.state = "walk"
        else: self.state = "idle"
        return direction

    def update_physics(self, world_x, map_objects):
        """Physics Engine: Gravity & Collision Resolution"""
        prev_foot_y = self.y + self.half_h
        self.dy += self.gravity 
        self.y += self.dy        
        curr_foot_y = self.y + self.half_h
        ground_y = 715 
        self.on_ground = False 
        
        # Ground Collision
        if curr_foot_y >= ground_y:
            self.y = ground_y - self.half_h
            self.dy = 0
            self.on_ground = True
            return 

        # Platform/Wall Collision (Landing Logic)
        if self.dy >= 0: 
            player_left = world_x - 20
            player_right = world_x + 20
            for obj in map_objects:
                ox1, oy1, ox2, oy2 = obj.get_rect()
                # X-Axis Overlap Check
                if (player_right > ox1) and (player_left < ox2):
                    # Y-Axis Landing Check (Pass-through if moving up, Collide if falling)
                    if prev_foot_y <= oy1 + 15 and curr_foot_y >= oy1:
                        self.dy = 0 
                        self.y = oy1 - self.half_h
                        self.on_ground = True
                        break

    def update_animation(self):
        """Update sprite frame based on state (idle/walk) and time delta"""
        key = f"{self.state}_{'R' if self.facing == 1 else 'L'}"
        frames = self.anim.get(key)
        if not frames or frames[0] is None: return 
        if len(frames) > 1: 
            if time.time() - self.last_anim_time > 0.05:
                self.frame_index = (self.frame_index + 1) % len(frames)
                self.last_anim_time = time.time()
                self.canvas.itemconfig(self.obj, image=frames[self.frame_index])
        else: self.canvas.itemconfig(self.obj, image=frames[0])

    def jump(self, pressed_keys):
        if self.on_ground: self.dy = self.jump_power; self.on_ground = False

    def set_screen_position(self, screen_x):
        self.x = screen_x
        try: self.canvas.coords(self.obj, self.x, self.y)
        except: pass
        self.update_animation()
    
    def get_y(self): return self.y
    def get_facing(self): return self.facing
    def get_shoot_pos(self):
        top_y = self.y - self.half_h; full_height = self.half_h * 2; shoot_y = top_y + (full_height * 0.69)
        return self.x, shoot_y
    def get_bbox(self): return self.canvas.bbox(self.obj)
    def get_damage_box(self):
        bbox = self.canvas.bbox(self.obj)
        if not bbox: return None
        margin = 15 
        return (bbox[0] + margin, bbox[1] + margin, bbox[2] - margin, bbox[3] - margin)




# =============================================================================
# [Entities] Enemy
# - Type: Mob, Data(Static Object), Boss, System Boss
# - AI: Simple tracking within visual range
# =============================================================================
class Enemy:
    def __init__(self, canvas, x, y, anim_frames, speed=3, hp=1, enemy_type="mob", can_shoot=False, is_boss=False, is_system=False):
        self.canvas = canvas; self.world_x = x; self.y = y
        self.speed = speed; 
        self.base_speed = speed 
        self.dy = 0; self.gravity = 0.9
        self.anim = anim_frames; self.facing = 1 
        self.hp = hp 
        self.max_hp = hp 
        self.enemy_type = enemy_type 
        self.can_shoot = can_shoot
        self.last_shot_time = time.time()
        
        # Boss Specific Attributes
        self.is_boss = is_boss
        self.is_system = is_system 
        self.wall_obj = None        
        self.wall_start_time = 0    
        self.last_wall_skill = time.time()
        self.last_teleport_auto = time.time()

        self.frame_index = 0; self.last_anim_time = time.time()
        
        # Init: Data Type Handling
        if self.enemy_type == "data":
            try:
                self.data_img = PhotoImage(file="image/data.png")
                self.obj = self.canvas.create_image(self.world_x, self.y, image=self.data_img)
                self.text_id = None; self.half_h = 60 
            except:
                self.obj = self.canvas.create_rectangle(0, 0, 60, 60, fill="blue", outline="white", width=2)
                self.text_id = self.canvas.create_text(0, 0, text="DATA", fill="white", font=("KOTRA_BOLD", 10))
                self.half_h = 30
        else:
            self.text_id = None
            current_frame = self.anim["walk_R"][0] if (self.anim["walk_R"] and self.anim["walk_R"][0]) else None
            if current_frame:
                self.obj = self.canvas.create_image(self.world_x, self.y, image=current_frame)
                self.half_h = current_frame.height() // 2
            else:
                color = "red" if is_boss else "green"
                if is_system: color = "cyan"
                self.obj = self.canvas.create_rectangle(0,0,40,40, fill=color)
                self.half_h = 20

    def update(self, player_world_x, map_objects, scroll_x, is_active):
        # 1. Culling (Skip update if off-screen)
        if not is_active: 
            screen_x = self.world_x - scroll_x
            if self.enemy_type == "data":
                 if self.text_id: 
                     self.canvas.coords(self.obj, screen_x - 30, self.y - 30, screen_x + 30, self.y + 30)
                     self.canvas.coords(self.text_id, screen_x, self.y)
                 else: 
                     if not self.text_id: self.canvas.coords(self.obj, screen_x, self.y)
                     else: self.canvas.coords(self.obj, screen_x - 30, self.y - 30, screen_x + 30, self.y + 30)
            else:
                 try: self.canvas.coords(self.obj, screen_x, self.y)
                 except: pass 
            return
            
        # ---------------------------------------------------------------------
        # [Boss Logic: System] (Floating, Static X-Axis with Teleport)
        # ---------------------------------------------------------------------
        if self.is_system:
            if self.world_x < player_world_x: self.facing = 1
            else: self.facing = -1 
            screen_x = self.world_x - scroll_x
            try:
                self.canvas.coords(self.obj, screen_x, self.y)
                self.update_animation()
            except: pass
            return
        # ---------------------------------------------------------------------

        # [Logic: Movement & AI]
        # Data type is static
        if self.enemy_type != "data":
            # Boss Enrage Mode (Speed Boost)
            if self.is_boss and self.hp <= 25: self.speed = self.base_speed * 1.5
            else: self.speed = self.base_speed
                
            # Tracking AI (X-Axis)
            dx = 0
            if abs(self.world_x - player_world_x) > 5:
                if self.world_x < player_world_x: dx = self.speed; self.facing = 1
                else: dx = -self.speed; self.facing = -1
            next_x = self.world_x + dx
            
            # Wall Collision Detection
            e_top = self.y - self.half_h; e_bottom = self.y + self.half_h
            e_left = next_x - 20; e_right = next_x + 20
            can_move = True
            for obj in map_objects:
                ox1, oy1, ox2, oy2 = obj.get_rect()
                if not (e_bottom <= oy1 or e_top >= oy2):
                    if (e_right > ox1) and (e_left < ox2): can_move = False; break
            if can_move: self.world_x = next_x
        
        # [Physics: Gravity] Applied to all entities including Data
        prev_foot_y = self.y + self.half_h
        self.dy += self.gravity; self.y += self.dy
        curr_foot_y = self.y + self.half_h
        ground_y = 715
        
        # 1. Floor Collision
        if curr_foot_y >= ground_y: self.y = ground_y - self.half_h; self.dy = 0
        
        # 2. Platform Collision
        elif self.dy >= 0:
            enemy_left = self.world_x - 20; enemy_right = self.world_x + 20
            for obj in map_objects:
                ox1, oy1, ox2, oy2 = obj.get_rect()
                if (enemy_right > ox1) and (enemy_left < ox2):
                    if prev_foot_y <= oy1 + 15 and curr_foot_y >= oy1: 
                        self.dy = 0; self.y = oy1 - self.half_h; break
        
        # [Render]
        screen_x = self.world_x - scroll_x
        
        # Render: Data Type
        if self.enemy_type == "data":
            if self.text_id: 
                self.canvas.coords(self.obj, screen_x - 30, self.y - 30, screen_x + 30, self.y + 30)
                self.canvas.coords(self.text_id, screen_x, self.y)
            else: 
                try: self.canvas.coords(self.obj, screen_x, self.y)
                except: pass
        # Render: Mobs/Bosses
        else:
            try:
                self.canvas.coords(self.obj, screen_x, self.y)
                self.update_animation()
            except: pass

    # (Animation & Box Helpers)
    def update_animation(self):
        if self.enemy_type == "data": return
        key = "walk_R" if self.facing == 1 else "walk_L"
        frames = self.anim.get(key)
        if not frames or frames[0] is None: return
        if time.time() - self.last_anim_time > 0.1:
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.last_anim_time = time.time()
            self.canvas.itemconfig(self.obj, image=frames[self.frame_index])

    def get_bbox(self): return self.canvas.bbox(self.obj)
    def get_damage_box(self):
        bbox = self.canvas.bbox(self.obj)
        if not bbox: return None
        margin = 15
        return (bbox[0] + margin, bbox[1] + margin, bbox[2] - margin, bbox[3] - margin)
    def delete(self): 
        self.canvas.delete(self.obj)
        if self.text_id: self.canvas.delete(self.text_id)



# =============================================================================
# [Scene: Core] Level Scene Base
# - 게임플레이의 핵심 로직 (렌더링, 물리, 충돌, UI)
# =============================================================================
class LevelScene:
    # [Inject] Game Manager dependency for global state (lives, transitions)
    def __init__(self, window, manager):
        self.window = window
        self.manager = manager 
        self.canvas = Canvas(self.window, bg="white", width=1280, height=720)
        self.map_width = 5351; self.screen_width = 1280; self.world_x = 200; self.scroll_x = 0        
        self.player = Player(self.canvas, 640, 715); self.pressed_keys = set() 
        self.bullets = []; self.bullet_speed = 50; self.last_shot_time = 0
        self.map_objects = []; self.bg_obj = None; self.floor_obj = None; self.is_bg_image = False
        self.enemies = []; self.enemy_anim = None; self.game_over = False; self.stage_clear = False; self.score = 0
        
        # [State] Retry Flag
        self.needs_retry = False

        # Boss HUD
        self.ui_boss_bg = None; self.ui_boss_bar = None; self.ui_boss_text = None
        
        # Main HUD (Enemies)
        self.ui_enemy_shadow = self.canvas.create_text(32, 32, text="", font=("KOTRA_BOLD", 20), fill="black", anchor="nw")
        self.ui_enemy_text = self.canvas.create_text(30, 30, text="", font=("KOTRA_BOLD", 20), fill="#00FF00", anchor="nw")
        
        # [New Feature] Life HUD (Hearts)
        self.ui_life_shadow = self.canvas.create_text(32, 72, text="", font=("KOTRA_BOLD", 20), fill="black", anchor="nw")
        self.ui_life_text = self.canvas.create_text(30, 70, text="", font=("KOTRA_BOLD", 20), fill="#FF4444", anchor="nw")

        # Siren Event System
        self.siren_enabled = False; self.siren_active = False; self.siren_start_time = 0; self.last_siren_check = time.time() 
        self.siren_interval = 15.0; self.siren_duration = 5.0        
        self.siren_overlay = self.canvas.create_rectangle(0, 0, 1280, 720, fill="red", outline="", stipple="gray25", state='hidden')

    def pack(self): self.canvas.pack(expand=True, fill=BOTH)
    def unpack(self): self.canvas.pack_forget()

    # [Logic] Unified Player Hit Handlerx
    def hit_player(self):
        if self.game_over or self.needs_retry: return

        self.whathitsound = random.randint(1, 100)
        if self.whathitsound < 95:
            sound_mgr.play_sfx("sfx_player_hit.wav")
        else:
            sound_mgr.play_sfx("sfx_player_hit_maybe.wav")

        # Life Decrement Logic
        if self.manager.lives > 1:
            self.manager.lives -= 1
            self.needs_retry = True # Signal for level reset
            # TODO: Add hit visual effect (flash)
        else:
            # Death
            self.manager.lives = 0
            sound_mgr.play_bgm("bgm_gameover.mp3")
            self.game_over = True
            draw_outlined_text(self.canvas, 640, 360, text="GAME OVER", font=("KOTRA_BOLD", 60, "bold"), fill_color="red", outline_color="white")

    def display(self):
        if self.game_over: return "GAME_OVER" 
        if self.needs_retry: return "RETRY" # [Signal] Reset Request
        if self.stage_clear: return

        # [Physics] Player Movement & World Collision
        move_dir = self.player.get_move_dir(self.pressed_keys)
        if move_dir != 0:
            next_x = self.world_x + (move_dir * self.player.speed)
            if next_x < 20: next_x = 20
            if next_x > self.map_width - 20: next_x = self.map_width - 20
            
            py_top = self.player.y - 40; py_bottom = self.player.y + 40
            for obj in self.map_objects:
                ox1, oy1, ox2, oy2 = obj.get_rect()
                if not (py_bottom < oy1 or py_top > oy2):
                    if move_dir > 0: 
                        if self.world_x + 20 <= ox1 and next_x + 20 > ox1: next_x = ox1 - 21 
                    elif move_dir < 0: 
                        if self.world_x - 20 >= ox2 and next_x - 20 < ox2: next_x = ox2 + 21 
            self.world_x = next_x

        self.player.update_physics(self.world_x, self.map_objects)
        
        # [Render] Camera Scroll Calculation
        ideal_scroll = self.world_x - (self.screen_width // 2)
        max_scroll = self.map_width - self.screen_width
        if ideal_scroll < 0: self.scroll_x = 0 
        elif ideal_scroll > max_scroll: self.scroll_x = max_scroll 
        else: self.scroll_x = ideal_scroll 
        
        # Parallax/Static Background
        if self.bg_obj:
            if self.is_bg_image: self.canvas.coords(self.bg_obj, (self.map_width // 2) - self.scroll_x, 360)
            else: self.canvas.coords(self.bg_obj, 0 - self.scroll_x, 0, self.map_width - self.scroll_x, 720)
        if self.floor_obj:
            self.canvas.coords(self.floor_obj, 0 - self.scroll_x, 715, self.map_width - self.scroll_x, 720)
        
        for obj in self.map_objects: obj.draw(self.scroll_x)
        
        player_screen_x = self.world_x - self.scroll_x
        self.player.set_screen_position(player_screen_x)
        
        # Update Sub-systems
        self.update_enemies()
        self.update_bullets()
        self.update_boss_ui()
        self.update_siren()
        self.update_enemy_count()
        self.update_life_ui() # HUD Update

    # [UI] Life Counter
    def update_life_ui(self):
        life_str = "♥ " * self.manager.lives
        self.canvas.itemconfigure(self.ui_life_shadow, text=life_str)
        self.canvas.itemconfigure(self.ui_life_text, text=life_str)
        self.canvas.tag_raise(self.ui_life_shadow)
        self.canvas.tag_raise(self.ui_life_text)

    # (HUD Updates: Enemies, Boss Bar, Siren)
    def update_enemy_count(self):
        # Clean up HUD if stage clear
        if self.stage_clear:
            self.canvas.itemconfigure(self.ui_enemy_shadow, state='hidden')
            self.canvas.itemconfigure(self.ui_enemy_text, state='hidden')
            return

        # Hide counter during Boss Fight
        boss_exists = False
        for e in self.enemies:
            if e.is_boss: boss_exists = True; break
        
        if boss_exists:
            self.canvas.itemconfigure(self.ui_enemy_shadow, state='hidden')
            self.canvas.itemconfigure(self.ui_enemy_text, state='hidden')
            return

        # Mob Counter
        count = 0
        for e in self.enemies:
            if e.enemy_type != "data": count += 1
            
        display_text = f"REMAINING ENEMIES: {count}"
        self.canvas.itemconfigure(self.ui_enemy_shadow, text=display_text, state='normal')
        self.canvas.itemconfigure(self.ui_enemy_text, text=display_text, state='normal')
        self.canvas.tag_raise(self.ui_enemy_shadow); self.canvas.tag_raise(self.ui_enemy_text)

    def update_boss_ui(self):
        boss = None
        for e in self.enemies:
            if e.is_boss: boss = e; break
        if not boss:
            if self.ui_boss_bg:
                self.canvas.delete(self.ui_boss_bg); self.canvas.delete(self.ui_boss_bar); self.canvas.delete(self.ui_boss_text)
                self.ui_boss_bg = None
            return
        bar_x = 340; bar_y = 50; bar_w = 600; bar_h = 25
        ratio = boss.hp / boss.max_hp
        current_w = bar_w * ratio
        name = "최종보스 : 시스템" if boss.is_system else "중간보스 : 경비대장"
        if self.ui_boss_bg is None:
            self.ui_boss_bg = self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, fill="#000000", outline="white", width=2)
            self.ui_boss_bar = self.canvas.create_rectangle(bar_x, bar_y, bar_x + current_w, bar_y + bar_h, fill="#FF0000", outline="")
            self.ui_boss_text = self.canvas.create_text(640, bar_y - 15, text=f"{name} ({int(boss.hp)}/{boss.max_hp})", font=("KOTRA_BOLD", 15, "bold"), fill="red")
        else:
            self.canvas.coords(self.ui_boss_bar, bar_x, bar_y, bar_x + current_w, bar_y + bar_h)
            self.canvas.itemconfigure(self.ui_boss_text, text=f"{name} ({int(boss.hp)}/{boss.max_hp})")
            self.canvas.tag_raise(self.ui_boss_bg); self.canvas.tag_raise(self.ui_boss_bar); self.canvas.tag_raise(self.ui_boss_text)

    def update_siren(self):
        if not self.siren_enabled: return 
        current_time = time.time()
        if not self.siren_active:
            if current_time - self.last_siren_check > self.siren_interval:
                self.siren_active = True; self.siren_start_time = current_time
                sound_mgr.play_sfx("sfx_siren.wav")
                print("[지평론 연구소] 비상 상황, 비상 상황. 시설 내 신원 미상 인원의 침입이 확인되었습니다. 이것은 훈련이 아닙니다. 실제 상황입니다. 시설 내 모든 연구원은 즉시 표준 대응 절차에 따라 안전 구역으로 대피하십시오.")
        else:
            elapsed = current_time - self.siren_start_time
            if elapsed > self.siren_duration:
                self.siren_active = False; self.last_siren_check = current_time
                self.canvas.itemconfigure(self.siren_overlay, state='hidden')
            else:
                if int(elapsed) % 2 == 0:
                    self.canvas.itemconfigure(self.siren_overlay, state='normal'); self.canvas.tag_raise(self.siren_overlay)
                    if self.ui_boss_bg: self.canvas.tag_raise(self.ui_boss_bg); self.canvas.tag_raise(self.ui_boss_bar); self.canvas.tag_raise(self.ui_boss_text)
                    self.canvas.tag_raise(self.ui_enemy_shadow); self.canvas.tag_raise(self.ui_enemy_text)
                    self.canvas.tag_raise(self.ui_life_shadow); self.canvas.tag_raise(self.ui_life_text) # Ensure Life HUD is visible
                else: self.canvas.itemconfigure(self.siren_overlay, state='hidden')

    def update_enemies(self):
        p_dbox = self.player.get_damage_box()
        active_min = self.scroll_x - 300; active_max = self.scroll_x + self.screen_width + 300
        
        for enemy in self.enemies:
            is_active = (active_min <= enemy.world_x <= active_max)
            enemy.update(self.world_x, self.map_objects, self.scroll_x, is_active)
            
            # AI: Combat Logic
            if is_active and enemy.can_shoot and enemy.enemy_type != "data":
                shoot_cooldown = 4.0
                if enemy.is_system:
                    shoot_cooldown = 4.0 
                    if enemy.hp <= enemy.max_hp * 0.5: shoot_cooldown = 3.0 
                    if enemy.hp <= enemy.max_hp * 0.5:
                        # System Boss: Auto Teleport Phase
                        if time.time() - enemy.last_teleport_auto > 10.0:
                            if hasattr(self, 'teleport_system_boss'):
                                self.teleport_system_boss(enemy)
                                enemy.last_teleport_auto = time.time()
                    if time.time() - enemy.last_shot_time > shoot_cooldown:
                        bullet_count = 3 if enemy.hp <= enemy.max_hp * 0.5 else 1
                        self.fire_enemy_bullet(enemy, aimed=True, count=bullet_count)
                        enemy.last_shot_time = time.time()
                else:
                    if enemy.is_boss and enemy.hp <= 25: shoot_cooldown = 1.5
                    if time.time() - enemy.last_shot_time > shoot_cooldown: 
                        self.fire_enemy_bullet(enemy)
                        enemy.last_shot_time = time.time()

            # Boss Skill: Wall Summon
            if is_active and enemy.is_boss and not enemy.is_system:
                current_time = time.time()
                if enemy.wall_obj is None:
                    if current_time - enemy.last_wall_skill > 8.0:
                        wall_x = enemy.world_x + (80 * enemy.facing)
                        new_wall = Wall(self.canvas, x=wall_x, y=500, w=20, h=315, color="#4B0082")
                        self.map_objects.append(new_wall); enemy.wall_obj = new_wall; enemy.wall_start_time = current_time
                else:
                    if current_time - enemy.wall_start_time > 3.0:
                        if enemy.wall_obj in self.map_objects: self.map_objects.remove(enemy.wall_obj)
                        self.canvas.delete(enemy.wall_obj.id); enemy.wall_obj = None; enemy.last_wall_skill = current_time 

            # Collision: Player vs Enemy Body
            e_dbox = enemy.get_damage_box()
            if p_dbox and e_dbox:
                if (p_dbox[0] < e_dbox[2] and p_dbox[2] > e_dbox[0] and p_dbox[1] < e_dbox[3] and p_dbox[3] > e_dbox[1]):
                    if enemy.enemy_type == "data": continue 
                    self.hit_player() 
                    return

    def fire_enemy_bullet(self, enemy, aimed=False, count=1):
        sound_mgr.play_sfx("sfx_shoot_enemy.wav")
        bx = enemy.world_x; by = enemy.y
        if aimed: 
            px = self.player.x + self.scroll_x 
            target_x = self.world_x 
            target_y = self.player.y
            angle = math.atan2(target_y - by, target_x - bx)
            speed = 15
            for i in range(count):
                spread = 0
                if count > 1: spread = (i - 1) * 0.2 
                final_angle = angle + spread
                vx = math.cos(final_angle) * speed
                vy = math.sin(final_angle) * speed
                b_id = self.canvas.create_oval(0, 0, 0, 0, fill="cyan")
                self.bullets.append({'id': b_id, 'world_x': bx, 'y': by, 'vx': vx, 'vy': vy, 'dir': 0, 'laps': 0, 'owner': 'enemy', 'aimed': True})
        else: 
            dir = -1 if self.world_x < enemy.world_x else 1
            b_id = self.canvas.create_oval(0, 0, 0, 0, fill="red")
            self.bullets.append({'id': b_id, 'world_x': bx, 'y': by, 'dir': dir, 'laps': 0, 'owner': 'enemy', 'aimed': False})

    def fire_bullet(self):
        if time.time() - self.last_shot_time < 0.2: return
        self.last_shot_time = time.time(); px, py = self.player.get_shoot_pos(); bx = self.world_x; by = py; facing = self.player.get_facing()
        sound_mgr.play_sfx("sfx_shoot.wav")
        b_id = self.canvas.create_oval(0, 0, 0, 0, fill="yellow")
        self.bullets.append({'id': b_id, 'world_x': bx, 'y': by, 'dir': facing, 'laps': 0, 'owner': 'player'})

    def update_bullets(self):
        steps = 20
        for b in self.bullets[:]:
            collision = False
            owner = b.get('owner', 'player') 
            aimed = b.get('aimed', False)
            step_speed_x = 0; step_speed_y = 0
            if owner == 'enemy' and aimed:
                step_speed_x = b['vx'] / steps
                step_speed_y = b['vy'] / steps
            else:
                current_speed = 20 if owner == 'enemy' else self.bullet_speed
                step_speed_x = (current_speed / steps) * b.get('dir', 1)
                step_speed_y = 0
            for _ in range(steps):
                b['world_x'] += step_speed_x
                b['y'] += step_speed_y
                screen_x = b['world_x'] - self.scroll_x
                
                # World Boundary Check (Looping for Player Bullets)
                if owner == 'player':
                    if b['dir'] == 1 and screen_x > self.screen_width: 
                        b['world_x'] = self.scroll_x; b['laps'] += 1
                    elif b['dir'] == -1 and screen_x < 0: 
                        b['world_x'] = self.scroll_x + self.screen_width; b['laps'] += 1
                else:
                    if screen_x > self.screen_width + 100 or screen_x < -100 or b['y'] > 800 or b['y'] < -100:
                        collision = True; break
                
                # Map Object Collision
                if not (owner == 'enemy' and aimed):
                    for obj in self.map_objects:
                        if obj.type == "glass": continue 
                        ox1, oy1, ox2, oy2 = obj.get_rect()
                        if (ox1 < b['world_x'] < ox2) and (oy1 < b['y'] < oy2): collision = True; break
                if collision: break
            
            if b['laps'] >= 2 or collision: self.canvas.delete(b['id']); self.bullets.remove(b); continue
            
            bullet_hit = False
            b_screen_x = b['world_x'] - self.scroll_x
            b_rect = (b_screen_x - 5, b['y'] - 5, b_screen_x + 5, b['y'] + 5)
            
            # [Hit Logic] Player Bullet -> Enemy
            if owner == 'player':
                for enemy in self.enemies[:]:
                    e_dbox = enemy.get_damage_box()
                    if e_dbox:
                        if (b_rect[0] < e_dbox[2] and b_rect[2] > e_dbox[0] and b_rect[1] < e_dbox[3] and b_rect[3] > e_dbox[1]):
                            if enemy.enemy_type == "data":
                                # Shield Logic: Mobs must be cleared first
                                mobs_alive = 0
                                for e in self.enemies:
                                    if e.enemy_type == "mob" or e.is_boss: mobs_alive += 1
                                if mobs_alive > 0:
                                    print("쉴드! 적을 먼저 처치하세요.")
                                    bullet_hit = True; break 
                            
                            enemy.hp -= 1
                            sound_mgr.play_sfx("sfx_enemy_die.wav")
                            
                            if enemy.is_system:
                                if hasattr(self, 'teleport_system_boss'): self.teleport_system_boss(enemy)
                            
                            if enemy.hp <= 0:
                                enemy.delete(); self.enemies.remove(enemy); self.score += 500
                            bullet_hit = True
                            
                            # [Stage Clear Condition]
                            if len(self.enemies) == 0:
                                self.stage_clear = True
                                
                                # System Boss Special Handling (No Clear BGM)
                                is_system_stage = isinstance(self, SystemBossScene)
                                
                                if not is_system_stage:
                                    sound_mgr.play_bgm("bgm_clear.mp3") 
                                
                                # UI Text
                                if is_system_stage:
                                    draw_outlined_text(self.canvas, 640, 300, text="SYSTEM SILENCED...", font=("KOTRA_BOLD", 70, "bold"), fill_color="gray", outline_color="white")
                                else:
                                    draw_outlined_text(self.canvas, 640, 300, text="STAGE CLEAR", font=("KOTRA_BOLD", 70, "bold"), fill_color="blue", outline_color="white")
                                
                                draw_outlined_text(self.canvas, 640, 450, text="[ Enter ]", font=("KOTRA_BOLD", 30), fill_color="white", outline_color="black")
                            break
            
            # [Hit Logic] Enemy Bullet -> Player
            elif owner == 'enemy':
                p_dbox = self.player.get_damage_box()
                if p_dbox:
                    if (b_rect[0] < p_dbox[2] and b_rect[2] > p_dbox[0] and b_rect[1] < p_dbox[3] and b_rect[3] > p_dbox[1]):
                        self.hit_player() 
                        bullet_hit = True
            
            if bullet_hit: self.canvas.delete(b['id']); self.bullets.remove(b); continue
            
            # Bullet Rendering
            screen_x = b['world_x'] - self.scroll_x; screen_y = b['y'] 
            self.canvas.coords(b['id'], screen_x - 5, screen_y - 5, screen_x + 5, screen_y + 5)
            if -50 < screen_x < self.screen_width + 50: self.canvas.itemconfigure(b['id'], state='normal')
            else: self.canvas.itemconfigure(b['id'], state='hidden')

    def keyPressHandler(self, event):
        if self.game_over or self.stage_clear: return 
        self.pressed_keys.add(event.keycode) 
        if event.keycode == 32: self.player.jump(self.pressed_keys) 
        if event.keycode == 65: self.fire_bullet() 

    def keyReleaseHandler(self, event):
        if event.keycode in self.pressed_keys: self.pressed_keys.remove(event.keycode)
        
        if self.stage_clear and event.keycode == 13: 
            # System Boss Special Return Signal
            if isinstance(self, SystemBossScene):
                return "SYSTEM_CLEARED"
            return "CLEARED"
        return -1


# =============================================================================
# [Levels] Concrete Stage Implementations
# - Map Layout, Enemy Placement
# =============================================================================
class Stage1Scene(LevelScene):
    def __init__(self, window, manager): 
        super().__init__(window, manager) 
        try:
            self.bg_img = PhotoImage(file="image/stg1.png")
            self.bg_obj = self.canvas.create_image(self.map_width//2, 360, image=self.bg_img)
            self.is_bg_image = True 
        except:
            self.bg_obj = self.canvas.create_rectangle(0, 0, self.map_width, 720, fill="#87CEEB")
            self.is_bg_image = False
        self.floor_obj = self.canvas.create_rectangle(0, 715, self.map_width, 720, fill="white", outline="")
        
        # Map Objects Setup
        self.map_objects.append(Glass(self.canvas, x=950, y=200, w=50, h=300))
        self.map_objects.append(Glass(self.canvas, x=1250, y=200, w=50, h=300))
        self.map_objects.append(Platform(self.canvas, x=800, y=500, w=500, h=20))
        self.map_objects.append(Wall(self.canvas, x=1600, y=0, w=50, h=300)) 
        self.map_objects.append(Wall(self.canvas, x=1800, y=500, w=50, h=215)) 
        self.map_objects.append(Platform(self.canvas, x=2200, y=500, w=500, h=20)) 
        self.map_objects.append(Platform(self.canvas, x=2200, y=300, w=500, h=20)) 
        self.map_objects.append(Wall(self.canvas, x=2200, y=0, w=50, h=500)) 
        self.map_objects.append(Glass(self.canvas, x=2450, y=0, w=50, h=500))  
        self.map_objects.append(Platform(self.canvas, x=2700, y=200, w=400, h=20)) 
        self.map_objects.append(Wall(self.canvas, x=3000, y=500, w=50, h=215,)) 
        self.map_objects.append(Wall(self.canvas, x=3250, y=500, w=50, h=215,)) 
        self.map_objects.append(Platform(self.canvas, x=3000, y=500, w=300, h=20)) 
        self.map_objects.append(Wall(self.canvas, x=3200, y=0, w=50, h=200,)) 
        self.map_objects.append(Platform(self.canvas, x=3200, y=200, w=300, h=20)) 
        self.map_objects.append(Glass(self.canvas, x=3450, y=0, w=50, h=200,)) 
        self.map_objects.append(Platform(self.canvas, x=3600, y=680, w=200, h=20)) 
        self.map_objects.append(Platform(self.canvas, x=3800, y=600, w=200, h=20))
        self.map_objects.append(Platform(self.canvas, x=4000, y=520, w=200, h=20)) 
        self.map_objects.append(Platform(self.canvas, x=4200, y=440, w=200, h=20))
        self.map_objects.append(Platform(self.canvas, x=4400, y=360, w=900, h=20)) 
        self.map_objects.append(Wall(self.canvas, x=4800, y=0, w=50, h=360)) 

        # Enemy Spawning
        self.enemy_anim = {"walk_R": [], "walk_L": []}
        self.enemy_anim["walk_R"] = load_gif_frames("image/char/enemy/e_walk_R.gif", 8, 6)
        self.enemy_anim["walk_L"] = load_gif_frames("image/char/enemy/e_walk_L.gif", 8, 6)
        
        enemy_spots = [
            (900, 650), (1200, 380), (2300, 380), (2300, 650), (2300, 200), (3150, 650), (3350, 100)  
        ]
        for ex, ey in enemy_spots: 
            self.enemies.append(Enemy(self.canvas, ex, ey, self.enemy_anim))
            
        data_obj = Enemy(self.canvas, x=5000, y=200, anim_frames=self.enemy_anim, speed=0, hp=5, enemy_type="data")
        self.enemies.append(data_obj)
        self.canvas.tag_raise(self.player.obj)

        self.siren_enabled = True

class Stage2Scene(LevelScene):
    def __init__(self, window, manager): 
        super().__init__(window, manager) 
        try:
            self.bg_img = PhotoImage(file="image/stg2.png") 
            self.bg_obj = self.canvas.create_image(self.map_width//2, 360, image=self.bg_img)
            self.is_bg_image = True 
        except:
            self.bg_obj = self.canvas.create_rectangle(0, 0, self.map_width, 720, fill="#555")
            self.is_bg_image = False
        self.floor_obj = self.canvas.create_rectangle(0, 715, self.map_width, 720, fill="gray", outline="")
        self.map_objects.append(Wall(self.canvas, x=500, y=500, w=50, h=215))
        self.map_objects.append(Wall(self.canvas, x=800, y=500, w=50, h=215)) 
        self.map_objects.append(Wall(self.canvas, x=1100, y=500, w=50, h=215))
        self.map_objects.append(Platform(self.canvas, x=500, y=500, w=1800, h=20))
        self.map_objects.append(Wall(self.canvas, x=1100, y=300, w=50, h=200))
        self.map_objects.append(Wall(self.canvas, x=1400, y=300, w=50, h=200))
        self.map_objects.append(Wall(self.canvas, x=1700, y=300, w=50, h=200))
        self.map_objects.append(Platform(self.canvas, x=1100, y=300, w=650, h=20))
        self.map_objects.append(Wall(self.canvas, x=3000, y=300, w=50, h=200))
        self.map_objects.append(Wall(self.canvas, x=3300, y=300, w=50, h=200))
        self.map_objects.append(Wall(self.canvas, x=3600, y=300, w=50, h=200))
        self.map_objects.append(Platform(self.canvas, x=3000, y=300, w=650, h=20))
        self.map_objects.append(Wall(self.canvas, x=3600, y=500, w=50, h=215))
        self.map_objects.append(Wall(self.canvas, x=3900, y=500, w=50, h=215))
        self.map_objects.append(Wall(self.canvas, x=4200, y=0, w=50, h=715))
        self.map_objects.append(Platform(self.canvas, x=2400, y=500, w=1850, h=20))

        self.enemy_anim = {"walk_R": [], "walk_L": []}
        self.enemy_anim["walk_R"] = load_gif_frames("image/char/enemy/e_walk_R.gif", 8, 6)
        self.enemy_anim["walk_L"] = load_gif_frames("image/char/enemy/e_walk_L.gif", 8, 6)
        enemy_spots = [(650, 680), (950, 680), (1250, 450), (1550, 450), (3150, 450), (3450, 450), (3750, 680), (4050, 680)]
        for ex, ey in enemy_spots: self.enemies.append(Enemy(self.canvas, ex, ey, self.enemy_anim))
        
        self.enemies.append(Enemy(self.canvas, x=700, y=450, anim_frames=self.enemy_anim, speed=8, hp=1, can_shoot=False))
        self.enemies.append(Enemy(self.canvas, x=1350, y=150, anim_frames=self.enemy_anim, speed=8, hp=1, can_shoot=False))
        self.enemies.append(Enemy(self.canvas, x=3200, y=150, anim_frames=self.enemy_anim, speed=8, hp=1, can_shoot=False))
        self.enemies.append(Enemy(self.canvas, x=1600, y=680, anim_frames=self.enemy_anim, speed=1, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=3000, y=680, anim_frames=self.enemy_anim, speed=1, hp=3, can_shoot=True))
        data_obj = Enemy(self.canvas, x=2350, y=680, anim_frames=self.enemy_anim, speed=0, hp=5, enemy_type="data")
        self.enemies.append(data_obj)
        self.canvas.tag_raise(self.player.obj)

        self.siren_enabled = True

class StageMidBossScene(LevelScene):
    def __init__(self, window, manager): 
        super().__init__(window, manager) 
        self.map_width = 1280 
        try:
            self.bg_img = PhotoImage(file="image/stg_mid.png") 
            self.bg_obj = self.canvas.create_image(640, 360, image=self.bg_img)
            self.is_bg_image = True 
        except:
            self.bg_obj = self.canvas.create_rectangle(0, 0, self.map_width, 720, fill="#440000") 
            self.is_bg_image = False
        self.floor_obj = self.canvas.create_rectangle(0, 715, self.map_width, 720, fill="#880000", outline="")
        self.map_objects.append(Platform(self.canvas, x=400, y=500, w=480, h=20, color="#8B0000")) 

        self.enemy_anim = {"walk_R": [], "walk_L": []}
        self.enemy_anim["walk_R"] = load_gif_frames("image/char/antagonist/b_walk_R.gif", 8, 6) 
        self.enemy_anim["walk_L"] = load_gif_frames("image/char/antagonist/b_walk_L.gif", 8, 6)

        # Spawn Mid-Boss
        boss = Enemy(self.canvas, x=1000, y=680, anim_frames=self.enemy_anim, speed=8, hp=50, can_shoot=True, is_boss=True)
        self.enemies.append(boss)
        self.canvas.tag_raise(self.player.obj)

class Stage3Scene(LevelScene):
    def __init__(self, window, manager): 
        super().__init__(window, manager) 
        try:
            self.bg_img = PhotoImage(file="image/stg3.png") 
            self.bg_obj = self.canvas.create_image(self.map_width//2, 360, image=self.bg_img)
            self.is_bg_image = True 
        except:
            self.bg_obj = self.canvas.create_rectangle(0, 0, self.map_width, 720, fill="#555")
            self.is_bg_image = False
        self.floor_obj = self.canvas.create_rectangle(0, 715, self.map_width, 720, fill="#555555", outline="")
        self.map_objects.append(Platform(self.canvas, x=600, y=500, w=500, h=20))
        
        
        self.map_objects.append(Wall(self.canvas, x=1200, y=300, w=50, h=200)) 
        self.map_objects.append(Glass(self.canvas, x=1200, y=500, w=50, h=215))
        self.map_objects.append(Wall(self.canvas, x=1500, y=300, w=50, h=415))
        self.map_objects.append(Platform(self.canvas, x=1200, y=300, w=300, h=20))
        self.map_objects.append(Platform(self.canvas, x=1200, y=500, w=300, h=20))

        self.map_objects.append(Platform(self.canvas, x=2000, y=300, w=400, h=20))
        self.map_objects.append(Platform(self.canvas, x=2000, y=500, w=400, h=20))
        self.map_objects.append(Platform(self.canvas, x=2500, y=300, w=500, h=20))
        self.map_objects.append(Platform(self.canvas, x=2500, y=500, w=500, h=20))

        self.map_objects.append(Wall(self.canvas, x=2500, y=300, w=50, h=200))

        self.map_objects.append(Glass(self.canvas, x=2700, y=0, w=50, h=715)) 
        self.map_objects.append(Wall(self.canvas, x=2950, y=0, w=50, h=715))
        
        self.map_objects.append(Glass(self.canvas, x=4500, y=0, w=50, h=715))

        
        
        self.enemy_anim = {"walk_R": [], "walk_L": []}
        self.enemy_anim["walk_R"] = load_gif_frames("image/char/enemy/es_walk_R.gif", 8, 6)
        self.enemy_anim["walk_L"] = load_gif_frames("image/char/enemy/es_walk_L.gif", 8, 6)

        self.enemies.append(Enemy(self.canvas, x=1300, y=600, anim_frames=self.enemy_anim, speed=8, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=1300, y=400, anim_frames=self.enemy_anim, speed=8, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2200, y=500, anim_frames=self.enemy_anim, speed=3, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2200, y=200, anim_frames=self.enemy_anim, speed=3, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2900, y=250, anim_frames=self.enemy_anim, speed=8, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2900, y=400, anim_frames=self.enemy_anim, speed=8, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2900, y=600, anim_frames=self.enemy_anim, speed=8, hp=3, can_shoot=True))
        self.enemies.append(Enemy(self.canvas, x=2600, y=250, anim_frames=self.enemy_anim, speed=0, hp=5, enemy_type="data"))
        self.enemies.append(Enemy(self.canvas, x=2600, y=600, anim_frames=self.enemy_anim, speed=0, hp=5, enemy_type="data"))
        self.enemies.append(Enemy(self.canvas, x=1100, y=600, anim_frames=self.enemy_anim, speed=0, hp=5, enemy_type="data"))

        self.siren_enabled = True

        self.canvas.tag_raise(self.player.obj)

# =============================================================================
# [Scene] Hidden Boss: System
# - 3단 구조 맵과 순간이동 패턴을 가진 히든 보스
# =============================================================================
class SystemBossScene(LevelScene):
    def __init__(self, window, manager): 
        super().__init__(window, manager) 
        self.map_width = 1280
        
        try:
            self.bg_img = PhotoImage(file="image/stg_system.png") 
            self.bg_obj = self.canvas.create_image(640, 360, image=self.bg_img)
            self.is_bg_image = True 
        except:
            self.bg_obj = self.canvas.create_rectangle(0, 0, self.map_width, 720, fill="#001133") 
            self.is_bg_image = False
        
        self.floor_obj = self.canvas.create_rectangle(0, 715, self.map_width, 720, fill="#000000", outline="")

        # ---------------------------------------------------------------------
        # [Map Layout] 3-Tier Structure (Void Center)
        # ---------------------------------------------------------------------
        # Tier 3 (Top) : y = 200
        self.map_objects.append(Platform(self.canvas, x=0, y=200, w=500, h=20, color="#004488"))   # L3 Left
        self.map_objects.append(Platform(self.canvas, x=780, y=200, w=500, h=20, color="#004488")) # L3 Right
        
        # Tier 2 (Mid) : y = 450
        self.map_objects.append(Platform(self.canvas, x=0, y=450, w=500, h=20, color="#004488"))   # L2 Left
        self.map_objects.append(Platform(self.canvas, x=780, y=450, w=500, h=20, color="#004488")) # L2 Right
        
        # ---------------------------------------------------------------------
        # [Cover Walls] Shield for Boss
        # ---------------------------------------------------------------------
        self.map_objects.append(Wall(self.canvas, x=900, y=450, w=30, h=270, color="#444444")) # Tier 1 Right
        self.map_objects.append(Wall(self.canvas, x=350, y=200, w=30, h=250, color="#444444")) # Tier 2 Left
        self.map_objects.append(Wall(self.canvas, x=900, y=0, w=30, h=200, color="#444444"))   # Tier 3 Right

        self.enemy_anim = {"walk_R": [], "walk_L": []}
        try:
            frames_R = load_gif_frames("image/char/hidden/fly_R.gif", frame_count=6, scale=6)
            frames_L = load_gif_frames("image/char/hidden/fly_L.gif", frame_count=6, scale=6)
            
            self.enemy_anim["walk_R"] = frames_R
            self.enemy_anim["walk_L"] = frames_L
        except:
            print("[Error] System boss anim load failed")

        # ---------------------------------------------------------------------
        # [Boss Spawn] Teleportation Spots
        # ---------------------------------------------------------------------
        self.boss_spots = [
            (1100, 600), # Spot 1: Tier 1 Right
            (150, 350),  # Spot 2: Tier 2 Left
            (1100, 100)  # Spot 3: Tier 3 Right
        ]
        self.current_spot_idx = 0
        start_x, start_y = self.boss_spots[0]

        # Init System Boss (Gravity Ignored)
        system_boss = Enemy(self.canvas, x=start_x, y=start_y, anim_frames=self.enemy_anim, 
                            speed=0, hp=30, can_shoot=True, is_boss=True, is_system=True)
        self.enemies.append(system_boss)
        
        self.siren_enabled = False
        
        self.canvas.tag_raise(self.player.obj)

    def teleport_system_boss(self, boss):
        """Teleport Boss to Random Spot (Excluding current)"""
        possible_indices = [i for i in range(len(self.boss_spots)) if i != self.current_spot_idx]
        new_idx = random.choice(possible_indices)
        
        self.current_spot_idx = new_idx
        new_x, new_y = self.boss_spots[new_idx]
        
        boss.world_x = new_x
        boss.y = new_y
        
        sound_mgr.play_sfx("sfx_warp.wav")


# =============================================================================
# [Main] Game Manager
# - Application entry point
# - Finite State Machine (FSM) for Scene Management
# =============================================================================
class Game_manager:
    def __init__(self):
        self.window = Tk(); self.window.title("지구는 둥그니까"); self.window.geometry("1280x720"); self.window.resizable(False, False)
        self.scene_idx = 0
        self.lives = 3 
        
        sound_mgr.play_bgm("bgm_main.mp3")

        self.menu = MenuScene(self.window, self)
        self.intro = DialogueScene(self.window, ["text1.png", "text2.png", "text3.png"], "story1.png")
        
        self.stage1 = Stage1Scene(self.window, self)
        self.stage2 = Stage2Scene(self.window, self)
        self.mid_dialogue = DialogueScene(self.window, ["mid_text1.png", "mid_text2.png", "mid_text3.png", "mid_text4.png", "mid_text5.png", "mid_text6.png", "mid_text7.png", "mid_text8.png"], "story_mid.png")
        self.mid_boss = StageMidBossScene(self.window, self)
        self.stage3 = Stage3Scene(self.window, self)
        self.boss = BossScene(self.window)
        self.gameover = GameOverScene(self.window)
        
        # [Content] System Boss Route Scenes
        self.sys_intro = DialogueScene(self.window, ["sys_in_text1.png", "sys_in_text2.png", "sys_in_text3.png", "sys_in_text4.png", "sys_in_text5.png", "sys_in_text6.png", "sys_in_text7.png"], "story_hidden.png") 
        self.system_boss = SystemBossScene(self.window, self)
        self.sys_outro = DialogueScene(self.window, ["sys_out_text1.png", "sys_out_text2.png", "sys_out_text3.png", "sys_out_text4.png", "sys_out_text5.png", "sys_out_text6.png", "sys_out_text7.png", "sys_out_text8.png", "sys_out_text9.png", "sys_out_text10.png", "sys_out_text11.png"], "story_hidden.png") 

        # Scene Registry
        self.scenes = [
            self.menu,          # 0
            self.intro,         # 1
            self.stage1,        # 2
            self.stage2,        # 3
            self.mid_dialogue,  # 4
            self.mid_boss,      # 5
            self.stage3,        # 6
            self.boss,          # 7 (Choice)
            self.gameover,      # 8
            self.sys_intro,     # 9  (Hidden Intro)
            self.system_boss,   # 10 (Hidden Boss)
            self.sys_outro      # 11 (Hidden Outro)
        ]
        self.menu.pack()
        self.window.bind("<KeyRelease>", self.keyReleaseHandler); self.window.bind("<KeyPress>", self.keyPressHandler)
        self.run_game()

    def reset_current_stage(self):
        idx = self.scene_idx
        print(f"[System] Stage Reset (Lives Left: {self.lives})")
        self.scenes[idx].unpack()
        
        if idx == 2: self.stage1 = Stage1Scene(self.window, self); self.scenes[2] = self.stage1
        elif idx == 3: self.stage2 = Stage2Scene(self.window, self); self.scenes[3] = self.stage2
        elif idx == 5: self.mid_boss = StageMidBossScene(self.window, self); self.scenes[5] = self.mid_boss
        elif idx == 6: self.stage3 = Stage3Scene(self.window, self); self.scenes[6] = self.stage3
        elif idx == 10: self.system_boss = SystemBossScene(self.window, self); self.scenes[10] = self.system_boss 
            
        self.scenes[idx].pack()
        self.fade_in_effect(self.scenes[idx].canvas)

    def run_game(self):
        while True:
            try:
                current_scene = self.scenes[self.scene_idx]
                result = None
                if hasattr(current_scene, 'display'): result = current_scene.display()
                if result == "GAME_OVER": self.change_scene(8)
                elif result == "RETRY": self.reset_current_stage()
                self.window.update(); self.window.after(33)
            except TclError as e: print(f"[CRITICAL] App Closed: {e}"); return
            except Exception as e: print(f"[Error] {e}"); return

    def keyPressHandler(self, event):
        current_scene = self.scenes[self.scene_idx]
        if hasattr(current_scene, 'keyPressHandler'): current_scene.keyPressHandler(event)

    def keyReleaseHandler(self, event):
        current_scene = self.scenes[self.scene_idx]
        result = current_scene.keyReleaseHandler(event)
        
        # [State Machine] Scene Transitions
        if self.scene_idx == 0 and result == 0: 
            self.change_scene(1)
        elif self.scene_idx == 1 and result == "NEXT":
            self.change_scene(2); sound_mgr.play_bgm("bgm_stage1.mp3")
        elif self.scene_idx == 2 and result == "CLEARED": 
            self.change_scene(3); sound_mgr.play_bgm("bgm_stage2.mp3")
        elif self.scene_idx == 3 and result == "CLEARED": 
            self.change_scene(4); sound_mgr.play_bgm("bgm_midboss.mp3")
        elif self.scene_idx == 4 and result == "NEXT":
            self.change_scene(5)
        elif self.scene_idx == 5 and result == "CLEARED": 
            self.change_scene(6); sound_mgr.play_bgm("bgm_stage3.mp3")
        elif self.scene_idx == 6 and result == "CLEARED":
            self.change_scene(7); sound_mgr.play_bgm("bgm_boss.mp3")
            
        # [Branch: Endings]
        elif self.scene_idx == 7:
            if result == "ENDING_1":
                self.ending = EndingScene(self.window, 1); self.scenes.append(self.ending); self.change_scene(len(self.scenes)-1)
                sound_mgr.play_bgm("bgm_ending1.mp3")
            elif result == "ENDING_2":
                self.ending = EndingScene(self.window, 2); self.scenes.append(self.ending); self.change_scene(len(self.scenes)-1)
                sound_mgr.play_bgm("bgm_ending2.mp3")
            
            # [Branch: Hidden Route]
            elif result == "HIDDEN_BOSS": 
                print("[System] Core Access Granted...")
                self.change_scene(9) # Go to Hidden Intro
                sound_mgr.play_bgm("bgm_system_intro.mp3") 

        elif self.scene_idx == 9 and result == "NEXT":
            self.change_scene(10) # Hidden Boss Fight
            sound_mgr.play_bgm("bgm_system_boss.mp3") 

        elif self.scene_idx == 10 and result == "SYSTEM_CLEARED":
            self.change_scene(11) # Hidden Outro
            sound_mgr.play_bgm("bgm_system_outro.mp3")

        elif self.scene_idx == 11 and result == "NEXT":
            self.ending = EndingScene(self.window, 3); self.scenes.append(self.ending); self.change_scene(len(self.scenes)-1)
            sound_mgr.play_bgm("bgm_true_ending.mp3") 

        # [Game Over -> Reset]
        elif self.scene_idx == 8 and result == "GO_TO_MENU":
            self.lives = 3 
            self.stage1 = Stage1Scene(self.window, self)
            self.stage2 = Stage2Scene(self.window, self)
            self.mid_boss = StageMidBossScene(self.window, self)
            self.stage3 = Stage3Scene(self.window, self)
            self.system_boss = SystemBossScene(self.window, self)
            
            self.scenes[2] = self.stage1
            self.scenes[3] = self.stage2
            self.scenes[5] = self.mid_boss
            self.scenes[6] = self.stage3
            self.scenes[10] = self.system_boss 
            
            self.intro.current_idx = 0; self.intro.draw_scene() 
            self.mid_dialogue.current_idx = 0; self.mid_dialogue.draw_scene() 
            self.boss.current_idx = 0; self.boss.state = "dialogue"; self.boss.draw_scene()
            self.sys_intro.current_idx = 0; self.sys_intro.draw_scene()
            self.sys_outro.current_idx = 0; self.sys_outro.draw_scene()
            
            self.menu.update_background()
            self.change_scene(0); sound_mgr.play_bgm("bgm_main.mp3")

    def change_scene(self, next_idx):
        self.scenes[self.scene_idx].unpack() 
        self.scene_idx = next_idx            
        self.scenes[self.scene_idx].pack()
        self.fade_in_effect(self.scenes[self.scene_idx].canvas)

    def fade_in_effect(self, canvas):
        try:
            fade_rect = canvas.create_rectangle(0, 0, 1280, 720, fill="black")
            self.window.after(15, lambda: canvas.itemconfigure(fade_rect, stipple="gray75"))
            self.window.after(30, lambda: canvas.itemconfigure(fade_rect, stipple="gray50"))
            self.window.after(45, lambda: canvas.itemconfigure(fade_rect, stipple="gray25"))
            self.window.after(60, lambda: canvas.itemconfigure(fade_rect, stipple="gray12"))
            self.window.after(75, lambda: canvas.delete(fade_rect))
        except: pass

if __name__=='__main__':
    Game_manager()