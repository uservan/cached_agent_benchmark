DOMAIN_GRID_DESCRIPTIONS = {
    "course": {
        "intro_template": (
            "This course scheduling plan has {rows} scheduling days as rows and {cols} class time slots "
            "per day as columns."
        ),
        "row_label": "day",
        "col_label": "time slot",
    },
    "shopping": {
        "intro_template": (
            "This grocery shopping plan has {rows} shopping days as rows and {cols} item slots "
            "to fill per day as columns."
        ),
        "row_label": "shopping day",
        "col_label": "item slot",
    },
    "travel": {
        "intro_template": (
            "This travel itinerary has {rows} travel days as rows and {cols} activity slots "
            "per day as columns."
        ),
        "row_label": "travel day",
        "col_label": "activity slot",
    },
    "workforce": {
        "intro_template": (
            "This workforce scheduling plan has {rows} work days as rows and {cols} shift slots "
            "to staff per day as columns."
        ),
        "row_label": "work day",
        "col_label": "shift slot",
    },
    "meal": {
        "intro_template": (
            "This meal planning task has {rows} planning days as rows and {cols} meal slots "
            "to fill per day as columns."
        ),
        "row_label": "meal day",
        "col_label": "meal slot",
    },
    "pc_build": {
        "intro_template": (
            "This PC build task has {rows} build configurations as rows and {cols} component slots "
            "within each configuration as columns."
        ),
        "row_label": "build track",
        "col_label": "component slot",
    },
}


DOMAIN_TASK_INSTRUCTIONS = {
    "course": (
        "You are solving a course scheduling task. Fill the {rows}x{cols} grid with course ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, but those slot-specific limits must be "
        "looked up from the dataset/database for that slot before deciding which candidate id to use.\n"
        "Return only a {rows}x{cols} list of course ids."
    ),
    "shopping": (
        "You are solving a grocery shopping task. Fill the {rows}x{cols} grid with product ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, but those slot-specific limits must be "
        "looked up from the dataset/database for that slot before deciding which candidate id to use.\n"
        "Return only a {rows}x{cols} list of product ids."
    ),
    "travel": (
        "You are solving a travel itinerary task. Fill the {rows}x{cols} grid with activity ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, but those slot-specific limits must be "
        "looked up from the dataset/database for that slot before deciding which candidate id to use.\n"
        "Return only a {rows}x{cols} list of activity ids."
    ),
    "workforce": (
        "You are solving a workforce scheduling task. Fill the {rows}x{cols} grid with worker ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, but those slot-specific "
        "limits must be looked up from the dataset/database for that slot before deciding which "
        "candidate id to use.\n"
        "Return only a {rows}x{cols} list of worker ids."
    ),
    "meal": (
        "You are solving a meal planning task. Fill the {rows}x{cols} grid with dish ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, "
        "but those slot-specific limits must be looked up from the dataset/database for that slot "
        "before deciding which candidate id to use.\n"
        "Return only a {rows}x{cols} list of dish ids."
    ),
    "pc_build": (
        "You are solving a PC build configuration task. Fill the {rows}x{cols} grid with component ids.\n"
        "{grid_description}\n"
        "Each cell must use exactly one candidate id from that slot.\n\n"
        "{global_constraints_text}\n\n"
        "{row_constraints_text}\n\n"
        "{col_constraints_text}\n\n"
        "Each slot also has its own local constraints, "
        "but those slot-specific limits must be looked up from the dataset/database for that slot "
        "before deciding which candidate id to use.\n"
        "Return only a {rows}x{cols} list of component ids."
    ),
}


def get_grid_description(domain, rows=None, cols=None):
    if domain not in DOMAIN_GRID_DESCRIPTIONS:
        raise KeyError(f"Unsupported domain for grid description: {domain}")
    description = DOMAIN_GRID_DESCRIPTIONS[domain].copy()
    if rows is not None and cols is not None:
        description["intro"] = description["intro_template"].format(rows=rows, cols=cols)
    else:
        description["intro"] = description["intro_template"]
    return description


def get_task_instruction(
    domain,
    rows=None,
    cols=None,
    grid_description=None,
    global_constraints_text=None,
    row_constraints_text=None,
    col_constraints_text=None,
):
    if domain not in DOMAIN_TASK_INSTRUCTIONS:
        raise KeyError(f"Unsupported domain for task instruction: {domain}")
    if (
        rows is None
        or cols is None
        or
        grid_description is None
        or
        global_constraints_text is None
        or row_constraints_text is None
        or col_constraints_text is None
    ):
        return DOMAIN_TASK_INSTRUCTIONS[domain]
    return DOMAIN_TASK_INSTRUCTIONS[domain].format(
        rows=rows,
        cols=cols,
        grid_description=grid_description,
        global_constraints_text=global_constraints_text,
        row_constraints_text=row_constraints_text,
        col_constraints_text=col_constraints_text,
    )
