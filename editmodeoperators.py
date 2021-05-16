import bpy
from . import surfacedivide

class _AssignCornerPoint( bpy.types.Operator ):
    def execute( self, context ):
        targetobject = context.active_object
        for v in targetobject.data.vertices:
            if v.select:
                selectedvertice = v
                break
        surfacename = ""
        surfacedivide.assign_cornerpoint( targetobject, selectedvertice, \
                                                surfacename, self.targetcorner )
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        return True
        targetobject = context.active_object
        selected_vertices = [v.index for v in targetobject.data.vertices \
                            if v.select ]
        condition = (len( selected_vertices ) == 1)
        return condition

class AssignRightUpCornerPoint( _AssignCornerPoint ):
    bl_idname = "mesh.assign_rightupcorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.RIGHTUP_CORNER

class AssignLeftUpCornerPoint( _AssignCornerPoint ):
    bl_idname = "mesh.assign_leftupcorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.LEFTUP_CORNER

class AssignLeftDownCornerPoint( _AssignCornerPoint ):
    bl_idname = "mesh.assign_leftdowncorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.LEFTDOWN_CORNER

class AssignRightDownCornerPoint( _AssignCornerPoint ):
    bl_idname = "mesh.assign_rightdowncorner"
    bl_label = "Assign rightupcornerpoint"
    bl_options = {'UNDO'}
    targetcorner = surfacedivide.RIGHTDOWN_CORNER
