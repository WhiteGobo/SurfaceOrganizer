import os
import sys
try:
    sys.path.insert( 0, os.environ["TESTSCRIPTS"] )
except KeyError:
    sys.path.insert( 0, os.getcwd() )
try:
    sys.path.insert( 0, os.environ["TESTMODULE"] )
except KeyError:
    sys.path.insert( 0, os.getcwd() )
import unittest
import importlib.resources
import tempfile
import bpy
import my_io_mesh_ply as main
from my_io_mesh_ply import plyhandler

import logging
logger = logging.getLogger( __name__ )

class test_blender_plyimporter( unittest.TestCase ):
    def setUp( self ):
        logging.basicConfig( level=logging.DEBUG )
        main.register()


    def test_load_ascii( self ):
        import my_io_mesh_ply.plyhandler.get_surfacemap_from_ply.tests \
                    as testdirectory1
        override = {}
        with importlib.resources.path( testdirectory1, "tmp.ply" ) as filepath:
            logger.critical( filepath )
            bpy.ops.import_mesh.ply_with_border( files=[{"name":str(filepath)}])

        objname = "tmp"
        newobj = bpy.data.objects[ -1 ] #last created object
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            override = { "selected_objects":[newobj] }
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )

    def test_save_ascii( self ):
        newobj = bpy.data.objects["PreparedWithBorderCube"] 
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            override = { "selected_objects":[newobj] }
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )

    def test_save_ascii_multiplesurfaces( self ):
        newobj = bpy.data.objects["PreparedWithMultipleSurfaces"] 
        scene = bpy.data.scenes["test_save_ascii_multiplesurfaces"]
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            override = { "selected_objects":[newobj] }
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )

    
    def test_assignborder( self ):
        obj = bpy.data.objects["planeforadding"] 
        override = {"scene":"borderadding", "selected_objects":[obj], \
                    "active_object":obj}
        for i, v in enumerate( obj.data.vertices ):
            v.select = (i==0)
        bpy.ops.mesh.assign_rightupcorner( override )
        for i, v in enumerate( obj.data.vertices ):
            v.select = (i==1)
        bpy.ops.mesh.assign_leftupcorner( override )
        for i, v in enumerate( obj.data.vertices ):
            v.select = (i==2)
        bpy.ops.mesh.assign_leftdowncorner( override )
        for i, v in enumerate( obj.data.vertices ):
            v.select = (i==3)
        bpy.ops.mesh.assign_rightdowncorner( override )
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            bpy.ops.export_mesh.ply_with_border( override, \
                                                filepath = filepath, \
                                                use_selection = True )


    def tearDown( self ):
        main.unregister()



if __name__=="__main__":
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()

