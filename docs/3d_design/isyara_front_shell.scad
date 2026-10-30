// ============================================================================
// ISYARA - Front Shell (Sisi Depan / Menghadap Lawan Bicara)
// Komponen: Camera Hole, Speaker Grille, USB-C Port, Logo Area
// Dimensi: 76 x 150 x 11.2 mm
// ============================================================================
// Export sebagai STL, lalu import ke TinkerCAD
// ============================================================================

// === PARAMETER UTAMA ===
width  = 76;    // Lebar (mm)
height = 150;   // Panjang/Tinggi (mm)
depth  = 11.2;  // Kedalaman shell (setengah total 22.4mm)
wall   = 2;     // Ketebalan dinding (mm)
radius = 3;     // Corner radius (mm)

// === PARAMETER KOMPONEN ===
// Camera
cam_diameter = 8.3;     // Diameter lubang kamera (+0.3 toleransi)
cam_x = width/2;        // Tengah horizontal
cam_y = height - 20;    // 20mm dari atas

// Speaker Grille
spk_diameter = 32;      // Diameter area grille
spk_hole_d   = 1.5;     // Diameter tiap lubang kecil
spk_x = width/2;        // Tengah horizontal
spk_y = height/2 + 5;   // Sedikit di atas tengah
spk_spacing  = 3.5;     // Jarak antar lubang

// USB-C Port
usbc_w = 9.3;           // Lebar lubang USB-C (+0.3 toleransi)
usbc_h = 3.8;           // Tinggi lubang USB-C (+0.3 toleransi)
usbc_x = width/2;       // Tengah horizontal
usbc_corner_r = 1.2;    // Radius sudut USB-C

// Logo Text Area (recessed)
logo_w = 40;
logo_h = 6;
logo_depth = 0.4;
logo_x = width/2;
logo_y = height - 10;

// Screw Posts
screw_outer_d = 5;
screw_inner_d = 2.2;    // M2 + toleransi
screw_height  = depth - wall - 1;
screw_positions = [
    [8, 8],
    [width-8, 8],
    [8, height-8],
    [width-8, height-8],
    [width/2, height/2 - 30],
    [width/2, height/2 + 30]
];

// === MODULES ===

// Rounded box
module rounded_box(w, h, d, r) {
    hull() {
        translate([r, r, 0])       cylinder(d, r, r, $fn=40);
        translate([w-r, r, 0])     cylinder(d, r, r, $fn=40);
        translate([r, h-r, 0])     cylinder(d, r, r, $fn=40);
        translate([w-r, h-r, 0])   cylinder(d, r, r, $fn=40);
    }
}

// Speaker grille pattern (array of small holes in circle)
module speaker_grille(cx, cy, diameter, hole_d, spacing) {
    r_max = diameter / 2 - hole_d;
    for (x = [-r_max : spacing : r_max]) {
        for (y = [-r_max : spacing : r_max]) {
            if (sqrt(x*x + y*y) <= r_max) {
                translate([cx + x, cy + y, -1])
                    cylinder(wall + 2, d=hole_d, $fn=16);
            }
        }
    }
}

// Rounded rectangle (for USB-C)
module rounded_rect(w, h, d, r) {
    hull() {
        translate([r, r, 0])     cylinder(d, r, r, $fn=20);
        translate([w-r, r, 0])   cylinder(d, r, r, $fn=20);
        translate([r, h-r, 0])   cylinder(d, r, r, $fn=20);
        translate([w-r, h-r, 0]) cylinder(d, r, r, $fn=20);
    }
}

// === MAIN BODY ===
module front_shell() {
    difference() {
        // Outer shell
        rounded_box(width, height, depth, radius);
        
        // Hollow interior (inner cavity)
        translate([wall, wall, wall])
            rounded_box(width - 2*wall, height - 2*wall, depth, radius - 0.5);
        
        // --- CUTOUTS ---
        
        // 1. Camera hole
        translate([cam_x, cam_y, -1])
            cylinder(wall + 2, d=cam_diameter, $fn=40);
        
        // Camera ring recess (decorative, 0.5mm deep)
        translate([cam_x, cam_y, -0.1])
            difference() {
                cylinder(0.6, d=cam_diameter + 4, $fn=40);
                cylinder(0.8, d=cam_diameter, $fn=40);
            }
        
        // 2. Speaker grille holes
        speaker_grille(spk_x, spk_y, spk_diameter, spk_hole_d, spk_spacing);
        
        // Speaker grille outer ring recess (decorative)
        translate([spk_x, spk_y, -0.1])
            difference() {
                cylinder(0.5, d=spk_diameter + 3, $fn=60);
                cylinder(0.7, d=spk_diameter - 1, $fn=60);
            }
        
        // 3. USB-C port (bottom edge)
        translate([usbc_x - usbc_w/2, -1, depth/2 - usbc_h/2])
            rotate([-90, 0, 0])
                rounded_rect(usbc_w, usbc_h, wall + 2, usbc_corner_r);
        
        // 4. Logo recess area (top)
        translate([logo_x - logo_w/2, logo_y - logo_h/2, -0.1])
            cube([logo_w, logo_h, logo_depth + 0.1]);
    }
    
    // --- ADDITIONS ---
    
    // Screw posts (bosses for M2 screws)
    for (pos = screw_positions) {
        translate([pos[0], pos[1], wall]) {
            difference() {
                cylinder(screw_height, d=screw_outer_d, $fn=30);
                cylinder(screw_height + 1, d=screw_inner_d, $fn=20);
            }
        }
    }
    
    // Speaker mount ring (inner support)
    translate([spk_x, spk_y, wall]) {
        difference() {
            cylinder(3, d=spk_diameter + 2, $fn=50);
            cylinder(4, d=spk_diameter - 2, $fn=50);
        }
    }
    
    // Camera mount ring (inner support)
    translate([cam_x, cam_y, wall]) {
        difference() {
            cylinder(4, d=cam_diameter + 6, $fn=40);
            cylinder(5, d=cam_diameter + 0.5, $fn=40);
        }
    }
    
    // PCB standoffs (4 posts)
    pcb_standoff_positions = [
        [12, 45], [width-12, 45],
        [12, 105], [width-12, 105]
    ];
    for (pos = pcb_standoff_positions) {
        translate([pos[0], pos[1], wall]) {
            difference() {
                cylinder(5, d=4.5, $fn=20);
                cylinder(6, d=2.2, $fn=16);
            }
        }
    }
}

// Render
front_shell();

echo("=== ISYARA Front Shell ===");
echo(str("Dimensions: ", width, " x ", height, " x ", depth, " mm"));
echo("Export: File > Export as STL");
echo("Import STL ke TinkerCAD: tinkercad.com > Import");
