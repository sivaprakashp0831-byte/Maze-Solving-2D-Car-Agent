# -*- coding: utf-8 -*-
"""
================================================================================
  MAZE SOLVING 2D CAR AGENT - COGNITIVE NAVIGATION SYSTEM v2.1
  Enterprise Autonomous Navigation System | Zero External Dependencies
  Standard Library Only: tkinter, math, time, random, collections
================================================================================
"""
import tkinter as tk
from tkinter import messagebox
import math
import time
import random
from collections import deque

# ── CYBERPUNK PALETTE ────────────────────────────────────────────────────────
C = {
    "bg":     "#0E1117",  # Master dark background
    "panel":  "#1F2937",  # Primary component panel
    "panel2": "#161B22",  # Secondary dark panel
    "cv":     "#111827",  # Viewport canvas
    "bdr":    "#30363D",  # Subtle border line
    "blue":   "#1F6FEB",  # Electric accent blue
    "green":  "#238636",  # Neon success green
    "yel":    "#E3B341",  # Cyber amber yellow
    "red":    "#DA3633",  # Alert red
    "ora":    "#D97706",  # Warning orange
    "th":     "#E6EDF3",  # Primary high-contrast text
    "tm":     "#8B949E",  # Muted secondary text
    "tg":     "#3FB950",  # Bright text green
    "ty":     "#E3B341",  # Bright text yellow
    "tr":     "#F85149",  # Bright text red
    "tb":     "#58A6FF",  # Bright text cyan/blue
    "to":     "#FFA657",  # Bright text orange
    "gl":     "#1C2333",  # Viewport grid line
    "wc":     "#4B5563",  # Wall core
    "wb":     "#6B7280",  # Wall bevel/highlight
    "gf":     "#0D4429",  # Goal fill
    "gb":     "#238636",  # Goal border
    "rd":     "#0D1117",  # Radar background
}

CW, CH = 800, 560
GOAL = (700, 460, 780, 540)
GCX = (GOAL[0] + GOAL[2]) // 2
GCY = (GOAL[1] + GOAL[3]) // 2


# ── MAZE GEOMETRY BUILDERS ───────────────────────────────────────────────────
def _b():
    """Canvas boundary walls with safety margin."""
    return [(8, 8, 792, 8), (792, 8, 792, 552), (792, 552, 8, 552), (8, 552, 8, 8)]


def rect_walls(x1, y1, x2, y2):
    """Generate 4 wall segments for a rectangular obstacle island."""
    return [(x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)]


# ── 9 GUARANTEED SOLVABLE PRESET MAZES ───────────────────────────────────────
# Format: (walls, start_x, start_y, start_heading, level_name)
MAZES = {
    # ═══════════════ EASY STAGE (Corridor Width: 130-160px) ═══════════════
    ("Easy", 1): (
        _b() + [(8, 180, 640, 180), (640, 180, 640, 420), (8, 420, 640, 420)],
        70, 90, 0, "Straight Track"
    ),
    ("Easy", 2): (
        _b() + [(8, 160, 380, 160), (380, 160, 380, 410), (510, 8, 510, 430), (8, 410, 380, 410)],
        70, 80, 0, "Single Corner"
    ),
    ("Easy", 3): (
        _b() + [
            (8, 160, 260, 160), (380, 8, 380, 270), (260, 160, 260, 420),
            (380, 270, 640, 270), (260, 420, 530, 420), (640, 270, 640, 430)
        ],
        70, 80, 0, "Dual Bend Corridor"
    ),

    # ═══════════════ MEDIUM STAGE (Corridor Width: 100-120px) ═════════════
    ("Medium", 1): (
        _b() + [(250, 8, 250, 360), (450, 170, 450, 552), (640, 8, 640, 380)],
        70, 70, 0, "Chicane Loop"
    ),
    ("Medium", 2): (
        _b() + rect_walls(240, 180, 560, 350) + [(8, 130, 160, 130), (8, 410, 160, 410)],
        70, 270, 0, "Split Lanes"
    ),
    ("Medium", 3): (
        _b() + [
            (8, 180, 360, 180), (8, 360, 360, 360),
            (360, 8, 360, 180), (520, 8, 520, 370),
            (360, 360, 360, 460), (520, 460, 680, 460)
        ],
        70, 270, 0, "T-Junction Avoidance"
    ),

    # ═══════════════ HARD STAGE (Corridor Width: 85-105px) ════════════════
    ("Hard", 1): (
        _b() + [
            (8, 120, 680, 120), (120, 230, 792, 230),
            (8, 340, 680, 340), (120, 450, 792, 450)
        ],
        60, 60, 0, "Complex Labyrinth"
    ),
    ("Hard", 2): (
        _b() + [
            (8, 150, 400, 150),
            (700, 8, 700, 220), (480, 220, 700, 220),
            (400, 150, 400, 360), (520, 220, 520, 420),
            (8, 360, 400, 360), (520, 420, 680, 420)
        ],
        60, 70, 0, "Decoy Corridors"
    ),
    ("Hard", 3): (
        _b() + rect_walls(180, 70, 260, 190) + rect_walls(180, 290, 260, 420) +
               rect_walls(380, 70, 460, 200) + rect_walls(380, 300, 460, 440) +
               rect_walls(580, 70, 660, 220) + rect_walls(580, 320, 660, 430),
        60, 60, 0, "Dense Obstacle Grid"
    ),
}


