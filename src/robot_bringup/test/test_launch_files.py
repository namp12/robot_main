import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCH_DIR = ROOT / 'launch'


@pytest.mark.parametrize(
    'launch_file',
    [
        'minimal.launch.py',
        'slam.launch.py',
        'nav2.launch.py',
        'ai.launch.py',
        'view_robot.launch.py',
        'full_robot.launch.py',
    ],
)
def test_launch_file_generates(launch_file):
    launch_path = LAUNCH_DIR / launch_file
    assert launch_path.exists(), f'{launch_file} does not exist'

    sys.path.insert(0, str(ROOT))
    import importlib.util

    spec = importlib.util.spec_from_file_location('launch_test', launch_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    description = module.generate_launch_description()
    assert description is not None
