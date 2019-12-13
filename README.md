KPET - Kernel Patch-Evaluated Testing
=====================================
![KPET logo](logo.png)

KPET is a framework which will execute targeted testing based on changes introduced
in the patch, e.g. a network driver or similar would trigger network related testing
to be invoked, or a filesystem change would invoke filesystem testing.  

Install KPET
-------------
`kpet` is written in Python that means you will need python3 installed in your
system. You can execute it directly from the repository `./bin/kpet` or you can
install it via pip and use it directly from your `PATH`.

```bash
$ pip install --user git+https://github.com/CKI-project/kpet
```

Install KPET Database
-------------
In order to use `kpet` you will need to download the kpet database which includes the
templates and pattern files needed to analyze the patch and generate the corresponding
beaker xml.

```bash
$ git clone <kpet-db>
```

How to run it
-------------
To preview patch generated test cases:
```bash
$ kpet run print-test-cases 001.patch
```

To generate complete Beaker XML:
```bash
$ kpet run generate --description 'skt ##KVER##' -a aarch64 -k '##KPG_URL##' -t upstream 001.patch
```

You have to run these commands in the kpet database directory, or specify
the `--db` option to point to the kpet database directory.

Exported variables for kpet database templates
----------------------------------------------
The following variables are passed to the Beaker templates in the kpet
database. They effectively are the interface between kpet and
whichever database you decide to use:

* `DESCRIPTION`: Description for the Beaker test run.
* `KURL`: URL of the kernel to be tested. Could be a tarball, a yum repo, etc.
* `ARCH`: Name of the architecture to run the tests on.
* `TREE`: Name of the tree to run the tests on.
* `VARIABLES`: Dictionary with extra template variables.
* `RECIPESETS`: List of recipe sets. See below for details.

Each recipe set is a *list* of "host" objects containing these attributes:

* `hostname`: Hostname if this will run on a specific machine, None otherwise.
* `ignore_panic`: If kernel panics should be ignored when running
  tests. Copied from the kpet database value of the same name.
* `hostRequires`: Jinja2 template path with the host requirements for
  the test run. Copied from the kpet database value of the same name.
* `partitions`: Jinja2 template path with custom partition
  configuration. Copied from the kpet database value of the same name. See
  https://beaker-project.org/docs/user-guide/customizing-partitions.html
  for more information.
* `kickstart`: Jinja2 template path with custom Anaconda kickstart
  configuration. Copied from the kpet database value of the same name. See
  https://beaker-project.org/docs/admin-guide/kickstarts.html for more
  information.
* `hostRequires_list`: a list of paths to Jinja2 templates with the host
  requirements for the test run. Contains the `hostRequires` database values
  of the host's type, and all the suites and cases executed on the host.
* `partitions_list`: a list of paths to Jinja2 templates with custom partition
  configuration. Contains the `partitions` database values of the host's type,
  and all the suites and cases executed on the host. See
  https://beaker-project.org/docs/user-guide/customizing-partitions.html for
  more information.
* `kickstart_list`: a list of paths to Jinja2 templates with custom Anaconda
  kickstart configuration. Contains the `kickstart` database values of the
  host's type, and all the suites and cases executed on the host. See
  https://beaker-project.org/docs/admin-guide/kickstarts.html for more
  information.
* `tasks`: Jinja2 template path with custom tasks (<task> elements)
  for the host type. Copied from the kpet database value of the same
  name. See https://beaker-project.org/docs/user-guide/tasks.html for
  more information.
* `tests`: List of tests.

Each test is an object with the following attributes:

* `name`: Name of the test.
* `origin`: The name of a test origin - the source for the test's code.
  One of the keys from the `origins` dictionary in the database's top
  `index.yaml` file. Undefined, if the latter is not defined. Examples:
  `github`, `beaker`, or `suites_zip`. See the `origins` dictionary in the
  database's top `index.yaml` for the available origins and the meanings they
  assign to `location` values.
* `location`: The location of the test's code, with whatever meaning the
  database choses to assign to it, but must be interpreted according to the
  `origin`, if specified. Examples: a tarball URL, a path inside a common
  tarball, a Beaker task name. See the `origins` dictionary in the database's
  top `index.yaml` for the available origins and the meanings they assign to
  `location` values.
* `max_duration_seconds`: Maximum number of seconds the test is allowed to
  run.
* `waived`: True if the test's result should be ignored when summarizing the
  overall run result, eg. because it's new or unstable.
* `role`: The value for the Beaker task's role attribute.
* `environment`: Dictionary with environment variables that should be
  set when running this test.
* `maintainers`: List of strings with the names and emails of the test
  maintainers.
