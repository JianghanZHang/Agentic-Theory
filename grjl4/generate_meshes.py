"""
Generate STL meshes for the block types (K_type = 1..4).

Types 1-2 use MuJoCo's built-in box geom (no mesh needed).
Types 3-4 require mesh files.

Type 1: 正方体 (cube)            — box 4x4x4 cm
Type 2: 长方体 (cuboid)          — box 4x4x8 cm
Type 3: 卯 (mortise)             — cuboid with triangular notch at bottom
Type 4: 榫 (tenon)               — cuboid with triangular protrusion at top

Constraint: mesh(3) + mesh(4) = box(2) [cuboid]

The triangular cut/protrusion runs the full depth (y-axis),
so the side view (along y) is a plain rectangle for both pieces.
"""

import numpy as np
import struct
from pathlib import Path


def write_stl(path: Path, vertices: np.ndarray, faces: np.ndarray):
    """Write a binary STL file."""
    with open(path, "wb") as f:
        f.write(b"\0" * 80)  # header
        f.write(struct.pack("<I", len(faces)))
        for face in faces:
            v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]
            normal = np.cross(v1 - v0, v2 - v0)
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal /= norm
            f.write(struct.pack("<3f", *normal))
            f.write(struct.pack("<3f", *v0))
            f.write(struct.pack("<3f", *v1))
            f.write(struct.pack("<3f", *v2))
            f.write(struct.pack("<H", 0))


def mortise_half(w: float, h: float, d: float, notch_h: float,
                 side: str = "left") -> tuple:
    """
    One convex half of the mortise (卯).

    MuJoCo computes the convex hull of every mesh, so a single concave
    mortise mesh loses its V-notch.  We decompose the mortise into two
    convex right-trapezoid prisms (left + right) that together recreate
    the concave shape.

    Cross-section (xz plane, front view) — LEFT half shown:

        ┌───────┐        z = +h/2
        │       │
        │       │
        │       ╱        z = -h/2 + notch_h  (notch apex at x=0)
        │      ╱
        └─────┘          z = -h/2

        x=-hw   x=0

    The RIGHT half is the mirror image (x=0 to x=+hw).

    Each half is a convex pentahedron (right-trapezoid prism):
      8 vertices, 12 triangles (6 quad faces, each split into 2 tris).

    Both halves are centred so that x=0 is the shared interface,
    matching the full cuboid's coordinate system.
    """
    hw, hh, hd = w / 2, h / 2, d / 2
    apex_z = -hh + notch_h

    if side == "left":
        # Left half: x ∈ [-hw, 0]
        # Front face (y = -hd): trapezoid with vertices
        #   bottom-left (-hw, -hd, -hh)
        #   bottom-right (0, -hd, -hh)    — but this edge is the slope
        #   Actually: 4 corners of the trapezoid
        verts = np.array([
            # Front face (y = -hd)
            [-hw, -hd, -hh],     # 0: outer bottom
            [0.0, -hd, -hh],     # 1: inner bottom
            [0.0, -hd, apex_z],  # 2: inner top (notch apex level)
            [-hw, -hd,  hh],     # 3: outer top
            # Back face (y = +hd)
            [-hw,  hd, -hh],     # 4: outer bottom
            [0.0,  hd, -hh],     # 5: inner bottom
            [0.0,  hd, apex_z],  # 6: inner top (notch apex level)
            [-hw,  hd,  hh],     # 7: outer top
        ], dtype=np.float32)
    else:
        # Right half: x ∈ [0, +hw], mirrored
        verts = np.array([
            # Front face (y = -hd)
            [0.0, -hd, -hh],     # 0: inner bottom
            [ hw, -hd, -hh],     # 1: outer bottom
            [ hw, -hd,  hh],     # 2: outer top
            [0.0, -hd, apex_z],  # 3: inner top (notch apex level)
            # Back face (y = +hd)
            [0.0,  hd, -hh],     # 4: inner bottom
            [ hw,  hd, -hh],     # 5: outer bottom
            [ hw,  hd,  hh],     # 6: outer top
            [0.0,  hd, apex_z],  # 7: inner top (notch apex level)
        ], dtype=np.float32)

    # Both halves have the same topology: a right-trapezoid prism
    # 6 faces (each a quad = 2 triangles) = 12 triangles total
    #
    # Vertex layout (both sides, after the if/else above):
    #   Front: 0-1-2-3 (trapezoid, y = -hd)
    #   Back:  4-5-6-7 (trapezoid, y = +hd)
    #
    # Outward normals via right-hand rule:
    faces = np.array([
        # Front face (y = -hd), normal = -y
        [0, 1, 2], [0, 2, 3],
        # Back face (y = +hd), normal = +y
        [4, 7, 6], [4, 6, 5],
        # Bottom face (z = -hh), normal = -z
        [0, 4, 5], [0, 5, 1],
        # Top face (outer edge), normal = +z (left) or slope (right)
        [3, 2, 6], [3, 6, 7],
        # Outer face (x = -hw for left, x = +hw for right)
        [0, 3, 7], [0, 7, 4],
        # Inner face (x = 0, the slope), normal = +x (left) or -x (right)
        [1, 5, 6], [1, 6, 2],
    ], dtype=np.int32)

    return verts, faces


