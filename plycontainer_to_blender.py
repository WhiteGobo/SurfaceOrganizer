import bpy.path
import bpy.data

import itertools
from .plyhandler.get_surfacemap_from_ply import load_ply_obj_from_filename

def load_ply( filepath, collection, view_layer ):
    """
    :param collection: context.collection from blenderoperator
    :param view_layer: context.view_layer from blenderoperator
    """
    #filename = "/home/hfechner/tmp.ply"
    #filename = "/home/hfechner/meshfortests.ply"
    ply_name = bpy.path.display_name_from_filepath( filepath )
    meshname = ply_name
    objectname = ply_name

    vertexlist, faces = load_meshdata_from_ply( filepath )

    generate_blender_object( meshname, objectname, blender_obj_info, \
                                                    collection, view_layer )
    return {'FINISHED'}

def load_meshdata_from_ply( filepath ):
    plyobj = load_ply_obj_from_filename( filepath )
    vertexpositions = myobj["vertex"].get_filtered_data( "x", "y", "z" )
    faceindices = myobj["face"].get_filtered_data( "indices" )
    return vertexpositions, faceindices


def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( meshname, objectname, vertices_list, faces, \
                                                    collection, view_layer ):
    mymesh = generate_mesh( vertices_list, faces, meshname )

    obj = bpy.data.objects.new( objectname, mymesh )

    collection.objects.link( obj )
    view_layer.objects.active = obj

    #add_vertexgroup_rand( obj, borderrectangle )

    obj.select_set(True)
    return obj, mymesh


def generate_mesh( vertices_list, faces, meshname ):
    mesh = bpy.data.meshes.new( name=ply_name )
    edgelist = [] # if faces are given no edges need to be provided
    mesh.from_pydata( vertices_list, faces, edgelist )
    #mesh.update()
    mesh.validate()

    return mesh


def add_vertexgroup_rand( obj, borderrectangle ):
    bordervert_leftup, bordervert_rightup, bordervert_rightdown, \
                                    bordervert_leftdown = borderrectangle
    create_vertexgroup_with_vertices( obj, "leftupcorner", [bordervert_leftup] )
    create_vertexgroup_with_vertices( obj, "rightupcorner",[bordervert_rightup])
    create_vertexgroup_with_vertices( obj, "rightdowncorner", \
                                    [bordervert_rightdown])
    create_vertexgroup_with_vertices( obj, "leftdowncorner", \
                                    [bordervert_leftdown] )
