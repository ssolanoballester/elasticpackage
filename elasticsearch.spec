#
# spec file for package elasticsearch
#
# Copyright (c) 2018 Samu Voutilainen
# Copyright (c) 2017 SUSE LINUX GmbH, Nuernberg, Germany.
# Copyright (c) 2016 kkaempf
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


%if 0%{?suse_version} > 1140 || 0%{?fedora_version} > 14
%define has_systemd 1
%else
%define has_systemd 0
%endif

%if ! %{defined _fillupdir}
%define _fillupdir /var/adm/fillup-templates
%endif

# "backport"
%{!?_initddir:    %{expand: %%global _initddir    %{_initrddir}}}
%{!?_rundir:      %{expand: %%global _rundir      /run}}
# these two are broken on SLE 11... so just "correct" them enough to work...
%{!?_tmpfilesdir: %{expand: %%global _tmpfilesdir %{_prefix}/lib/tmpfiles.d}}
%{!?_sysctldir:   %{expand: %%global _sysctldir   %{_prefix}/lib/sysctl.d}}

Name:           elasticsearch
Version:        6.2.4
Release:        5.2
Summary:        Open Source, Distributed, RESTful Search Engine
License:        Apache-2.0
Group:          Productivity/Databases/Tools
Url:            https://github.com/elastic/elasticsearch
Source0:        https://github.com/elastic/elasticsearch/archive/%{version}/%{name}-%{version}.tar.gz

Source2:        %{name}.logrotate
Source5:        %{name}.tmpfiles.d
Source7:        %{name}.SuSEfirewall2
Source8:        %{name}.init
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildRequires:  git
# gradle > 4 is needed for openjdk 9
BuildRequires:  gradle > 4
BuildRequires:  libjnidispatch

%if 0%{?suse_version} > 1010
BuildRequires:  fdupes
%endif
BuildRequires:  java-devel = 10

# %%{version}
BuildRequires:  elasticsearch-kit == %{version}

%if 0%{?has_systemd}
BuildRequires:  systemd
%{?systemd_requires}
%endif

# SLE_12 and Leap 42 need this:
BuildRequires:  mozilla-nss

BuildArch:      noarch
Provides:       mvn(org.elasticsearch:core) == %{version}
Provides:       mvn(org.elasticsearch:dev-tools) == %{version}
Provides:       mvn(org.elasticsearch:distribution) == %{version}
Provides:       mvn(org.elasticsearch:modules) == %{version}
Provides:       mvn(org.elasticsearch:plugins) == %{version}
Provides:       mvn(org.elasticsearch:qa) == %{version}
Provides:       mvn(org.elasticsearch:rest-api-spec) == %{version}
Provides:       mvn(org:elasticsearch) == %{version}

%if 0%{?has_systemd}
Requires(post): %fillup_prereq
%else
Requires(post): %insserv_prereq  %fillup_prereq
%endif

Requires:       java-headless = 10
Requires:       logrotate
# for sysctl:
Requires:       procps
# for elasticsearch-plugin:
Requires:       hostname
Requires:       which
# mkdir, chown in %%pre
Requires(pre):  coreutils

%description
Elasticsearch is a distributed RESTful search engine built for the
cloud. Reference documentation can be found at
https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html
and the 'Elasticsearch: The Definitive Guide' book can be found at
https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html

%prep
%setup -q -c -n src
rm -rf /tmp/gradle* /tmp/apache*
cp -Rf %{_datadir}/tetra/gradle* /tmp
cp -Rf %{_datadir}/tetra/apache* /tmp

%build
cd ../src/%{name}-%{version}
export GRADLE_OPTS="-Xmx1024m"
export GRADLE_USER_HOME=/tmp/gradle
gradle \
  --gradle-user-home $GRADLE_USER_HOME \
  --project-cache-dir /tmp/gradle-project \
  -Dbuild.snapshot=false \
  --offline \
  --no-daemon \
  assemble

%clean
rm -rf ~/.gradle

%install
export BUILD_VCS_NUMBER=%{version}
export NO_BRP_CHECK_BYTECODE_VERSION=true
cd %{name}-%{version}

#
# bin

install -d %{buildroot}%{_datadir}
tar -C %{buildroot}%{_datadir} -xf distribution/tar/build/distributions/%{name}-%{version}.tar.gz
mv %{buildroot}%{_datadir}/%{name}-%{version} %{buildroot}%{_datadir}/%{name}

# handled as %%doc
rm -f %{buildroot}%{_datadir}/%{name}/README.textile
rm -f %{buildroot}%{_datadir}/%{name}/LICENSE.txt
rm -f %{buildroot}%{_datadir}/%{name}/NOTICE.txt

