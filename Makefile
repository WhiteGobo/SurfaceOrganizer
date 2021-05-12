
.PHONY: test
test: test/test.py test/test.blend
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ../) \
		blender -b $(word 2, $^) --python $(word 1, $^)
