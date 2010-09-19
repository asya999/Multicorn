
# -*- coding: utf-8 -*-
# This file is part of Dyko
# Copyright © 2008-2009 Kozea
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kalamar.  If not, see <http://www.gnu.org/licenses/>.

"""
Memory test
===========

Test the Memory access point.

"""

from nose.tools import eq_, nottest, raises, assert_equal, assert_raises
from kalamar import Site, MultipleMatchingItems, ItemDoesNotExist
from kalamar.access_point.memory import Memory
from kalamar.property import Property
from kalamar.access_point.cache import make_cache


@nottest
def make_test_ap():
    AccessPointMemoryCached = make_cache(Memory)
    return AccessPointMemoryCached({"id": Property(int), "name": Property(str)}, "id")

# TODO: this first part is carbon copy from test_memory.py... Try to refactor it

@nottest
def make_test_site():
    site = Site()
    site.register("things", make_test_ap())
    site.create("things", {"id": 1, "name": "foo"}).save()
    site.create("things", {"id": 2, "name": "bar"}).save()
    site.create("things", {"id": 3, "name": "bar"}).save()
    return site


def test_single_item():
    """Save a single item and retrieve it."""
    site = Site()
    site.register("things", make_test_ap())
    site.create("things", {"id": 1, "name": "foo"}).save()
    all_items = list(site.search("things"))
    eq_(len(all_items), 1)
    item = all_items[0]
    eq_(item["id"], 1)
    eq_(item["name"], "foo")

def test_search():
    site = make_test_site()

    results = site.search("things", {"name": "bar"})
    eq_(set(item["id"] for item in results), set([2, 3]))

def test_open_one():
    site = make_test_site()
    result = site.open("things", {"name": "foo"})
    eq_(result["id"], 1)

@raises(MultipleMatchingItems)
def test_open_two():
    site = make_test_site()
    result = site.open("things", {"name": "bar"})

@raises(ItemDoesNotExist)
def test_open_zero():
    site = make_test_site()
    result = site.open("things", {"name": "nonexistent"})

def test_delete():
    site = make_test_site()
    item = site.open("things", {"name": "foo"})
    item.delete()
    eq_(list(site.search("things", {"name": "foo"})), [])

def test_delete_many():
    site = make_test_site()
    site.delete_many("things", {"name": "bar"})
    eq_(list(site.search("things", {"name": "bar"})), [])


# end of carbon copy. here comes the real code

def test_cache():
    site = make_test_site()
    ap = site.access_points['things']

    # search one item
    all_items = list(site.search("things"))
    eq_(len(all_items), 3)
    item = all_items[0]
    eq_(item["id"], 1)
    eq_(item["name"], "foo")

    # monkey patch to disable ap
    old_search = ap.__class__.__bases__[0].search
    ap.__class__.__bases__[0].search = None
    
    # search one item
    # with no ap, this must work !
    all_items = list(site.search("things"))
    eq_(len(all_items), 3)
    item = all_items[0]
    eq_(item["id"], 1)
    eq_(item["name"], "foo")

    # restore request
    ap.__class__.__bases__[0].search = old_search

    # update the item
    item["name"] = 'bob'
    site.save("things", item)

    # monkey patch to disable ap
    ap.__class__.__bases__[0].search = None

    # this may fail because cache is invalided and ap is None
    assert_raises(TypeError, site.search, "things")

    # restore the ap
    ap.__class__.__bases__[0].search = old_search
    
    # search one item
    all_items = list(site.search("things"))
    eq_(len(all_items), 3)
    item = all_items[0]
    eq_(item["id"], 1)
    eq_(item["name"], "bob")

    #remove the ap and search again with cache
    ap.__class__.__bases__[0].search = None
    
    # search one item
    all_items = list(site.search("things"))
    eq_(len(all_items), 3)
    item = all_items[0]
    eq_(item["id"], 1)
    eq_(item["name"], "bob")
    
    # restore it
    ap.__class__.__bases__[0].search = old_search

def test_delegate():
    '''
    Test that the delegated class behave correctly
    '''
    site = make_test_site()

    # search one item
    all_items = list(site.search("things"))
    eq_(len(all_items), 3)
    item = all_items[0]

    # we previously had issues with item not knowing their access point
    repr(item)
    item.identity