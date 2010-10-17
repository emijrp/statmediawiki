#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 StatMediaWiki
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

#StatMediaWiki modules
import smwanal
import smwanon
import smwdb
import smwconfig
import smwinit
import smwload
import smwoutput

#todo:
#con que numero se lanzan los sys.exit() cuando hay un fallo?
#que las rutas ../../ no sean relativas, buscar algo como $IP o __file__ ?
#len() devuelve bytes?

#conv:
#convenciones:
#solo contamos los añadidos de texto, no cuando se elimina texto (no se penaliza a nadie)

#el usuario que hace las consultas sql debe tener acceso lectura a las bbdd, con los datos de .my.cnf

def main():
    smwinit.welcome()
    smwinit.getParameters()

    smwload.load()

    if smwconfig.preferences["anonymous"]:
        smwanon.anonimize()

    smwoutput.manageOutputDir()
    smwanal.generateAnalysis()
    smwoutput.copyFiles()

    smwinit.bye()

if __name__ == "__main__":
    main()
