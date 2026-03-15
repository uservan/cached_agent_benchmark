import json
import os
import sys
from dataclasses import dataclass

try:
    from .config import get_grid_description, get_task_instruction
except ImportError:
    from config import get_grid_description, get_task_instruction

try:
    from data_generation.domains import DOMAIN_SPECS
except ImportError:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
    if PROJECT_ROOT not in sys.path:
        sys.path.append(PROJECT_ROOT)
    from data_generation.domains import DOMAIN_SPECS


DEFAULT_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

DOMAIN_ITEM_LABELS = {
    "course": ("course", "courses"),
    "shopping": ("product", "products"),
    "travel": ("activity", "activities"),
    "workforce": ("worker", "workers"),
    "meal": ("dish", "dishes"),
    "pc_build": ("component", "components"),
}

ATTRIBUTE_LABELS = {
    "credits": "credits",
    "price": "price",
    "difficulty": "difficulty",
    "teacher": "teacher",
    "calories": "calories",
    "protein": "protein",
    "brand": "brand",
    "cost": "cost",
    "duration": "duration",
    "crowd_level": "crowd level",
    "location": "location",
    "skill": "skill",
    "hourly_cost": "hourly cost",
    "experience": "experience",
    "cuisine": "cuisine",
    "dish_id": "dish",
    "performance": "performance",
    "power": "power",
    "worker_id": "worker",
}


@dataclass
class SavedDatasetObject:
    domain: str
    instance_id: str
    meta: dict
    global_constraints: dict
    row_constraints: list
    col_constraints: list
    item_pool: dict
    truth_solution: list
    slots: list
    task_instruction: str
    source_path: str
    source_filename: str


def _label_for_attr(attr_name):
    return ATTRIBUTE_LABELS.get(attr_name, attr_name.replace("_", " "))


def _format_rule_text(domain, rule, value, scope_text):
    item_singular, item_plural = DOMAIN_ITEM_LABELS[domain]
    rule_type = rule["type"]

    if rule_type == "sum_min":
        attr_label = _label_for_attr(rule["attr"])
        return f"the total {attr_label} of all {item_plural} in {scope_text} must be at least {value}"

    if rule_type == "sum_max":
        attr_label = _label_for_attr(rule["attr"])
        return f"the total {attr_label} of all {item_plural} in {scope_text} must be at most {value}"

    if rule_type == "max_cap":
        attr_label = _label_for_attr(rule["attr"])
        return f"the maximum {attr_label} of any {item_singular} in {scope_text} must be at most {value}"

    if rule_type == "repeat_max":
        attr_label = _label_for_attr(rule["attr"])
        return f"the same {attr_label} can appear at most {value} times in {scope_text}"

    if rule_type == "count_min":
        predicate_key = _label_for_attr(rule["predicate_key"])
        predicate_value = rule["predicate_value"]
        return (
            f"there must be at least {value} {item_plural} in {scope_text} whose "
            f"{predicate_key} is {predicate_value}"
        )

    if rule_type == "count_min_threshold":
        attr_label = _label_for_attr(rule["attr"])
        threshold = rule["threshold"]
        return (
            f"there must be at least {value} {item_plural} in {scope_text} whose "
            f"{attr_label} is at least {threshold}"
        )

    if rule_type == "max_row_sum":
        attr_label = _label_for_attr(rule["attr"])
        return f"for any single row in {scope_text}, the total {attr_label} must be at most {value}"

    raise ValueError(f"Unsupported rule type for natural-language formatting: {rule_type}")


def _numbered_rule_texts(rule_texts):
    return "\n".join(
        f"({index}) {rule_text}."
        for index, rule_text in enumerate(rule_texts, start=1)
    )


def _format_global_constraints(domain, global_constraints):
    rule_texts = []
    for rule in DOMAIN_SPECS[domain]["global_rules"]:
        value = global_constraints[rule["name"]]
        rule_texts.append(_format_rule_text(domain, rule, value, "the whole grid"))
    return (
        "Across the whole grid, the plan must satisfy these global constraints:\n"
        + _numbered_rule_texts(rule_texts)
    )