def tenon(w: float, h: float, d: float, tab_h: float) -> tuple:
    """
    Tenon (榫): cuboid with a triangular protrusion added on top centre.

    The protrusion is a triangular prism running the full depth (y-axis):
      - protrusion base = w (full width of the cuboid top)
      - protrusion apex at z = +h/2 + tab_h

    Cross-section (xz plane, front view):

              ╱╲           z = +h/2 + tab_h  (protrusion apex)
             ╱  ╲
        ┌───╱────╲───┐    z = +h/2
        │              │
        │              │
        │              │
        └──────────────┘   z = -h/2

    Side view (yz plane): plain rectangle (protrusion runs full depth).

    Centred at the geometric centre of the BASE cuboid (excluding protrusion),
    so the base cuboid spans [-hw, hw] x [-hd, hd] x [-hh, hh].
    """
    hw, hh, hd = w / 2, h / 2, d / 2
    apex_z = hh + tab_h  # z of the protrusion apex

    # 10 vertices
    verts = np.array([
        # Front face (y = -hd), 5 vertices
        [-hw, -hd, -hh],    # 0: bottom-left
        [ hw, -hd, -hh],    # 1: bottom-right
        [ hw, -hd,  hh],    # 2: top-right
        [-hw, -hd,  hh],    # 3: top-left
        [0.0, -hd, apex_z], # 4: protrusion apex (front)
        # Back face (y = +hd), 5 vertices
        [-hw,  hd, -hh],    # 5: bottom-left
        [ hw,  hd, -hh],    # 6: bottom-right
        [ hw,  hd,  hh],    # 7: top-right
        [-hw,  hd,  hh],    # 8: top-left
        [0.0,  hd, apex_z], # 9: protrusion apex (back)
    ], dtype=np.float32)

    faces = np.array([
        # Front face (y = -hd): pentagon = 3 triangles
        [0, 1, 4],   # lower portion
        [0, 4, 3],   # left portion
        [1, 2, 4],   # right portion (but we need: 4 connects to 2 and 3)
        # Actually let's redo: pentagon is 0-1-2-4-3 (ccw from outside = cw looking at -y)
        # Wait, we're looking at front face from -y direction, normals point -y.
        # Pentagon vertices in order: 0(BL), 1(BR), 2(TR), 4(apex), 3(TL)
        # We need CW winding when viewed from -y (i.e., CCW in right-hand rule for -y normal)
        # Actually for front face (y=-hd), outward normal is -y.
        # Right-hand rule: CCW when looking from outside (-y direction) = CW in our coords
        # Let me just do it carefully:
        #   Front face normal should point -y.
        #   Triangle (a,b,c): normal = (b-a)x(c-a)
        #   For [0,1,2]: (1-0)x(2-0) = (+x)x(+z) = -y  ✓
    ], dtype=np.int32)

    # Redo faces properly
    faces = np.array([
        # Front face (y = -hd): pentagon 0-1-2-4-3, normal = -y
        [0, 1, 2],
        [0, 2, 4],
        [0, 4, 3],
        # Back face (y = +hd): pentagon 5-6-7-9-8, normal = +y
        [5, 8, 9],
        [5, 9, 7],
        [5, 7, 6],
        # Bottom face
        [0, 5, 6], [0, 6, 1],
        # Left face (x = -hw)
        [0, 3, 8], [0, 8, 5],
        # Right face (x = +hw)
        [1, 6, 7], [1, 7, 2],
        # Top-left slope (protrusion left face)
        [3, 4, 9], [3, 9, 8],
        # Top-right slope (protrusion right face)
        [2, 7, 9], [2, 9, 4],
    ], dtype=np.int32)

    return verts, faces


