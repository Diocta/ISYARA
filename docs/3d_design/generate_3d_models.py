"""
ISYARA 3D Enclosure Generator
Generates STL and OBJ files ready for TinkerCAD import and 3D printing.
Uses Manifold3D (high-performance manifold CSG) and Trimesh.
"""

import os
import math
import numpy as np
import manifold3d as m3d
import trimesh

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================
# PARAMETERS (in mm)
# ==============================================================================
WIDTH = 76.0        # Enclosure width (X)
HEIGHT = 150.0      # Enclosure height (Y)
DEPTH = 11.2        # Shell depth (Z) - Half of 22.4mm total
WALL = 2.0          # Wall thickness
RADIUS = 3.0        # Corner fillet radius

# Camera
CAM_DIAMETER = 8.3  # Hole diameter (with +0.3mm tolerance)
CAM_X = WIDTH / 2.0
CAM_Y = HEIGHT - 20.0

# Speaker Grille
SPK_DIAMETER = 32.0
SPK_HOLE_D = 1.6
SPK_SPACING = 3.5
SPK_X = WIDTH / 2.0
SPK_Y = HEIGHT / 2.0 + 5.0

# USB-C Port
USBC_W = 9.4
USBC_H = 3.8
USBC_R = 1.2
USBC_X = WIDTH / 2.0

# Logo Recess
LOGO_W = 40.0
LOGO_H = 6.0
LOGO_DEPTH = 0.5
LOGO_X = WIDTH / 2.0
LOGO_Y = HEIGHT - 10.0

# Power Switch (Right side)
SW_W = 4.4
SW_H = 7.4
SW_Y = HEIGHT - 30.0

# OLED SSD1306 (0.96")
OLED_W = 25.4
OLED_H = 13.4
OLED_X = WIDTH / 2.0
OLED_Y = HEIGHT - 22.0

# TFT LCD ST7735S (1.77")
TFT_W = 36.4
TFT_H = 29.4
TFT_X = WIDTH / 2.0
TFT_Y = HEIGHT - 52.0

# 16-Button Keypad (4x4)
BTN_DIAMETER = 12.4  # Diameter for button opening
KEYPAD_CENTER_X = WIDTH / 2.0
KEYPAD_CENTER_Y = 38.0
KEYPAD_SPACING_X = 15.0
KEYPAD_SPACING_Y = 14.0

# Screw Posts
SCREW_OD = 5.0
SCREW_ID = 2.2
SCREW_HEIGHT = DEPTH - WALL - 0.5
SCREW_POSITIONS = [
    (8.0, 8.0),
    (WIDTH - 8.0, 8.0),
    (8.0, HEIGHT - 8.0),
    (WIDTH - 8.0, HEIGHT - 8.0),
    (WIDTH / 2.0, HEIGHT / 2.0 - 30.0),
    (WIDTH / 2.0, HEIGHT / 2.0 + 30.0)
]

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def make_rounded_rect_2d(w, h, r, segments=32):
    """Create 2D rounded rectangle cross-section."""
    r = min(r, w / 2.0 - 0.1, h / 2.0 - 0.1)
    c1 = m3d.CrossSection.circle(r, segments).translate([r, r])
    c2 = m3d.CrossSection.circle(r, segments).translate([w - r, r])
    c3 = m3d.CrossSection.circle(r, segments).translate([w - r, h - r])
    c4 = m3d.CrossSection.circle(r, segments).translate([r, h - r])
    return m3d.CrossSection.batch_hull([c1, c2, c3, c4])

def make_rounded_box(w, h, d, r, segments=32):
    """Extrude 2D rounded rectangle into 3D rounded box."""
    cs = make_rounded_rect_2d(w, h, r, segments)
    return cs.extrude(d)