rm -f %{buildroot}%{_datadir}/%{name}/bin/*.exe
rm -f %{buildroot}%{_datadir}/%{name}/bin/*.bat

#
# var

%{__install} -d -m 755 %{buildroot}%{_localstatedir}/log/%{name}
%{__install} -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}
%{__install} -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}/data
%{__install} -d -m 755 %{buildroot}%{_localstatedir}/lib/%{name}/work
%{__install} -d -m 755 %{buildroot}%{_rundir}/%{name}

#
# /usr/share
%{__install} -d %{buildroot}%{_datadir}/%{name}

#
# tmpfiles.d
%{__install} -d -m 755 %{buildroot}%{_tmpfilesdir}
%{__install} -m 644 %{S:5} %{buildroot}%{_tmpfilesdir}/%{name}.conf

#
# sbin
%{__install} -d %{buildroot}%{_sbindir}

#
# init scripts / systemd

%if 0%{?has_systemd}
%{__install} -D -m 644 distribution/rpm/build/packaging/systemd/elasticsearch.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
%{__install} -D -m 644 distribution/src/main/packaging/systemd/sysctl/%{name}.conf $RPM_BUILD_ROOT%{_sysconfdir}/sysctl.d/%{name}.conf

# rc%%{name}
ln -sf %{_sbindir}/service $RPM_BUILD_ROOT%{_sbindir}/rc%{name}
%else
mkdir -p $RPM_BUILD_ROOT%{_initddir}
%{__install} -m 755 %{S:8} $RPM_BUILD_ROOT%{_initddir}/%{name}
ln -sf %{_initddir}/%{name} $RPM_BUILD_ROOT%{_sbindir}/rc%{name}
%endif

#
# logrotate

%{__install} -D -m 644 %{S:2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

#
# SuSEfirewall2
%{__install} -D -m 644 %{S:7} %{buildroot}%{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/%{name}

#
# /etc/elasticsearch
%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
%{__install} -m 644 distribution/rpm/build/packaging/etc/elasticsearch/%{name}.yml %{buildroot}%{_sysconfdir}/%{name}
%{__install} -m 644 distribution/rpm/build/packaging/etc/elasticsearch/jvm.options %{buildroot}%{_sysconfdir}/%{name}
%{__install} -m 644 distribution/rpm/build/packaging/etc/elasticsearch/log4j2.properties %{buildroot}%{_sysconfdir}/%{name}
%{__install} -d -m 755 %{buildroot}%{_sysconfdir}/%{name}/scripts

#
# sysconfig template
%{__install} -d -m 755 %{buildroot}%{_fillupdir}
%{__install} -m 644 distribution/rpm/build/packaging/env/%{name} %{buildroot}%{_fillupdir}/sysconfig.%{name}

%if 0%{?suse_version} > 1010
%fdupes %{buildroot}%{_datadir}/%{name}
%endif

%pre
%if 0%{?has_systemd}
%service_add_pre %{name}.service
%endif

## create %%{name} group and user
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || useradd -r -g %{name} -d %{_localstatedir}/lib/%{name} -s /sbin/nologin -c "service user for elasticsearch" %{name}
exit 0

%post
%{fillup_and_insserv -n -y %{name}}
%service_add_post %{name}.service

# rpm is kinda stupid ...
# Create our dirs immediatly, after a manual package install.
# After a reboot systemd/aaa_base will take care.
%if 0%{?has_systemd}
systemd-tmpfiles --create %{_tmpfilesdir}/%{name}.conf
%else
test -d %{_rundir}/%{name} || mkdir -m 755 %{_rundir}/%{name} && chown %{name}.%{name} %{_rundir}/%{name}
%endif

%preun
%if 0%{?has_systemd}
%service_del_preun %{name}.service
%else
%stop_on_removal
%endif

%postun
## no auto restart on update
export DISABLE_RESTART_ON_UPDATE=1

%if 0%{?has_systemd}
%service_del_postun %{name}.service
%else
%insserv_cleanup
%endif

# only execute in case of package removal, not on upgrade
if [ $1 -eq 0 ] ; then
  getent passwd %{name} > /dev/null
  if [ "$?" == "0" ] ; then
    userdel %{name}
  fi

  getent group %{name} >/dev/null
  if [ "$?" == "0" ] ; then
    groupdel %{name}
  fi
fi

%files
%defattr(-,root,root)

%doc %{name}-%{version}/README.textile
%doc %{name}-%{version}/LICENSE.txt
%doc %{name}-%{version}/NOTICE.txt

%dir %{_datadir}/%{name}

%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/scripts
%config(noreplace) %attr(644,root,%{name}) %{_sysconfdir}/%{name}/*

%dir %{_fillupdir}
%{_fillupdir}/sysconfig.%{name}

%config %{_sysconfdir}/sysctl.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config %{_sysconfdir}/sysconfig/SuSEfirewall2.d/services/%{name}

%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*

%if 0%{?has_systemd}
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf
%else
%attr(755,root,root) %{_initddir}/%{name}
%exclude %{_tmpfilesdir}/%{name}.conf
%dir %{_sysctldir}
%{_sysctldir}/%{name}.conf
%endif

%{_sbindir}/rc%{name}

%dir %attr(755,%{name},%{name}) %{_localstatedir}/lib/%{name}
%dir %attr(755,%{name},%{name}) %{_localstatedir}/log/%{name}
%dir %attr(755,%{name},%{name}) %{_datadir}/%{name}/plugins
%dir %ghost %attr(755,%{name},%{name}) %{_rundir}/%{name}

%changelog
* Wed May 30 2018 kkaempf@suse.com
- Update to 6.2.4
  see https://www.elastic.co/guide/en/elasticsearch/reference/6.2/es-release-notes.html
- Build with Java 10
* Mon Apr 16 2018 samu.voutilainen@gmail.com
- Ensured Java version to be smaller than 10
  Elasticsearch is recommended to use with Java 8, but Java still works,
  but Java 10’s modularization updates breaks current Elasticsearch version
- Modified fillup entries to properly clean up itself
* Wed Nov 15 2017 kkaempf@suse.com
- Update to 6.0.0
  Major upgrade, many breaking changes
  see https://www.elastic.co/guide/en/elasticsearch/reference/6.0/release-notes-6.0.0.html
* Fri Sep  1 2017 kkaempf@suse.com
- Update to 5.5.2
  Breaking changes
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.5/breaking-changes-5.5.html
  and https://www.elastic.co/guide/en/elasticsearch/reference/5.5/release-notes-5.5.2.html
- add init.gradle to set local maven repo
* Tue Jun 13 2017 kkaempf@suse.com
- Update to 5.4.1
  Breaking changes
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.4/breaking-changes-5.4.html
  Bugfix release
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.4/release-notes-5.4.1.html
* Tue May  9 2017 kkaempf@suse.com
- add Requires(post) for %%fillup_and_insserve
* Wed Mar 22 2017 kkaempf@suse.com
- elasticsearch-plugin needs 'which' and 'hostname'
* Fri Mar  3 2017 kkaempf@suse.com
- Update to 5.2.2
  Breaking changes
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.2/breaking-changes-5.2.html
  Bugfix release
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.2/release-notes-5.2.2.html
* Thu Feb 23 2017 kkaempf@suse.com
- install /etc/sysctl.d/elasticsearch.conf
* Tue Jan 17 2017 kkaempf@suse.com
- update to 5.1.2
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.1/release-notes-5.1.2.html
- use upstream versions of
  * elasticsearch.conf
  * elasticsearch.in.sh
  * elasticsearch.service
  * elasticsearch.sysconfig
* Sun Jan 15 2017 kkaempf@suse.com
- update to 5.1.1
  see https://www.elastic.co/guide/en/elasticsearch/reference/5.1/release-notes-5.1.1.html
- build with gradle
- add 0001-Local-maven-repo.patch to enforce offline build
* Mon Oct 24 2016 boris@steki.net
- updated package to 2.4.1
  See https://www.elastic.co/guide/en/elasticsearch/reference/current/release-notes-2.4.1.html
* Wed Aug  3 2016 boris@steki.net
- fixed wrapper script for correct version of package
* Fri Jul 29 2016 kkaempf@suse.com
- Update to 2.3.4
  See https://www.elastic.co/guide/en/elasticsearch/reference/current/release-notes-2.3.4.html
* Fri Jul 29 2016 kkaempf@suse.com
- add SuSEfirewall2 configuration
* Tue Jun  7 2016 kkaempf@suse.com
- update to 2.3.3
  See https://www.elastic.co/guide/en/elasticsearch/reference/current/release-notes-2.3.3.html
* Tue Jan 12 2016 t.neuburger@telekom.de
- fixes for SysV and systemd
  * own sysVinit init script
  * update systemd unit file
  * new pre exec environment script for both SysV and systemd
* Wed Dec  9 2015 t.neuburger@telekom.de
- initial elasticsearch build
  * based on elasticsearch-2.1.0.tar.gz
  * sysVinit script from centos rpm
  * own created systemd unit file
