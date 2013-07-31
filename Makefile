check: pep8 tests
	@echo ====================
	@echo \|\| It all passed! \|\|
	@echo ====================

pep8:
	@echo ================================================
	@echo \|\| Running pep8 checks against code and tests \|\|
	@echo ================================================
	pep8 -v bisect_b2g tests


TEST_RUNNER=python -m unittest discover -v
#TEST_RUNNER=nosetests -v
#TEST_RUNNER=py.test

tests:
	@echo ========================
	@echo \|\| Running unit tests \|\|
	@echo ========================
	$(TEST_RUNNER) $(PWD)/tests

.PHONY: check pep8 tests



# So that there is a standard name and url for releases
remotes:
	git remote add mozilla-b2g github.com:mozilla-b2g/bisect_b2g.git

# Do a release!
release:
	[ -f ~/.pypirc ] # So automatic submission works
	[ "x$(version)" != "x" ] # Make sure that there is a version defined
	@echo Version Bump
	sed -i '' -e 's/version[[:space:]]*=.*$$/version = "$(version)",/g' setup.py
	git commit -m "Version $(version)" setup.py | true
	git tag -d "v$(version)"
	git tag -m "Version $(version)" "v$(version)"
	git push origin "v$(version)"
	git push mozilla-org "v$(version)"
	@echo Building source package
	python setup.py clean sdist 
	@echo Uploading
	python setup.py upload
