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
.. module: security_monkey.common.utils.PolicyDiff
    :platform: Unix
    :synopsis: Takes two JSON or dict objects and finds their differences. Returns color-coded HTML.
    Needs to be refactored completely.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

import json
import sys
import collections


def i(indentlevel):
    retstr = ''
    for i in range(0, indentlevel):
        # The &emsp; prevents a user from copying the output from a browser window into anything that requires
        # valid JSON. Instead of copying as a tab or space character, it copies as an invalid whitespace character HEX E28083
        #retstr += '&emsp;'
        retstr += '&nbsp;&nbsp;&nbsp;&nbsp;'
    return retstr


# ADDED
# CHANGED
#   Type Change
#   Regular Change
# DELETED
def processSubDict(key, sda, sdb, indentlevel):
    if type(sda) is not type(sdb):
        raise ValueError("processSubDict requires that both items have the same type.")
        # BUG: What if going from None to 'vpc-1de23c'

    retstr = ''
    brackets = charfortype(sda)
    if type(sda) is str or type(sdb) is unicode:
        if sda == sdb:
            retstr += same("{4}\"{0}\": {2}{1}{3},".format(key, sda, brackets[0], brackets[1], i(indentlevel)))
        else:
            retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(key, sdb, brackets[0], brackets[1], i(indentlevel)))
            retstr += added("{4}\"{0}\": {2}{1}{3},".format(key, sda, brackets[0], brackets[1], i(indentlevel)))
    elif type(sda) is type(None) or type(sda) is bool or type(sda) is int:
        if sda == sdb:
            retstr += same("{2}\"{0}\": {1},".format(key, json.dumps(sda), i(indentlevel)))
        else:
            retstr += deleted("{2}\"{0}\": {1},".format(key, json.dumps(sda), i(indentlevel)))
            retstr += added("{2}\"{0}\": {1},".format(key, json.dumps(sda), i(indentlevel)))
    elif type(sda) is dict:
        retstr += same("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(key, diffdict(sda, sdb, indentlevel+1), brackets[0], brackets[1],i(indentlevel)))
    elif type(sda) is list:
        retstr += same("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(key, difflist(sda, sdb, indentlevel+1), brackets[0], brackets[1],i(indentlevel)))
    else:
        print "processSubDict - Unexpected diffdict type {}".format(type(sda))
    return retstr

def formbrack(value, indentlevel):
    brackets = {}
    brackets['open'] = ''
    brackets['close'] = ''

    if type(value) is str or type(value) is unicode:
        brackets['open'] = '"'
        brackets['close'] = '"'
    elif type(value) is dict:
        brackets['open'] = '{<br/>\n'
        brackets['close'] = i(indentlevel)+'}'
    elif type(value) is list:
        brackets['open'] = '[<br/>\n'
        brackets['close'] = i(indentlevel)+']'
    else:
        # print "formbrack - Unexpected diffdict type {}".format(type(value))
        pass
    return brackets

def printlist(structure, action, indentlevel):
    retstr = ''
    for value in structure:
        brackets = formbrack(value, indentlevel)
        new_value = ""
        if type(value) is str or type(value) is unicode:
            new_value = value
        elif type(value) is dict:
            new_value = printdict(value, action, indentlevel+1)
        elif type(value) is list:
            new_value = printlist(value, action, indentlevel+1)
        else:
            print "printlist - Unexpected diffdict type {}".format(type(value))

        content = "{3}{1}{0}{2},".format(new_value, brackets['open'], brackets['close'],i(indentlevel))

        if action is 'same':
            retstr += same(content)
        elif action is 'deleted':
            retstr += deleted(content)
        elif action is 'added':
            retstr += added(content)
    return removeLastComma(retstr)

def printdict(structure, action, indentlevel):
    retstr = ''
    for key in structure.keys():
        value = structure[key]
        brackets = formbrack(value, indentlevel)
        new_value = ''
        if type(value) is str or type(value) is unicode or type(value) is int:
            new_value = value
        elif type(value) is bool or type(value) is type(None):
            new_value = json.dumps(value)
        elif type(value) is dict:
            new_value = printdict(value, action, indentlevel+1)
        elif type(value) is list:
            new_value = printlist(value, action, indentlevel+1)
        else:
            print "printdict - Unexpected diffdict type {}".format(type(value))

        content = "{4}\"{0}\": {2}{1}{3},".format(key, new_value, brackets['open'], brackets['close'],i(indentlevel))

        if action is 'same':
            retstr += same(content)
        elif action is 'deleted':
            retstr += deleted(content)
        elif action is 'added':
            retstr += added(content)
    return removeLastComma(retstr)

def printsomething(value, action, indentlevel):
    if type(value) is str or type(value) is unicode or type(value) is int:
        return value
    elif type(value) is bool or type(value) is type(None):
        new_value = json.dumps(value)
    elif type(value) is dict:
        return printdict(value, action, indentlevel)
    elif type(value) is list:
        return printlist(value, action, indentlevel)
    else:
        print "printsomething - Unexpected diffdict type {}".format(type(value))
    return ''



def diffdict(dicta, dictb, indentlevel):
    """
        diffdict and difflist are recursive methods which build an HTML representation of the differences between two objects.
        TODO: diffdict does not add commas
    """
    retstr = ''
    for keya in dicta.keys():
        if not dictb.has_key(keya):
            brackets = charfortype(dicta[keya])
            if type(dicta[keya]) is str or type(dicta[keya]) is unicode:
                retstr += added("{4}\"{0}\": {2}{1}{3},".format(keya, printsomething(dicta[keya], 'added', indentlevel+1), brackets[0], brackets[1], i(indentlevel)))
            if type(dicta[keya]) is list or type(dicta[keya]) is dict:
                retstr += added("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(keya, printsomething(dicta[keya], 'added', indentlevel+1), brackets[0], brackets[1], i(indentlevel)))
        else:
            if not type(dicta[keya]) is type(dictb[keya]):
                brackets = charfortype(dictb[keya])
                retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(keya, dictb[keya], brackets[0], brackets[1], i(indentlevel)))
                brackets = charfortype(dicta[keya])
                retstr += added("{4}\"{0}\": {2}{1}{3},".format(keya, dicta[keya], brackets[0], brackets[1],i(indentlevel)))
            else:
                retstr += processSubDict(keya, dicta[keya], dictb[keya], indentlevel)
    for keyb in dictb.keys():
        if not dicta.has_key(keyb):
            brackets = charfortype(dictb[keyb])
            if type(dictb[keyb]) is str or type(dictb[keyb]) is unicode:
                retstr += deleted("{4}\"{0}\": {2}{1}{3},".format(keyb, printsomething(dictb[keyb], 'deleted', indentlevel+1), brackets[0], brackets[1],i(indentlevel)))
            if type(dictb[keyb]) is list or type(dictb[keyb]) is dict:
                retstr += deleted("{4}\"{0}\": {2}<br/>\n{1}{4}{3},".format(keyb, printsomething(dictb[keyb], 'deleted', indentlevel+1), brackets[0], brackets[1],i(indentlevel)))
    return removeLastComma(retstr)

def removeLastComma(str):
    position = str.rfind(',')
    retstr = str[:position] + str[position+1:]
    return retstr

def difflist(lista, listb, indentlevel):
    """
        diffdict and difflist are recursive methods which build an HTML representation of the differences between two objects.
        TODO: difflist adds commas after every entry, even the last entry.

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
            brackets = charfortype(item)
            if type(item) is str or type(item) is unicode:
                retstr += same("{3}{1}{0}{2},".format(item, brackets[0], brackets[1],i(indentlevel)))
            else:
                # Handle lists and dicts here:
                diffstr = ''
                if type(item) is list or type(item) is dict:
                    diffstr = printsomething(item, 'same', indentlevel+1)
                retstr += same("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets[0], brackets[1],i(indentlevel)))
        else:
            addedlist.append(item)
    for item in listb:
        if not item in lista:
            deletedlist.append(item)
    for item in addedlist:
        bestmatch = findmostsimilar(item, deletedlist)
        brackets = charfortype(item)
        if None is bestmatch:
            if type(item) is str or type(item) is unicode:
                retstr += added("{3}{1}{0}{2},".format(item, brackets[0], brackets[1],i(indentlevel)))
            else:
                # Handle lists and dicts here:
                diffstr = ''
                if type(item) is list or type(item) is dict:
                    diffstr = printsomething(item, 'added', indentlevel+1)
                retstr += added("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets[0], brackets[1],i(indentlevel)))
        else:
            if type(item) is str or type(item) is unicode:
                retstr += deleted("{3}{1}{0}{2},".format(bestmatch, brackets[0], brackets[1],i(indentlevel)))
                retstr += added("{3}{1}{0}{2},".format(item, brackets[0], brackets[1],i(indentlevel)))
            else:
                # Handle lists and dicts here:
                diffstr = ''
                if type(item) is list:
                    diffstr = difflist(item, bestmatch, indentlevel+1)
                elif type(item) is dict:
                    diffstr = diffdict(item, bestmatch, indentlevel+1)
                retstr += same("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets[0], brackets[1],i(indentlevel)))
            deletedlist.remove(bestmatch)
    for item in deletedlist:
        brackets = charfortype(item)
        if type(item) is str or type(item) is unicode:
            retstr += deleted("{3}{1}{0}{2},".format(item, brackets[0], brackets[1],i(indentlevel)))
        else:
            # Handle lists and dicts here:
            diffstr = ''
            if type(item) is list or type(item) is dict:
                diffstr = printsomething(item, 'deleted', indentlevel+1)
            retstr += deleted("{3}{1}<br/>\n{0}{3}{2},".format(diffstr, brackets[0], brackets[1],i(indentlevel)))
    return removeLastComma(retstr)

# levenshtein - http://hetland.org/coding/python/levenshtein.py
def strdistance(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
    return current[n]

def findmostsimilar(item, list):
    stritem = str(item)
    mindistance = sys.maxint
    bestmatch = None

    # Small performance boost.  Skip the expensive algo
    # if we know what it will return.
    if len(list) == 1 and type(item) is type(list[0]):
        return list[0]

    for listitem in list:
        if type(listitem) == type(item):
            strlistitem = str(listitem)
            distance = strdistance(stritem, strlistitem)
            if distance == 0:
                return listitem
            if distance < mindistance:
                bestmatch = listitem
                mindistance = distance
    return bestmatch

def charfortype(obj):
    if type(obj) is str or type(obj) is unicode:
        return "\"\""
    if type(obj) is list:
        return "[]"
    if type(obj) is dict:
        return "{}"
    return "  "

def color(text, color):
    return "<font color='{0}'>{1}</font><br/>\n".format(color, text)

def added(text):
    return color(text, "green")

def deleted(text):
    return color(text, "red")

def same(text):
    return color(text, "black")

class PolicyDiff(object):

    def __init__(self, new_policy, old_policy):
        self._new_policy = None
        self._old_policy = None

        if isinstance(new_policy, basestring):
            try:
                self._new_policy = json.loads(new_policy)
            except:
                print "Could not read policy in as json. Type: {} Policy: {}".format(type(new_policy), new_policy)
                self._new_policy = new_policy

        if isinstance(old_policy, basestring):
            try:
                self._old_policy = json.loads(old_policy)
            except:
                print "Could not read policy in as json. Type: {} Policy: {}".format(type(old_policy), old_policy)
                self._old_policy = old_policy

        if type(new_policy) is list or isinstance(new_policy, dict):
            self._new_policy = new_policy
            if type(self._new_policy) is collections.defaultdict:
                self._new_policy = dict(self._new_policy)

        if type(old_policy) is list or isinstance(old_policy, dict):
            self._old_policy = old_policy
            if type(self._old_policy) is collections.defaultdict:
                self._old_policy = dict(self._old_policy)

        if self._old_policy == None or self._new_policy == None:
            raise ValueError("PolicyDiff could not process old policy or new policy or both.")

        if not type(self._old_policy) is type(self._new_policy):
            print "OLD: {}".format(self._old_policy)
            print "NEW: {}".format(self._new_policy)
            print "Type OLD: {} Type New: {}".format(type(self._old_policy), type(self._new_policy))
            raise ValueError("Policies passed into PolicyDiff must be the same outer type (dict, list, str, unicode).")

    def produceDiffHTML(self):
        if self._old_policy == None or self._new_policy == None:
            raise ValueError("PolicyDiff could not process old policy or new policy or both.")

        if not type(self._old_policy) is type(self._new_policy):
            raise ValueError("Policies passed into PolicyDiff must be the same outer type (dict, list, str, unicode).")

        if self._old_policy == {} and self._new_policy == {}:
            return "No Policy.<br/>"

        if isinstance(self._old_policy, basestring):
            return "{0}<br/>{1}".format(deleted(self._old_policy), added(self._new_policy))

        brackets = charfortype(self._new_policy)
        inner_html = None

        if type(self._new_policy) is dict:
            inner_html = diffdict(self._new_policy, self._old_policy, 1)
        elif type(self._new_policy) is list:
            inner_html = difflist(self._new_policy, self._old_policy, 1)
        else:
            raise ValueError("PolicyDiff::produceDiffHTML cannot process items of type: {}".format(type(self._new_policy)))

        return "{1}<br/>\n{0}{2}<br/>\n".format(inner_html, brackets[0], brackets[1])

if __name__ == "__main__":

    old_pol = "{}"
    new_pol = """
    {
        "create_date": "2013-09-12T18:28:21Z",
        "must_change_password": "false",
        "user_name": "test"
    }
    """

    pdiddy = PolicyDiff(old_pol, new_pol)
    print pdiddy.produceDiffHTML()