def _format_row_constraints(domain, row_constraints, row_label):
    parts = []
    for constraint in row_constraints:
        row_index = constraint["row"]
        rule_texts = []
        for rule in DOMAIN_SPECS[domain]["row_rules"]:
            value = constraint[rule["name"]]
            rule_texts.append(_format_rule_text(domain, rule, value, f"{row_label} {row_index}"))
        parts.append(f"For {row_label} {row_index}:\n{_numbered_rule_texts(rule_texts)}")
    return "For the row constraints:\n" + "\n\n".join(parts)


def _format_col_constraints(domain, col_constraints, col_label):
    parts = []
    for constraint in col_constraints:
        col_index = constraint["col"]
        rule_texts = []
        for rule in DOMAIN_SPECS[domain]["col_rules"]:
            value = constraint[rule["name"]]
            rule_texts.append(_format_rule_text(domain, rule, value, f"{col_label} {col_index}"))
        parts.append(f"For {col_label} {col_index}:\n{_numbered_rule_texts(rule_texts)}")
    return "For the column constraints:\n" + "\n\n".join(parts)


def _build_dataset_object(instance, source_path):
    domain = instance["domain"]
    grid_description = get_grid_description(
        domain,
        rows=instance["meta"]["rows"],
        cols=instance["meta"]["cols"],
    )
    global_constraints_text = _format_global_constraints(domain, instance["global_constraints"])
    row_constraints_text = _format_row_constraints(
        domain,
        instance["row_constraints"],
        grid_description["row_label"],
    )
    col_constraints_text = _format_col_constraints(
        domain,
        instance["col_constraints"],
        grid_description["col_label"],
    )

    return SavedDatasetObject(
        domain=domain,
        instance_id=instance["instance_id"],
        meta=instance["meta"],
        global_constraints=instance["global_constraints"],
        row_constraints=instance["row_constraints"],
        col_constraints=instance["col_constraints"],
        item_pool=instance["item_pool"],
        truth_solution=instance["truth_solution"],
        slots=instance["slots"],
        task_instruction=get_task_instruction(
            domain,
            rows=instance["meta"]["rows"],
            cols=instance["meta"]["cols"],
            grid_description=grid_description["intro"],
            global_constraints_text=global_constraints_text,
            row_constraints_text=row_constraints_text,
            col_constraints_text=col_constraints_text,
        ),
        source_path=source_path,
        source_filename=os.path.basename(source_path),
    )


def load_dataset_objects_from_file(path):
    with open(path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if "instances" not in payload:
        raise ValueError(f"Dataset file does not contain 'instances': {path}")

    return [
        _build_dataset_object(instance, path)
        for instance in payload["instances"]
    ]


def load_dataset_object(path, instance_index=0):
    dataset_objects = load_dataset_objects_from_file(path)
    if instance_index < 0 or instance_index >= len(dataset_objects):
        raise IndexError(f"instance_index {instance_index} is out of range for {path}")
    return dataset_objects[instance_index]


def load_all_dataset_objects(data_dir=DEFAULT_DATA_DIR):
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    dataset_objects = []
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".json"):
            continue
        file_path = os.path.join(data_dir, filename)
        dataset_objects.extend(load_dataset_objects_from_file(file_path))

    return dataset_objects


def load_dataset_objects_by_domain(data_dir=DEFAULT_DATA_DIR):
    grouped = {}
    for dataset_object in load_all_dataset_objects(data_dir=data_dir):
        grouped.setdefault(dataset_object.domain, []).append(dataset_object)
    return grouped


if __name__ == "__main__":
    dataset_objects = load_all_dataset_objects(data_dir=DEFAULT_DATA_DIR)
    for dataset_object in dataset_objects:
        print(dataset_object.task_instruction)
    print(f"Loaded {len(dataset_objects)} dataset objects from {DEFAULT_DATA_DIR}")

    for dataset_object in dataset_objects:
        print(
            f"- {dataset_object.domain} | {dataset_object.instance_id} | "
            f"{dataset_object.source_filename}"
        )

    if dataset_objects:
        sample = dataset_objects[0]
        print("\nSample task instruction:\n")
        print(sample.task_instruction)

# 我现在需要写tools，也是在/Users/yangwang/dev_programs/python/cached_agent_benchmark/saved_datasets下面写个文件夹，然后对应每个domain的有着对应的tools。 具体的tools （1）对于每个slot，查询candidate，包括对应的id，name和 category；（2）根据id查询item的信息 （3）在slot写入对应的id （4）在slot去掉对应的id
