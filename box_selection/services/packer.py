"""
Pure-Python 3D Bin Packing and Geometric Placement Engine.
Supports 6-DOF item rotation, 3D coordinate collision detection,
weight enforcement, and spatial utilization metrics.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any


@dataclass
class ItemToPack:
    name: str
    sku: str
    length: float
    width: float
    height: float
    weight: float
    is_fragile: bool = False
    allow_rotation: bool = True
    quantity: int = 1

    @property
    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class PlacedItem:
    name: str
    sku: str
    x: float
    y: float
    z: float
    length: float  # Dimension along X axis in packed orientation
    width: float   # Dimension along Y axis in packed orientation
    height: float  # Dimension along Z axis in packed orientation
    weight: float
    is_fragile: bool = False

    def overlaps_with(self, other: 'PlacedItem') -> bool:
        """Check if two 3D cuboids intersect in Cartesian space."""
        # Check X overlap
        if self.x >= other.x + other.length or self.x + self.length <= other.x:
            return False
        # Check Y overlap
        if self.y >= other.y + other.width or self.y + self.width <= other.y:
            return False
        # Check Z overlap
        if self.z >= other.z + other.height or self.z + self.height <= other.z:
            return False
        return True


@dataclass
class PackingResult:
    fitted: bool
    box_id: Optional[int]
    box_name: str
    box_code: str
    box_dimensions: Tuple[float, float, float]
    box_volume: float
    box_max_weight: float
    box_cost: float
    packed_items: List[PlacedItem] = field(default_factory=list)
    unpacked_items: List[Dict[str, Any]] = field(default_factory=list)
    total_packed_weight: float = 0.0
    total_packed_volume: float = 0.0
    volume_utilization: float = 0.0
    weight_utilization: float = 0.0
    rejection_reason: Optional[str] = None


class BoxPacker3D:
    """
    3D Coordinate Packing Engine.
    Employs an Anchor-Point First-Fit Decreasing heuristic with 3D rotation.
    """

    @staticmethod
    def get_rotations(length: float, width: float, height: float, allow_rotation: bool = True) -> List[Tuple[float, float, float]]:
        """
        Return valid 3D orientations.
        If allow_rotation is True: all 6 permutations.
        If False (e.g. liquid/upright): only yaw rotation around Z axis (2 permutations).
        """
        if not allow_rotation:
            return [
                (length, width, height),
                (width, length, height),
            ]
        
        unique_orientations = {
            (length, width, height),
            (length, height, width),
            (width, length, height),
            (width, height, length),
            (height, length, width),
            (height, width, length),
        }
        return list(unique_orientations)

    @classmethod
    def pack(
        cls,
        box_length: float,
        box_width: float,
        box_height: float,
        box_max_weight: float,
        items: List[ItemToPack],
        box_id: Optional[int] = None,
        box_name: str = "",
        box_code: str = "",
        box_cost: float = 0.0,
    ) -> PackingResult:
        """
        Simulate packing a list of items into a box.
        Returns PackingResult with fitted status, item coordinates, and metrics.
        """
        box_volume = box_length * box_width * box_height

        # Flatten items by quantity
        expanded_items: List[Dict[str, Any]] = []
        total_items_weight = 0.0
        total_items_volume = 0.0

        for itm in items:
            for i in range(itm.quantity):
                expanded_items.append({
                    'name': itm.name,
                    'sku': itm.sku,
                    'length': itm.length,
                    'width': itm.width,
                    'height': itm.height,
                    'weight': itm.weight,
                    'volume': itm.volume,
                    'is_fragile': itm.is_fragile,
                    'allow_rotation': itm.allow_rotation,
                })
                total_items_weight += itm.weight
                total_items_volume += itm.volume

        base_result = PackingResult(
            fitted=False,
            box_id=box_id,
            box_name=box_name,
            box_code=box_code,
            box_dimensions=(box_length, box_width, box_height),
            box_volume=round(box_volume, 2),
            box_max_weight=box_max_weight,
            box_cost=box_cost,
            total_packed_weight=round(total_items_weight, 3),
            total_packed_volume=round(total_items_volume, 2),
        )

        # 1. Weight Constraint Validation
        if total_items_weight > box_max_weight:
            base_result.rejection_reason = (
                f"Weight limit exceeded: Order weight ({total_items_weight:.2f} kg) "
                f"exceeds box capacity ({box_max_weight:.2f} kg) by {total_items_weight - box_max_weight:.2f} kg."
            )
            return base_result

        # 2. Volume Constraint Validation
        if total_items_volume > box_volume:
            base_result.rejection_reason = (
                f"Volume exceeded: Total item volume ({total_items_volume:.1f} cm³) "
                f"exceeds box volume ({box_volume:.1f} cm³)."
            )
            return base_result

        # 3. Individual Dimension Feasibility Check
        sorted_box_dims = sorted([box_length, box_width, box_height], reverse=True)
        for itm in expanded_items:
            sorted_itm_dims = sorted([itm['length'], itm['width'], itm['height']], reverse=True)
            if any(i_dim > b_dim for i_dim, b_dim in zip(sorted_itm_dims, sorted_box_dims)):
                base_result.rejection_reason = (
                    f"Product '{itm['name']}' dimensions ({itm['length']}×{itm['width']}×{itm['height']} cm) "
                    f"exceed box dimensions ({box_length}×{box_width}×{box_height} cm) in all rotations."
                )
                return base_result

        # 4. Sort Items for Packing: First-Fit Decreasing
        # Primary: Volume descending, Secondary: Weight descending (heavier/bigger at base)
        sorted_items = sorted(
            expanded_items,
            key=lambda x: (x['volume'], x['weight'], max(x['length'], x['width'], x['height'])),
            reverse=True
        )

        placed_items: List[PlacedItem] = []
        # Candidate anchor points: list of (x, y, z) coordinates where an item can be placed
        pivot_points = [(0.0, 0.0, 0.0)]

        for item_data in sorted_items:
            placed = False
            rotations = cls.get_rotations(
                item_data['length'],
                item_data['width'],
                item_data['height'],
                item_data['allow_rotation']
            )

            # Sort pivot points to pack bottom-up (z asc), back-to-front (y asc), left-to-right (x asc)
            pivot_points.sort(key=lambda pt: (pt[2], pt[1], pt[0]))

            best_point = None
            best_rotation = None

            for pt in pivot_points:
                px, py, pz = pt

                for r_len, r_wid, r_hgt in rotations:
                    # Boundary check
                    if px + r_len > box_length or py + r_wid > box_width or pz + r_hgt > box_height:
                        continue

                    candidate = PlacedItem(
                        name=item_data['name'],
                        sku=item_data['sku'],
                        x=px,
                        y=py,
                        z=pz,
                        length=r_len,
                        width=r_wid,
                        height=r_hgt,
                        weight=item_data['weight'],
                        is_fragile=item_data['is_fragile'],
                    )

                    # Collision check with already placed items
                    has_collision = any(candidate.overlaps_with(p) for p in placed_items)
                    if not has_collision:
                        best_point = pt
                        best_rotation = (r_len, r_wid, r_hgt)
                        break

                if best_point is not None:
                    break

            if best_point is not None and best_rotation is not None:
                px, py, pz = best_point
                r_len, r_wid, r_hgt = best_rotation

                new_item = PlacedItem(
                    name=item_data['name'],
                    sku=item_data['sku'],
                    x=px,
                    y=py,
                    z=pz,
                    length=r_len,
                    width=r_wid,
                    height=r_hgt,
                    weight=item_data['weight'],
                    is_fragile=item_data['is_fragile'],
                )
                placed_items.append(new_item)

                # Remove the used pivot point
                pivot_points.remove(best_point)

                # Generate new candidate anchor points from the 3 exposed faces
                new_anchors = [
                    (px + r_len, py, pz),
                    (px, py + r_wid, pz),
                    (px, py, pz + r_hgt),
                ]
                for anchor in new_anchors:
                    if (anchor[0] < box_length and anchor[1] < box_width and anchor[2] < box_height
                            and anchor not in pivot_points):
                        pivot_points.append(anchor)
                placed = True
            else:
                # Item could not be placed due to 3D geometry
                base_result.unpacked_items.append(item_data)

        if len(placed_items) == len(sorted_items):
            # All items successfully placed!
            base_result.fitted = True
            base_result.placed_items = placed_items
            base_result.volume_utilization = round((total_items_volume / box_volume) * 100, 1)
            base_result.weight_utilization = round((total_items_weight / box_max_weight) * 100, 1)
            base_result.rejection_reason = None
            return base_result
        else:
            base_result.fitted = False
            base_result.rejection_reason = (
                f"3D packing collision: Only {len(placed_items)} of {len(sorted_items)} items could fit "
                f"due to geometric spatial arrangement constraints."
            )
            return base_result