def export_manifold(manifold_obj, filename_base):
    """Export a Manifold object to both STL and OBJ formats via Trimesh."""
    mesh_data = manifold_obj.to_mesh()
    verts = mesh_data.vert_properties[:, :3]
    faces = mesh_data.tri_verts
    
    tm = trimesh.Trimesh(vertices=verts, faces=faces)
    
    stl_path = os.path.join(OUTPUT_DIR, f"{filename_base}.stl")
    obj_path = os.path.join(OUTPUT_DIR, f"{filename_base}.obj")
    
    # Export STL (binary format for TinkerCAD compatibility)
    tm.export(stl_path, file_type='stl')
    # Export OBJ (wavefront obj with materials/groups compatibility)
    tm.export(obj_path, file_type='obj')
    
    print(f"Exported: {filename_base}.stl ({os.path.getsize(stl_path):,} bytes)")
    print(f"Exported: {filename_base}.obj ({os.path.getsize(obj_path):,} bytes)")
    print(f"  Watertight: {tm.is_watertight}, Faces: {len(faces):,}, Vertices: {len(verts):,}")
    return tm

# ==============================================================================
# FRONT SHELL (Menghadap Lawan Bicara: Kamera, Speaker, USB-C)
# ==============================================================================
def build_front_shell():
    print("\n--- Generating Front Shell ---")
    # 1. Base outer shell
    outer = make_rounded_box(WIDTH, HEIGHT, DEPTH, RADIUS)
    
    # 2. Inner cavity (hollow)
    inner = make_rounded_box(WIDTH - 2*WALL, HEIGHT - 2*WALL, DEPTH, RADIUS - 0.5)
    inner = inner.translate([WALL, WALL, WALL])
    
    shell = outer - inner
    
    # 3. Cutout: Camera Hole
    cam_hole = m3d.Manifold.cylinder(WALL + 2.0, CAM_DIAMETER / 2.0, CAM_DIAMETER / 2.0, 36)
    cam_hole = cam_hole.translate([CAM_X, CAM_Y, -1.0])
    shell = shell - cam_hole
    
    # 3b. Camera decorative outer bezel recess (0.5mm deep)
    cam_bezel_outer = m3d.Manifold.cylinder(0.6, (CAM_DIAMETER + 4.0)/2.0, (CAM_DIAMETER + 4.0)/2.0, 36)
    cam_bezel_inner = m3d.Manifold.cylinder(1.0, (CAM_DIAMETER + 1.0)/2.0, (CAM_DIAMETER + 1.0)/2.0, 36)
    cam_recess = (cam_bezel_outer - cam_bezel_inner).translate([CAM_X, CAM_Y, -0.1])
    shell = shell - cam_recess
    
    # 4. Cutout: Speaker Grille (Circular cluster of holes)
    r_max = SPK_DIAMETER / 2.0 - SPK_HOLE_D
    grid_coords = np.arange(-r_max, r_max + SPK_SPACING, SPK_SPACING)
    hole_cyl = m3d.Manifold.cylinder(WALL + 2.0, SPK_HOLE_D / 2.0, SPK_HOLE_D / 2.0, 16)
    
    spk_holes = []
    for x in grid_coords:
        for y in grid_coords:
            if math.sqrt(x*x + y*y) <= r_max:
                spk_holes.append(hole_cyl.translate([SPK_X + x, SPK_Y + y, -1.0]))
    
    if spk_holes:
        shell = shell - m3d.Manifold.batch_boolean(spk_holes, m3d.OpType.Add)
    
    # 5. Cutout: USB-C Port at bottom edge
    # Extrude rounded rect in Y direction (cutting through bottom wall)
    usbc_cs = make_rounded_rect_2d(USBC_W, USBC_H, USBC_R, 16)
    usbc_solid = usbc_cs.extrude(WALL + 4.0)
    # Rotate from XY plane to XZ plane: rotate around X axis by 90 degrees
    usbc_solid = usbc_solid.rotate([90, 0, 0])
    usbc_solid = usbc_solid.translate([USBC_X - USBC_W / 2.0, WALL + 2.0, (DEPTH / 2.0) - (USBC_H / 2.0)])
    shell = shell - usbc_solid
    
    # 6. Cutout: Logo area recess
    logo_cut = m3d.Manifold.cube([LOGO_W, LOGO_H, LOGO_DEPTH + 0.1])
    logo_cut = logo_cut.translate([LOGO_X - LOGO_W / 2.0, LOGO_Y - LOGO_H / 2.0, -0.05])
    shell = shell - logo_cut
    
    # 7. Additions: Screw Bosses (M2 posts)
    screw_bosses = []
    outer_cyl = m3d.Manifold.cylinder(SCREW_HEIGHT, SCREW_OD / 2.0, SCREW_OD / 2.0, 24)
    inner_cyl = m3d.Manifold.cylinder(SCREW_HEIGHT + 1.0, SCREW_ID / 2.0, SCREW_ID / 2.0, 20)
    boss_single = outer_cyl - inner_cyl
    for sx, sy in SCREW_POSITIONS:
        screw_bosses.append(boss_single.translate([sx, sy, WALL]))
    
    # 8. Additions: Camera Support Ring (interior)
    cam_mount_outer = m3d.Manifold.cylinder(4.0, (CAM_DIAMETER + 5.0)/2.0, (CAM_DIAMETER + 5.0)/2.0, 32)
    cam_mount_inner = m3d.Manifold.cylinder(5.0, (CAM_DIAMETER + 0.6)/2.0, (CAM_DIAMETER + 0.6)/2.0, 32)
    cam_mount = (cam_mount_outer - cam_mount_inner).translate([CAM_X, CAM_Y, WALL])
    
    # 9. Additions: Speaker Support Ring (interior)
    spk_ring_outer = m3d.Manifold.cylinder(3.0, (SPK_DIAMETER + 2.0)/2.0, (SPK_DIAMETER + 2.0)/2.0, 48)
    spk_ring_inner = m3d.Manifold.cylinder(4.0, (SPK_DIAMETER - 2.0)/2.0, (SPK_DIAMETER - 2.0)/2.0, 48)
    spk_ring = (spk_ring_outer - spk_ring_inner).translate([SPK_X, SPK_Y, WALL])
    
    all_additions = [shell] + screw_bosses + [cam_mount, spk_ring]
    front_final = m3d.Manifold.batch_boolean(all_additions, m3d.OpType.Add)
    return front_final

