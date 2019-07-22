clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -f tests/.coverage
	-rm container_shell.spec
	-docker rm $(shell docker ps -aq)
	-docker rmi $(shell docker images -q --filter "dangling=true")

whl: clean
	python setup.py bdist_wheel --universal

binary: clean
	pyinstaller -F container_shell/container_shell.py

uninstall:
	-pip uninstall -y container-shell

install: uninstall whl
	pip install --trusted-host pypi.org -U dist/*.whl

lint:
	pylint container_shell

test: uninstall install
	cd tests && nosetests -v --with-coverage --cover-package=container_shell
