# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from os.path import join

import click
import semantic_version

from platformio import app, commands, exception, util
from platformio.managers.package import BasePkgManager


class LibraryManager(BasePkgManager):

    def __init__(self, package_dir=None):
        if not package_dir:
            package_dir = join(util.get_home_dir(), "lib")
        BasePkgManager.__init__(self, package_dir)

    @property
    def manifest_name(self):
        return ".library.json"

    @staticmethod
    def normalize_dependencies(dependencies):
        if not dependencies:
            return []
        items = []
        if isinstance(dependencies, dict):
            if "name" in dependencies:
                items.append(dependencies)
            else:
                for name, version in dependencies.items():
                    items.append({"name": name, "version": version})
        elif isinstance(dependencies, list):
            items = [d for d in dependencies if "name" in d]
        for item in items:
            for k in ("frameworks", "platforms"):
                if k not in item or isinstance(k, list):
                    continue
                if item[k] == "*":
                    del item[k]
                elif isinstance(item[k], basestring):
                    item[k] = [i.strip() for i in item[k].split(",")
                               if i.strip()]
        return items

    @staticmethod
    def max_satisfying_repo_version(versions, requirements=None):

        def _cmp_dates(datestr1, datestr2):
            from datetime import datetime
            assert "T" in datestr1 and "T" in datestr2
            dateformat = "%Y-%m-%d %H:%M:%S"
            date1 = datetime.strptime(datestr1[:-1].replace("T", " "),
                                      dateformat)
            date2 = datetime.strptime(datestr2[:-1].replace("T", " "),
                                      dateformat)
            if date1 == date2:
                return 0
            return -1 if date1 < date2 else 1

        item = None
        reqspec = None
        if requirements:
            try:
                reqspec = semantic_version.Spec(requirements)
            except ValueError:
                pass
        for v in versions:
            specver = None
            try:
                specver = semantic_version.Version(v['version'], partial=True)
            except ValueError:
                pass

            if reqspec:
                if not specver or specver not in reqspec:
                    continue
                if not item or semantic_version.Version(
                        item['version'], partial=True) < specver:
                    item = v
            elif requirements:
                if requirements == v['version']:
                    return v
            else:
                if not item or _cmp_dates(item['date'], v['date']) == -1:
                    item = v
        return item

    def get_latest_repo_version(self, name, requirements):
        item = self.max_satisfying_repo_version(
            util.get_api_result("/lib/versions/%d" % self._get_pkg_id_by_name(
                name, requirements)), requirements)
        return item['version'] if item else None

    def _get_pkg_id_by_name(self, name, requirements, silent=False):
        if name.startswith("id="):
            return int(name[3:])
        # try to find ID from installed packages
        installed_dir = self.get_installed_dir(name, requirements)
        if installed_dir:
            manifest = self.load_manifest(installed_dir)
            if "id" in manifest:
                return int(manifest['id'])
        return int(self.search_for_library({"name": name}, silent)['id'])

    def _install_from_piorepo(self, name, requirements):
        assert name.startswith("id=")
        version = self.get_latest_repo_version(name, requirements)
        if not version:
            raise exception.UndefinedPackageVersion(requirements or "latest",
                                                    util.get_systype())
        dl_data = util.get_api_result(
            "/lib/download/" + str(name[3:]), dict(version=version))
        assert dl_data
        pkg_dir = None
        try:
            pkg_dir = self._install_from_url(
                name, dl_data['url'].replace("http://", "https://"),
                requirements)
        except exception.APIRequestError:
            pkg_dir = self._install_from_url(name, dl_data['url'],
                                             requirements)
        return pkg_dir

    def install(self,
                name,
                requirements=None,
                silent=False,
                trigger_event=True):
        _name, _requirements, _url = self.parse_pkg_name(name, requirements)
        if not _url:
            _name = "id=%d" % self._get_pkg_id_by_name(
                _name, _requirements, silent=silent)
        already_installed = self.get_installed_dir(_name, _requirements, _url)
        pkg_dir = BasePkgManager.install(self, _name if not _url else name,
                                         _requirements, silent, trigger_event)

        if already_installed:
            return

        manifest = self.load_manifest(pkg_dir)
        if "dependencies" not in manifest:
            return pkg_dir

        if not silent:
            click.secho("Installing dependencies", fg="yellow")

        for filters in self.normalize_dependencies(manifest['dependencies']):
            assert "name" in filters
            if any([s in filters.get("version", "") for s in ("\\", "/")]):
                self.install("{name}={version}".format(**filters))
            else:
                lib_info = self.search_for_library(filters, silent)
                if filters.get("version"):
                    self.install(
                        lib_info['id'],
                        requirements=filters.get("version"),
                        silent=silent,
                        trigger_event=trigger_event)
                else:
                    self.install(
                        lib_info['id'],
                        silent=silent,
                        trigger_event=trigger_event)
        return pkg_dir

    @staticmethod
    def search_for_library(  # pylint: disable=too-many-branches
            filters, silent=False):
        assert isinstance(filters, dict)
        assert "name" in filters
        if not silent:
            click.echo("Looking for %s library in registry" % click.style(
                filters['name'], fg="cyan"))
        query = []
        for key in filters:
            if key not in ("name", "authors", "frameworks", "platforms"):
                continue
            values = filters[key]
            if not isinstance(values, list):
                values = [v.strip() for v in values.split(",") if v]
            for value in values:
                query.append('%s:"%s"' % (key[:-1] if key.endswith("s") else
                                          key, value))

        lib_info = None
        result = util.get_api_result(
            "/lib/search", dict(query=" ".join(query)))
        if result['total'] == 1:
            lib_info = result['items'][0]
        elif result['total'] > 1:
            click.secho(
                "Conflict: More than one library has been found "
                "by request %s:" % json.dumps(filters),
                fg="red")
            commands.lib.echo_liblist_header()
            for item in result['items']:
                commands.lib.echo_liblist_item(item)

            if not app.get_setting("enable_prompts"):
                click.echo("Automatically chose the first available library")
                lib_info = result['items'][0]
            else:
                deplib_id = click.prompt(
                    "Please choose library ID",
                    type=click.Choice([str(i['id']) for i in result['items']]))
                for item in result['items']:
                    if item['id'] == int(deplib_id):
                        lib_info = item
                        break

        if not lib_info:
            raise exception.LibNotFound(str(filters))
        if not silent:
            click.echo("Found: %s" % click.style(
                "http://platformio.org/lib/show/{id}/{name}".format(
                    **lib_info),
                fg="blue"))
        return lib_info
