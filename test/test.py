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
        pass


    def tearDown( self ):
        main.unregister()


if __name__=="__main__":
    sys.argv = [__file__] \
            + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()