## ── Scale support ────────────────────────────────────────────────

# Discrete scale factors for mesh types (mortise, tenon).
# Box types (cube, cuboid) are scaled at runtime via model.geom_size.
SCALES = [0.7, 1.0, 1.3]


def scale_tag(s: float) -> str:
    """'s070', 's100', 's130' — used in filenames and XML mesh names."""
    return f"s{int(s * 100):03d}"


def main():
    out = Path(__file__).parent / "assets"
    out.mkdir(exist_ok=True)

    # Base dimensions (metres) — all fit in 80mm gripper at scale 1.0
    CUBOID_W = 0.04  # 4cm wide
    CUBOID_H = 0.08  # 8cm tall (full cuboid = type 2)
    CUBOID_D = 0.04  # 4cm deep
    HALF_H = CUBOID_H / 2  # 4cm per piece
    NOTCH_H = 0.02  # 2cm notch depth / tab height

    for scale in SCALES:
        tag = scale_tag(scale)
        w = CUBOID_W * scale
        h = HALF_H * scale
        d = CUBOID_D * scale
        nh = NOTCH_H * scale

        # Type 3: mortise (卯) — two convex halves
        for side in ("left", "right"):
            lr = "L" if side == "left" else "R"
            v, f = mortise_half(w=w, h=h, d=d, notch_h=nh, side=side)
            # scale 1.0 → canonical names (backwards compatible)
            if scale == 1.0:
                fname = f"mortise_{lr}.stl"
            else:
                fname = f"mortise_{lr}_{tag}.stl"
            write_stl(out / fname, v, f)
            print(f"mortise {lr} (scale {scale}): {len(v)} verts, "
                  f"{len(f)} tris → {fname}")

        # Type 4: tenon (榫)
        v, f = tenon(w=w, h=h, d=d, tab_h=nh)
        if scale == 1.0:
            fname = "tenon.stl"
        else:
            fname = f"tenon_{tag}.stl"
        write_stl(out / fname, v, f)
        print(f"tenon    (scale {scale}): {len(v)} verts, "
              f"{len(f)} tris → {fname}")

    # Verify complementarity at each scale
    print(f"\nVolume check (mortise + tenon = cuboid) per scale:")
    for scale in SCALES:
        w = CUBOID_W * scale
        h = HALF_H * scale
        d = CUBOID_D * scale
        nh = NOTCH_H * scale
        vol_half = w * h * d
        vol_tri = 0.5 * w * nh * d
        vol_mortise = vol_half - vol_tri
        vol_tenon = vol_half + vol_tri
        vol_cuboid = w * (2 * h) * d
        ok = abs(vol_mortise + vol_tenon - vol_cuboid) < 1e-12
        print(f"  scale {scale}: {vol_mortise*1e6:.1f} + "
              f"{vol_tenon*1e6:.1f} = {(vol_mortise+vol_tenon)*1e6:.1f} "
              f"vs cuboid {vol_cuboid*1e6:.1f} cm³  {'✓' if ok else '✗'}")

    # Clean up old mesh files
    for old in ["triangular_prism.stl", "half_cylinder.stl", "arch.stl",
                 "mortise.stl"]:
        p = out / old
        if p.exists():
            p.unlink()
            print(f"Removed old mesh: {old}")


if __name__ == "__main__":
    main()