# ── RAY-CASTING & CONTINUOUS COLLISION RESOLUTION ────────────────────────────
def dist_pt_seg(px, py, x1, y1, x2, y2):
    """Euclidean distance and closest point from (px, py) to line segment (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1), x1, y1
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    nx, ny = x1 + t * dx, y1 + t * dy
    return math.hypot(px - nx, py - ny), nx, ny


def resolve_collision(x, y, walls, radius=13):
    """
    Physical circle-segment collision solver.
    Guarantees the car never clips or phases through walls.
    """
    hit = False
    for _ in range(2):
        for w in walls:
            d, nx, ny = dist_pt_seg(x, y, *w)
            if d < radius:
                hit = True
                if d < 1e-4:
                    x += radius
                    y += radius
                else:
                    ux = (x - nx) / d
                    uy = (y - ny) / d
                    x = nx + ux * radius
                    y = ny + uy * radius
    return x, y, hit


def _seg_hit(rx, ry, rdx, rdy, x1, y1, x2, y2):
    """Ray-segment intersection test returning ray distance t or None."""
    dx, dy = x2 - x1, y2 - y1
    d = rdx * dy - rdy * dx
    if abs(d) < 1e-10:
        return None
    t = ((x1 - rx) * dy - (y1 - ry) * dx) / d
    u = ((x1 - rx) * rdy - (y1 - ry) * rdx) / d
    return t if t >= 0 and 0 <= u <= 1 else None


def cast_ray(cx, cy, a_rad, walls, md=600):
    """Cast ray from (cx, cy) in direction a_rad against walls."""
    rdx, rdy = math.cos(a_rad), math.sin(a_rad)
    best = md
    for w in walls:
        t = _seg_hit(cx, cy, rdx, rdy, *w)
        if t is not None and t < best:
            best = t
    return cx + rdx * best, cy + rdy * best, best


# ── COGNITIVE CAR AGENT (Spatial Heatmap + Dead-End Recovery) ─────────────────
class CarAgent:
    NRAYS = 32
    CW, CH = 22, 34
    VMAX = 4.2
    VMIN = 0.8
    ACCEL = 0.22
    DECEL = 0.30
    SMAX = 7.0
    CELL = 28
    HLEN = 36
    STUCK_SPAN = 28

    def __init__(self, x, y, h=0.0):
        self.x = float(x)
        self.y = float(y)
        self.heading = float(h)
        self.speed = 0.0
        self.steer = 0.0
        self.state = "IDLE"
        self.steps = 0
        self.wall_hits = 0
        self.evasive = 0
        self.safe_pct = 100.0
        self.rays = []
        self.heat = {}
        self.hist = deque(maxlen=self.HLEN)
        self.escape_timer = 0

    def reset(self, x, y, h=0.0):
        self.__init__(x, y, h)

    def _gp(self):
        return (int(self.x / self.CELL), int(self.y / self.CELL))

    def _heat_at(self, rel_deg, dist=45):
        a = math.radians(self.heading + rel_deg)
        gp = (
            int((self.x + math.cos(a) * dist) / self.CELL),
            int((self.y + math.sin(a) * dist) / self.CELL),
        )
        return self.heat.get(gp, 0)

    def _is_stuck(self):
        if len(self.hist) < self.HLEN:
            return False
        pts = list(self.hist)
        span = max(
            max(p[0] for p in pts) - min(p[0] for p in pts),
            max(p[1] for p in pts) - min(p[1] for p in pts),
        )
        return span < self.STUCK_SPAN

    def _sector_min(self, rs, re):
        v = []
        for _, _, d, a in self.rays:
            r = (a - self.heading + 360) % 360
            ok = (rs <= r < re) if rs < re else (r >= rs or r < re)
            if ok:
                v.append(d)
        return min(v) if v else 600.0

    def sense(self, walls):
        step = 360.0 / self.NRAYS
        self.rays = []
        for i in range(self.NRAYS):
            a = (self.heading + i * step) % 360
            hx, hy, d = cast_ray(self.x, self.y, math.radians(a), walls)
            self.rays.append((hx, hy, d, a))

    def act(self, gx, gy, walls, spd_scale=1.0):
        """Execute one simulation step with memory-guided cognitive navigation."""
        gp = self._gp()
        self.heat[gp] = self.heat.get(gp, 0) + 1
        self.hist.append((self.x, self.y))

        # Sector distances
        front = self._sector_min(345, 15)
        frl = self._sector_min(300, 345)
        frr = self._sector_min(15, 60)
        left = self._sector_min(240, 300)
        right = self._sector_min(60, 120)

        # ── DEAD-END & STUCK DETECTION ───────────────────────────────────────
        is_trapped = front < 50 and frl < 55 and frr < 55 and (left < 65 or right < 65)
        if (self._is_stuck() or is_trapped) and self.escape_timer <= 0:
            self.escape_timer = 38
            self.evasive += 1
            # Search open rear hemisphere (90° to 270°)
            rear_rays = [
                (d, a)
                for _, _, d, a in self.rays
                if 90 <= ((a - self.heading + 360) % 360) <= 270
            ]
            if rear_rays:
                _, best_a = max(rear_rays, key=lambda item: item[0])
                self.heading = best_a
            else:
                self.heading = (self.heading + 180) % 360
            self.speed = self.VMIN + 0.8
            self.hist.clear()
            self.state = "UNSTUCK_ESCAPE"
            return (
                f"> 2D Car Agent: [UNSTUCK_ESCAPE] 180° Dead-End Recovery | "
                f"Evasive#{self.evasive} | Spd={self.speed:.2f}"
            )

        # ── ESCAPE PHASE (Prioritizes Open Corridors) ─────────────────────────
        if self.escape_timer > 0:
            self.escape_timer -= 1
            self.state = "UNSTUCK_ESCAPE"
            self.speed = min(self.VMAX * 0.75 * spd_scale, self.speed + self.ACCEL)
            if frl < frr:
                self.steer = min(self.steer + self.SMAX * 0.7, self.SMAX)
            else:
                self.steer = max(self.steer - self.SMAX * 0.7, -self.SMAX)
            self._move_and_resolve(walls)
            return (
                f"> 2D Car Agent: [UNSTUCK_ESCAPE] Escaping Pocket "
                f"({self.escape_timer}f remaining) | Spd={self.speed:.2f}"
            )

        # ── REGULAR COGNITIVE NAVIGATION ─────────────────────────────────────
        target_ang = math.degrees(math.atan2(gy - self.y, gx - self.x))
        ad = ((target_ang - self.heading) + 360) % 360
        if ad > 180:
            ad -= 360

        hl = self._heat_at(270)
        hr = self._heat_at(90)
        hfl = self._heat_at(315)
        hfr = self._heat_at(45)

        # State 1: Emergency Evade (Obstacle within braking distance)
        if front < 48:
            self.state = "EMERGENCY_EVADE"
            self.evasive += 1
            self.speed = max(self.VMIN, self.speed - self.DECEL * 1.5)
            score_right = right / (1.0 + hr * 0.5)
            score_left = left / (1.0 + hl * 0.5)
            if score_right >= score_left:
                self.steer = min(self.steer + self.SMAX * 0.95, self.SMAX)
                ds = "RIGHT"
            else:
                self.steer = max(self.steer - self.SMAX * 0.95, -self.SMAX)
                ds = "LEFT"
            log = (
                f"> 2D Car Agent: [EMERGENCY_EVADE] Front={front:.0f}px → STEER {ds} | "
                f"Heat(L={hl},R={hr}) | Spd={self.speed:.2f}"
            )

        # State 2: Wall Avoidance (Front-diagonal clearance control)
        elif min(frl, frr) < 55 or front < 80:
            self.state = "WALL_AVOIDANCE"
            self.speed = max(self.VMIN + 0.4, self.speed - self.DECEL * 0.5)
            score_right = frr / (1.0 + hfr * 0.4)
            score_left = frl / (1.0 + hfl * 0.4)
            if score_left < score_right:
                self.steer = min(self.steer + self.SMAX * 0.7, self.SMAX)
                ds = "RIGHT"
            else:
                self.steer = max(self.steer - self.SMAX * 0.7, -self.SMAX)
                ds = "LEFT"
            log = (
                f"> 2D Car Agent: [WALL_AVOIDANCE] Clearance: L={frl:.0f}px R={frr:.0f}px → "
                f"Steer {ds} | Spd={self.speed:.2f}"
            )

        # State 3: Lane Centering (Tunnel corridor balancing)
        elif min(left, right) < 50:
            self.state = "LANE_CENTERING"
            self.speed = min(self.VMAX * spd_scale, self.speed + self.ACCEL)
            corr = (right - left) * 0.08 + (hl - hr) * 0.05
            self.steer = max(-self.SMAX, min(self.SMAX, corr))
            log = (
                f"> 2D Car Agent: [LANE_CENTERING] Corridors: L={left:.0f}px R={right:.0f}px | "
                f"Steer={self.steer:+.1f}° | Spd={self.speed:.2f}"
            )

        # State 4: Goal Pursuit (Heat-penalized goal seeking)
        else:
            self.state = "PURSUING_GOAL"
            self.speed = min(self.VMAX * spd_scale, self.speed + self.ACCEL * 1.2)
            heat_bias = (hfl - hfr) * 0.1
            target_steer = max(-self.SMAX, min(self.SMAX, ad * 0.3 + heat_bias))
            self.steer = self.steer * 0.5 + target_steer * 0.5
            log = (
                f"> 2D Car Agent: [PURSUING_GOAL] Goal bearing Δhdg={ad:+.1f}° | "
                f"HeatBias={heat_bias:+.2f} | Spd={self.speed:.2f}"
            )

        self._move_and_resolve(walls)
        return log

    def _move_and_resolve(self, walls):
        self.heading = (self.heading + self.steer) % 360
        rad = math.radians(self.heading)
        self.x += math.cos(rad) * self.speed
        self.y += math.sin(rad) * self.speed

        # Zero-clipping physical collision resolution
        self.x, self.y, hit = resolve_collision(self.x, self.y, walls)
        self.steps += 1
        if hit:
            self.wall_hits += 1
            self.speed = max(self.VMIN, self.speed * 0.7)

        self.safe_pct = max(
            0.0, round(100.0 * (1.0 - self.wall_hits / max(1, self.steps)), 1)
        )


# ── MAIN APPLICATION WINDOW ──────────────────────────────────────────────────
class App:
    TICK_MS = 40
    LOG_MAX = 350

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MAZE SOLVING 2D CAR AGENT | Cognitive Autonomous System v2.1")
        self.root.geometry("1280x780")
        self.root.resizable(False, False)
        self.root.configure(bg=C["bg"])

        # Core State
        self.running = False
        self.custom_mode = False
        self.drawing = False
        self.draw_start = (0, 0)
        self.custom_walls = []
        self.walls = []
        self.stage = "Easy"
        self.level = 1
        self.speed_scale = 1.0
        self.goal_reached = False
        self._after_id = None
        self._frame = 0
        self._radar_sw = 0.0
        self._log_state = ""
        self._log_time = 0.0
        self._log_lines = 0
        self.car = CarAgent(70, 90, 0)

        self._build_ui()
        self._load("Easy", 1)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(800, lambda: self.root.attributes("-topmost", False))
        self.root.after(500, self._start)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.mainloop()

    # ─────────────────────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = tk.Frame(self.root, bg=C["bg"], padx=6, pady=6)
        outer.pack(fill="both", expand=True)

        # Header Title Bar
        tb = tk.Frame(outer, bg=C["panel2"], height=32, highlightbackground=C["bdr"], highlightthickness=1)
        tb.pack(fill="x", pady=(0, 5))
        tb.pack_propagate(False)

        tk.Label(
            tb,
            text="◈  MAZE SOLVING 2D CAR AGENT  |  Autonomous Cognitive Navigation Engine v2.1",
            bg=C["panel2"],
            fg=C["blue"],
            font=("Consolas", 11, "bold"),
        ).pack(side="left", padx=10)

        self._badge = tk.Label(
            tb, text="● STANDBY", bg=C["panel2"], fg=C["tm"], font=("Consolas", 9, "bold")
        )
        self._badge.pack(side="right", padx=10)

        body = tk.Frame(outer, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_left(body)
        self._build_right(body)

    # ─────────────────────────────────────────────────────────────────────────
    def _build_left(self, parent):
        lp = tk.Frame(parent, bg=C["panel"], highlightbackground=C["bdr"], highlightthickness=1)
        lp.pack(side="left", fill="y", padx=(0, 5))

        # Viewport Header
        ph = tk.Frame(lp, bg=C["panel2"], height=34)
        ph.pack(fill="x")
        ph.pack_propagate(False)
        tk.Label(
            ph, text="  NAVIGATION VIEWPORT (800x560)", bg=C["panel2"], fg=C["th"], font=("Consolas", 10, "bold")
        ).pack(side="left", padx=8)
        tk.Label(
            ph, text="LiDAR: 32 Rays • Continuous Collision Resolution  ", bg=C["panel2"], fg=C["tm"], font=("Consolas", 8)
        ).pack(side="right")

        # Viewport Canvas
        cf = tk.Frame(lp, bg=C["bdr"], padx=1, pady=1)
        cf.pack(padx=7, pady=(4, 5))
        self.canvas = tk.Canvas(cf, width=CW, height=CH, bg=C["cv"], highlightthickness=0, cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._cv_click)
        self.canvas.bind("<B1-Motion>", self._cv_drag)
        self.canvas.bind("<ButtonRelease-1>", self._cv_release)

        # Control Panel
        ctrl = tk.Frame(lp, bg=C["panel2"], highlightbackground=C["bdr"], highlightthickness=1)
        ctrl.pack(fill="x", padx=7, pady=(0, 5))

        # Row 1: Stage Selectors + Custom Mode
        sr = tk.Frame(ctrl, bg=C["panel2"])
        sr.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(sr, text="STAGE:", bg=C["panel2"], fg=C["tm"], font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 6))

        self._stg_btns = {}
        for stg, col in [("Easy", C["green"]), ("Medium", C["yel"]), ("Hard", C["red"])]:
            b = tk.Button(
                sr,
                text=stg,
                width=8,
                command=lambda s=stg: self._set_stage(s),
                bg=C["panel"],
                fg=C["th"],
                font=("Consolas", 9, "bold"),
                relief="flat",
                padx=6,
                pady=3,
                activebackground=col,
                cursor="hand2",
                bd=0,
                highlightbackground=C["bdr"],
                highlightthickness=1,
            )
            b.pack(side="left", padx=2)
            self._stg_btns[stg] = (b, col)

        tk.Frame(sr, bg=C["bdr"], width=1).pack(side="left", fill="y", padx=6)
        self._cust_btn = tk.Button(
            sr,
            text="✏ Custom Draw",
            width=13,
            command=self._activate_custom,
            bg="#4B5563",
            fg="white",
            font=("Consolas", 9, "bold"),
            relief="flat",
            padx=6,
            pady=3,
            activebackground="#6B7280",
            cursor="hand2",
            bd=0,
        )
        self._cust_btn.pack(side="left", padx=2)

        # Row 2: Sub-Level Selectors (L1, L2, L3)
        lr = tk.Frame(ctrl, bg=C["panel2"])
        lr.pack(fill="x", padx=8, pady=(2, 3))
        tk.Label(lr, text="LEVEL:", bg=C["panel2"], fg=C["tm"], font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 6))

        self._lvl_btns = {}
        for lvl in range(1, 4):
            b = tk.Button(
                lr,
                text=f"L{lvl}",
                width=5,
                command=lambda l=lvl: self._set_level(l),
                bg=C["panel"],
                fg=C["th"],
                font=("Consolas", 9, "bold"),
                relief="flat",
                padx=4,
                pady=3,
                activebackground=C["blue"],
                cursor="hand2",
                bd=0,
                highlightbackground=C["bdr"],
                highlightthickness=1,
            )
            b.pack(side="left", padx=2)
            self._lvl_btns[lvl] = b

        self._lvl_lbl = tk.Label(lr, text="Straight Track", bg=C["panel2"], fg=C["tb"], font=("Consolas", 8, "bold"))
        self._lvl_lbl.pack(side="left", padx=(12, 0))

        # Row 3: Run / Reset / SPEED CONTROL SLIDER
        rr = tk.Frame(ctrl, bg=C["panel2"])
        rr.pack(fill="x", padx=8, pady=(3, 7))

        self._run_btn = tk.Button(
            rr,
            text="▶  RUN AI",
            width=11,
            command=self._toggle_run,
            bg=C["blue"],
            fg="white",
            font=("Consolas", 9, "bold"),
            relief="flat",
            padx=8,
            pady=4,
            activebackground="#388BFD",
            cursor="hand2",
            bd=0,
        )
        self._run_btn.pack(side="left", padx=2)

        tk.Button(
            rr,
            text="↺  RESET",
            width=9,
            command=self._reset,
            bg=C["panel"],
            fg=C["th"],
            font=("Consolas", 9, "bold"),
            relief="flat",
            padx=6,
            pady=4,
            activebackground=C["bdr"],
            cursor="hand2",
            bd=0,
            highlightbackground=C["bdr"],
            highlightthickness=1,
        ).pack(side="left", padx=3)

        tk.Frame(rr, bg=C["bdr"], width=1).pack(side="left", fill="y", padx=8)

        # SPEED CONTROL SLIDER
        tk.Label(rr, text="SPEED CONTROL", bg=C["panel2"], fg=C["ty"], font=("Consolas", 8, "bold")).pack(
            side="left", padx=(0, 6)
        )
        self._spd_var = tk.DoubleVar(value=1.0)
        self._spd_lbl = tk.Label(rr, text="1.0×", bg=C["panel2"], fg=C["ty"], font=("Consolas", 9, "bold"), width=4)
        self._spd_lbl.pack(side="right", padx=4)

        tk.Scale(
            rr,
            from_=0.2,
            to=3.0,
            resolution=0.1,
            orient="horizontal",
            variable=self._spd_var,
            command=self._spd_chg,
            bg=C["panel2"],
            fg=C["th"],
            troughcolor=C["bdr"],
            highlightthickness=0,
            activebackground=C["blue"],
            length=210,
            sliderlength=14,
            showvalue=False,
            relief="flat",
        ).pack(side="left")

        self._refresh_stage_btns()
        self._refresh_lvl_btns()

    # ─────────────────────────────────────────────────────────────────────────
    def _build_right(self, parent):
        rp = tk.Frame(parent, bg=C["panel"], highlightbackground=C["bdr"], highlightthickness=1)
        rp.pack(side="left", fill="both", expand=True)

        rh = tk.Frame(rp, bg=C["panel2"], height=34)
        rh.pack(fill="x")
        rh.pack_propagate(False)
        tk.Label(rh, text="◈  COGNITIVE INSIGHTS SUITE", bg=C["panel2"], fg=C["blue"], font=("Consolas", 10, "bold")).pack(
            side="left", padx=10
        )

        self._build_radar(rp)
        self._build_peas(rp)
        self._build_log(rp)

    def _build_radar(self, p):
        sec = self._sec(p, "[ FRONT-VIEW RADAR VECTOR ]")
        rf = tk.Frame(sec, bg=C["bdr"], padx=1, pady=1)
        rf.pack(padx=6, pady=(0, 4), fill="x")
        self.rc = tk.Canvas(rf, width=420, height=124, bg=C["rd"], highlightthickness=0)
        self.rc.pack(fill="x")
        self._radar_idle()

    def _build_peas(self, p):
        sec = self._sec(p, "[ LIVE PEAS METRIC TABLE ]")
        g = tk.Frame(sec, bg=C["panel"])
        g.pack(fill="x", padx=8, pady=(2, 4))
        rows = [
            ("PERF", "Performance", "Safety: 100%  |  Steps: 0", C["tg"]),
            ("ENV", "Environment", "Easy L1 — Straight Track", C["tg"]),
            ("ACT", "Actuator State", "IDLE (0.0 px/f) | Steer: 0.0°", C["tb"]),
            ("SENS", "Sensor Array", "ACTIVE (360° LiDAR, 32 Rays)", C["tg"]),
            ("EVAD", "Evasive Warns", "0 triggers logged", C["tg"]),
            ("MEM", "Memory/Heat", "Cells: 0 | Stuck escapes: 0", C["to"]),
        ]
        self._peas = {}
        for i, (k, lbl, val, col) in enumerate(rows):
            tk.Label(g, text=f"  {lbl}:", bg=C["panel"], fg=C["tm"], font=("Consolas", 9), anchor="w", width=18).grid(
                row=i, column=0, sticky="w", pady=1
            )
            v = tk.Label(g, text=val, bg=C["panel"], fg=col, font=("Consolas", 9, "bold"), anchor="w")
            v.grid(row=i, column=1, sticky="w", padx=4, pady=1)
            self._peas[k] = v

    def _build_log(self, p):
        sec = self._sec(p, "[ COGNITIVE THINKING LOG ]")
        sec.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        lw = tk.Frame(sec, bg=C["panel2"], highlightbackground=C["bdr"], highlightthickness=1)
        lw.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        vsb = tk.Scrollbar(lw, orient="vertical", bg=C["panel2"], troughcolor=C["bdr"])
        vsb.pack(side="right", fill="y")

        self.log = tk.Text(
            lw,
            bg=C["panel2"],
            fg=C["tm"],
            font=("Consolas", 7),
            insertbackground=C["th"],
            selectbackground=C["blue"],
            relief="flat",
            wrap="word",
            yscrollcommand=vsb.set,
            state="disabled",
            cursor="arrow",
        )
        self.log.pack(fill="both", expand=True, padx=2, pady=2)
        vsb.config(command=self.log.yview)

        for tag, col in [
            ("E", C["tr"]),
            ("A", C["to"]),
            ("G", C["tg"]),
            ("L", C["tb"]),
            ("U", C["ty"]),
            ("I", C["tm"]),
        ]:
            self.log.tag_config(tag, foreground=col)

        self._xlog("> System online. Cognitive Navigation Engine v2.1 initialized.", "I")
        self._xlog("> Spatial Heatmap: 28 px grid | Continuous collision resolution active.", "I")
        self._xlog("> Select Stage -> Level -> RUN AI to begin autonomous navigation.", "I")

    def _sec(self, parent, title):
        f = tk.Frame(parent, bg=C["panel"], highlightbackground=C["bdr"], highlightthickness=1)
        f.pack(fill="x", padx=5, pady=2)
        tk.Label(f, text=f"  {title}", bg=C["panel"], fg=C["ty"], font=("Consolas", 8, "bold"), anchor="w").pack(
            fill="x", pady=(4, 2), padx=2
        )
        return f

    # ─────────────────────────────────────────────────────────────────────────
    # SELECTION & STYLING
    # ─────────────────────────────────────────────────────────────────────────
    def _refresh_stage_btns(self):
        for s, (b, col) in self._stg_btns.items():
            if s == self.stage and not self.custom_mode:
                b.config(bg=col, fg="white")
            else:
                b.config(bg=C["panel"], fg=C["th"])
        self._cust_btn.config(bg=C["blue"] if self.custom_mode else "#4B5563")

    def _refresh_lvl_btns(self):
        for l, b in self._lvl_btns.items():
            if l == self.level and not self.custom_mode:
                b.config(bg=C["blue"], fg="white")
            else:
                b.config(bg=C["panel"], fg=C["th"])

    def _set_stage(self, s):
        self.stage = s
        self.level = 1
        self.custom_mode = False
        self.canvas.config(cursor="crosshair")
        self._refresh_stage_btns()
        self._refresh_lvl_btns()
        self._load(s, 1)

    def _set_level(self, l):
        if self.custom_mode:
            return
        self.level = l
        self._refresh_lvl_btns()
        self._load(self.stage, l)

    def _load(self, stage, level):
        self._stop()
        key = (stage, level)
        if key not in MAZES:
            return
        walls, sx, sy, sh, name = MAZES[key]
        self.walls = list(walls)
        self.car.reset(sx, sy, sh)
        self.goal_reached = False
        self._badge.config(text="● STANDBY", fg=C["tm"])
        self._lvl_lbl.config(text=name)
        self._peas["ENV"].config(text=f"{stage} L{level} — {name}", fg=C["tg"])
        self._peas["EVAD"].config(text="0 triggers logged", fg=C["tg"])
        self._peas["MEM"].config(text="Cells: 0 | Stuck escapes: 0", fg=C["to"])
        self._xlog(f"> [{stage} L{level}] {name} loaded. Car @ ({sx},{sy}) hdg={sh}°", "I")
        self._draw()
        self._upd_peas()

    def _activate_custom(self):
        self._stop()
        self.custom_mode = True
        self.walls = list(_b())
        self.custom_walls = []
        self.car.reset(80, 80, 0)
        self.goal_reached = False
        self.canvas.config(cursor="pencil")
        self._badge.config(text="● DRAW MODE", fg=C["ty"])
        self._refresh_stage_btns()
        self._peas["ENV"].config(text="Custom — Draw walls on canvas", fg=C["ty"])
        self._xlog("> Custom Draw active. Click & drag on canvas to place walls.", "I")
        self._draw()

    # ─────────────────────────────────────────────────────────────────────────
    # CANVAS EVENTS (Custom Draw)
    # ─────────────────────────────────────────────────────────────────────────
    def _cv_click(self, e):
        if self.custom_mode and not self.running:
            self.drawing = True
            self.draw_start = (e.x, e.y)

    def _cv_drag(self, e):
        if self.custom_mode and self.drawing:
            self.canvas.delete("prev")
            x1, y1 = self.draw_start
            self.canvas.create_line(x1, y1, e.x, e.y, fill=C["wb"], width=3, tags="prev", dash=(6, 3))

    def _cv_release(self, e):
        if self.custom_mode and self.drawing:
            self.drawing = False
            self.canvas.delete("prev")
            x1, y1 = self.draw_start
            x2, y2 = e.x, e.y
            if abs(x2 - x1) + abs(y2 - y1) > 8:
                self.walls.append((x1, y1, x2, y2))
                self.custom_walls.append((x1, y1, x2, y2))
                self._xlog(f"> Wall placed: ({x1},{y1}) -> ({x2},{y2}) | Total: {len(self.walls)}", "I")
            self._draw()

    # ─────────────────────────────────────────────────────────────────────────
    # SIMULATION CONTROLS
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_run(self):
        if self.goal_reached:
            return
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self.running = True
        self._run_btn.config(text="⏸  PAUSE", bg="#6B7280")
        self._badge.config(text="● RUNNING", fg=C["tg"])
        self._xlog("> AI Cognitive Engine engaged. Autonomous drive active.", "G")
        self._tick()

    def _stop(self):
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._run_btn.config(text="▶  RUN AI", bg=C["blue"])
        if not self.goal_reached:
            self._badge.config(text="● PAUSED", fg=C["ty"])

    def _reset(self):
        self._stop()
        if self.custom_mode:
            self.walls = list(_b()) + list(self.custom_walls)
            self.car.reset(80, 80, 0)
        else:
            self._load(self.stage, self.level)
            return
        self.goal_reached = False
        self._badge.config(text="● STANDBY", fg=C["tm"])
        self._xlog("> Simulation reset. Car repositioned.", "I")
        self._draw()
        self._upd_peas()

    def _spd_chg(self, v):
        self.speed_scale = float(v)
        self._spd_lbl.config(text=f"{float(v):.1f}×")

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN SIMULATION TICK
    # ─────────────────────────────────────────────────────────────────────────
    def _tick(self):
        if not self.running:
            return
        car = self.car
        car.sense(self.walls)
        log = car.act(GCX, GCY, self.walls, self.speed_scale)
        car.x = max(18, min(CW - 18, car.x))
        car.y = max(18, min(CH - 18, car.y))

        self._draw()
        self._upd_peas()
        self._upd_radar()

        # Throttled logging
        tmap = {
            "EMERGENCY": "E",
            "WALL_AVOID": "A",
            "LANE_CENTER": "L",
            "PURSUING": "G",
            "UNSTUCK": "U",
        }
        tag = next((v for k, v in tmap.items() if k in log), "I")
        self._maybe_log(log, tag)
        self._frame += 1

        if self._goal_check():
            self._goal_win()
            return

        delay = max(8, int(self.TICK_MS / max(0.1, self.speed_scale)))
        self._after_id = self.root.after(delay, self._tick)

    # ─────────────────────────────────────────────────────────────────────────
    # LOG THROTTLING
    # ─────────────────────────────────────────────────────────────────────────
    def _maybe_log(self, text, tag):
        now = time.time()
        prefix = text[:45]
        if prefix != self._log_state:
            self._log_state = prefix
            self._log_time = now
            self._xlog(text, tag)
        elif now - self._log_time >= 0.38:
            self._log_time = now
            self._xlog(text, tag)

    def _xlog(self, text, tag="I"):
        self.log.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log.insert("end", f"[{ts}] {text}\n", tag)
        self._log_lines += 1
        if self._log_lines > self.LOG_MAX:
            self.log.delete("1.0", "60.0")
            self._log_lines -= 60
        self.log.see("end")
        self.log.config(state="disabled")

    # ─────────────────────────────────────────────────────────────────────────
    # GOAL CHECK & VICTORY
    # ─────────────────────────────────────────────────────────────────────────
    def _goal_check(self):
        return GOAL[0] < self.car.x < GOAL[2] and GOAL[1] < self.car.y < GOAL[3]

    def _goal_win(self):
        self._stop()
        self.goal_reached = True
        self._badge.config(text="★ GOAL REACHED!", fg=C["tg"])
        car = self.car
        self._xlog(
            f"> ★ GOAL REACHED! Steps={car.steps} Safety={car.safe_pct}% "
            f"WallHits={car.wall_hits} Evasive={car.evasive}",
            "G",
        )
        self._draw()
        messagebox.showinfo(
            "★  GOAL REACHED!",
            f"Maze solved successfully!\n\n"
            f"  Steps taken    : {car.steps}\n"
            f"  Safety score   : {car.safe_pct}%\n"
            f"  Wall contacts  : {car.wall_hits}\n"
            f"  Evasive moves  : {car.evasive}\n"
            f"  Cells visited  : {len(car.heat)}\n"
            f"  Preset Level   : {self.stage} L{self.level}\n\n"
            f"Press  ↺ RESET  or pick another level to run again.",
        )

    # ─────────────────────────────────────────────────────────────────────────
    # VIEWPORT RENDERING ENGINE
    # ─────────────────────────────────────────────────────────────────────────
    def _draw(self):
        cv = self.canvas
        cv.delete("all")
        self._d_grid(cv)
        self._d_heat(cv)
        self._d_trail(cv)
        self._d_goal(cv)
        self._d_walls(cv)
        self._d_rays(cv)
        self._d_car(cv)

    def _d_grid(self, cv):
        for x in range(0, CW + 1, 40):
            cv.create_line(x, 0, x, CH, fill=C["gl"], width=1)
        for y in range(0, CH + 1, 40):
            cv.create_line(0, y, CW, y, fill=C["gl"], width=1)

    def _d_heat(self, cv):
        h = self.car.heat
        if not h:
            return
        mx = max(h.values())
        cell = CarAgent.CELL
        if mx < 2:
            return
        for (gx, gy), cnt in h.items():
            if cnt < 2:
                continue
            px = gx * cell + cell // 2
            py = gy * cell + cell // 2
            t = min(cnt / mx, 1.0)
            r = int(190 * t)
            g2 = int(50 * (1 - t))
            col = f"#{r:02x}{g2:02x}00"
            sz = max(2, int(7 * t))
            cv.create_oval(px - sz, py - sz, px + sz, py + sz, fill=col, outline="", stipple="gray25")

    def _d_trail(self, cv):
        pts = list(self.car.hist)
        n = len(pts)
        if n < 2:
            return
        for i, (px, py) in enumerate(pts):
            a = (i + 1) / n
            b = int(220 * a)
            cv.create_oval(px - 1.5, py - 1.5, px + 1.5, py + 1.5, fill=f"#00{b:02x}{b:02x}", outline="")

    def _d_goal(self, cv):
        gx1, gy1, gx2, gy2 = GOAL
        for i in range(4, 0, -1):
            e = i * 3
            shd = ["#061710", "#0A2318", "#0D2E20", "#104028"]
            cv.create_rectangle(gx1 - e, gy1 - e, gx2 + e, gy2 + e, fill=shd[i - 1], outline="")
        cv.create_rectangle(gx1, gy1, gx2, gy2, fill=C["gf"], outline=C["gb"], width=2)
        p = 0.5 + 0.5 * math.sin(self._frame * 0.16)
        gi = int(80 + 100 * p)
        cv.create_text((gx1 + gx2) // 2, (gy1 + gy2) // 2 - 7, text="GOAL", fill=f"#00{gi:02x}00", font=("Consolas", 9, "bold"))
        cv.create_text((gx1 + gx2) // 2, (gy1 + gy2) // 2 + 7, text="ZONE", fill=C["tg"], font=("Consolas", 8, "bold"))

    def _d_walls(self, cv):
        for x1, y1, x2, y2 in self.walls:
            cv.create_line(x1, y1, x2, y2, fill="#080C14", width=7, capstyle="round")
            cv.create_line(x1, y1, x2, y2, fill=C["wc"], width=3.0, capstyle="round")
            cv.create_line(x1, y1, x2, y2, fill=C["wb"], width=0.8, capstyle="round")

    def _d_rays(self, cv):
        car = self.car
        if not car.rays:
            return
        for hx, hy, dist, a_deg in car.rays:
            rel = ((a_deg - car.heading) + 360) % 360
            if rel > 180:
                rel -= 360
            fwd = -30 <= rel <= 30
            col = C["yel"] if fwd else C["ora"]
            lw = 1.2 if fwd else 0.6
            cv.create_line(car.x, car.y, hx, hy, fill=col, width=lw, stipple="gray50")
            if dist < 590:
                r = 2.8 if fwd else 1.6
                hc = C["red"] if dist < 45 else (C["yel"] if fwd else C["ora"])
                cv.create_oval(hx - r, hy - r, hx + r, hy + r, fill=hc, outline="")

    def _d_car(self, cv):
        car = self.car
        rad = math.radians(car.heading)
        fwd = (math.cos(rad), math.sin(rad))
        perp = (math.cos(rad + math.pi / 2), math.sin(rad + math.pi / 2))
        hw = car.CW / 2
        hl = car.CH / 2

        def pt(lx, ly):
            return (car.x + fwd[0] * lx + perp[0] * ly, car.y + fwd[1] * lx + perp[1] * ly)

        corners = [pt(hl, hw), pt(hl, -hw), pt(-hl, -hw), pt(-hl, hw)]
        flat = [v for p in corners for v in p]

        # Drop shadow & chassis
        shd = [(x + 3, y + 3) for x, y in corners]
        cv.create_polygon(*[v for p in shd for v in p], fill="#050811", outline="")
        cv.create_polygon(*flat, fill=C["blue"], outline=C["tb"], width=1.5)

        # Cockpit windshield
        roof = [
            pt(hl * 0.5, hw * 0.55),
            pt(hl * 0.5, -hw * 0.55),
            pt(-hl * 0.3, -hw * 0.55),
            pt(-hl * 0.3, hw * 0.55),
        ]
        cv.create_polygon(*[v for p in roof for v in p], fill=C["tb"], outline="#A0C4FF", width=0.8)

        # Twin Headlights
        for ly in [hw * 0.45, -hw * 0.45]:
            hx2, hy2 = pt(hl, ly)
            bx, by = pt(hl + 18, ly)
            cv.create_oval(hx2 - 3, hy2 - 3, hx2 + 3, hy2 + 3, fill="#FFFDE0", outline=C["yel"])
            cv.create_line(hx2, hy2, bx, by, fill="#FFFDE0", width=1, stipple="gray25")

        # 4 Alloy Wheels
        for lx, ly in [
            (hl * 0.68, hw * 1.05),
            (hl * 0.68, -hw * 1.05),
            (-hl * 0.68, hw * 1.05),
            (-hl * 0.68, -hw * 1.05),
        ]:
            wx, wy = pt(lx, ly)
            cv.create_oval(wx - 4, wy - 4, wx + 4, wy + 4, fill="#1A1A2E", outline=C["yel"], width=1.4)
            cv.create_oval(wx - 1.8, wy - 1.8, wx + 1.8, wy + 1.8, fill=C["yel"], outline="")

        # Forward Direction Pointer
        tip = pt(hl + 10, 0)
        cv.create_line(car.x, car.y, tip[0], tip[1], fill=C["yel"], width=2, arrow="last", arrowshape=(8, 11, 3))

        # Overhead State Badge
        sc_map = {
            "EMERGENCY_EVADE": C["red"],
            "WALL_AVOIDANCE": C["ora"],
            "LANE_CENTERING": C["blue"],
            "PURSUING_GOAL": C["tg"],
            "UNSTUCK_ESCAPE": C["ty"],
            "IDLE": C["tm"],
        }
        sc = sc_map.get(car.state, C["tm"])
        by2 = car.y - hl - 16
        cv.create_rectangle(car.x - 48, by2 - 7, car.x + 48, by2 + 7, fill=C["cv"], outline=sc, width=1)
        cv.create_text(car.x, by2, text=car.state.replace("_", " "), fill=sc, font=("Consolas", 7, "bold"))

    # ─────────────────────────────────────────────────────────────────────────
    # RADAR DISPLAY
    # ─────────────────────────────────────────────────────────────────────────
    def _radar_idle(self):
        rc = self.rc
        rc.delete("all")
        cx, cy = 65, 62
        for r in [52, 38, 24, 10]:
            rc.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C["bdr"], width=1)
        rc.create_line(cx - 55, cy, cx + 55, cy, fill=C["bdr"], width=1)
        rc.create_line(cx, cy - 55, cx, cy + 55, fill=C["bdr"], width=1)
        rc.create_text(240, 62, text="Awaiting sensor stream...", fill=C["tm"], font=("Consolas", 9))

    def _upd_radar(self):
        rc = self.rc
        rc.delete("all")
        car = self.car
        cx, cy = 65, 62
        mx = 300.0

        for r, lbl in [(52, "300"), (38, "200"), (24, "100"), (10, "50px")]:
            rc.create_oval(cx - r, cy - r, cx + r, cy + r, outline=C["bdr"], width=1)
            rc.create_text(cx + r + 2, cy - 6, text=lbl, fill=C["tm"], font=("Consolas", 6), anchor="w")
        rc.create_line(cx - 55, cy, cx + 55, cy, fill=C["bdr"], width=1)
        rc.create_line(cx, cy - 55, cx, cy + 55, fill=C["bdr"], width=1)
        rc.create_text(cx, cy + 58, text=f"HDG: {car.heading:.0f}°", fill=C["tm"], font=("Consolas", 7))

        self._radar_sw = (self._radar_sw + 6) % 360
        rc.create_arc(
            cx - 52, cy - 52, cx + 52, cy + 52,
            start=90 - self._radar_sw, extent=30, fill="#091526", outline="", style="pieslice"
        )
        rc.create_arc(
            cx - 52, cy - 52, cx + 52, cy + 52,
            start=90 - self._radar_sw, extent=2, outline=C["blue"], width=2, style="arc"
        )

        fwd_rays = []
        for hx, hy, d, a in car.rays:
            rel = ((a - car.heading) + 360) % 360
            if rel > 180:
                rel -= 360
            if -65 <= rel <= 65:
                fwd_rays.append((rel, d))
                rp = max(3, min(52, int(52 * d / mx)))
                ar = math.radians(-90 + rel)
                px = cx + math.cos(ar) * rp
                py = cy + math.sin(ar) * rp
                col = C["red"] if d < 55 else (C["yel"] if d < 140 else C["green"])
                sz = 3.2 if d < 55 else (2.4 if d < 140 else 1.8)
                rc.create_oval(px - sz, py - sz, px + sz, py + sz, fill=col, outline="")

        fm = min((d for _, d in fwd_rays), default=600)
        if fm < 180:
            dr = max(3, min(52, int(52 * fm / mx)))
            rc.create_arc(
                cx - dr, cy - dr, cx + dr, cy + dr,
                start=60, extent=60, outline=C["red"], width=1, style="arc", dash=(3, 3)
            )

        # Distance Telemetry Gauges
        for i, (lbl, ds) in enumerate([
            ("FWD", [d for r, d in fwd_rays if -18 <= r <= 18]),
            ("L45", [d for r, d in fwd_rays if -65 <= r < -18]),
            ("R45", [d for r, d in fwd_rays if 18 < r <= 65]),
        ]):
            bx = 140 + i * 94
            by = 106
            bh = 72
            dv = min(ds) if ds else 600
            bh2 = int(bh * min(dv, 350) / 350)
            col = C["red"] if dv < 50 else (C["yel"] if dv < 120 else C["green"])
            rc.create_rectangle(bx, by - bh, bx + 68, by, fill=C["panel2"], outline=C["bdr"])
            if bh2 > 0:
                rc.create_rectangle(bx, by - bh2, bx + 68, by, fill=col, outline="")
            rc.create_text(bx + 34, by + 9, text=lbl, fill=C["tm"], font=("Consolas", 7))
            rc.create_text(bx + 34, by - bh2 - 10, text=f"{int(dv)}px", fill=col, font=("Consolas", 7, "bold"))

    # ─────────────────────────────────────────────────────────────────────────
    # PEAS LIVE METRICS
    # ─────────────────────────────────────────────────────────────────────────
    def _upd_peas(self):
        car = self.car
        pc = C["tg"] if car.safe_pct > 80 else (C["ty"] if car.safe_pct > 50 else C["tr"])
        self._peas["PERF"].config(
            text=f"Safety: {car.safe_pct}%  |  Steps: {car.steps}  |  Hits: {car.wall_hits}", fg=pc
        )
        act = "DRIVE" if car.speed > 0.1 else "IDLE"
        self._peas["ACT"].config(text=f"{act} ({car.speed:.2f} px/f) | Steer: {car.steer:+.1f}°", fg=C["tb"])
        self._peas["SENS"].config(text="ACTIVE (360° LiDAR, 32 Rays)", fg=C["tg"])
        ec = C["tr"] if car.evasive > 15 else (C["ty"] if car.evasive > 5 else C["tg"])
        self._peas["EVAD"].config(text=f"{car.evasive} trigger(s) logged", fg=ec)
        self._peas["MEM"].config(
            text=f"Cells: {len(car.heat)} | Stuck escapes: {car.evasive}", fg=C["to"]
        )

    # ─────────────────────────────────────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────────────────────────────────────
    def _close(self):
        self._stop()
        self.root.destroy()


if __name__ == "__main__":
    App()
