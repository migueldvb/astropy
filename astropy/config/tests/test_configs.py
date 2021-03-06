# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ...tests.helper import catch_warnings
from ...extern import six

import io

from ...utils.data import get_pkg_data_filename
from .. import configuration


def test_paths():
    from ..paths import get_config_dir, get_cache_dir

    assert 'astropy' in get_config_dir()
    assert 'astropy' in get_cache_dir()


def test_config_file():
    from ..configuration import get_config, reload_config, save_config

    apycfg = get_config('astropy')
    assert apycfg.filename.endswith('astropy.cfg')

    cfgsec = get_config('astropy.config')
    assert cfgsec.depth == 1
    assert cfgsec.name == 'config'
    assert cfgsec.parent.filename.endswith('astropy.cfg')

    reload_config('astropy')


def test_configitem():
    from ..configuration import ConfigurationItem, get_config

    ci = ConfigurationItem('tstnm', 34, 'this is a Description')

    assert ci.module == 'astropy.config.tests.test_configs'
    assert ci() == 34
    assert ci.description == 'this is a Description'

    sec = get_config(ci.module)
    assert sec['tstnm'] == 34

    ci.description = 'updated Descr'
    ci.set(32)
    assert ci() == 32

    # It's useful to go back to the default to allow other test functions to
    # call this one and still be in the default configuration.
    ci.description = 'this is a Description'
    ci.set(34)
    assert ci() == 34


def test_configitem_types():
    from ..configuration import ConfigurationItem
    from ...tests.helper import pytest

    ci1 = ConfigurationItem('tstnm1', 34)
    assert isinstance(ci1(), int)

    ci2 = ConfigurationItem('tstnm2', 34.3)
    assert isinstance(ci2(), float)

    ci3 = ConfigurationItem('tstnm3', True)
    assert isinstance(ci3(), bool)

    ci4 = ConfigurationItem('tstnm4', 'astring')
    assert isinstance(ci4(), six.text_type)

    with pytest.raises(TypeError):
        ci1.set(34.3)
    ci2.set(12)  # this would should succeed as up-casting
    with pytest.raises(TypeError):
        ci3.set('fasd')
    with pytest.raises(TypeError):
        ci4.set(546.245)


def test_configitem_options(tmpdir):
    from ..configuration import ConfigurationItem, get_config
    from ...tests.helper import pytest

    cio = ConfigurationItem('tstnmo', ['op1', 'op2', 'op3'])
    sec = get_config(cio.module)

    assert isinstance(cio(), six.text_type)
    assert cio() == 'op1'
    assert sec['tstnmo'] == 'op1'

    cio.set('op2')
    with pytest.raises(TypeError):
        cio.set('op5')
    assert sec['tstnmo'] == 'op2'

    # now try saving
    apycfg = sec
    while apycfg.parent is not apycfg:
        apycfg = apycfg.parent
    f = tmpdir.join('astropy.cfg')
    with io.open(f.strpath, 'w', encoding='utf-8') as fd:
        apycfg.write(fd)
    with io.open(f.strpath, 'rU', encoding='utf-8') as fd:
        lns = [x.strip() for x in f.readlines()]

    assert 'tstnmo = op2' in lns


def test_config_noastropy_fallback(monkeypatch):
    """
    Tests to make sure configuration items fall back to their defaults when
    there's a problem accessing the astropy directory
    """
    from ...tests.helper import pytest
    from .. import paths, configuration

    # make sure the config directory is not searched
    monkeypatch.setenv('XDG_CONFIG_HOME', 'foo')
    monkeypatch.delenv('XDG_CONFIG_HOME')

    # make sure the _find_or_create_astropy_dir function fails as though the
    # astropy dir could not be accessed
    def osraiser(dirnm, linkto):
        raise OSError
    monkeypatch.setattr(paths, '_find_or_create_astropy_dir', osraiser)

    # also have to make sure the stored configuration objects are cleared
    monkeypatch.setattr(configuration, '_cfgobjs', {})

    with pytest.raises(OSError):
        # make sure the config dir search fails
        paths.get_config_dir()

    # now run the basic tests, and make sure the warning about no astropy
    # is present
    with catch_warnings(configuration.ConfigurationMissingWarning) as w:
        test_configitem()
    assert len(w) == 1
    w = w[0]
    assert 'Configuration defaults will be used' in str(w.message)


