"""Configuration and attributes."""

from . import domain

DOMAIN_HANDLERS = {
    "course": domain.course_tools.CourseToolsHandler(),
    "shopping": domain.shopping_tools.ShoppingToolsHandler(),
    "travel": domain.travel_tools.TravelToolsHandler(),
    "workforce": domain.workforce_tools.WorkforceToolsHandler(),
    "meal": domain.meal_tools.MealToolsHandler(),
    "pc_build": domain.pc_build_tools.PcBuildToolsHandler(),
}
