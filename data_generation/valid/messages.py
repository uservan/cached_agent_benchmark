DOMAIN_ITEM_LABELS = {
    "course": ("course", "courses"),
    "shopping": ("product", "products"),
    "travel": ("activity", "activities"),
    "workforce": ("worker", "workers"),
    "meal": ("dish", "dishes"),
    "pc_build": ("component", "components"),
}


def label_for_attr(attr_name):
    return attr_name.replace("_", " ")


def format_rule_message(domain, rule, value, scope_text):
    item_singular, item_plural = DOMAIN_ITEM_LABELS[domain]
    rule_type = rule["type"]

    if rule_type == "sum_min":
        return f"the total {label_for_attr(rule['attr'])} of all {item_plural} in {scope_text} must be at least {value}"
    if rule_type == "sum_max":
        return f"the total {label_for_attr(rule['attr'])} of all {item_plural} in {scope_text} must be at most {value}"
    if rule_type == "max_cap":
        return f"the maximum {label_for_attr(rule['attr'])} of any {item_singular} in {scope_text} must be at most {value}"
    if rule_type == "repeat_max":
        return f"the same {label_for_attr(rule['attr'])} can appear at most {value} times in {scope_text}"
    if rule_type == "count_min":
        return (
            f"there must be at least {value} {item_plural} in {scope_text} whose "
            f"{label_for_attr(rule['predicate_key'])} is {rule['predicate_value']}"
        )
    if rule_type == "count_min_threshold":
        return (
            f"there must be at least {value} {item_plural} in {scope_text} whose "
            f"{label_for_attr(rule['attr'])} is at least {rule['threshold']}"
        )
    if rule_type == "max_row_sum":
        return f"for any single row in {scope_text}, the total {label_for_attr(rule['attr'])} must be at most {value}"
    return f"constraint '{rule['name']}' failed in {scope_text}"
