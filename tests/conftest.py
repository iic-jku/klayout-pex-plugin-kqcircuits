#
# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2026 Martin Jan Köhler and Harald Pretl
# Johannes Kepler University, Institute for Integrated Circuits.
#
# This file is part of klayout-pex-plugin-kqcircuits
# (see https://github.com/iic-jku/klayout-pex-plugin-kqcircuits).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# SPDX-License-Identifier: GPL-3.0-or-later
# --------------------------------------------------------------------------------
#

"""Resolved scenes and subprocess checks shared by the contract tests."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import TYPE_CHECKING, Callable, List

import pytest

if TYPE_CHECKING:
    from klayout_pex_protobuf.kpex.pex25d.pex25d_scene_pb2 import PEX25DScene

RunPython = Callable[[List[str]], subprocess.CompletedProcess[str]]


@pytest.fixture
def scene_path() -> Path:
    return Path(__file__).resolve().parent.parent / 'testdata' / 'two_nets.pex25d'


@pytest.fixture
def scene(scene_path: Path) -> PEX25DScene:
    from klayout_pex import pex25d
    return pex25d.resolve(pex25d.read(str(scene_path)))


@pytest.fixture
def run_python(tmp_path: Path) -> RunPython:
    def run(arguments: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, '-I', *arguments], cwd=tmp_path,
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60, check=False)
    return run


def pytest_collection_modifyitems(items: List[pytest.Item]):
    for item in items:
        for label_type, value in (
                ('parentSuite', 'Plugin Tests'),
                ('suite', 'klayout-pex-plugin-kqcircuits'),
                ('subSuite', item.module.__name__.rsplit('.', 1)[-1])):
            item.add_marker(pytest.mark.allure_label(value, label_type=label_type))
