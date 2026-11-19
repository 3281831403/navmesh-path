import pytest

from gameplay import navmesh as mod

CASES = [
    ('manhattan', [(0, 0), (3, 4)], 7, False),
    ('diagonal_cost', [2, 2], 2.8284271247461903, True),
    ('diagonal_cost', [2, 1], 2.414213562373095, True),
    ('cache_key', [(0, 0), (1, 1), 7], '(0, 0):(1, 1):7', False),
    ('line_blocked', [[(0, 0), (1, 0)], {(1, 0)}], True, False),
    ('line_blocked', [[(0, 0), (1, 0)], {(2, 0)}], False, False),
    ('separation_force', [(0, 0), [(1, 0), (0, 2)], 3], [-1.0, -1.0], True),
    ('clamp_cost', [12, 10], 10, False),
    ('stale_result', [3, 4], True, False),
    ('stale_result', [4, 4], False, False),
    ('smooth_weight', [0, 5], 1.0, True),
    ('smooth_weight', [2, 5], 0.5, True),
    ('cell_to_world', [(2, 3), 0.5], [1.0, 1.5], True),
    ('commit_agents', [[True, True]], True, False),
    ('manhattan', [(1, 1), (1, 1)], 0, False),
]


@pytest.mark.parametrize("func_name,args,expected,approx", CASES)
def test_navmesh_contract(func_name, args, expected, approx):
    func = getattr(mod, func_name)
    result = func(*args)
    if approx:
        assert result == pytest.approx(expected)
    else:
        assert result == expected
