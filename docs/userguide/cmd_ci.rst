..  Copyright 2014-present PlatformIO <contact@platformio.org>
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

.. _cmd_ci:

platformio ci
=============

.. contents::

Usage
-----

.. code-block:: bash

    platformio ci [OPTIONS] [SRC]


Description
-----------

:ref:`cmd_ci` command is conceived of as "hot key" for building project with
arbitrary source code structure. In a nutshell, using ``SRC`` and
:option:`platformio ci --lib` contents PlatformIO initializes via
:ref:`cmd_init` new project in :option:`platformio ci --build-dir`
with the build environments (using :option:`platformio ci --board` or
:option:`platformio ci --project-conf`) and processes them via :ref:`cmd_run`
command.

:ref:`cmd_ci` command accepts **multiple** ``SRC`` arguments,
:option:`platformio ci --lib` and :option:`platformio ci --exclude` options
which can be a path to directory, file or
`Glob Pattern <http://en.wikipedia.org/wiki/Glob_(programming)>`_.
Also, you can omit ``SRC`` argument and set path (multiple paths are allowed
denoting with ``:``) to
``PLATFORMIO_CI_SRC`` `Environment variable <http://en.wikipedia.org/wiki/Environment_variable>`_

For more details as for integration with the popular Continuous Integration
Systems please follow to :ref:`ci` page.

.. note::
    :ref:`cmd_ci` command is useful for library developers. It allows to build
    different examples without creating own project per them. Also, is possible
    to upload firmware to the target device. In this case, need to create
    :ref:`projectconf` where specify "upload" :ref:`projectconf_targets`. Custom
    upload port can be overridden with :ref:`projectconf_upload_port` option.
    Then need to specify the path to this :ref:`projectconf` to
    :option:`platformio ci --project-conf`. For example,

    .. code-block:: ini

        [env:uno]
        platform = atmelavr
        framework = arduino
        targets = upload
        ; custom upload port
        ; upload_port = ...

Options
-------

.. program:: platformio ci

.. option::
    -l, --lib

Source code which will be copied to ``%build_dir%/lib`` directly.

If :option:`platformio ci --lib` is a path to file (not to directory), then
PlatformIO will create temporary directory within ``%build_dir%/lib`` and copy
the rest files into it.


.. option::
    --exclude

Exclude directories and/-or files from :option:`platformio ci --build-dir`. The
path must be relative to PlatformIO project within
:option:`platformio ci --build-dir`.

For example, exclude from project ``src`` directory:

* ``examples`` folder
* ``*.h`` files from ``foo`` folder

.. code-block:: bash

    platformio ci --exclude=src/examples --exclude=src/foo/*.h [SRC]

.. option::
    -b, --board

Build project with automatically pre-generated environments based on board
settings.

For more details please look into :option:`platformio init --board`.

.. option::
    --build-dir

Path to directory where PlatformIO will initialise new project. By default it's
temporary directory within your operation system.

.. note::

    This directory will be removed at the end of build process. If you want to
    keep it, please use :option:`platformio ci --keep-build-dir`.

.. option::
    --keep-build-dir

Don't remove :option:`platformio ci --build-dir` after build process.

.. option::
    --project-conf

Buid project using pre-configured :ref:`projectconf`.

.. option::
    -v, --verbose

Shows detailed information when processing environments.

This option can be set globally using :ref:`setting_force_verbose` setting
or by environment variable :envvar:`PLATFORMIO_SETTING_FORCE_VERBOSE`.

Examples
--------

For the others examples please follow to :ref:`ci` page.
