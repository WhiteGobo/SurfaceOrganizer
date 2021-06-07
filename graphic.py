import bpy.types
import bpy.utils
from . import editmodeoperators
from bpy.props import FloatProperty, BoolProperty
import logging
logger = logging.getLogger( __name__ )



class OBJECT_UL_surfacethingy( bpy.types.UIList ):
    def draw_item(self, _context, layout, _data, item, icon, \
                                    _active_data_, _active_propname, _index):
        #assert( isinstance(item, bpy.types.VertexGroup) )
        vgroup = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(vgroup, "name", text="", emboss=False, icon_value=icon)
            #icon = 'LOCKED' if vgroup.lock_weight else 'UNLOCKED'
            #layout.prop(vgroup, "lock_weight", text="",icon=icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class MainPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_select"
    bl_label = "Select"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data" #"object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    #def draw_header(self, context):
    #    layout = self.layout
    #    layout.label(text="My Select Panel")

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Assign Cornerpoints")
        row = box.row()
        qwer = row.operator("mesh.assign_leftupcorner", text="left up")
        row.operator("mesh.assign_rightupcorner", text="right up")
        row = box.row()
        row.operator("mesh.assign_leftdowncorner", text="left down")
        row.operator("mesh.assign_rightdowncorner", text="right down")
        box = layout.box()
        row = box.row()
        row.operator("mesh.toggle_leftupcorner", text="left up")
        row.operator("mesh.toggle_rightupcorner", text="right up")
        row = box.row()
        row.operator("mesh.toggle_leftdowncorner", text="left down")
        row.operator("mesh.toggle_rightdowncorner", text="right down")

        box = layout.box()
        box.label(text="SecondBox")
        #box.prop( qwer, "brubru", slider=True )
        #box.prop( bpy.types.Scene.brubrusettings, "my_settings" )
        obj = context.active_object
        #box.prop( obj.partial_surface_information, "my_settings" )
        row = box.row()
        row.template_list( 
                listtype_name = "OBJECT_UL_surfacethingy", 
                list_id = "", \
                dataptr = obj.partial_surface_information,
                propname = "partial_surface_info", 
                active_dataptr = obj.partial_surface_information, 
                active_propname = "active_surface_index", 
                rows = 3,\
                )
        sidebar = row.column()
        sidebar.operator("mesh.new_partialsurface", text="", icon="ADD")
        sidebar.operator("mesh.remove_partialsurface",text="",icon="REMOVE")
        partlist = obj.partial_surface_information.partial_surface_info
        index = obj.partial_surface_information.active_surface_index
        try:
            current_partialsurface = partlist[ index ]
        except Exception:
            current_partialsurface = None
        if current_partialsurface is not None:
            from .utils import border_operators as bod
            row = box.row()
            row.operator( bod.add_new_border_up.bl_idname, \
                                        text="Assign upborder")
            row = box.row()
            row.operator(bod.add_new_border_left.bl_idname, \
                                        text="Assign leftborder")
            row = box.row()
            row.operator(bod.add_new_border_down.bl_idname, \
                                        text="Assign downborder")
            row = box.row()
            row.operator(bod.add_new_border_right.bl_idname, \
                                        text="Assign rightborder")
            box.prop( current_partialsurface, "vertexgroup" )
        box.operator( "mesh.autocomplete_bordered_partialsurface", \
                        text="autom. surf.complete")


    #@classmethod
    #def poll( cls, context ):
    #    return editmodeoperators._AssignCornerPoint.poll( context )
    #    return False


_classes = ( \
        MainPanel, \
        OBJECT_UL_surfacethingy, \
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
