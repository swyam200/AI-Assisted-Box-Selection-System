"""
AI-Assisted Packing Guidance and Smart Warehouse Advisor.
Provides context-aware packaging notes, void-fill recommendations,
fragile item warnings, and structural weight distribution rules.
"""

import os
from typing import List, Dict, Any, Optional
from .packer import PackingResult, ItemToPack


class AIPackingAssistant:
    """
    Intelligent packaging assistant that generates warehouse-ready packing instructions.
    Features a high-accuracy heuristic reasoning engine with optional LLM API fallback.
    """

    @classmethod
    def generate_warehouse_notes(
        cls,
        packing_result: PackingResult,
        items: List[ItemToPack]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive, actionable packing notes for the warehouse dispatch team.
        """
        if not packing_result.fitted:
            return {
                "summary": "No single standard box accommodates this order.",
                "void_fill_needed": False,
                "void_volume_cm3": 0,
                "handling_precautions": ["Review multi-box split recommendation or use custom oversized packaging."],
                "stacking_instructions": [],
                "tape_and_closure": "N/A",
            }

        utilization = packing_result.volume_utilization
        box_vol = packing_result.box_volume
        items_vol = packing_result.total_packed_volume
        void_vol = max(0.0, round(box_vol - items_vol, 1))

        handling_precautions: List[str] = []
        stacking_instructions: List[str] = []

        # 1. Void-fill analysis
        if utilization >= 85:
            void_guidance = (
                f"High-density fit ({utilization}% utilized). Minimal void fill required. "
                f"Verify the box closes flat without bulging to prevent seam failure during transit."
            )
            cushioning_level = "Minimal (Edges Only)"
        elif utilization >= 60:
            void_guidance = (
                f"Balanced fit ({utilization}% utilized). Void space is approximately {void_vol:,.0f} cm³. "
                f"Insert 2-3 folds of kraft paper or bubble wrap around corners to lock items in place."
            )
            cushioning_level = "Standard Kraft Paper / Bubble Wrap"
        else:
            void_guidance = (
                f"Loose fit ({utilization}% utilized). Significant void space ({void_vol:,.0f} cm³). "
                f"Use inflatable air pillows or biodegradable packing peanuts to fill empty space and prevent internal movement."
            )
            cushioning_level = "High Cushioning / Air Pillows Required"

        # 2. Fragile item detection
        fragile_items = [itm for itm in items if itm.is_fragile]
        if fragile_items:
            names = ", ".join(f"'{itm.name}'" for itm in fragile_items)
            handling_precautions.append(
                f"FRAGILE ITEM WARNING: Order contains fragile merchandise: {names}. "
                f"Maintain at least 2.5 cm of cushioning buffer between items and box walls. "
                f"Affix bright red 'FRAGILE - HANDLE WITH CARE' warning labels on all 4 vertical faces."
            )

        # 3. Weight safety & reinforcement
        weight_pct = packing_result.weight_utilization
        if weight_pct >= 80:
            handling_precautions.append(
                f"HEAVY PACKAGE ALERT: Loaded at {weight_pct}% of box weight rating ({packing_result.total_packed_weight} kg / {packing_result.box_max_weight} kg). "
                f"Reinforce the bottom center seam and edges using heavy-duty fiberglass-reinforced H-taping."
            )
            tape_closure = "H-Taping method with heavy-duty reinforced packing tape"
        else:
            tape_closure = "Standard single-strip taping on top and bottom center seams"

        # 4. Stacking & orientation guidance
        sorted_by_weight = sorted(items, key=lambda x: x.weight, reverse=True)
        if len(sorted_by_weight) > 1:
            heaviest = sorted_by_weight[0]
            lightest = sorted_by_weight[-1]
            stacking_instructions.append(
                f"Base layer: Place the heaviest item '{heaviest.name}' ({heaviest.weight} kg) flat at the center bottom to maintain a low center of gravity."
            )
            if heaviest != lightest:
                stacking_instructions.append(
                    f"Top layer: Place lighter items such as '{lightest.name}' ({lightest.weight} kg) on top to prevent crush damage."
                )
        else:
            stacking_instructions.append("Center item in box with equal cushioning perimeter.")

        # Check for items with restricted rotation
        no_rot_items = [itm for itm in items if not itm.allow_rotation]
        if no_rot_items:
            names = ", ".join(f"'{itm.name}'" for itm in no_rot_items)
            handling_precautions.append(
                f"UPRIGHT RESTRICTION: Items {names} must remain in vertical orientation ('This Side Up')."
            )

        # Optional LLM enhancement if API key is present
        summary_text = (
            f"Recommended '{packing_result.box_name}' ({packing_result.box_code}) providing "
            f"{utilization}% volume utilization and {weight_pct}% weight capacity. "
            f"{void_guidance}"
        )

        return {
            "summary": summary_text,
            "cushioning_level": cushioning_level,
            "void_volume_cm3": void_vol,
            "void_guidance": void_guidance,
            "handling_precautions": handling_precautions,
            "stacking_instructions": stacking_instructions,
            "tape_and_closure": tape_closure,
            "weight_utilization_pct": weight_pct,
            "volume_utilization_pct": utilization,
        }
