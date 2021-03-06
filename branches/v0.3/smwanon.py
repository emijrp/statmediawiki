#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010, 2011 StatMediaWiki
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#import hashlib #From python2.5
import md5
import random

import smwconfig

def noise(s):
    s = "%s%s%s" % (random.randint(1, 999999999), s, random.randint(1, 999999999))
    s = md5.new(s.encode(smwconfig.preferences['codification'])).hexdigest()
    return s

def anonimize():
    #tables & dicts with user information:
    #* images: img_user, img_user_text
    #* users: key, user_name
    #* revisions: rev_user, rev_user_text
    #* pages: nothing
    #* categories: nothing

    users_ = {}
    anonymous_table = {}
    #create anonymous table which is destroyed after exit this function
    #anonimyze users dict
    for user_id, user_props in smwconfig.users.items():
        user_name_ = noise(user_props["user_name_"])
        while user_name_ in anonymous_table.values(): #uniq md5
            user_name_ = noise(user_props["user_name_"])
        
        #tiene algun sentido tener distintos md5 (uno para el id, otro para el user_text) de cada usuario?
        #en la tabla de conversión, dejamos solo el campo user_name_, que es ell que usamos para convertir los dicts de imgs y revs de más abajo
        
        #anonymous_table[user_props["user_id"]] = user_name_
        #anonymous_table[user_props["user_name"]] = user_name_
        anonymous_table[user_props["user_name_"]] = user_name_

        user_props_ = user_props
        user_props_["user_id"] = user_name_
        user_props_["user_name"] = user_name_
        user_props_["user_name_"] = user_name_

        users_[user_name_] = user_props_
    smwconfig.users = users_

    #anonimize images dict
    for img_name, img_props in smwconfig.images.items():
        img_props_ = img_props
        img_props_["img_user"] = anonymous_table[img_props_["img_user_text_"]]
        img_props_["img_user_text"] = anonymous_table[img_props_["img_user_text_"]]
        img_props_["img_user_text_"] = anonymous_table[img_props_["img_user_text_"]]
        smwconfig.images[img_name] = img_props_

    #anonimize revisions dict
    for rev_id, rev_props in smwconfig.revisions.items():
        rev_props_ = rev_props
        rev_props_["rev_user"] = anonymous_table[rev_props_["rev_user_text_"]]
        rev_props_["rev_user_text"] = anonymous_table[rev_props_["rev_user_text_"]]
        rev_props_["rev_user_text_"] = anonymous_table[rev_props_["rev_user_text_"]]
        smwconfig.revisions[rev_id] = rev_props_
