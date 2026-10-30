// ============================================================================
// ISYARA - Back Shell (Sisi User / Menghadap Pengguna)
// Komponen: OLED Window, TFT LCD Window, 16-Button Keypad (4x4), Power Switch
// Dimensi: 76 x 150 x 11.2 mm
// ============================================================================
// Export sebagai STL, lalu import ke TinkerCAD
// ============================================================================

// === PARAMETER UTAMA ===
width  = 76;    // Lebar (mm)
height = 150;   // Panjang/Tinggi (mm)
depth  = 11.2;  // Kedalaman shell
wall   = 2;     // Ketebalan dinding (mm)
radius = 3;     // Corner radius (mm)

// === PARAMETER DISPLAY ===
// OLED SSD1306 0.96" Window
oled_w = 25.3;   // +0.3 toleransi
oled_h = 13.3;   // +0.3 toleransi
oled_x = width/2;
oled_y = height - 22;  // 22mm dari atas

// TFT LCD ST7735S 1.77" Window
tft_w = 36.3;    // +0.3 toleransi
tft_h = 29.3;    // +0.3 toleransi
tft_x = width/2;
tft_y = height - 52;  // Di bawah OLED

// === PARAMETER KEYPAD 4x4 ===
btn_diameter = 12.3;   // Diameter lubang tombol (+0.3 toleransi)
keypad_cols = 4;
keypad_rows = 4;
keypad_spacing_x = 15; // Jarak antar tombol horizontal
keypad_spacing_y = 14; // Jarak antar tombol vertikal

// Posisi grid keypad (center of 4x4 matrix)
keypad_center_x = width / 2;
keypad_center_y = 38;  // Posisi tengah-bawah device

// === PARAMETER POWER SWITCH ===
sw_w = 7.3;     // +0.3 toleransi
sw_h = 4.3;     // +0.3 toleransi
sw_y = height - 30;  // Posisi switch di sisi kanan

// === PARAMETER SCREW ===
screw_outer_d = 5;
screw_inner_d = 2.2;
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

module rounded_box(w, h, d, r) {
    hull() {
        translate([r, r, 0])       cylinder(d, r, r, $fn=40);
        translate([w-r, r, 0])     cylinder(d, r, r, $fn=40);
        translate([r, h-r, 0])     cylinder(d, r, r, $fn=40);
        translate([w-r, h-r, 0])   cylinder(d, r, r, $fn=40);
    }
}

module rounded_rect_cutout(w, h, d, r) {
    hull() {
        translate([r, r, 0])     cylinder(d, r, r, $fn=20);
        translate([w-r, r, 0])   cylinder(d, r, r, $fn=20);
        translate([r, h-r, 0])   cylinder(d, r, r, $fn=20);
        translate([w-r, h-r, 0]) cylinder(d, r, r, $fn=20);
    }
}

// Keypad button positions (4x4 grid)
function keypad_pos(row, col) = [
    keypad_center_x + (col - 1.5) * keypad_spacing_x,
    keypad_center_y + (1.5 - row) * keypad_spacing_y
];

