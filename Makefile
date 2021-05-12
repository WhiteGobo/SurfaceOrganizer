ZIP = zip
ZIP_ARGS = 
blenderpackagefiles = \
	./blender_to_plycontainer.py \
	./__init__.py \
	./plycontainer_to_blender.py \
	./plyhandler/get_surfacemap_from_ply/datacontainer.py \
	./plyhandler/get_surfacemap_from_ply/__init__.py \
	./plyhandler/get_surfacemap_from_ply/myexport_ply.py \
	./plyhandler/get_surfacemap_from_ply/create_surfacemap.py \
	./plyhandler/get_surfacemap_from_ply/myimport_ply.py \
	./plyhandler/get_surfacemap_from_ply/main.py

default: my_io_mesh_ply.zip

my_io_mesh_ply.zip: $(blenderpackagefiles)
	$(ZIP) $(ZIP_ARGS) $@ $^

.PHONY: test
test: test/test.py test/test.blend
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ../) \
		blender -b $(word 2, $^) --python $(word 1, $^)

.PHONY: clear

clear:
	-rm my_io_mesh_ply.zip
