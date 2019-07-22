VERSION  = $(shell cat VERSION)

clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -f tests/.coverage
	-rm container_shell.spec
	-rm -rf ContainerShell-*/
	-docker rm $(shell docker ps -aq)
	-docker rmi $(shell docker images -q --filter "dangling=true")

whl: clean
	python setup.py bdist_wheel

uninstall:
	-pip uninstall -y container-shell

install: uninstall whl
	pip install --trusted-host pypi.org -U dist/*.whl

binary: install
	pyinstaller -F container_shell/container_shell.py

deb:
	mkdir -p ContainerShell-$(VERSION)/DEBIAN/
	mkdir -p ContainerShell-$(VERSION)/usr/bin/
	mkdir -p ContainerShell-$(VERSION)/etc/container_shell/
	cp sample.config.ini ContainerShell-$(VERSION)/etc/container_shell/
	cp dist/container_shell ContainerShell-$(VERSION)/usr/bin/
	cp postinst ContainerShell-$(VERSION)/DEBIAN/
	cp control ContainerShell-$(VERSION)/DEBIAN/
	sed -i -e 's/VERSION/'$(VERSION)'/g' ContainerShell-$(VERSION)/DEBIAN/control
	sudo chown root:root -R ContainerShell-$(VERSION)
	dpkg -b ContainerShell-$(VERSION)
	mv ContainerShell*.deb dist/

pkgs: binary deb


lint:
	pylint container_shell

test: uninstall install
	cd tests && nosetests -v --with-coverage --cover-package=container_shell
