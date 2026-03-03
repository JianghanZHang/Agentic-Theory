"""
Wrist observer — block pose estimation.

Two modes:
    A. Ground truth: read poses directly from MuJoCo (for sim training).
    B. Vision: pretrained encoder + detection head (for sim2real).

Mode A is used for curriculum phases 1-4.  Mode B is added later
when the vision backbone is integrated.

Each observation is a dict mapping block_body_id → BlockObs.
"""

from dataclasses import dataclass
import numpy as np
import mujoco


@dataclass
class BlockObs:
    """Observation of a single block."""
    body_id: int
    body_name: str
    block_type: str          # 'cube', 'cuboid', 'mortise', 'tenon'
    position: np.ndarray     # (3,) world-frame position
    quaternion: np.ndarray   # (4,) wxyz quaternion
    visible: bool            # whether block is in camera FOV
    mass_estimate: float     # estimated mass (kg); 0 = unknown


# ── Block type registry ───────────────────────────────────────────

_TYPE_FROM_NAME = {
    'block_cube':    'cube',
    'block_cuboid':  'cuboid',
    'block_mortise': 'mortise',
    'block_tenon':   'tenon',
}


def _infer_block_type(body_name: str) -> str:
    """Infer block type from body name (e.g., 'block_cube_0' → 'cube')."""
    for prefix, btype in _TYPE_FROM_NAME.items():
        if body_name.startswith(prefix):
            return btype
    return 'unknown'


# ── Ground-truth observer ─────────────────────────────────────────

class GroundTruthObserver:
    """Mode A: read block poses directly from MuJoCo.

    Parameters
    ----------
    model : MjModel
        Loaded MuJoCo model.
    block_body_names : list[str]
        Names of block bodies in the scene.
    """

    def __init__(self, model: mujoco.MjModel, block_body_names: list[str]):
        self.model = model
        self.block_info = []
        for name in block_body_names:
            bid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name)
            btype = _infer_block_type(name)
            self.block_info.append((bid, name, btype))

    def observe(self, data: mujoco.MjData) -> dict[int, BlockObs]:
        """Return ground-truth poses for all blocks."""
        obs = {}
        for bid, name, btype in self.block_info:
            obs[bid] = BlockObs(
                body_id=bid,
                body_name=name,
                block_type=btype,
                position=data.xpos[bid].copy(),
                quaternion=data.xquat[bid].copy(),
                visible=True,  # always visible in GT mode
                mass_estimate=self.model.body_mass[bid],
            )
        return obs

    @property
    def block_body_ids(self) -> list[int]:
        return [bid for bid, _, _ in self.block_info]


# ── Convenience constructor ───────────────────────────────────────

def make_observer(model: mujoco.MjModel, mode: str = "gt") -> GroundTruthObserver:
    """Create an observer for all blocks in the scene.

    Automatically discovers block bodies by name prefix.
    """
    block_names = []
    for i in range(model.nbody):
        name = model.body(i).name
        if name.startswith('block_'):
            block_names.append(name)

    if mode == "gt":
        return GroundTruthObserver(model, block_names)
    else:
        raise NotImplementedError(f"Vision mode not yet implemented: {mode}")
