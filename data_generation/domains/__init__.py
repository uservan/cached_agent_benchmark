from .course import SPEC as COURSE_SPEC, build_item as build_course_item
from .meal import SPEC as MEAL_SPEC, build_item as build_meal_item
from .pc_build import SPEC as PC_BUILD_SPEC, build_item as build_pc_build_item
from .shopping import SPEC as SHOPPING_SPEC, build_item as build_shopping_item
from .travel import SPEC as TRAVEL_SPEC, build_item as build_travel_item
from .workforce import SPEC as WORKFORCE_SPEC, build_item as build_workforce_item


DOMAIN_SPECS = {
    "course": COURSE_SPEC,
    "shopping": SHOPPING_SPEC,
    "travel": TRAVEL_SPEC,
    "workforce": WORKFORCE_SPEC,
    "meal": MEAL_SPEC,
    "pc_build": PC_BUILD_SPEC,
}

DOMAIN_BUILDERS = {
    "course": build_course_item,
    "shopping": build_shopping_item,
    "travel": build_travel_item,
    "workforce": build_workforce_item,
    "meal": build_meal_item,
    "pc_build": build_pc_build_item,
}

SUPPORTED_DOMAINS = tuple(DOMAIN_SPECS.keys())
