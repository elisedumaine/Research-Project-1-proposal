"""Build the kit's character generator HDA (lpk_character) in the open Houdini.

Run from the kit folder:
    python Tools/houdini.py -f scripts/build_character.py

A low-poly "figurine" made of rigid pieces, built on the joints of Unreal's
Quinn mannequin (the Third Person template player) in its rest pose.  Every
face carries the name of the bone it belongs to (prim attribute `bone`), so
Unreal can hang each piece on its bone and Quinn's own animations move it:
no skinning needed.

Choices (menus, the Studio shows them as arrows): body, head size, skin,
hair style and color, facial hair, top, bottom, shoes, hat, extra, and the
colors of the clothes.  Units are meters, Y up, facing +Z (Unreal +Y).
"""
import json
import os

import hou

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
HDA_PATH = KIT + "/hda/lpk_character.hda"

# Quinn's joints in its rest pose: Unreal component space (cm, Z up, facing +Y).
QUINN = {
    "pelvis": (0.0, 2.28, 95.9), "spine_03": (0.0, 4.25, 113.42), "neck_01": (0.0, -1.57, 152.8),
    "head": (0.0, 0.66, 162.58), "upperarm_l": (19.01, -2.56, 143.58), "lowerarm_l": (35.01, -1.91, 120.89),
    "hand_l": (47.77, 15.7, 104.47), "upperarm_r": (-19.01, -2.56, 143.58), "lowerarm_r": (-35.01, -1.91, 120.89),
    "hand_r": (-47.77, 15.7, 104.47), "thigh_l": (9.97, 2.54, 93.54), "calf_l": (12.33, 2.6, 50.27),
    "foot_l": (14.09, -0.99, 8.24), "ball_l": (15.78, 13.93, 0.75), "thigh_r": (-9.97, 2.55, 93.54),
    "calf_r": (-12.33, 2.61, 50.27), "foot_r": (-14.09, -0.98, 8.24), "ball_r": (-15.78, 13.94, 0.75),
}

BODY = ("Average", "Slim", "Sturdy")
HEAD = ("Normal", "Big", "Chibi")
SKIN = (("Peach", (0.72, 0.45, 0.32)), ("Light", (0.82, 0.58, 0.45)), ("Tan", (0.55, 0.32, 0.20)),
        ("Brown", (0.34, 0.17, 0.09)), ("Deep", (0.17, 0.08, 0.045)), ("Fairy blue", (0.30, 0.46, 0.78)),
        ("Forest green", (0.30, 0.52, 0.28)))
HAIR = ("Short", "Bob", "Long", "Ponytail", "Bun", "Spiky", "Mohawk", "Curly", "Bald")
HAIR_COLOR = (("Brown", (0.12, 0.06, 0.03)), ("Black", (0.02, 0.016, 0.016)), ("Auburn", (0.30, 0.08, 0.04)),
              ("Blonde", (0.75, 0.55, 0.25)), ("Ginger", (0.70, 0.25, 0.05)), ("Silver", (0.60, 0.60, 0.62)),
              ("Pink", (0.90, 0.35, 0.55)), ("Blue", (0.15, 0.30, 0.80)))
FACIAL = ("None", "Moustache", "Beard", "Goatee", "Full beard")
TOP = ("T-shirt", "Long sleeves", "Tank top", "Hoodie", "Striped")
BOTTOM = ("Trousers", "Shorts", "Skirt")
SHOES = ("Sneakers", "Boots", "Sandals")
HAT = ("None", "Cap", "Beanie", "Wizard", "Flower crown", "Bucket hat")
EXTRA = ("None", "Backpack", "Scarf", "Glasses")
CLOTH = (("Apricot", (0.86, 0.42, 0.18)), ("Cream", (0.85, 0.78, 0.62)), ("Blush", (0.70, 0.27, 0.23)),
         ("Sage", (0.36, 0.52, 0.30)), ("Forest", (0.08, 0.20, 0.08)), ("Navy", (0.04, 0.07, 0.20)),
         ("Denim", (0.15, 0.25, 0.45)), ("Charcoal", (0.05, 0.05, 0.06)), ("Lilac", (0.45, 0.35, 0.70)),
         ("Mustard", (0.75, 0.55, 0.08)), ("Red", (0.70, 0.05, 0.04)), ("White", (0.90, 0.90, 0.88)))


