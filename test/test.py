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


    def test_load_and_save_ascii( self ):
        import my_io_mesh_ply.plyhandler.get_surfacemap_from_ply.tests \
                    as testdirectory1
        override = {}
        with importlib.resources.path( testdirectory1, "tmp.ply" ) as filepath:
            logger.critical( filepath )
            bpy.ops.import_mesh.ply_with_border( files=[{"name":str(filepath)}])
        objname = "tmp"
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join( tmpdir, "tmpfile.ply" )
            bpy.ops.export_mesh.ply_with_border( filepath = filepath )



    def tearDown( self ):
        main.unregister()


if __name__=="__main__":
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()

