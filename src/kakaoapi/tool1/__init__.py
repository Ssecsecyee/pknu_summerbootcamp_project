# =====================================================
# 낚시장소 Tool
# =====================================================

from .fishing_tool import (
    search_fishing_spots_by_location_name,
    get_fishing_spots
)


# =====================================================
# 위험구역 Tool
# =====================================================

from .danger_tool import (
    search_danger_by_location_name,
    get_danger_zones
)


# =====================================================
# 어종 분류 Tool
# =====================================================

from .fish_classification_tool import (
    classify_fish
)