def _vex_colors(name, table):
    return "vector %s[] = {%s};" % (name, ", ".join("{%g, %g, %g}" % c for _n, c in table))


def _vex_joints():
    lines = []
    for bone, (x, y, z) in QUINN.items():
        lines.append("vector J_%s = {%g, %g, %g};" % (bone, x / 100.0, z / 100.0, y / 100.0))
    return "\n".join(lines)


CHARACTER_VEX = r"""
// ================================================================ helpers
// A tube along pts with an elliptical section (rx across, rz deep), capped
// at both ends.  Every face is painted `c` and belongs to `bone`.
void tube(vector pts[]; float rx[]; float rz[]; int sides; vector c; string bone) {
    int n = len(pts);
    int first[];
    for (int i = 0; i < n; i++) {
        vector dir = normalize(i == n - 1 ? pts[i] - pts[i - 1] : pts[i + 1] - pts[i]);
        vector ref = abs(dir.z) < 0.9 ? set(0, 0, 1) : set(1, 0, 0);
        vector a = normalize(cross(dir, ref));
        if (dot(a, {1, 0, 0}) < 0) a = -a;
        vector b = normalize(cross(a, dir));
        for (int s = 0; s < sides; s++) {
            float ang = 2.0 * PI * (s + 0.5) / sides;
            int pt = addpoint(0, pts[i] + rx[i] * cos(ang) * a + rz[i] * sin(ang) * b);
            if (s == 0) append(first, pt);
        }
    }
    for (int j = 0; j < n - 1; j++) {
        for (int s = 0; s < sides; s++) {
            int s2 = (s + 1) % sides;
            int pr = addprim(0, "poly", first[j] + s, first[j + 1] + s, first[j + 1] + s2, first[j] + s2);
            setprimattrib(0, "Cd", pr, c);
            setprimattrib(0, "bone", pr, bone);
        }
    }
    int cap0[], cap1[];
    for (int s = 0; s < sides; s++) append(cap0, first[0] + s);
    for (int s = sides - 1; s >= 0; s--) append(cap1, first[n - 1] + s);
    int p0 = addprim(0, "poly", cap0);
    int p1 = addprim(0, "poly", cap1);
    setprimattrib(0, "Cd", p0, c); setprimattrib(0, "bone", p0, bone);
    setprimattrib(0, "Cd", p1, c); setprimattrib(0, "bone", p1, bone);
}

void limb(vector a; vector b; float ra; float rb; int sides; vector c; string bone) {
    tube(array(a, b), array(ra, rb), array(ra, rb), sides, c, bone);
}

// A low-poly ellipsoid, or a band of it: latitudes from lat0 to lat1
// (0 = bottom pole, 1 = top pole).  open_face > 0 leaves the face free:
// no quads in front (z > 0) below that latitude.
void blob(vector c; vector r; int rows; int cols; float lat0; float lat1; float open_face; vector col; string bone) {
    int ring[];
    for (int i = 0; i <= rows; i++) {
        float lat = lerp(lat0, lat1, float(i) / rows);
        float phi = PI * (lat - 0.5);
        for (int k = 0; k < cols; k++) {
            float th = 2.0 * PI * (k + 0.5 * (i % 2)) / cols;
            int pt = addpoint(0, c + set(cos(phi) * sin(th) * r.x, sin(phi) * r.y, cos(phi) * cos(th) * r.z));
            if (k == 0) append(ring, pt);
        }
    }
    for (int i = 0; i < rows; i++) {
        float lat = lerp(lat0, lat1, (i + 0.5) / rows);
        for (int k = 0; k < cols; k++) {
            int k2 = (k + 1) % cols;
            float th = 2.0 * PI * (k + 0.5) / cols;
            if (open_face > 0 && lat < open_face && cos(th) > 0.35) continue;
            int pr = addprim(0, "poly", ring[i] + k, ring[i] + k2, ring[i + 1] + k2, ring[i + 1] + k);
            setprimattrib(0, "Cd", pr, col);
            setprimattrib(0, "bone", pr, bone);
        }
    }
    // Close a full top or bottom with a fan.
    if (lat1 >= 0.999 || lat0 <= 0.001) {
        for (int end = 0; end < 2; end++) {
            if ((end == 0 && lat0 > 0.001) || (end == 1 && lat1 < 0.999)) continue;
            int pole = addpoint(0, c + set(0, (end == 1 ? 1 : -1) * r.y, 0));
            int base = ring[end == 1 ? rows : 0];
            for (int k = 0; k < cols; k++) {
                int pr = end == 1 ? addprim(0, "poly", base + k, base + (k + 1) % cols, pole)
                                  : addprim(0, "poly", base + (k + 1) % cols, base + k, pole);
                setprimattrib(0, "Cd", pr, col);
                setprimattrib(0, "bone", pr, bone);
            }
        }
    }
}

// An axis-aligned box.
void box(vector c; vector h; vector col; string bone) {
    int p[];
    for (int i = 0; i < 8; i++)
        append(p, addpoint(0, c + set((i & 1) ? h.x : -h.x, (i & 2) ? h.y : -h.y, (i & 4) ? h.z : -h.z)));
    int faces[] = {0,2,3,1, 4,5,7,6, 0,1,5,4, 2,6,7,3, 0,4,6,2, 1,3,7,5};
    for (int f = 0; f < 6; f++) {
        int pr = addprim(0, "poly", p[faces[f*4]], p[faces[f*4+1]], p[faces[f*4+2]], p[faces[f*4+3]]);
        setprimattrib(0, "Cd", pr, col);
        setprimattrib(0, "bone", pr, bone);
    }
}

// A cone from a base center, pointing along dir.
void cone(vector base; vector dir; float r; float h; int sides; vector col; string bone) {
    vector d = normalize(dir);
    vector ref = abs(d.y) < 0.9 ? set(0, 1, 0) : set(1, 0, 0);
    vector a = normalize(cross(d, ref)), b = normalize(cross(a, d));
    int first = -1;
    for (int s = 0; s < sides; s++) {
        float ang = 2.0 * PI * s / sides;
        int pt = addpoint(0, base + r * (cos(ang) * a + sin(ang) * b));
        if (s == 0) first = pt;
    }
    int tip = addpoint(0, base + d * h);
    int bottom[];
    for (int s = 0; s < sides; s++) {
        int pr = addprim(0, "poly", first + s, first + (s + 1) % sides, tip);
        setprimattrib(0, "Cd", pr, col); setprimattrib(0, "bone", pr, bone);
        insert(bottom, 0, first + s);
    }
    int pb = addprim(0, "poly", bottom);
    setprimattrib(0, "Cd", pb, col); setprimattrib(0, "bone", pb, bone);
}

// ================================================================ choices
%(joints)s
%(skin)s
%(hair_colors)s
%(cloth)s

int body = chi("../body"), headsize = chi("../head_size");
int hair = chi("../hair"), facial = chi("../facial_hair");
int top = chi("../top"), bottom = chi("../bottom"), shoes = chi("../shoes");
int hat = chi("../hat"), extra = chi("../extra");
int detail = chi("../detail");
vector skin = SKIN[chi("../skin")];
vector hc = HAIR_COLOR[chi("../hair_color")];
vector shirt = CLOTH[chi("../top_color")];
vector pants = CLOTH[chi("../bottom_color")];
vector shoe = CLOTH[chi("../shoe_color")];
vector acc = CLOTH[chi("../accent_color")];
vector dark = {0.02, 0.015, 0.015};

string LR[] = {"l", "r"};
float SIGNS[] = {-1.0, 1.0};
addprimattrib(0, "bone", "");
addprimattrib(0, "Cd", {1, 1, 1});

float bw = body == 1 ? 0.85 : (body == 2 ? 1.25 : 1.0);    // body width
float hs = headsize == 1 ? 1.25 : (headsize == 2 ? 1.6 : 1.0);
int sides = 5 + detail;                                    // 6..10 around a limb

// ================================================================ body
// Hips and torso.
tube(array(set(0, 0.86, 0.02), set(0, 1.0, 0.025)), array(0.145 * bw, 0.15 * bw), array(0.10 * bw, 0.10 * bw),
     sides + 2, bottom == 2 ? pants : pants, "pelvis");
vector torso[] = array(set(0, 0.99, 0.025), set(0, 1.12, 0.035), set(0, 1.27, 0.04), set(0, 1.42, 0.01), set(0, 1.48, -0.005));
float trx[] = array(0.145, 0.15, 0.165, 0.175, 0.12);
float trz[] = array(0.10, 0.11, 0.125, 0.11, 0.08);
for (int i = 0; i < len(trx); i++) { trx[i] *= bw * (top == 3 ? 1.08 : 1.0); trz[i] *= bw * (top == 3 ? 1.08 : 1.0); }
if (top == 4) {
    // Striped: the torso in bands, shirt color and cream.
    for (int i = 0; i < len(torso) - 1; i++)
        tube(array(torso[i], torso[i + 1]), array(trx[i], trx[i + 1]), array(trz[i], trz[i + 1]), sides + 2,
             i % 2 == 0 ? shirt : CLOTH[1], "spine_03");
} else {
    tube(torso, trx, trz, sides + 2, shirt, "spine_03");
}
if (top == 3) blob(set(0, 1.47, -0.09), set(0.13, 0.11, 0.08) * bw, 3, sides + 2, 0.2, 1.0, 0, shirt, "spine_03");  // hood
limb(set(0, 1.45, -0.01), set(0, 1.58, 0.0), 0.048 * bw, 0.045 * bw, sides, skin, "neck_01");

// Arms: sleeves follow the top.
vector upper_c = top == 2 ? skin : shirt;
vector lower_c = (top == 1 || top == 3) ? shirt : skin;
foreach (string side; LR) {
    vector sh = side == "l" ? J_upperarm_l : J_upperarm_r;
    vector el = side == "l" ? J_lowerarm_l : J_lowerarm_r;
    vector wr = side == "l" ? J_hand_l : J_hand_r;
    if (top == 0 || top == 4) {
        // T-shirt: a short sleeve, then bare arm.
        vector mid = lerp(sh, el, 0.55);
        limb(sh, mid, 0.058 * bw, 0.052 * bw, sides, shirt, "upperarm_" + side);
        limb(mid, el, 0.046 * bw, 0.042 * bw, sides, skin, "upperarm_" + side);
    } else {
        limb(sh, el, 0.055 * bw, 0.046 * bw, sides, upper_c, "upperarm_" + side);
    }
    limb(el, wr, 0.042 * bw, 0.034 * bw, sides, lower_c, "lowerarm_" + side);
    vector hd = normalize(wr - el);
    blob(wr + hd * 0.045, set(0.035, 0.045, 0.03), 3, sides, 0, 1, 0, skin, "hand_" + side);
}

// Legs and feet.
foreach (string side; LR) {
    vector hip = side == "l" ? J_thigh_l : J_thigh_r;
    vector knee = side == "l" ? J_calf_l : J_calf_r;
    vector ankle = side == "l" ? J_foot_l : J_foot_r;
    vector ball = side == "l" ? J_ball_l : J_ball_r;
    vector thigh_c = bottom == 2 ? skin : pants;
    vector calf_c = bottom == 0 ? pants : skin;
    limb(hip, knee, 0.078 * bw, 0.056 * bw, sides, thigh_c, "thigh_" + side);
    if (bottom == 1) {
        // Shorts: the legs of the shorts stop above the knee.
        limb(hip, lerp(hip, knee, 0.55), 0.083 * bw, 0.07 * bw, sides, pants, "thigh_" + side);
    }
    limb(knee, ankle, 0.054 * bw, 0.04 * bw, sides, calf_c, "calf_" + side);
    if (shoes == 1) limb(lerp(knee, ankle, 0.45), ankle, 0.058 * bw, 0.05 * bw, sides, shoe, "calf_" + side);
    vector toe = ball + set(0, 0, 0.05);
    vector mid = (ankle + toe) * 0.5;
    vector sole = shoes == 2 ? skin : shoe;
    box(set(mid.x, 0.04, mid.z), set(0.045, 0.04, (toe.z - ankle.z) * 0.5 + 0.035), sole, "foot_" + side);
    if (shoes == 2) box(set(mid.x, 0.008, mid.z), set(0.05, 0.008, (toe.z - ankle.z) * 0.5 + 0.04), shoe, "foot_" + side);
    if (shoes == 0) box(set(mid.x, 0.012, mid.z), set(0.048, 0.012, (toe.z - ankle.z) * 0.5 + 0.038), CLOTH[11], "foot_" + side);
}
if (bottom == 2) {
    // Skirt: a flared cone from the waist.
    tube(array(set(0, 1.0, 0.025), set(0, 0.68, 0.025)), array(0.155 * bw, 0.22 * bw), array(0.11 * bw, 0.17 * bw),
         sides + 3, pants, "pelvis");
}

// ================================================================ head
vector hcen = J_head + set(0, 0.075, 0.02) * hs;
vector hr = set(0.105, 0.12, 0.112) * hs;
blob(hcen, hr, 3 + detail / 2, sides + 2, 0, 1, 0, skin, "head");
// Face: two eyes and a small nose.
float fz = hcen.z + hr.z * 0.93;
box(set(hcen.x - 0.04 * hs, hcen.y + 0.01 * hs, fz), set(0.012, 0.016, 0.008) * hs, dark, "head");
box(set(hcen.x + 0.04 * hs, hcen.y + 0.01 * hs, fz), set(0.012, 0.016, 0.008) * hs, dark, "head");
box(set(hcen.x, hcen.y - 0.025 * hs, fz + 0.012 * hs), set(0.012, 0.016, 0.014) * hs, skin * 0.85, "head");

// Hair.
vector hair_r = hr * 1.09;
if (hair == 0) blob(hcen, hair_r, 2, sides + 2, 0.55, 1.0, 0, hc, "head");
if (hair == 1 || hair == 2 || hair == 3) blob(hcen, hair_r * 1.03, 4, sides + 2, 0.3, 1.0, 0.72, hc, "head");
if (hair == 2) box(hcen + set(0, -0.12 * hs, -hr.z * 0.75), set(hr.x * 0.95, 0.12 * hs, 0.03 * hs), hc, "head");
if (hair == 3) blob(hcen + set(0, -0.08 * hs, -hr.z * 1.15), set(0.04, 0.11, 0.04) * hs, 3, sides, 0, 1, 0, hc, "head");
if (hair == 4) {
    blob(hcen, hair_r, 2, sides + 2, 0.5, 1.0, 0.72, hc, "head");
    blob(hcen + set(0, hr.y * 0.95, -hr.z * 0.45), set(0.06, 0.055, 0.06) * hs, 3, sides, 0, 1, 0, hc, "head");
}
if (hair == 5) {
    blob(hcen, hair_r, 2, sides + 2, 0.55, 1.0, 0, hc, "head");
    for (int s = 0; s < 7; s++) {
        float a = s * 2.0 * PI / 7.0;
        vector d = normalize(set(cos(a) * 0.6, 1.0, sin(a) * 0.6 - 0.2));
        cone(hcen + d * hr.y * 0.85, d, 0.03 * hs, 0.08 * hs, 4, hc, "head");
    }
}
if (hair == 6) {
    for (int s = 0; s < 5; s++) {
        float t = (s - 2) / 2.0;
        vector d = normalize(set(0, 1.0, t * 0.9));
        cone(hcen + d * hr.y * 0.9, d, 0.03 * hs, 0.09 * hs, 4, hc, "head");
    }
}
if (hair == 7) {
    for (int s = 0; s < 9; s++) {
        float a = s * 2.39996;
        vector d = normalize(set(cos(a) * 0.8, 0.7 + rand(s) * 0.5, sin(a) * 0.8 - 0.25));
        blob(hcen + d * hr.y * 0.95, set(0.05, 0.05, 0.05) * hs, 2, 5, 0, 1, 0, hc, "head");
    }
}

// Facial hair.
vector mouth = set(hcen.x, hcen.y - 0.055 * hs, fz - 0.005);
if (facial == 1 || facial == 4) box(mouth + set(0, 0.012 * hs, 0.006), set(0.04, 0.009, 0.01) * hs, hc, "head");
if (facial == 2 || facial == 4) blob(hcen, hr * 1.05, 2, sides + 2, 0.05, 0.42, 0, hc, "head");
if (facial == 3) box(mouth + set(0, -0.045 * hs, 0.0), set(0.022, 0.025, 0.02) * hs, hc, "head");

// Hats.
if (hat == 1) {
    blob(hcen, hr * 1.14, 2, sides + 2, 0.6, 1.0, 0, acc, "head");
    box(hcen + set(0, hr.y * 0.3, hr.z * 1.15), set(0.09, 0.008, 0.06) * hs, acc, "head");
}
if (hat == 2) {
    blob(hcen, hr * 1.15, 3, sides + 2, 0.5, 1.0, 0, acc, "head");
    tube(array(hcen + set(0, hr.y * 0.0, 0), hcen + set(0, hr.y * 0.15, 0)), array(hr.x * 1.2, hr.x * 1.2),
         array(hr.z * 1.2, hr.z * 1.2), sides + 2, acc * 0.8, "head");
}
if (hat == 3) {
    tube(array(hcen + set(0, hr.y * 0.55, 0), hcen + set(0, hr.y * 0.62, 0)), array(hr.x * 2.0, hr.x * 2.0),
         array(hr.z * 2.0, hr.z * 2.0), sides + 3, acc, "head");
    cone(hcen + set(0, hr.y * 0.6, 0), set(0.15, 1.0, -0.2), hr.x * 1.05, 0.32 * hs, sides + 1, acc, "head");
}
if (hat == 4) {
    for (int s = 0; s < 9; s++) {
        float a = s * 2.0 * PI / 9.0;
        vector p = hcen + set(sin(a) * hr.x * 1.02, hr.y * 0.55, cos(a) * hr.z * 1.02);
        blob(p, set(0.025, 0.025, 0.025) * hs, 2, 5, 0, 1, 0, s % 2 == 0 ? CLOTH[2] : CLOTH[9], "head");
    }
}
if (hat == 5) {
    blob(hcen, hr * 1.13, 2, sides + 2, 0.55, 1.0, 0, acc, "head");
    tube(array(hcen + set(0, hr.y * 0.35, 0), hcen + set(0, hr.y * 0.15, 0)), array(hr.x * 1.15, hr.x * 1.6),
         array(hr.z * 1.15, hr.z * 1.6), sides + 3, acc, "head");
}

// Extras.
if (extra == 1) {
    box(set(0, 1.25, -0.17 * bw), set(0.12 * bw, 0.15, 0.06), acc, "spine_03");
    box(set(0, 1.17, -0.235 * bw), set(0.09 * bw, 0.06, 0.02), acc * 0.75, "spine_03");
}
if (extra == 2) {
    tube(array(set(0, 1.44, 0.0), set(0, 1.52, 0.0)), array(0.08 * bw, 0.075 * bw), array(0.075 * bw, 0.07 * bw),
         sides + 2, acc, "neck_01");
    box(set(0.05 * bw, 1.33, 0.09 * bw), set(0.025, 0.08, 0.012), acc, "spine_03");
}
if (extra == 3) {
    foreach (float sx; SIGNS)
        tube(array(set(hcen.x + sx * 0.04 * hs, hcen.y + 0.01 * hs, fz + 0.004), set(hcen.x + sx * 0.04 * hs, hcen.y + 0.01 * hs, fz + 0.014)),
             array(0.026 * hs, 0.026 * hs), array(0.026 * hs, 0.026 * hs), 6, dark, "head");
    box(set(hcen.x, hcen.y + 0.012 * hs, fz + 0.01), set(0.018, 0.004, 0.004) * hs, dark, "head");
}
"""


