%bcond_without bootstrap

%global resolver_version 2.0.24
%global bundled_slf4j_version 2.0.17
%global sysjar_drops --drop org.codehaus.mojo:animal-sniffer-maven-plugin --drop org.apache.rat:apache-rat-plugin --drop org.apache.maven.plugins:maven-enforcer-plugin --drop org.codehaus.mojo:buildnumber-maven-plugin --drop ch.qos.logback:logback-classic --drop org.powermock:powermock-reflect --drop biz.aQute.bnd:bnd-maven-plugin --drop org.eclipse.jetty:jetty-bom
%if %{with bootstrap}
%global sysjar_bootstrap 1
%{!?_sysjar_mvn:%global _sysjar_mvn %{_datadir}/javapackages-bootstrap/bin/mvn}
%{!?sysjar_bootstrap_root:%global sysjar_bootstrap_root /}
# Resolver 2.0.24 is not in the bootstrap set (that set has 2.0.9). The
# stage-0 sisu indexer is taught the running JDK and installed into jdk27-root
# first. A command-line definition wins.
%{!?sysjar_extra:%global sysjar_extra --root / --root %{_builddir}/jdk27-root --root %{_builddir}/resolver-root}
%endif

Name:		maven
Epoch:		1
Version:	3.10.0
Release:	1
Summary:	Java project management and project comprehension tool
# maven itself is Apache-2.0
# maven-slf4j-provider vendors SLF4J simple sources, which are MIT
License:	Apache-2.0 AND MIT
Group:		Development/Java
URL:		https://maven.apache.org/
BuildArch:	noarch

Source0:	https://archive.apache.org/dist/maven/maven-3/%{version}/source/apache-maven-%{version}-src.tar.gz
Source1:	maven-bash-completion
Source2:	mvn.1
Source3:	https://repo1.maven.org/maven2/org/slf4j/slf4j-simple/%{bundled_slf4j_version}/slf4j-simple-%{bundled_slf4j_version}-sources.jar
Source4:	https://archive.apache.org/dist/maven/resolver/maven-resolver-%{resolver_version}-source-release.zip
Source5:	maven-resolver-%{resolver_version}-subset.patch
Source6:	sisu-jdk27.py

# logback is not installed; call it by reflection so the class is optional
Patch0:		0002-Invoke-logback-via-reflection.patch
# Offline build: no staging repos, no FFM terminal, no sources-classifier unpack
Patch1:		maven-3.10.0-offline-build.patch

BuildRequires:	python
BuildRequires:	unzip
BuildRequires:	sysjar
BuildSystem:	maven
BuildOption:	-Dproject.build.sourceEncoding=UTF-8

Provides:	bundled(slf4j) = %{bundled_slf4j_version}
Provides:	maven-lib = %{EVRD}
Provides:	maven-jdk-binding = %{EVRD}
Obsoletes:	maven-lib < 1:%{version}-%{release}
Obsoletes:	maven-openjdk21 < 1:%{version}-%{release}
Obsoletes:	maven-openjdk25 < 1:%{version}-%{release}
Obsoletes:	maven-unbound < 1:%{version}-%{release}
Requires:	%{_sysjar_java_requires}

%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

This package is the upstream distribution, installed under /usr/share/maven
and built against system jars. It replaces the split maven-lib package and
the JDK binding subpackages.

%prep -a
find . -name '*.java' -exec sed -i 's/\r//' {} +
find . -name 'pom.xml' -exec sed -i 's/\r//' {} +
sed -i 's/\r//' apache-maven/src/conf/settings.xml apache-maven/src/conf/toolchains.xml

find . -name '*.jar' -not -path '*/test/*' -delete
find . -name '*.class' -delete
find . -name '*.bat' -delete
rm -f apache-maven/src/main/appended-resources/META-INF/LICENSE.vm

