# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name":        "User Report Wrapper Demo",
    "description": "Demo addon showcasing error wrapper handling and reporting",
    "author":      "Patrick W. Crawford",
    "version":     (1, 0, 0),
    "blender":     (2, 80, 0),
    "location":    "Info: Help > Report Error",
    "warning":     "",
    "tracker_url": "https://github.com/TheDuckCow/user-report-wrapper",
    "category":    "System"
    }


import importlib

if "load_modules" in locals():
    importlib.reload(user_reporting)
    importlib.reload(operators)
else:
    from . import user_reporting
    from . import operators
import bpy


def register():
    user_reporting.register(bl_info)
    operators.register()


def unregister():
    user_reporting.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
