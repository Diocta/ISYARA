"""
Render multi-angle previews of ISYARA STL 3D models into high-resolution images.
Generates:
1. preview_back_shell.png
2. preview_assembled_enclosure.png
3. preview_front_shell.png
"""

import os
import math
import numpy as np
import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

def render_mesh_to_axis(ax, mesh, elev=30, azim=-60, title="3D View", 
                        base_color=np.array([0.22, 0.58, 0.90]), 
                        bg_color='#0f141c'):
    """Renders a single 3D mesh into a matplotlib 3D axis with lighting."""
    v = mesh.vertices
    faces = mesh.faces
    normals = mesh.face_normals
    
    # Dual directional lighting (Key light + Fill light)
    # Key light from upper-left
    az1, alt1 = np.radians(225), np.radians(50)
    l1 = np.array([np.sin(az1)*np.cos(alt1), np.cos(az1)*np.cos(alt1), np.sin(alt1)])
    l1 = l1 / np.linalg.norm(l1)
    
    # Fill light from upper-right
    az2, alt2 = np.radians(45), np.radians(30)
    l2 = np.array([np.sin(az2)*np.cos(alt2), np.cos(az2)*np.cos(alt2), np.sin(alt2)])
    l2 = l2 / np.linalg.norm(l2)
    
    dot1 = np.clip(np.dot(normals, l1), 0, 1)
    dot2 = np.clip(np.dot(normals, l2), 0, 1)
    
    intensity = 0.65 * dot1 + 0.20 * dot2 + 0.25 # ambient
    intensity = np.clip(intensity, 0.15, 1.0)
    
    face_colors = intensity[:, None] * base_color
    
    poly = Poly3DCollection(v[faces], facecolors=face_colors, edgecolor='#000000', linewidths=0.15, alpha=1.0)
    ax.add_collection3d(poly)
    
    # Equal aspect ratio bounds
    max_range = np.array([v[:,0].max()-v[:,0].min(), 
                          v[:,1].max()-v[:,1].min(), 
                          v[:,2].max()-v[:,2].min()]).max() / 2.0
    
    mid_x = (v[:,0].max() + v[:,0].min()) * 0.5
    mid_y = (v[:,1].max() + v[:,1].min()) * 0.5
    mid_z = (v[:,2].max() + v[:,2].min()) * 0.5
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    ax.view_init(elev=elev, azim=azim)
    ax.axis('off')
    ax.set_title(title, color='#e2e8f0', fontsize=12, fontweight='bold', pad=10)

def generate_back_shell_preview():
    print("Rendering preview for isyara_back_shell.stl...")
    stl_path = os.path.join(OUTPUT_DIR, "isyara_back_shell.stl")
    mesh = trimesh.load(stl_path)
    
    fig = plt.figure(figsize=(16, 12), dpi=140, facecolor='#0b0f19')
    fig.suptitle("ISYARA V2 — Back Shell (Sisi User) 3D Model Preview\nFormat: STL | Dimensi: 76 x 150 x 11.2 mm | 16-Button Keypad & Dual Display", 
                 color='#38bdf8', fontsize=15, fontweight='bold', y=0.96)
    
    # 4 Subplots: Isometric Front-Left, Top (User-facing), Isometric Inside, Side
    ax1 = fig.add_subplot(221, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax1, mesh, elev=35, azim=-50, 
                        title="1. Isometric View (Tampak 3D Sisi User)\nOLED + TFT LCD + 16 Tombol 4x4",
                        base_color=np.array([0.22, 0.60, 0.95]))
    
    ax2 = fig.add_subplot(222, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax2, mesh, elev=89, azim=-90, 
                        title="2. Tampak Datar Luar (User Facing Flat)\nPosisi Presisi Komponen",
                        base_color=np.array([0.25, 0.65, 0.98]))
    
    ax3 = fig.add_subplot(223, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax3, mesh, elev=-45, azim=-55, 
                        title="3. Tampak Sisi Dalam (Internal Standoffs & Guides)\nRail Mount Display & 6x M2 Screw Bosses",
                        base_color=np.array([0.20, 0.50, 0.85]))
    
    ax4 = fig.add_subplot(224, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax4, mesh, elev=15, azim=-15, 
                        title="4. Tampak Samping Kanan (Side Profile)\nCutout Switch ON/OFF & Profil Ketebalan 11.2mm",
                        base_color=np.array([0.18, 0.45, 0.80]))
    
    out_img = os.path.join(OUTPUT_DIR, "preview_back_shell.png")
    plt.tight_layout(rect=[0, 0.03, 1, 0.92])
    plt.savefig(out_img, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_img} ({os.path.getsize(out_img):,} bytes)")

def generate_assembled_preview():
    print("Rendering preview for isyara_assembled_enclosure.stl...")
    stl_path = os.path.join(OUTPUT_DIR, "isyara_assembled_enclosure.stl")
    mesh = trimesh.load(stl_path)
    
    fig = plt.figure(figsize=(16, 12), dpi=140, facecolor='#0b0f19')
    fig.suptitle("ISYARA V2 — Assembled Enclosure (Casing Lengkap) 3D Model Preview\nFormat: STL | Dimensi Total: 76 x 150 x 22.4 mm | Full Assembly", 
                 color='#10b981', fontsize=15, fontweight='bold', y=0.96)
    
    # 4 Subplots
    ax1 = fig.add_subplot(221, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax1, mesh, elev=30, azim=-50, 
                        title="1. Isometric View Sisi User (Belakang)\nDual Display & 16-Button Braille Keypad",
                        base_color=np.array([0.16, 0.75, 0.55]))
    
    ax2 = fig.add_subplot(222, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax2, mesh, elev=150, azim=130, 
                        title="2. Isometric View Sisi Depan (Lawan Bicara)\nKamera ESP32-CAM & Speaker Grille",
                        base_color=np.array([0.20, 0.65, 0.75]))
    
    ax3 = fig.add_subplot(223, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax3, mesh, elev=10, azim=-80, 
                        title="3. Tampak Samping (Side Thickness Profile)\nKetebalan Enclosure 22.4mm & Switch ON/OFF",
                        base_color=np.array([0.22, 0.70, 0.50]))
    
    ax4 = fig.add_subplot(224, projection='3d', facecolor='#0b0f19')
    render_mesh_to_axis(ax4, mesh, elev=-70, azim=-90, 
                        title="4. Tampak Bawah (Bottom Edge View)\nPort USB-C Charging & Sudut Membulat R=3mm",
                        base_color=np.array([0.18, 0.60, 0.45]))
    
    out_img = os.path.join(OUTPUT_DIR, "preview_assembled_enclosure.png")
    plt.tight_layout(rect=[0, 0.03, 1, 0.92])
    plt.savefig(out_img, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_img} ({os.path.getsize(out_img):,} bytes)")

if __name__ == '__main__':
    generate_back_shell_preview()
    generate_assembled_preview()
    print("All STL preview images rendered successfully!")