// === MAIN BODY ===
module back_shell() {
    difference() {
        // Outer shell
        rounded_box(width, height, depth, radius);
        
        // Hollow interior
        translate([wall, wall, wall])
            rounded_box(width - 2*wall, height - 2*wall, depth, radius - 0.5);
        
        // --- DISPLAY CUTOUTS ---
        
        // 1. OLED window (0.96")
        translate([oled_x - oled_w/2, oled_y - oled_h/2, -1])
            rounded_rect_cutout(oled_w, oled_h, wall + 2, 1);
        
        // OLED bezel recess (0.5mm deep frame around window)
        translate([oled_x - oled_w/2 - 2, oled_y - oled_h/2 - 2, -0.1])
            difference() {
                rounded_rect_cutout(oled_w + 4, oled_h + 4, 0.6, 1.5);
                translate([1.5, 1.5, -0.1])
                    rounded_rect_cutout(oled_w + 1, oled_h + 1, 0.8, 0.8);
            }
        
        // 2. TFT LCD window (1.77")
        translate([tft_x - tft_w/2, tft_y - tft_h/2, -1])
            rounded_rect_cutout(tft_w, tft_h, wall + 2, 1.5);
        
        // TFT bezel recess
        translate([tft_x - tft_w/2 - 2, tft_y - tft_h/2 - 2, -0.1])
            difference() {
                rounded_rect_cutout(tft_w + 4, tft_h + 4, 0.6, 2);
                translate([1.5, 1.5, -0.1])
                    rounded_rect_cutout(tft_w + 1, tft_h + 1, 0.8, 1.2);
            }
        
        // --- 16-BUTTON KEYPAD CUTOUTS (4x4 Grid) ---
        // Row 0: S1(MODE) S2(DOT1) S3(DOT4) S4(CLEAR)
        // Row 1: S5(BKSP) S6(DOT2) S7(DOT5) S8(ENTER)
        // Row 2: S9(SPACE) S10(DOT3) S11(DOT6) S12(NUM)
        // Row 3: S13(BKSP) S14(SPACE) S15(ENTER) S16(TTS)
        
        for (row = [0:3]) {
            for (col = [0:3]) {
                pos = keypad_pos(row, col);
                translate([pos[0], pos[1], -1])
                    cylinder(wall + 2, d=btn_diameter, $fn=30);
            }
        }
        
        // --- POWER SWITCH CUTOUT (sisi kanan) ---
        translate([width - wall - 1, sw_y - sw_h/2, depth/2 - sw_w/2 + 1])
            cube([wall + 2, sw_h, sw_w]);
    }
    
    // --- ADDITIONS ---
    
    // Screw post holes (matching front shell)
    for (pos = screw_positions) {
        translate([pos[0], pos[1], wall]) {
            difference() {
                cylinder(screw_height, d=screw_outer_d, $fn=30);
                // Lubang tembus untuk screw dari front shell
                cylinder(screw_height + 1, d=screw_inner_d, $fn=20);
            }
        }
    }
    
    // Display mount rails (OLED)
    // Rail kiri OLED
    translate([oled_x - oled_w/2 - 1, oled_y - oled_h/2 - 1, wall])
        cube([1, oled_h + 2, 2]);
    // Rail kanan OLED
    translate([oled_x + oled_w/2, oled_y - oled_h/2 - 1, wall])
        cube([1, oled_h + 2, 2]);
    
    // Display mount rails (TFT)
    // Rail kiri TFT
    translate([tft_x - tft_w/2 - 1, tft_y - tft_h/2 - 1, wall])
        cube([1, tft_h + 2, 3]);
    // Rail kanan TFT
    translate([tft_x + tft_w/2, tft_y - tft_h/2 - 1, wall])
        cube([1, tft_h + 2, 3]);
    // Rail bawah TFT
    translate([tft_x - tft_w/2 - 1, tft_y - tft_h/2 - 1, wall])
        cube([tft_w + 2, 1, 3]);
    
    // Button guide rings (inner side, for tactile switch alignment)
    for (row = [0:3]) {
        for (col = [0:3]) {
            pos = keypad_pos(row, col);
            translate([pos[0], pos[1], wall]) {
                difference() {
                    cylinder(1.5, d=btn_diameter + 2, $fn=30);
                    cylinder(2, d=btn_diameter, $fn=30);
                }
            }
        }
    }
    
    // Internal rib reinforcements
    // Horizontal rib antara displays dan keypad
    translate([wall + 2, tft_y - tft_h/2 - 5, wall])
        cube([width - 2*wall - 4, 1.5, 3]);
    
    // Vertical center rib
    translate([width/2 - 0.75, 8, wall])
        cube([1.5, keypad_center_y - keypad_spacing_y * 2 - 8, 3]);
}

// Render
back_shell();

echo("=== ISYARA Back Shell ===");
echo(str("Dimensions: ", width, " x ", height, " x ", depth, " mm"));
echo(str("Keypad: 4x4 grid, ", keypad_cols * keypad_rows, " buttons"));
echo("Export: File > Export as STL");
echo("Import STL ke TinkerCAD: tinkercad.com > Import");
