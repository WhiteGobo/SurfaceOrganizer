
.PHONY: test
test: test/test.py
	env TESTSCRIPTS=$(abspath test/) TESTMODULE=$(abspath ../) \
		blender -b --python $(word 1, $^)