def _menu(name, label, options, default=0):
    labels = [o[0] if isinstance(o, tuple) else o for o in options]
    return hou.MenuParmTemplate(name, label, menu_items=[str(i) for i in range(len(labels))],
                                menu_labels=labels, default_value=default)


ORIENT_VEX = r"""
// For every connected piece: do its faces point away from its middle?
int count = nprimitives(0);
int pieces = 0;
for (int i = 0; i < count; i++) pieces = max(pieces, prim(0, "shape_id", i) + 1);
vector middle[];
int faces[];
float vote[];
resize(middle, pieces); resize(faces, pieces); resize(vote, pieces);
for (int i = 0; i < count; i++) {
    int c = prim(0, "shape_id", i);
    middle[c] += vector(prim(0, "P", i));
    faces[c] += 1;
}
for (int c = 0; c < pieces; c++) middle[c] /= max(faces[c], 1);
for (int i = 0; i < count; i++) {
    int c = prim(0, "shape_id", i);
    vector center = vector(prim(0, "P", i));
    vote[c] += dot(prim_normal(0, i, {0.5, 0.5}), center - middle[c]) > 0 ? 1 : -1;
}
addprimattrib(0, "flip", 0);
for (int i = 0; i < count; i++)
    if (vote[prim(0, "shape_id", i)] < 0) setprimattrib(0, "flip", i, 1);
"""


