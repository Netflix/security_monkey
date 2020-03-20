#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# ^^ required by pep-0263 for "¿?"
#     Copyright 2014 Netflix, Inc.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
"""
.. module: security_monkey.common.PolicyDiff
    :platform: Unix
    :synopsis: Takes two JSON or dict objects and finds their differences. Returns color-coded HTML.
    Needs to be refactored completely.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

import json
import sys
import html
from html import escape as cgi_escape


def escape(data):
    return cgi_escape(str(data), quote=False)


def i(indentation):
    return '&nbsp;&nbsp;&nbsp;&nbsp;' * indentation


# ADDED
# CHANGED
#   Type Change
#   Regular Change
# DELETED
def process_sub_dict(key, sda, sdb, indentation):
    if type(sda) is not type(sdb):
        raise ValueError("process_sub_dict requires that both items have the same type.")
        # BUG: What if going from None to 'vpc-1de23c'

    retstr = ''
    brackets = get_brackets(sda)
    print(brackets)
    if type(sda) in [str]:
        if sda == sdb:
            retstr += same("{4}\"{0}\": {2}{1}{3},".format(key, escape(sda), brackets['open'], brackets['close'], i(indentation)))
        else:
            retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(key, escape(sdb), brackets['open'], brackets['close'], i(indentation)))
            retstr += added("{4}\"{0}\": {2}{1}{3},".format(key, escape(sda), brackets['open'], brackets['close'], i(indentation)))
    elif type(sda) in [bool, type(None), int, float]:
        if sda == sdb:
            retstr += same("{2}\"{0}\": {1},".format(key, json.dumps(sda), i(indentation)))
        else:
            retstr += deleted("{2}\"{0}\": {1},".format(key, json.dumps(sdb), i(indentation)))
            retstr += added("{2}\"{0}\": {1},".format(key, json.dumps(sda), i(indentation)))
    elif type(sda) is dict:
        retstr += same("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(key, diff_dict(sda, sdb, indentation + 1), brackets['open'], brackets['close'], i(indentation)))
    elif type(sda) is list:
        retstr += same("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(key, diff_list(sda, sdb, indentation + 1), brackets['open'], brackets['close'], i(indentation)))
    else:
        print(("process_sub_dict - Unexpected type {}".format(type(sda))))
    return retstr


def print_list(structure, action, indentation):
    retstr = ''
    for value in structure:
        brackets = form_brackets(value, indentation)
        new_value = ""
        if type(value) in [str, int, float]:
            new_value = escape(value)
        elif type(value) in [bool, type(None)]:
            new_value = json.dumps(value)
        elif type(value) is dict:
            new_value = print_dict(value, action, indentation + 1)
        elif type(value) is list:
            new_value = print_list(value, action, indentation + 1)
        else:
            print(("print_list - Unexpected type {}".format(type(value))))

        content = "{3}{1}{0}{2},".format(new_value, brackets['open'], brackets['close'], i(indentation))

        if action is 'same':
            retstr += same(content)
        elif action is 'deleted':
            retstr += deleted(content)
        elif action is 'added':
            retstr += added(content)
    return remove_last_comma(retstr)


def print_dict(structure, action, indentation):
    retstr = ''
    for key in list(structure.keys()):
        value = structure[key]
        brackets = form_brackets(value, indentation)
        new_value = ''
        if type(value) in [str, int, float]:
            new_value = escape(value)
        elif type(value) in [bool, type(None)]:
            new_value = json.dumps(value)
        elif type(value) is dict:
            new_value = print_dict(value, action, indentation + 1)
        elif type(value) is list:
            new_value = print_list(value, action, indentation + 1)
        else:
            print(("print_dict - Unexpected type {}".format(type(value))))

        content = "{4}\"{0}\": {2}{1}{3},".format(
                escape(key),
                new_value,
                brackets['open'],
                brackets['close'],
                i(indentation)
        )

        if action is 'same':
            retstr += same(content)
        elif action is 'deleted':
            retstr += deleted(content)
        elif action is 'added':
            retstr += added(content)
    return remove_last_comma(retstr)


def print_item(value, action, indentlevel):
    if type(value) in [str, int, float]:
        return escape(value)
    elif type(value) in [bool, type(None)]:
        return json.dumps(value)
    elif type(value) is dict:
        return print_dict(value, action, indentlevel)
    elif type(value) is list:
        return print_list(value, action, indentlevel)
    else:
        print(("print_item - Unexpected diff_dict type {}".format(type(value))))
    return ''


def diff_dict(dicta, dictb, indentation):
    """
        diff_dict and diff_list are recursive methods which build an HTML representation of the differences between two objects.
    """
    retstr = ''
    for keya in list(dicta.keys()):
        if keya not in dictb:
            brackets = get_brackets(dicta[keya])
            if type(dicta[keya]) in [str, int, float, bool, type(None)]:
                retstr += added("{4}\"{0}\": {2}{1}{3},".format(keya, print_item(dicta[keya], 'added', indentation + 1), brackets['open'], brackets['close'], i(indentation)))
            if type(dicta[keya]) in [list, dict]:
                retstr += added("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(keya, print_item(dicta[keya], 'added', indentation + 1), brackets['open'], brackets['close'], i(indentation)))
        else:
            if not type(dicta[keya]) is type(dictb[keya]):
                brackets = get_brackets(dictb[keya])
                retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(keya, dictb[keya], brackets['open'], brackets['close'], i(indentation)))
                brackets = get_brackets(dicta[keya])
                retstr += added("{4}\"{0}\": {2}{1}{3},".format(keya, dicta[keya], brackets['open'], brackets['close'], i(indentation)))
            else:
                retstr += process_sub_dict(keya, dicta[keya], dictb[keya], indentation)
    for keyb in list(dictb.keys()):
        if keyb not in dicta:
            brackets = get_brackets(dictb[keyb])
            if type(dictb[keyb]) in [str, int, float, bool, type(None)]:
                retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(keyb, print_item(dictb[keyb], 'deleted', indentation + 1), brackets['open'], brackets['close'], i(indentation)))
            if type(dictb[keyb]) in [list, dict]:
                retstr += deleted("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(keyb, print_item(dictb[keyb], 'deleted', indentation + 1), brackets['open'], brackets['close'], i(indentation)))
    return remove_last_comma(retstr)


def remove_last_comma(str):
    position = str.rfind(',')
    return str[:position] + str[position + 1:]


def diff_list(lista, listb, indentation):
    """
        diff_dict and diff_list are recursive methods which build an HTML representation of the differences between two objects.

        When multiple items in a list have been modified, the levenshtein distance is used to find which items most likely
            were modified from one object to the next.  Although this may not be necessary when the list items are primatives
            like strings, it is very useful when the two list items are multi-level dicts.  This allows us to only color-code the
            actual change and not the entire sub structure.

        [{name: 'Patrick', colleagues: ['Sam', 'Jason']}]
        [{name: 'Patrick', colleagues: ['Sam', 'Jason', 'Ben']}]

        * By Using levenshtein, we can color green just the string 'Ben'. (Preferred)
            BLACK - [{name: 'Patrick', colleagues: ['Sam', 'Jason',
            GREEN - 'Ben'
            BLACK - ]}]
        * Without levenshtein, we would end up coloring the entire dict twice:
            RED - {name: 'Patrick', colleagues: ['Sam', 'Jason']}
            GREEN - {name: 'Patrick', colleagues: ['Sam', 'Jason', 'Ben']}
    """
    retstr = ''
    addedlist = []
    deletedlist = []

    for item in lista:
        if item in listb:
            brackets = get_brackets(item)
            if type(item) in [str, int, float]:
                retstr += same("{3}{1}{0}{2},".format(escape(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) in [bool, type(None)]:
                retstr += same("{3}{1}{0}{2},".format(json.dumps(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) in [list, dict]:
                diffstr = print_item(item, 'same', indentation + 1)
                retstr += same("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets['open'], brackets['close'], i(indentation)))
            else:
                print(("diff_list - Unexpected Type {}".format(type(item))))
        else:
            addedlist.append(item)

    for item in listb:
        if item not in lista:
            deletedlist.append(item)

    for item in addedlist:
        bestmatch = find_most_similar(item, deletedlist)
        brackets = get_brackets(item)
        if None is bestmatch:
            if type(item) in [str, int, float]:
                retstr += added("{3}{1}{0}{2},".format(escape(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) in [bool, type(None)]:
                retstr += added("{3}{1}{0}{2},".format(json.dumps(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) in [list, dict]:
                diffstr = print_item(item, 'added', indentation + 1)
                retstr += added("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets['open'], brackets['close'], i(indentation)))
            else:
                print(("diff_list - Unexpected Type {}".format(type(item))))
        else:
            if type(item) in [str, int, float]:
                retstr += deleted("{3}{1}{0}{2},".format(escape(bestmatch), brackets['open'], brackets['close'], i(indentation)))
                retstr += added("{3}{1}{0}{2},".format(escape(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) in [bool, type(None)]:
                retstr += deleted("{3}{1}{0}{2},".format(json.dumps(bestmatch), brackets['open'], brackets['close'], i(indentation)))
                retstr += added("{3}{1}{0}{2},".format(json.dumps(item), brackets['open'], brackets['close'], i(indentation)))
            elif type(item) is list:
                diffstr = diff_list(item, bestmatch, indentation + 1)
                retstr += same("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets['open'], brackets['close'], i(indentation)))
            elif type(item) is dict:
                diffstr = diff_dict(item, bestmatch, indentation + 1)
                retstr += same("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets['open'], brackets['close'], i(indentation)))
            else:
                print(("diff_list - Unexpected Type {}".format(type(item))))
            deletedlist.remove(bestmatch)

    for item in deletedlist:
        brackets = get_brackets(item)
        if type(item) in [str, int, float]:
            retstr += deleted("{3}{1}{0}{2},".format(escape(item), brackets['open'], brackets['close'], i(indentation)))
        elif type(item) in [bool, type(None)]:
            retstr += deleted("{3}{1}{0}{2},".format(json.dumps(item), brackets['open'], brackets['close'], i(indentation)))
        elif type(item) in [list, dict]:
            diffstr = print_item(item, 'deleted', indentation + 1)
            retstr += deleted("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets['open'], brackets['close'], i(indentation)))
        else:
            print(("diff_list - Unexpected Type {}".format(type(item))))
    return remove_last_comma(retstr)


# levenshtein - http://hetland.org/coding/python/levenshtein.py
def str_distance(a, b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a, b = b, a
        n, m = m, n
    current = list(range(n+1))
    for i in range(1, m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1, n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change += 1
            current[j] = min(add, delete, change)
    return current[n]


def find_most_similar(item, list):
    stritem = str(item)
    mindistance = sys.maxsize
    bestmatch = None

    # Small performance boost.  Skip the expensive algo
    # if we know what it will return.
    if len(list) == 1 and type(item) is type(list[0]):
        return list[0]

    for listitem in list:
        if type(listitem) == type(item):
            strlistitem = str(listitem)
            distance = str_distance(stritem, strlistitem)
            if distance == 0:
                return listitem
            if distance < mindistance:
                bestmatch = listitem
                mindistance = distance
    return bestmatch


def form_brackets(value, indentation):
    brackets = {'open': '', 'close': ''}

    if type(value) in [str]:
        brackets['open'] = '"'
        brackets['close'] = '"'
    elif type(value) is dict:
        brackets['open'] = '{<br/>\n'
        brackets['close'] = i(indentation) + '}'
    elif type(value) is list:
        brackets['open'] = '[<br/>\n'
        brackets['close'] = i(indentation) + ']'
    return brackets


def get_brackets(item):
    brackets = {'open': '', 'close': ''}

    if type(item) in [str]:
        brackets['open'] = '"'
        brackets['close'] = '"'
    if type(item) is list:
        brackets['open'] = '['
        brackets['close'] = ']'
    if type(item) is dict:
        brackets['open'] = '{'
        brackets['close'] = '}'
    return brackets


def color(text, color):
    return "<font color='{0}'>{1}</font><br/>\n".format(color, text)


def added(text):
    return color(text, "green")


def deleted(text):
    return color(text, "red")


def same(text):
    return color(text, "black")


class PolicyDiff(object):
    """
    old_pol = "{}"
    new_pol = {
        "create_date": "2013-09-12T18:28:21Z",
        "must_change_password": "false",
        "user_name": "test"
    }

    differ = PolicyDiff(new_pol, old_pol)
    print(differ.produceDiffHTML())
    """

    def __init__(self, new_policy, old_policy):
        self._new_policy = None
        self._old_policy = None

        if isinstance(new_policy, str):
            try:
                self._new_policy = json.loads(new_policy)
            except Exception:
                print(("Could not read policy in as json. Type: {} Policy: {}".format(type(new_policy), new_policy)))
                self._new_policy = new_policy
        else:
            self._new_policy = json.loads(json.dumps(new_policy))

        if isinstance(old_policy, str):
            try:
                self._old_policy = json.loads(old_policy)
            except Exception:
                print(("Could not read policy in as json. Type: {} Policy: {}".format(type(old_policy), old_policy)))
                self._old_policy = old_policy
        else:
            self._old_policy = json.loads(json.dumps(old_policy))

        if self._old_policy is None or self._new_policy is None:
            raise ValueError("PolicyDiff could not process old policy or new policy or both.")

        if not type(self._old_policy) is type(self._new_policy):
            print(("OLD: {}".format(self._old_policy)))
            print(("NEW: {}".format(self._new_policy)))
            print(("Type OLD: {} Type New: {}".format(type(self._old_policy), type(self._new_policy))))
            raise ValueError("Policies passed into PolicyDiff must be the same outer type (dict, list, str, unicode).")

    def produceDiffHTML(self):
        if self._old_policy is None or self._new_policy is None:
            raise ValueError("PolicyDiff could not process old policy or new policy or both.")

        if not type(self._old_policy) is type(self._new_policy):
            raise ValueError("Policies passed into PolicyDiff must be the same outer type (dict, list, str, unicode).")

        if self._old_policy == {} and self._new_policy == {}:
            return "No Policy.<br/>"

        if isinstance(self._old_policy, str):
            return "{0}<br/>{1}".format(deleted(self._old_policy), added(self._new_policy))

        brackets = get_brackets(self._new_policy)

        if type(self._new_policy) is dict:
            inner_html = diff_dict(self._new_policy, self._old_policy, 1)
        elif type(self._new_policy) is list:
            inner_html = diff_list(self._new_policy, self._old_policy, 1)
        else:
            raise ValueError("PolicyDiff::produceDiffHTML cannot process items of type: {}".format(type(self._new_policy)))

        return "{1}<br/>\n{0}{2}<br/>\n".format(inner_html, brackets['open'], brackets['close'])
