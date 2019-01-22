KPET - Kernel Patch-Evaluated Testing
=====================================
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
$ kpet --db . run print-test-cases 001.patch
```

To generate complete beaker xml:
```bash
$ kpet --db . run generate --description 'skt ##KVER##' -a aarch64 -k '##KPG_URL##' -t upstream 001.patch
```
