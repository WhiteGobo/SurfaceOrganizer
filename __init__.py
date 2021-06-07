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

# <pep8-80 compliant>

bl_info = {
    "name": "Stanford PLY format for createcloth",
    "author": "Richard Fechner",
    "version": (0, 0, 1),
    "blender": (2, 90, 0),
    "location": "File > Import/Export",
    "description": "Import-Export PLY mesh data for createcloth",
    #"doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/mesh_ply.html",
    #"support": 'OFFICIAL',
    "category": "Import-Export",
}

#if "bpy" in locals():
#    import importlib
#    if "export_ply" in locals():
#        importlib.reload(export_ply)
#    if "import_ply" in locals():
#        importlib.reload(import_ply)


import bpy
from bpy.props import (
    CollectionProperty,
    StringProperty,
    BoolProperty,
    FloatProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    axis_conversion,
    orientation_helper,
)
import logging
logger = logging.getLogger( __name__ )

from . import custom_properties
from . import utils
from . import exporter




classes = tuple(
    #MyImportPLY,
    #MyExportPLY,
    #PLY_PT_export_transform,
    #AssignRightUpCornerPoint,
    #AssignLeftUpCornerPoint,
    #AssignLeftDownCornerPoint,
    #AssignRightDownCornerPoint,
)
from .exceptions import RegisterError

from . import editmodeoperators as edop
def register():
    exporter.register()
    #if bpy.app.version >= (2,93,0):
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as err:
            raise RegisterError( cls ) from err
    #for cls in (edop.AssignRightUpCornerPoint, edop.AssignLeftUpCornerPoint,
    #        edop.AssignLeftDownCornerPoint, edop.AssignRightDownCornerPoint):
    #    bpy.utils.register_class( cls )
    try:
        custom_properties.register()
    except Exception as err:
        raise RegisterError( "couldnt register 'custom_properties'" ) from err
    try:
        edop.register()
    except Exception as err:
        raise RegisterError( "couldnt register 'editmodeoperators'" ) from err
    try:
        utils.register()
    except Exception as err:
        raise RegisterError( "couldnt register 'utils'" ) from err

    from . import graphic
    try:
        graphic.register()
    except Exception as err:
        raise RegisterError( "couldnt register 'graphic'" ) from err


class UnregisterError( Exception ):
    pass
def unregister():
    exporter.unregister()
    from . import editmodeoperators as edop
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except (ValueError, RuntimeError) as err:
            logger.debug( err )
    edop.unregister()

    from . import graphic
    graphic.unregister()
    utils.unregister()
    #custom_properties.unregister()


if __name__ == "__main__":
    register()
