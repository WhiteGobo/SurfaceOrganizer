import bpy

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

    vertexlist, faces, rightup, leftup, leftdown, rightdown \
                    = load_meshdata_from_ply( filepath )

    generate_blender_object( meshname, objectname, vertexlist, faces, \
                                        rightup, leftup, leftdown, rightdown, \
                                        collection, view_layer )
    return {'FINISHED'}

def load_meshdata_from_ply( filepath ):
    plyobj = load_ply_obj_from_filename( filepath )
    vertexpositions = plyobj["vertex"].get_filtered_data( "x", "y", "z" )
    faceindices = plyobj["face"].get_filtered_data( "vertex_indices" )
    faceindices = [ f[0] for f in faceindices ]
    border = plyobj["cornerrectangle"].get_filtered_data( \
                                            "rightup", "leftup", \
                                            "leftdown", "rightdown" )
    rightup, leftup, leftdown, rightdown = border[0]
    return vertexpositions, faceindices, rightup, leftup, leftdown, rightdown


def extract_vertex_positions( blender_obj_info ):
    vertexpositions = blender_obj_info.vertex 
    vertexnumber = len( blender_obj_info.vertex )
    return vertexpositions, vertexnumber


def generate_blender_object( meshname, objectname, vertices_list, faces, \
                                        rightup, leftup, leftdown, rightdown, \
                                        collection, view_layer ):
    mymesh = generate_mesh( vertices_list, faces, meshname )

    obj = bpy.data.objects.new( objectname, mymesh )

    collection.objects.link( obj )
    view_layer.objects.active = obj

    create_vertexgroup_with_vertice( obj, "leftup", leftup )
    create_vertexgroup_with_vertice( obj, "rightup", rightup )
    create_vertexgroup_with_vertice( obj, "rightdown", rightdown )
    create_vertexgroup_with_vertice( obj, "leftdown", leftdown )

    obj.select_set(True)
    return obj, mymesh


def generate_mesh( vertices_list, faces, meshname ):
    mesh = bpy.data.meshes.new( name=meshname )
    edgelist = [] # if faces are given no edges need to be provided
    mesh.from_pydata( vertices_list, edgelist, faces )
    #mesh.update()
    mesh.validate()

    return mesh


def create_vertexgroup_with_vertice( obj, vertexgroupname, vertice ):
    weight, add_type = 1, "REPLACE"
    obj.vertex_groups.new( name=vertexgroupname )
    obj.vertex_groups[ vertexgroupname ].add( [vertice], weight, add_type )


