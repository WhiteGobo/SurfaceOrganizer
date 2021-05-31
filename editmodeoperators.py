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


def _toggle_vertice( targetobject, vertice_index ):
    mode = targetobject.mode
    for sc in bpy.data.scenes:
        if targetobject.name in sc.objects:
            scene = sc
            break
    override = { "scene": scene, "active_object": targetobject }
    bpy.ops.object.mode_set( override, mode='EDIT' )
    #bpy.ops.mesh.select_mode( type='VERT' )
    #bpy.ops.mesh.select_all( action='DESELECT' )
    bpy.ops.object.mode_set( override, mode='OBJECT' )
    v = targetobject.data.vertices[ vertice_index ]
    v.select = not v.select
    bpy.ops.object.mode_set( override, mode=mode )

class _ToggleCornerPoint:
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index 
        partsurf_info = allinfo.partial_surface_info[ index ]
        vert = self.get_corner( partsurf_info )
        _toggle_vertice( targetobject, vert )
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        if context.active_object == None:
            return False
        if context.active_object.mode != 'EDIT':
            return False
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        index = allinfo.active_surface_index 
        if index < 0 or index >= len( allinfo.partial_surface_info ):
            return False
        if cls.get_corner( allinfo.partial_surface_info[ index ] ) < 0:
            return False
        return True

class toggle_rightupcorner( _ToggleCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.toggle_rightupcorner"
    bl_label = "Toggle rightupcornerpoint"
    @classmethod
    def get_corner( cls, partsurf_info ):
        return partsurf_info.rightup_corner
class toggle_leftupcorner( _ToggleCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.toggle_leftupcorner"
    bl_label = "Toggle leftupcornerpoint"
    @classmethod
    def get_corner( cls, partsurf_info ):
        return partsurf_info.leftup_corner
class toggle_leftdowncorner( _ToggleCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.toggle_leftdowncorner"
    bl_label = "Toggle leftdowncornerpoint"
    @classmethod
    def get_corner( cls, partsurf_info ):
        return partsurf_info.leftdown_corner
class toggle_rightdowncorner( _ToggleCornerPoint, bpy.types.Operator ):
    bl_idname = "mesh.toggle_rightdowncorner"
    bl_label = "Toggle rightdowncornerpoint"
    @classmethod
    def get_corner( cls, partsurf_info ):
        return partsurf_info.rightdown_corner


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
        toggle_rightupcorner, toggle_leftupcorner, \
        toggle_leftdowncorner, toggle_rightdowncorner, \
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
