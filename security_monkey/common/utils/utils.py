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
.. module: security_monkey.common.utils.utils
    :platform: Unix
    :synopsis: Utility methods pasted and bastardized from all over the place. Can probably be removed completely.

.. version:: $$VERSION$$
.. moduleauthor:: Patrick Kelley <pkelley@netflix.com> @monkeysecurity

"""

prims = [int, str, unicode, bool, type(None)]


def sub_list(l):
    r = []

    for i in l:
        if type(i) in prims:
            r.append(i)
        elif type(i) is list:
            r.append(sub_list(i))
        elif type(i) is dict:
            r.append(sub_dict(i))
        else:
            print "Unknown Type: {}".format(type(i))
    r = sorted(r)
    return r


def sub_dict(d):
    r = {}
    for k in d:
        if type(d[k]) in prims:
            r[k] = d[k]
        elif type(d[k]) is list:
            r[k] = sub_list(d[k])
        elif type(d[k]) is dict:
            r[k] = sub_dict(d[k])
        else:
            print "Unknown Type: {}".format(type(d[k]))
    return r
