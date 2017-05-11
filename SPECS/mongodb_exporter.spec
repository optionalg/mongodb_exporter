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

Source1: %{name}.service
Source2: %{name}.default
Source3: %{name}.init

Patch0: vendor.patch

%{?el6:Requires(post): chkconfig}
%{?el6:Requires(preun): chkconfig, initscripts}
Requires(pre): shadow-utils
%{?el6:Requires: daemonize}
%{?el7:%{?systemd_requires}}
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
%{?el6:mkdir -vp %{buildroot}/usr/sbin}
%{?el7:mkdir -vp %{buildroot}/usr/bin}
%{?el6:mkdir -vp %{buildroot}%{_initddir}}
%{?el7:mkdir -vp %{buildroot}/usr/lib/systemd/system}
mkdir -vp %{buildroot}/etc/default
%{?el6:install -m 755 $GOPATH/%{_git_slug}/%{name} %{buildroot}/usr/sbin/%{name}}
%{?el7:install -m 755 $GOPATH/%{_git_slug}/%{name} %{buildroot}/usr/bin/%{name}}
%{?el6:install -m 755 %{SOURCE3} %{buildroot}%{_initddir}/%{name}}
%{?el7:install -m 755 %{SOURCE1} %{buildroot}/usr/lib/systemd/system/%{name}.service}
install -m 644 %{SOURCE2} %{buildroot}/etc/default/%{name}

%pre
getent group prometheus >/dev/null || groupadd -r prometheus
getent passwd prometheus >/dev/null || \
  useradd -r -g prometheus -d /var/lib/prometheus -s /sbin/nologin \
          -c "Prometheus services" prometheus
exit 0

%post
%{?el6:/sbin/chkconfig --add %{name}}
%{?el7:%systemd_post %{name}.service}

%preun
%{?el6:
if [ $1 -eq 0 ] ; then
    /sbin/service %{name} stop >/dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi
}
%{?el7:%systemd_preun %{name}.service}

%postun
%{?el6:
if [ "$1" -ge "1" ] ; then
    /sbin/service %{name} restart >/dev/null 2>&1
fi
}
%{?el7:%systemd_postun %{name}.service}

%files
%defattr(-,root,root,-)
%{?el6:/usr/sbin/%{name}}
%{?el7:/usr/bin/%{name}}
%{?el6:%{_initddir}/%{name}}
%{?el7:/usr/lib/systemd/system/%{name}.service}
%config(noreplace) /etc/default/%{name}
%attr(755, prometheus, prometheus)/var/lib/prometheus
%doc _build/%{_git_slug}/LICENSE _build/%{_git_slug}/README.md

%changelog
* Mon Mar 20 2017 Ilya Otyutskiy <ilya.otyutskiy@icloud.com> - 0.1.1-0.20170320git.vortex
- Initial packaging
