import random

from data_generation.domains import DOMAIN_BUILDERS, DOMAIN_SPECS


def estimate_pool_size(total_cells, min_valid_options, max_valid_options):
    local_target = max_valid_options * 4
    return (total_cells - 1) + local_target


def generate_item_pool(
    domain,
    total_cells,
    min_valid_options,
    max_valid_options,
    pool_size=None,
):
    size = pool_size or estimate_pool_size(total_cells, min_valid_options, max_valid_options)
    builder = DOMAIN_BUILDERS[domain]
    return [builder(index) for index in range(size)]


def sample_solution_items(item_pool, total_cells):
    if len(item_pool) < total_cells:
        raise ValueError(
            f"item_pool has {len(item_pool)} items, but truth_solution needs {total_cells} unique items"
        )
    return random.sample(item_pool, total_cells)


def generate_truth_solution(domain, item_pool, rows, cols):
    id_key = DOMAIN_SPECS[domain]["id_key"]
    selected_items = sample_solution_items(item_pool, rows * cols)
    truth_solution = []
    item_lookup = {item[id_key]: item for item in item_pool}

    for row_index in range(rows):
        row = []
        for col_index in range(cols):
            item = selected_items[row_index * cols + col_index]
            row.append(item[id_key])
        truth_solution.append(row)

    return truth_solution, item_lookup
