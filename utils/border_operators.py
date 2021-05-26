import bpy.types

class asdf( bpy.types.Operator ):
    bl_idname = "mesh.asdf"
    bl_label = "Add borderthingies"
    bl_options = {'UNDO'}
    def execute( self, context ):
        targetobject = context.active_object
        allinfo = targetobject.partial_surface_information
        return {'FINISHED'}

    @classmethod
    def poll( cls, context ):
        targetobject = context.active_object
        if targetobject == None:
            return False
        allinfo = targetobject.partial_surface_information
        partsurf_info = allinfo.partial_surface_info[ index ]
        first, second = cls.get_cornerindices( partsurf_info )
        lenvertices = len( allinfo.partial_surface_info )
        if not all( first < 0, first > lenvertices,
                    second < 0, second > lenvertices):
            return False
        return True