# ==============================================================================
# BACK SHELL (Menghadap Pengguna: OLED, TFT LCD, 16 Tombol Braille, Power Switch)
# ==============================================================================
def build_back_shell():
    print("\n--- Generating Back Shell ---")
    # 1. Base outer shell
    outer = make_rounded_box(WIDTH, HEIGHT, DEPTH, RADIUS)
    
    # 2. Inner cavity (hollow)
    inner = make_rounded_box(WIDTH - 2*WALL, HEIGHT - 2*WALL, DEPTH, RADIUS - 0.5)
    inner = inner.translate([WALL, WALL, WALL])
    
    shell = outer - inner
    
    # 3. Cutout: OLED Window (SSD1306 0.96")
    oled_cs = make_rounded_rect_2d(OLED_W, OLED_H, 1.2, 16)
    oled_hole = oled_cs.extrude(WALL + 2.0).translate([OLED_X - OLED_W/2.0, OLED_Y - OLED_H/2.0, -1.0])
    shell = shell - oled_hole
    
    # 3b. OLED Bezel recess (0.6mm deep frame around display window)
    oled_recess_outer = make_rounded_rect_2d(OLED_W + 3.0, OLED_H + 3.0, 1.5, 16).extrude(0.6)
    oled_recess_inner = make_rounded_rect_2d(OLED_W + 0.8, OLED_H + 0.8, 1.0, 16).extrude(1.0)
    oled_recess = (oled_recess_outer - oled_recess_inner).translate([OLED_X - (OLED_W + 3.0)/2.0, OLED_Y - (OLED_H + 3.0)/2.0, -0.05])
    shell = shell - oled_recess
    
    # 4. Cutout: TFT LCD Window (ST7735S 1.77")
    tft_cs = make_rounded_rect_2d(TFT_W, TFT_H, 1.5, 16)
    tft_hole = tft_cs.extrude(WALL + 2.0).translate([TFT_X - TFT_W/2.0, TFT_Y - TFT_H/2.0, -1.0])
    shell = shell - tft_hole
    
    # 4b. TFT Bezel recess
    tft_recess_outer = make_rounded_rect_2d(TFT_W + 3.0, TFT_H + 3.0, 1.8, 16).extrude(0.6)
    tft_recess_inner = make_rounded_rect_2d(TFT_W + 0.8, TFT_H + 0.8, 1.2, 16).extrude(1.0)
    tft_recess = (tft_recess_outer - tft_recess_inner).translate([TFT_X - (TFT_W + 3.0)/2.0, TFT_Y - (TFT_H + 3.0)/2.0, -0.05])
    shell = shell - tft_recess
    
    # 5. Cutouts: 16-Button Keypad (4x4 Matrix)
    # Positions: col from 0 to 3, row from 0 to 3
    btn_cyl = m3d.Manifold.cylinder(WALL + 2.0, BTN_DIAMETER / 2.0, BTN_DIAMETER / 2.0, 32)
    btn_holes = []
    btn_guides = []
    
    guide_outer = m3d.Manifold.cylinder(1.6, (BTN_DIAMETER + 2.4)/2.0, (BTN_DIAMETER + 2.4)/2.0, 32)
    guide_inner = m3d.Manifold.cylinder(2.0, BTN_DIAMETER/2.0, BTN_DIAMETER/2.0, 32)
    guide_ring = guide_outer - guide_inner
    
    for row in range(4):
        for col in range(4):
            bx = KEYPAD_CENTER_X + (col - 1.5) * KEYPAD_SPACING_X
            by = KEYPAD_CENTER_Y + (1.5 - row) * KEYPAD_SPACING_Y
            btn_holes.append(btn_cyl.translate([bx, by, -1.0]))
            btn_guides.append(guide_ring.translate([bx, by, WALL]))
            
    shell = shell - m3d.Manifold.batch_boolean(btn_holes, m3d.OpType.Add)
    
    # 6. Cutout: Power Switch on Right Side
    # Cuts horizontally through side wall (X=WIDTH)
    sw_cut = m3d.Manifold.cube([WALL + 2.0, SW_H, SW_W])
    sw_cut = sw_cut.translate([WIDTH - WALL - 1.0, SW_Y - SW_H/2.0, (DEPTH/2.0) - (SW_W/2.0)])
    shell = shell - sw_cut
    
    # 7. Additions: Screw Bosses (matching Front Shell)
    screw_bosses = []
    outer_cyl = m3d.Manifold.cylinder(SCREW_HEIGHT, SCREW_OD / 2.0, SCREW_OD / 2.0, 24)
    inner_cyl = m3d.Manifold.cylinder(SCREW_HEIGHT + 1.0, SCREW_ID / 2.0, SCREW_ID / 2.0, 20)
    boss_single = outer_cyl - inner_cyl
    for sx, sy in SCREW_POSITIONS:
        screw_bosses.append(boss_single.translate([sx, sy, WALL]))
        
    # 8. Additions: Display Mount Rails (Internal)
    # OLED rails (left and right)
    oled_rail_l = m3d.Manifold.cube([1.2, OLED_H + 2.0, 2.0]).translate([OLED_X - OLED_W/2.0 - 1.2, OLED_Y - OLED_H/2.0 - 1.0, WALL])
    oled_rail_r = m3d.Manifold.cube([1.2, OLED_H + 2.0, 2.0]).translate([OLED_X + OLED_W/2.0, OLED_Y - OLED_H/2.0 - 1.0, WALL])
    
    # TFT rails (left, right, bottom)
    tft_rail_l = m3d.Manifold.cube([1.2, TFT_H + 2.0, 3.0]).translate([TFT_X - TFT_W/2.0 - 1.2, TFT_Y - TFT_H/2.0 - 1.0, WALL])
    tft_rail_r = m3d.Manifold.cube([1.2, TFT_H + 2.0, 3.0]).translate([TFT_X + TFT_W/2.0, TFT_Y - TFT_H/2.0 - 1.0, WALL])
    tft_rail_b = m3d.Manifold.cube([TFT_W + 2.4, 1.2, 3.0]).translate([TFT_X - TFT_W/2.0 - 1.2, TFT_Y - TFT_H/2.0 - 1.2, WALL])
    
    # Structural reinforcement rib between TFT and Keypad
    h_rib = m3d.Manifold.cube([WIDTH - 2*WALL - 4.0, 1.5, 3.0]).translate([WALL + 2.0, TFT_Y - TFT_H/2.0 - 5.0, WALL])
    
    all_additions = [shell] + screw_bosses + btn_guides + [
        oled_rail_l, oled_rail_r, tft_rail_l, tft_rail_r, tft_rail_b, h_rib
    ]
    back_final = m3d.Manifold.batch_boolean(all_additions, m3d.OpType.Add)
    return back_final

