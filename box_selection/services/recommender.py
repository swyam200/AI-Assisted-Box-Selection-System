"""
High-Level Box Recommendation Service.
Orchestrates candidate box filtering, 3D packing simulation, cost-minimization ranking,
multi-box fallback partitioning, and AI packing guidance.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from .packer import BoxPacker3D, ItemToPack, PackingResult
from .ai_assistant import AIPackingAssistant


class BoxRecommenderService:
    """
    Main recommendation engine.
    Finds the optimal shipping box that satisfies geometric, weight, and operational constraints
    while minimizing packaging cost.
    """

    @classmethod
    def recommend_for_items(
        cls,
        items: List[ItemToPack],
        boxes: Optional[List[Any]] = None,
        save_history_for_order: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate candidate boxes and return recommendation result.
        'boxes' can be a list of Box model instances or dicts. If None, queries Box.objects.filter(is_active=True).
        """
        if boxes is None:
            from box_selection.models import Box
            boxes = list(Box.objects.filter(is_active=True))

        if not items:
            return {
                "success": False,
                "message": "No items provided for packaging recommendation.",
                "recommended_box": None,
                "alternatives": [],
                "rejected_boxes": [],
                "multi_box_recommendation": None,
                "ai_notes": None,
            }

        total_weight = sum(itm.weight * itm.quantity for itm in items)
        total_volume = sum(itm.volume * itm.quantity for itm in items)

        successful_results: List[PackingResult] = []
        rejected_results: List[PackingResult] = []

        for b in boxes:
            # Handle both Django Model instance and dict/mock object
            b_id = getattr(b, 'id', None)
            b_name = getattr(b, 'name', '')
            b_code = getattr(b, 'code', '')
            b_len = float(getattr(b, 'length', 0.0))
            b_wid = float(getattr(b, 'width', 0.0))
            b_hgt = float(getattr(b, 'height', 0.0))
            b_max_wt = float(getattr(b, 'max_weight', 0.0))
            b_cost = float(getattr(b, 'cost', 0.0))

            res = BoxPacker3D.pack(
                box_length=b_len,
                box_width=b_wid,
                box_height=b_hgt,
                box_max_weight=b_max_wt,
                items=items,
                box_id=b_id,
                box_name=b_name,
                box_code=b_code,
                box_cost=b_cost,
            )

            if res.fitted:
                successful_results.append(res)
            else:
                rejected_results.append(res)

        # Optimization & Ranking:
        # 1. Cost ascending (cheapest box first)
        # 2. Volume ascending (minimizes excess void space for tie-breaks)
        successful_results.sort(key=lambda r: (r.box_cost, r.box_volume))

        if successful_results:
            best_fit = successful_results[0]
            alternatives = successful_results[1:]
            ai_notes = AIPackingAssistant.generate_warehouse_notes(best_fit, items)

            response_data = {
                "success": True,
                "message": f"Optimal box found: {best_fit.box_name} (${best_fit.box_cost:.2f})",
                "recommended_box": {
                    "box_id": best_fit.box_id,
                    "name": best_fit.box_name,
                    "code": best_fit.box_code,
                    "dimensions": {
                        "length": best_fit.box_dimensions[0],
                        "width": best_fit.box_dimensions[1],
                        "height": best_fit.box_dimensions[2],
                    },
                    "cost": best_fit.box_cost,
                    "box_volume_cm3": best_fit.box_volume,
                    "max_weight_kg": best_fit.box_max_weight,
                    "total_order_weight_kg": round(total_weight, 3),
                    "total_order_volume_cm3": round(total_volume, 2),
                    "volume_utilization_pct": best_fit.volume_utilization,
                    "weight_utilization_pct": best_fit.weight_utilization,
                    "items_packed_count": len(best_fit.placed_items),
                    "coordinates": [
                        {
                            "name": p.name,
                            "sku": p.sku,
                            "x": p.x,
                            "y": p.y,
                            "z": p.z,
                            "length": p.length,
                            "width": p.width,
                            "height": p.height,
                            "weight": p.weight,
                        }
                        for p in best_fit.placed_items
                    ],
                },
                "alternatives": [
                    {
                        "box_id": alt.box_id,
                        "name": alt.box_name,
                        "code": alt.box_code,
                        "cost": alt.box_cost,
                        "cost_diff": round(alt.box_cost - best_fit.box_cost, 2),
                        "volume_utilization_pct": alt.volume_utilization,
                        "weight_utilization_pct": alt.weight_utilization,
                    }
                    for alt in alternatives
                ],
                "rejected_boxes": [
                    {
                        "box_id": rej.box_id,
                        "name": rej.box_name,
                        "code": rej.box_code,
                        "cost": rej.box_cost,
                        "reason": rej.rejection_reason,
                    }
                    for rej in rejected_results
                ],
                "multi_box_recommendation": None,
                "ai_notes": ai_notes,
            }

            # Optional persistence to history
            if save_history_for_order:
                cls._persist_history(save_history_for_order, best_fit, ai_notes)

            return response_data
        else:
            # No single box fits -> compute multi-box split
            multi_box = cls.partition_multi_box(items, boxes)
            ai_notes = {
                "summary": "Order exceeds the physical or weight capacity of all single available boxes. Multi-box shipment recommended.",
                "void_guidance": "Pack items into separate boxes as indicated in the multi-box split schedule.",
                "handling_precautions": [
                    "Multi-package shipment: Ensure all parcels are labeled with master shipment tracking (e.g., 'Box 1 of 2', 'Box 2 of 2')."
                ],
                "stacking_instructions": ["Distribute heavy and fragile items according to the per-box plan."],
                "tape_and_closure": "Reinforce all cartons with heavy-duty box tape.",
            }

            return {
                "success": False,
                "message": "No single available box can accommodate this order. Multi-box shipment plan generated.",
                "recommended_box": None,
                "alternatives": [],
                "rejected_boxes": [
                    {
                        "box_id": rej.box_id,
                        "name": rej.box_name,
                        "code": rej.box_code,
                        "cost": rej.box_cost,
                        "reason": rej.rejection_reason,
                    }
                    for rej in rejected_results
                ],
                "multi_box_recommendation": multi_box,
                "ai_notes": ai_notes,
            }

    @classmethod
    def partition_multi_box(cls, items: List[ItemToPack], boxes: List[Any]) -> Dict[str, Any]:
        """
        Greedy multi-box partitioner for orders that exceed single box capacity.
        Assigns items to minimal cost boxes iteratively.
        """
        # Flatten all items into single unit items
        remaining_units: List[ItemToPack] = []
        for itm in items:
            for _ in range(itm.quantity):
                remaining_units.append(ItemToPack(
                    name=itm.name,
                    sku=itm.sku,
                    length=itm.length,
                    width=itm.width,
                    height=itm.height,
                    weight=itm.weight,
                    is_fragile=itm.is_fragile,
                    allow_rotation=itm.allow_rotation,
                    quantity=1
                ))

        # Sort units largest first
        remaining_units.sort(key=lambda u: (u.volume, u.weight), reverse=True)

        assigned_boxes: List[Dict[str, Any]] = []
        total_cost = 0.0

        # Sort candidate boxes by cost ascending
        available_boxes = sorted(boxes, key=lambda b: (float(getattr(b, 'cost', 0.0)), float(getattr(b, 'length', 0.0)) * float(getattr(b, 'width', 0.0)) * float(getattr(b, 'height', 0.0))))

        while remaining_units:
            best_batch_result = None
            best_box = None
            items_to_remove = []

            # Try to pack as many remaining units as possible into the best available box
            for b in available_boxes:
                b_len = float(getattr(b, 'length', 0.0))
                b_wid = float(getattr(b, 'width', 0.0))
                b_hgt = float(getattr(b, 'height', 0.0))
                b_max_wt = float(getattr(b, 'max_weight', 0.0))
                b_cost = float(getattr(b, 'cost', 0.0))
                b_name = getattr(b, 'name', '')
                b_code = getattr(b, 'code', '')

                # Greedily test subsets
                packed_subset: List[ItemToPack] = []
                for unit in remaining_units:
                    test_list = packed_subset + [unit]
                    res = BoxPacker3D.pack(
                        box_length=b_len,
                        box_width=b_wid,
                        box_height=b_hgt,
                        box_max_weight=b_max_wt,
                        items=test_list,
                        box_name=b_name,
                        box_code=b_code,
                        box_cost=b_cost,
                    )
                    if res.fitted:
                        packed_subset.append(unit)

                if packed_subset:
                    if best_batch_result is None or len(packed_subset) > len(items_to_remove):
                        best_box = b
                        items_to_remove = packed_subset
                        best_batch_result = BoxPacker3D.pack(
                            box_length=b_len,
                            box_width=b_wid,
                            box_height=b_hgt,
                            box_max_weight=b_max_wt,
                            items=packed_subset,
                            box_name=b_name,
                            box_code=b_code,
                            box_cost=b_cost,
                        )

            if not items_to_remove:
                # An item is completely unpackable even alone in any box
                unfit = remaining_units.pop(0)
                assigned_boxes.append({
                    "box_name": "CUSTOM / OVERSIZED CRATE REQUIRED",
                    "box_code": "CUSTOM",
                    "cost": 0.0,
                    "items": [{"name": unfit.name, "sku": unfit.sku, "weight": unfit.weight}],
                    "warning": f"Item '{unfit.name}' exceeds the dimensions or weight capacity of all standard boxes."
                })
                continue

            for unit in items_to_remove:
                remaining_units.remove(unit)

            total_cost += float(getattr(best_box, 'cost', 0.0))
            assigned_boxes.append({
                "box_name": getattr(best_box, 'name', ''),
                "box_code": getattr(best_box, 'code', ''),
                "cost": float(getattr(best_box, 'cost', 0.0)),
                "items": [{"name": u.name, "sku": u.sku, "weight": u.weight} for u in items_to_remove],
                "volume_utilization_pct": best_batch_result.volume_utilization if best_batch_result else 0.0,
                "weight_utilization_pct": best_batch_result.weight_utilization if best_batch_result else 0.0,
            })

        return {
            "total_boxes_needed": len(assigned_boxes),
            "estimated_total_cost": round(total_cost, 2),
            "box_breakdown": assigned_boxes,
        }

    @classmethod
    def _persist_history(cls, order: Any, packing_result: PackingResult, ai_notes: Dict[str, Any]):
        try:
            from box_selection.models import BoxRecommendationHistory, Box
            box_instance = None
            if packing_result.box_id:
                box_instance = Box.objects.filter(id=packing_result.box_id).first()

            BoxRecommendationHistory.objects.create(
                order=order,
                recommended_box=box_instance,
                is_feasible=packing_result.fitted,
                total_weight=packing_result.total_packed_weight,
                total_volume=packing_result.total_packed_volume,
                utilization_rate=packing_result.volume_utilization,
                box_cost=Decimal(str(packing_result.box_cost)),
                packing_layout_json={
                    "coordinates": [
                        {
                            "name": p.name,
                            "sku": p.sku,
                            "x": p.x,
                            "y": p.y,
                            "z": p.z,
                            "length": p.length,
                            "width": p.width,
                            "height": p.height,
                        }
                        for p in packing_result.placed_items
                    ]
                },
                ai_notes=ai_notes.get("summary", "")
            )
        except Exception:
            pass  # Non-fatal if history logging fails