def test_configitem_setters():
    from ..configuration import ConfigurationItem

    ci = ConfigurationItem('tstnm12', 42, 'this is another Description')

    assert ci() == 42
    with ci.set_temp(45):
        assert ci() == 45
    assert ci() == 42

    ci.set(43)
    assert ci() == 43

    with ci.set_temp(46):
        assert ci() == 46

    # Make sure it is reset even with Exception
    try:
        with ci.set_temp(47):
            raise Exception
    except:
        pass

    assert ci() == 43


def test_empty_config_file():
    from ..configuration import is_unedited_config_file

    fn = get_pkg_data_filename('data/empty.cfg')
    assert is_unedited_config_file(fn)

    fn = get_pkg_data_filename('data/not_empty.cfg')
    assert not is_unedited_config_file(fn)

    fn = get_pkg_data_filename('data/astropy.0.3.cfg')
    assert is_unedited_config_file(fn)


def test_alias():
    import astropy

    with catch_warnings() as w:
        with astropy.UNICODE_OUTPUT.set_temp(False):
            pass

    assert len(w) == 1
    assert str(w[0].message) == (
        "Since 0.4, config parameter 'astropy.UNICODE_OUTPUT' is deprecated. "
        "Use 'astropy.conf.unicode_output' instead.")


def test_alias2():
    from ...coordinates import name_resolve
    from ...utils.data import conf

    # REMOVE in astropy 0.5

    with catch_warnings() as w:
        x = name_resolve.NAME_RESOLVE_TIMEOUT()
    assert x == 3
    assert len(w) == 1
    assert str(w[0].message) == (
        "Since 0.4, config parameter "
        "'astropy.coordinates.name_resolve.NAME_RESOLVE_TIMEOUT' is deprecated. "
        "Use 'astropy.utils.data.conf.remote_timeout' instead.")

    with catch_warnings() as w:
        name_resolve.NAME_RESOLVE_TIMEOUT.set(10)
    assert conf.remote_timeout == 10
    assert len(w) == 1
    assert str(w[0].message) == (
        "Since 0.4, config parameter "
        "'astropy.coordinates.name_resolve.NAME_RESOLVE_TIMEOUT' is deprecated. "
        "Use 'astropy.utils.data.conf.remote_timeout' instead.")

    with catch_warnings() as w:
        with name_resolve.NAME_RESOLVE_TIMEOUT.set_temp(42):
            assert conf.remote_timeout == 42
    assert len(w) == 1
    assert str(w[0].message) == (
        "Since 0.4, config parameter "
        "'astropy.coordinates.name_resolve.NAME_RESOLVE_TIMEOUT' is deprecated. "
        "Use 'astropy.utils.data.conf.remote_timeout' instead.")
    assert name_resolve.NAME_RESOLVE_TIMEOUT() == 10
    assert conf.remote_timeout == 10

    with catch_warnings() as w:
        name_resolve.NAME_RESOLVE_TIMEOUT.reload()
    assert len(w) == 1
    assert str(w[0].message) == (
        "Since 0.4, config parameter "
        "'astropy.coordinates.name_resolve.NAME_RESOLVE_TIMEOUT' is deprecated. "
        "Use 'astropy.utils.data.conf.remote_timeout' instead.")
    assert x == 3
    assert name_resolve.NAME_RESOLVE_TIMEOUT() == 3


class TestAliasRead(object):
    def setup_class(self):
        configuration._override_config_file = get_pkg_data_filename('data/alias.cfg')

    def test_alias_read(self):
        from astropy.utils.data import conf

        with catch_warnings() as w:
            conf.reload()
            assert conf.remote_timeout == 42

        assert len(w) == 1
        assert str(w[0].message).startswith(
            "Config parameter 'name_resolve_timeout' in section "
            "[coordinates.name_resolve]")

    def teardown_class(self):
        from astropy.utils.data import conf

        configuration._override_config_file = None
        conf.reload()


def test_configitem_unicode(tmpdir):
    from ..configuration import ConfigurationItem, get_config

    cio = ConfigurationItem('астрономия', 'ასტრონომიის')
    sec = get_config(cio.module)

    assert isinstance(cio(), six.text_type)
    assert cio() == 'ასტრონომიის'
    assert sec['астрономия'] == 'ასტრონომიის'