# ==============================================================================
# INDIVIDUAL BRAILLE KEYPAD BUTTON CAP (Ready to 3D Print)
# ==============================================================================
def build_button_cap():
    print("\n--- Generating Tactile Button Cap ---")
    cap_d = 11.6        # 11.6mm diameter fits comfortably in 12.4mm hole
    cap_h = 4.5         # Height of button stem/cap
    flange_d = 13.8     # Base flange prevents falling through hole
    flange_h = 1.0      # Base flange height
    stem_inner_d = 4.0  # Recess to fit 6x6 tactile switch actuator
    stem_inner_h = 2.5
    
    # Base flange
    flange = m3d.Manifold.cylinder(flange_h, flange_d/2.0, flange_d/2.0, 32)
    # Button main body
    body = m3d.Manifold.cylinder(cap_h, cap_d/2.0, cap_d/2.0, 32).translate([0, 0, flange_h])
    
    # Tactile switch stem pocket (bottom recess)
    pocket = m3d.Manifold.cylinder(stem_inner_h + 0.1, stem_inner_d/2.0, stem_inner_d/2.0, 20).translate([0, 0, -0.05])
    
    # Braille tactile dot on top (dome)
    # Using small sphere or small dome cylinder
    dot = m3d.Manifold.cylinder(0.8, 1.0, 0.4, 16).translate([0, 0, flange_h + cap_h])
    
    btn = (flange + body - pocket) + dot
    return btn

