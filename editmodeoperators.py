#import bpy
import bpy.types
import bpy.utils
from . import surfacedivide
from . import custom_properties
import bmesh
from bpy.props import FloatProperty, BoolProperty
import logging
logger = logging.getLogger( __name__ )

class NewPartialSurface( bpy.types.Operator ):
    bl_idname = "mesh.new_partialsurface"
    bl_label = "New Partialsurface"
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        allinfo.partial_surface_info.add()
        allinfo.active_surface_index = 1 + len( allinfo.partial_surface_info )
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        if context.active_object == None:
            return False
        return True

class RemovePartialSurface( bpy.types.Operator ):
    bl_idname = "mesh.remove_partialsurface"
    bl_label = "Remove Partialsurface"
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index

        allinfo.partial_surface_info.remove( index )
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        if context.active_object == None:
            return False
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index
        if index >= len( allinfo.partial_surface_info ) or index < 0:
            return False
        return True


class _AssignCornerPoint:
    def execute( self, context ):
        surfacename = None
        targetobject = context.active_object
        helpmesh = bmesh.from_edit_mesh( targetobject.data )

        surfacedivide.ensure_partial_surface( targetobject )
        for v in helpmesh.verts:
            if v.select:
                selectedvertice = v
                break
        surfacedivide.assign_cornerpoint( targetobject, selectedvertice, \
                                                self.targetcorner )
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        if context.active_object == None:
            return False
        if context.active_object.mode != 'EDIT':
            return False
        targetobject = context.active_object
        helpmesh = bmesh.from_edit_mesh( targetobject.data )
        number_selected = sum( 1 for v in helpmesh.verts if v.select )
        #helpmesh.free() #no free because bmesh.from_edit_mesh ???
        return number_selected == 1

class AssignRightUpCornerPoint( _AssignCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.assign_rightupcorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.RIGHTUP_CORNER

class AssignLeftUpCornerPoint( _AssignCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.assign_leftupcorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.LEFTUP_CORNER

class AssignLeftDownCornerPoint( _AssignCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.assign_leftdowncorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.LEFTDOWN_CORNER

class AssignRightDownCornerPoint( _AssignCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.assign_rightdowncorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.RIGHTDOWN_CORNER



_classes = ( \
        AssignRightUpCornerPoint, AssignLeftUpCornerPoint, \
        AssignLeftDownCornerPoint, AssignRightDownCornerPoint,\
        NewPartialSurface, \
        RemovePartialSurface, \
        )

def register():
    for cls in _classes:
        bpy.utils.register_class( cls )

def unregister():
    for cls in reversed( _classes ):
        try:
            bpy.utils.unregister_class( cls )
        except (ValueError, RuntimeError) as err:
            logger.debug( err )
