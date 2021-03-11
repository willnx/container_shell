Name: ContainerShell
Version: VERSION
Release: 1
Summary: Drops you into a container, instead of the host environment.
License: Apache2
Source0: ContainerShell-VERSION.tar.gz
Url: https://github.com/willnx/container_shell

%description
 To run a docker command you need to be root or part of the docker group (which
 effectively is root). Container Shell avoids this by leveraging the setgid
 permission, allowing a user that is not part of the docker group the ability to
 access a admin-defined container.

%prep
%setup -q

%build

%install
echo ${buildroot}
rm -rf %{buildroot}
mkdir -p %{buildroot}

cp -R * %{buildroot}

%clean
rm -rf %{buildroot}

%post
chown root /usr/bin/container_shell
chmod u+s /usr/bin/container_shell

mkdir -p /var/log/container_shell
# Yeah, this is a bit cheesy, but it:
#   A) Centralized the location of the log file
#   B) Allows all users to write to it, without opening all of /var/log
# If you have a better idea, I'd love to hear what it is!
chmod 777 /var/log/container_shell


%files
/usr/bin/container_shell
/etc/container_shell/sample.config.ini
