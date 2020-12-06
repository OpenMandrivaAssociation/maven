# Bootstrap mode "cheats" by using the prebuilt jar files from upstream.
# There's not much of a way around it, given Maven requires Maven to
# build these days.
%bcond_with bootstrap
# Bootstrap2 builds maven from source, but uses binary downloads of
# various libraries used by maven that often need to be built with
# maven. Refer to the maven-package-dependencies script to see where
# the binaries come from.
%bcond_without bootstrap2

Name:           maven
Version:        3.6.3
Release:        1
Summary:        Java project management and project comprehension tool
Group:		Development/Java

License:        ASL 2.0
URL:            http://maven.apache.org/
%if %{with bootstrap}
Source0:	https://www-us.apache.org/dist/maven/maven-3/%{version}/binaries/apache-maven-%{version}-bin.tar.gz
%else
Source0:        http://archive.apache.org/dist/%{name}/%{name}-3/%{version}/source/apache-%{name}-%{version}-src.tar.gz
%endif
Source1:        maven-bash-completion
Source2:        mvn.1
%if %{with bootstrap2}
# Generated from Source1000
Source3:	maven-dependencies-%{version}.tar.zst
Source1000:	maven-package-dependencies
%endif
%if ! %{with bootstrap}
BuildRequires:	maven
BuildRequires:	jdk-current
%endif
Patch1:		0005-Use-generics-in-modello-generated-code.patch

BuildArch:      noarch

%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

%package        javadoc
Summary:        API documentation for %{name}

%description    javadoc
%{summary}.

%prep
%if %{with bootstrap}
%setup -n apache-maven-%{version}
%else
%autosetup -p1 -n apache-%{name}-%{version}%{?ver_add}
. %{_sysconfdir}/profile.d/90java.sh
%if %{with bootstrap2}
cd ..
tar xf %{S:3}
cd -
%endif

# Use Eclipse Sisu plugin
sed -i s/org.sonatype.plugins/org.eclipse.sisu/ maven-core/pom.xml

# fix for animal-sniffer (we don't generate 1.5 signatures)
sed -i 's:check-java-1.5-compat:check-java-1.6-compat:' pom.xml

rm -f apache-maven/src/bin/*.bat
sed -i 's:\r::' apache-maven/src/conf/settings.xml

# Update shell scripts to use unversioned classworlds
sed -i -e s:'-classpath "${M2_HOME}"/boot/plexus-classworlds-\*.jar':'-classpath "${M2_HOME}"/boot/plexus-classworlds.jar':g \
        apache-maven/src/bin/mvn*
%endif

%build
%if ! %{with bootstrap}
. %{_sysconfdir}/profile.d/90java.sh
%if %{with bootstrap2}
mvn -Dmaven.repo.local=$(pwd)/../repository -Dproject.build.sourceEncoding=UTF-8 compile
mvn -Dmaven.repo.local=$(pwd)/../repository -Dproject.build.sourceEncoding=UTF-8 verify
mvn -Dmaven.repo.local=$(pwd)/../repository -Dproject.build.sourceEncoding=UTF-8 validate
%else
mvn -Dproject.build.sourceEncoding=UTF-8 compile
mvn -Dproject.build.sourceEncoding=UTF-8 verify
mvn -Dproject.build.sourceEncoding=UTF-8 validate
%endif
%endif

%install
%if ! %{with bootstrap}
. %{_sysconfdir}/profile.d/90java.sh
%if %{without bootstrap2}
mvn -Dmaven.repo.local=$(pwd)/../repository -Dproject.build.sourceEncoding=UTF-8 install
%else
mvn -Dproject.build.sourceEncoding=UTF-8 install
%endif

tar xf apache-maven/target/*.tar.gz
cd apache-maven-%{version}
%endif

install -d -m 755 %{buildroot}%{_datadir}/%{name}/bin
install -d -m 755 %{buildroot}%{_datadir}/%{name}/conf
install -d -m 755 %{buildroot}%{_datadir}/%{name}/boot
install -d -m 755 %{buildroot}%{_datadir}/%{name}/lib/ext
install -d -m 755 %{buildroot}%{_bindir}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m 755 %{buildroot}%{_datadir}/bash-completion/completions
install -d -m 755 %{buildroot}%{_mandir}/man1

cat >%{buildroot}%{_bindir}/mvn <<'EOF'
#!/bin/sh
export M2_HOME="${M2_HOME:-/usr/share/maven}"
exec $M2_HOME/bin/mvn "$@"
EOF
chmod +x %{buildroot}%{_bindir}/mvn

install -p -m 644 %{SOURCE2} %{buildroot}%{_mandir}/man1
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/%{name}
mv bin/m2.conf %{buildroot}%{_sysconfdir}
ln -sf %{_sysconfdir}/m2.conf %{buildroot}%{_datadir}/%{name}/bin/m2.conf
mv conf/settings.xml %{buildroot}%{_sysconfdir}/%{name}
ln -sf %{_sysconfdir}/%{name}/settings.xml %{buildroot}%{_datadir}/%{name}/conf/settings.xml
mv conf/logging %{buildroot}%{_sysconfdir}/%{name}
ln -sf %{_sysconfdir}/%{name}/logging %{buildroot}%{_datadir}/%{name}/conf

cp -a bin/* %{buildroot}%{_datadir}/%{name}/bin
cp -a boot %{buildroot}%{_datadir}/%{name}

cp -a lib/*.jar %{buildroot}%{_datadir}/%{name}/lib/

mkdir -p %{buildroot}%{_javadir}/%{name}
for i in %{buildroot}%{_datadir}/%{name}/lib/maven*.jar; do
	FN="$(basename $i .jar |rev |cut -d- -f2- |rev)"
	ln -s `echo $i |sed -e 's,^%{buildroot},,'` %{buildroot}%{_javadir}/%{name}/$FN.jar
done


%files
%doc LICENSE NOTICE
%{_datadir}/%{name}
%{_bindir}/mvn
%dir %{_javadir}/%{name}
%{_javadir}/%{name}/*.jar
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/logging
%config(noreplace) %{_sysconfdir}/m2.conf
%config(noreplace) %{_sysconfdir}/%{name}/settings.xml
%config(noreplace) %{_sysconfdir}/%{name}/logging/simplelogger.properties
%{_datadir}/bash-completion/completions/%{name}
%{_mandir}/man1/mvn.1*
