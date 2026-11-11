#
# --------------------------------------------------------------------------------
# SPDX-FileCopyrightText: 2026 Martin Jan Köhler and Harald Pretl
# Johannes Kepler University, Institute for Integrated Circuits.
#
# This file is part of klayout-pex-plugin-kqcircuits
# (see https://github.com/martinjankoehler/klayout-pex-plugin-kqcircuits).
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

"""The unfinished adapter must be discoverable without claiming export success."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from conftest import RunPython
    from klayout_pex_protobuf.kpex.pex25d.pex25d_scene_pb2 import PEX25DScene

from klayout_pex import pex25d
from klayout_pex_plugins.kqcircuits import KQCircuitsSceneExporter, create_exporter


def test_registered_factory_is_loadable():
    entry_points = [point for point in metadata.entry_points(group='klayout_pex.exporters.v1')
                    if point.name == 'kqcircuits']
    assert len(entry_points) == 1
    assert entry_points[0].dist.name == 'klayout-pex-plugin-kqcircuits'
    assert isinstance(entry_points[0].load()(), KQCircuitsSceneExporter)
    assert isinstance(create_exporter(), KQCircuitsSceneExporter)


@pytest.mark.parametrize('selector', [
    'kqcircuits', 'klayout-pex-plugin-kqcircuits:kqcircuits',
])
def test_kpex_registry_loads_fresh_exporters(selector: str):
    registry = pex25d.exporter_registry()
    assert registry.get_info(selector).distribution == 'klayout-pex-plugin-kqcircuits'
    first = registry.load(selector)
    assert isinstance(first, KQCircuitsSceneExporter)
    assert registry.load(selector) is not first


@pytest.mark.parametrize('existing_directory', [False, True])
@pytest.mark.parametrize('prefix', ['', 'cell_'])
def test_export_reports_unimplemented_without_side_effects(scene: PEX25DScene, tmp_path: Path,
                                                          existing_directory: bool,
                                                          prefix: str):
    # A failed exporter must neither create a new directory nor overwrite a
    # previous run. Immutable options catch accidental mutation by an adapter.
    destination = tmp_path / 'solver inputs'
    if existing_directory:
        destination.mkdir()
        (destination / 'keep.txt').write_text('previous result', encoding='utf-8')
    before_scene = scene.SerializeToString(deterministic=True)
    options = MappingProxyType({})

    with pytest.raises(NotImplementedError, match='KQCircuits export is not implemented yet'):
        pex25d.export(scene, target='kqcircuits', output_dir_path=str(destination),
                      prefix=prefix, options=options)

    assert scene.SerializeToString(deterministic=True) == before_scene
    assert dict(options) == {}
    if existing_directory:
        assert sorted(path.name for path in destination.iterdir()) == ['keep.txt']
        assert (destination / 'keep.txt').read_text(encoding='utf-8') == 'previous result'
    else:
        assert not destination.exists()


def test_cli_lists_the_installed_plugin(run_python: RunPython):
    result = run_python(['-m', 'klayout_pex.pex25d', 'exporters'])
    assert result.returncode == 0, result.stderr
    assert 'klayout-pex-plugin-kqcircuits:kqcircuits' in result.stdout


def test_cli_reports_not_implemented(scene_path: Path, tmp_path: Path, run_python: RunPython):
    destination = tmp_path / 'solver inputs'
    result = run_python([
        '-m', 'klayout_pex.pex25d', 'export', str(scene_path),
        '--to', 'kqcircuits', '--out-dir', str(destination),
    ])
    output = result.stdout + result.stderr
    assert result.returncode == 3, output
    assert 'KQCircuits export is not implemented yet' in output
    assert 'Traceback' not in output
    assert not destination.exists()


def test_discovery_and_factory_do_not_load_optional_backends(run_python: RunPython):
    # A fresh interpreter avoids passing only because geometry modules were
    # already imported by another test. Block imports even when installed.
    result = run_python(['-c', """
import importlib.abc
import sys

class NoBackends(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {
                'klayout', 'pya', 'gmsh', 'kqcircuits', 'klayout_pex_protobuf', 'kpex'}:
            raise AssertionError('Unexpected optional import: ' + fullname)

sys.meta_path.insert(0, NoBackends())
from klayout_pex.pex25d import exporter_registry
registry = exporter_registry()
assert registry.get_info('kqcircuits').name == 'kqcircuits'
assert callable(registry.load('kqcircuits').export)
assert callable(registry.load('fastercap').export)
"""])
    assert result.returncode == 0, result.stderr


def test_namespace_does_not_hide_another_plugin(tmp_path: Path, run_python: RunPython):
    # Install a peer on a distinct import root, just as independently installed
    # distributions can contribute to the same implicit namespace.
    peer_root = tmp_path / 'other distribution'
    peer_package = peer_root / 'klayout_pex_plugins' / 'fixture_peer'
    peer_package.mkdir(parents=True)
    (peer_package / '__init__.py').write_text('IDENTITY = "independent plugin"\n', encoding='utf-8')
    result = run_python(['-c', """
import sys
sys.path.insert(0, sys.argv[1])
import klayout_pex_plugins
from klayout_pex_plugins.kqcircuits import create_exporter
from klayout_pex_plugins.fixture_peer import IDENTITY
assert klayout_pex_plugins.__file__ is None
assert IDENTITY == 'independent plugin'
assert callable(create_exporter().export)
""", str(peer_root)])
    assert result.returncode == 0, result.stderr