def build():
    work = hou.node("/obj").createNode("geo", "lpk_character_build")
    subnet = work.createNode("subnet", "lpk_character")
    body = subnet.createNode("attribwrangle", "body")
    body.parm("class").set("detail")
    snippet = CHARACTER_VEX
    for token, text in (("joints", _vex_joints()), ("skin", _vex_colors("SKIN", SKIN)),
                        ("hair_colors", _vex_colors("HAIR_COLOR", HAIR_COLOR)), ("cloth", _vex_colors("CLOTH", CLOTH))):
        snippet = snippet.replace("%(" + token + ")s", text)
    body.parm("snippet").set(snippet)

    # Faces must look outward: Unreal draws only that side, so an inward-facing
    # part looks hollow (you see the inside of the back through the chest).
    # Each connected piece votes; a piece whose faces mostly look inward is flipped.
    pieces = subnet.createNode("connectivity", "pieces")
    pieces.setInput(0, body)
    pieces.parm("connecttype").set("prim")
    pieces.parm("attribname").set("shape_id")
    vote = subnet.createNode("attribwrangle", "outward_vote")
    vote.setInput(0, pieces)
    vote.parm("class").set("detail")
    vote.parm("snippet").set(ORIENT_VEX)
    flip = subnet.createNode("reverse", "flip_inward")
    flip.setInput(0, vote)
    flip.parm("group").set("@flip==1")
    tidy = subnet.createNode("attribdelete", "tidy")
    tidy.setInput(0, flip)
    tidy.parm("primdel").set("shape_id flip")

    facets = subnet.createNode("normal", "facets")
    facets.setInput(0, tidy)
    facets.parm("cuspangle").set(0.0)
    out = subnet.createNode("output", "out")
    out.setInput(0, facets)
    out.setDisplayFlag(True)
    subnet.layoutChildren()

    asset = subnet.createDigitalAsset(name="lpk_character", hda_file_name=HDA_PATH, description="LPK Character",
                                      min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    group = definition.parmTemplateGroup()
    look = hou.FolderParmTemplate("look_folder", "Character", folder_type=hou.folderType.Simple)
    for template in (
        _menu("body", "Body", BODY), _menu("head_size", "Head", HEAD), _menu("skin", "Skin", SKIN),
        _menu("hair", "Hair", HAIR), _menu("hair_color", "Hair Color", HAIR_COLOR),
        _menu("facial_hair", "Facial Hair", FACIAL), _menu("top", "Top", TOP), _menu("top_color", "Top Color", CLOTH),
        _menu("bottom", "Bottom", BOTTOM), _menu("bottom_color", "Bottom Color", CLOTH, 6),
        _menu("shoes", "Shoes", SHOES), _menu("shoe_color", "Shoe Color", CLOTH, 7),
        _menu("hat", "Hat", HAT), _menu("extra", "Extra", EXTRA), _menu("accent_color", "Accent Color", CLOTH, 2),
        hou.IntParmTemplate("detail", "Detail", 1, default_value=(1,), min=1, max=4),
    ):
        look.addParmTemplate(template)
    group.append(look)
    definition.setParmTemplateGroup(group)
    definition.save(HDA_PATH)
    work.destroy()
    print("HDA saved:", HDA_PATH)


if __name__ in ("__main__", "__iwb_bridge__"):
    build()
