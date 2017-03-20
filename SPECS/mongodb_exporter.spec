%define debug_package %{nil}

%define _git_url https://github.com/percona/mongodb_exporter
%define _git_slug src/github.com/percona/mongodb_exporter
%define _git_release 20170320

Name:    mongodb_exporter
Version: 0.1.1
Release: 0.%{_git_release}git.vortex%{?dist}
Summary: Prometheus exporter for machine metrics
License: MIT
Vendor:  Vortex RPM
URL:     https://github.com/percona/mongodb_exporter

Source2: %{name}.default
Source3: %{name}.init

Patch0: vendor.patch

Requires(post): chkconfig
Requires(preun): chkconfig, initscripts
Requires(pre): shadow-utils
Requires: daemonize
BuildRequires: golang, git

%description
Prometheus exporter for MongoDB.

%prep
# Create GOPATH
mkdir _build
export GOPATH=$(pwd)/_build

# Install govendor
go get -v github.com/kardianos/govendor
git clone %{_git_url} $GOPATH/%{_git_slug}

# Patch vendor-file to exclude mgo
cd $GOPATH/%{_git_slug}
pushd vendor
%patch0
popd

# Install mgo manually
git clone https://github.com/go-mgo/mgo $GOPATH/src/gopkg.in/mgo.v2
pushd $GOPATH/src/gopkg.in/mgo.v2
git checkout v2
popd

# Run govendor
$GOPATH/bin/govendor sync -v

%build
export GOPATH=$(pwd)/_build
cd $GOPATH/%{_git_slug}
go build -o mongodb_exporter mongodb_exporter.go
strip mongodb_exporter

%install
export GOPATH=$(pwd)/_build
mkdir -vp %{buildroot}/var/lib/prometheus
mkdir -vp %{buildroot}/usr/sbin
mkdir -vp %{buildroot}%{_initddir}
mkdir -vp %{buildroot}/etc/default
install -m 755 $GOPATH/%{_git_slug}/%{name} %{buildroot}/usr/sbin/%{name}
install -m 755 %{SOURCE3} %{buildroot}%{_initddir}/%{name}
install -m 644 %{SOURCE2} %{buildroot}/etc/default/%{name}

%pre
getent group prometheus >/dev/null || groupadd -r prometheus
getent passwd prometheus >/dev/null || \
  useradd -r -g prometheus -d /var/lib/prometheus -s /sbin/nologin \
          -c "Prometheus services" prometheus
exit 0

%post
/sbin/chkconfig --add %{name}

%preun
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%postun
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} restart >/dev/null 2>&1
fi

%files
%defattr(-,root,root,-)
/usr/sbin/%{name}
%{_initddir}/%{name}
%config(noreplace) /etc/default/%{name}
%attr(755, prometheus, prometheus)/var/lib/prometheus
%doc _build/%{_git_slug}/LICENSE _build/%{_git_slug}/README.md

%changelog
* Mon Mar 20 2017 Ilya Otyutskiy <ilya.otyutskiy@icloud.com> - 0.1.1-0.20170320git.vortex
- Initial packaging