# ==============================================================================
# ASSEMBLED ENCLOSURE (Front + Back Shells joined for 3D View / Showcase)
# ==============================================================================
def build_assembled_enclosure(front_shell, back_shell):
    print("\n--- Assembling Full Enclosure ---")
    # Back shell sits on bottom: Z from 0 to DEPTH
    # Front shell is flipped upside down (rotated 180 around Y or X) and placed on top
    # Front shell flipped: rotated 180 around X axis
    # When rotated 180 around X: Y becomes -Y, Z becomes -Z
    # Translate back to positive bounds: Y += HEIGHT, Z += 2*DEPTH
    front_flipped = front_shell.rotate([180, 0, 0]).translate([0, HEIGHT, 2 * DEPTH])
    
    # Union both shells into one assembled unit
    assembled = m3d.Manifold.batch_boolean([back_shell, front_flipped], m3d.OpType.Add)
    return assembled

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("ISYARA 3D Enclosure Generation")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)
    
    # Build models
    front = build_front_shell()
    export_manifold(front, "isyara_front_shell")
    
    back = build_back_shell()
    export_manifold(back, "isyara_back_shell")
    
    button = build_button_cap()
    export_manifold(button, "isyara_braille_button_cap")
    
    assembled = build_assembled_enclosure(front, back)
    export_manifold(assembled, "isyara_assembled_enclosure")
    
    print("\nAll 3D models generated successfully!")
    print("=" * 60)