install -d maven-slf4j-provider/src/main/java/org/slf4j/simple
slf4j_src=$(mktemp -d)
unzip -q -d "$slf4j_src" %{SOURCE3} 'org/slf4j/simple/*.java'
rm -f "$slf4j_src/org/slf4j/simple/SimpleServiceProvider.java"
cp -a "$slf4j_src"/org/slf4j/simple/*.java maven-slf4j-provider/src/main/java/org/slf4j/simple/
rm -rf "$slf4j_src"

%if %{with bootstrap}
unzip -q -d %{_builddir} %{SOURCE4}
rm -rf \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-demos \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-generator-gnupg \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-generator-sigstore \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-named-locks-hazelcast \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-named-locks-ipc \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-named-locks-redisson \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-supplier-mvn3 \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-supplier-mvn4 \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-test-http \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-test-util \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-tools \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-transport-classpath \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-transport-jdk-parent \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-transport-jetty \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-transport-minio \
	%{_builddir}/maven-resolver-%{resolver_version}/maven-resolver-transport-url
patch -d %{_builddir}/maven-resolver-%{resolver_version} -p1 < %{SOURCE5}
%endif

# Bootstrap jars are not separate packages. Do not emit them as BuildRequires.
%generate_buildrequires
%if %{without bootstrap}
%buildsystem_maven_generate_buildrequires
%else
:
%endif

%build -p
%if %{with bootstrap}
# Shaded ASM in the stage-0 indexer stops at Java 25. Keep the rest of that
# jar and raise the class-file ceiling to the running JDK.
python %{SOURCE6} \
	%{sysjar_bootstrap_root}/usr/share/javapackages-bootstrap/org.eclipse.sisu.inject.jar \
	%{_builddir}/org.eclipse.sisu.inject.jar
install -d %{_builddir}/sisu-pom
cat > %{_builddir}/sisu-pom/org.eclipse.sisu.inject.pom <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.eclipse.sisu</groupId>
  <artifactId>org.eclipse.sisu.inject</artifactId>
  <version>0.9.0.M3</version>
</project>
EOF
sysjar install --buildroot %{_builddir}/jdk27-root \
	--artifact %{_builddir}/sisu-pom/org.eclipse.sisu.inject.pom:%{_builddir}/org.eclipse.sisu.inject.jar
(
	cd %{_builddir}/maven-resolver-%{resolver_version}
	%__sysjar_use_java_home
	export MAVEN_SKIP_RC=1
	%sysjar_mvn -Dmaven.test.skip=true -Dproject.build.sourceEncoding=UTF-8 package
	sysjar install --buildroot %{_builddir}/resolver-root --auto .
)
%endif

%install
install -d %{buildroot}%{_datadir}
tar -C %{buildroot}%{_datadir} -xzf apache-maven/target/apache-maven-%{version}-bin.tar.gz
mv %{buildroot}%{_datadir}/apache-maven-%{version} %{buildroot}%{_datadir}/maven
rm -f %{buildroot}%{_datadir}/maven/bin/*.cmd

install -d %{buildroot}%{_sysconfdir}/maven/logging
mv %{buildroot}%{_datadir}/maven/conf/settings.xml %{buildroot}%{_sysconfdir}/maven/settings.xml
mv %{buildroot}%{_datadir}/maven/conf/toolchains.xml %{buildroot}%{_sysconfdir}/maven/toolchains.xml
mv %{buildroot}%{_datadir}/maven/conf/logging/simplelogger.properties %{buildroot}%{_sysconfdir}/maven/logging/simplelogger.properties
rmdir %{buildroot}%{_datadir}/maven/conf/logging
mv %{buildroot}%{_datadir}/maven/bin/m2.conf %{buildroot}%{_sysconfdir}/m2.conf
ln -s %{_sysconfdir}/maven/settings.xml %{buildroot}%{_datadir}/maven/conf/settings.xml
ln -s %{_sysconfdir}/maven/toolchains.xml %{buildroot}%{_datadir}/maven/conf/toolchains.xml
ln -s %{_sysconfdir}/maven/logging %{buildroot}%{_datadir}/maven/conf/logging
ln -s %{_sysconfdir}/m2.conf %{buildroot}%{_datadir}/maven/bin/m2.conf

install -d %{buildroot}%{_bindir}
ln -s ../share/maven/bin/mvn %{buildroot}%{_bindir}/mvn
ln -s ../share/maven/bin/mvnDebug %{buildroot}%{_bindir}/mvnDebug
ln -s ../share/maven/bin/mvnyjp %{buildroot}%{_bindir}/mvnyjp
install -d %{buildroot}%{_datadir}/bash-completion/completions
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/mvn
install -d %{buildroot}%{_mandir}/man1
install -p -m 644 %{SOURCE2} %{buildroot}%{_mandir}/man1/mvn.1
ln -s mvn.1 %{buildroot}%{_mandir}/man1/mvnDebug.1

%files
%license LICENSE NOTICE
%doc README.md
%{_datadir}/maven
%dir %{_sysconfdir}/maven
%dir %{_sysconfdir}/maven/logging
%config(noreplace) %{_sysconfdir}/m2.conf
%config(noreplace) %{_sysconfdir}/maven/settings.xml
%config(noreplace) %{_sysconfdir}/maven/toolchains.xml
%config(noreplace) %{_sysconfdir}/maven/logging/simplelogger.properties
%{_bindir}/mvn
%{_bindir}/mvnDebug
%{_bindir}/mvnyjp
%{_datadir}/bash-completion/completions/mvn
%{_mandir}/man1/mvn.1*
%{_mandir}/man1/mvnDebug.1*
