VERSION  = $(shell cat VERSION)
CWD = $(shell pwd)

clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf *.egg-info
	-rm -f tests/.coverage
	-rm container_shell.spec
	-rm -rf ContainerShell-*/
	-rm -rf rpmbuild
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

rpm:
	mkdir -p build/ContainerShell-$(VERSION)/usr/bin
	mkdir -p build/ContainerShell-$(VERSION)/etc/container_shell
	cp sample.config.ini build/ContainerShell-$(VERSION)/etc/container_shell
	cp dist/container_shell build/ContainerShell-$(VERSION)/usr/bin
	cd build && tar -czvf ../dist/ContainerShell-$(VERSION).tar.gz ContainerShell-$(VERSION)
	mkdir -p build/rpm/BUILD
	mkdir -p build/rpm/SOURCES
	mkdir -p build/rpm/SPECS
	mv dist/ContainerShell-$(VERSION).tar.gz build/rpm/SOURCES
	cp container_shell.rpm.spec build/rpm/SPECS/container_shell.spec
	sed -i -e 's/VERSION/'$(VERSION)'/g' build/rpm/SPECS/container_shell.spec
	rpmbuild --bb --define '_topdir '$(CWD)'/build/rpm' build/rpm/SPECS/container_shell.spec
	mv build/rpm/RPMS/x86_64/ContainerShell*.rpm dist/


pkgs: binary deb rpm
	sudo rm -rf ContainerShell-$(VERSION)
	rm -rf build/ContainerShell-$(VERSION)


lint:
	pylint container_shell

test: uninstall install
	cd tests && nosetests -v --with-coverage --cover-package=container_shell
