%global xversion 4.0.0-rc-4
%global bundled_slf4j_version 1.7.36
%global homedir %{_datadir}/maven
%global confdir %{_sysconfdir}/maven

Name:		maven
Epoch:		1
Version:	4.0.0.rc4
Release:	1
Summary:	Java project management and project comprehension tool
# maven itself is Apache-2.0
# bundled slf4j is MIT
License:	Apache-2.0 AND MIT
Group:		Development/Java
URL:		https://maven.apache.org/
BuildArch:	noarch

Source0:	https://archive.apache.org/dist/maven/maven-4/%{xversion}/source/apache-maven-%{xversion}-src.tar.gz
Source1:	maven-bash-completion
Source2:	mvn.1

Patch1:	 0001-Adapt-mvn-script.patch
# Downstream-specific, avoids build-dependency on logback
Patch2:	 0002-Invoke-logback-via-reflection.patch
Patch3:	 0003-Port-tests-to-work-with-Mockito-3.patch

BuildRequires:	gnutar
BuildRequires:	javapackages-bootstrap

Requires: %{name}-lib = %{epoch}:%{version}-%{release}
Requires: %{name}-jdk-binding
Suggests: %{name}-openjdk25 = %{epoch}:%{version}-%{release}

%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

%package lib
Summary:	Core part of Maven
# If XMvn is part of the same RPM transaction then it should be
# installed first to avoid triggering rhbz#1014355.
OrderWithRequires: xmvn-minimal

# Maven upstream uses patched version of SLF4J.  They unpack
# slf4j-simple-sources.jar, apply non-upstreamable, Maven-specific
# patch (using a script written in Groovy), compile and package as
# maven-slf4j-provider.jar, together with Maven-specific additions.
Provides:	bundled(slf4j) = %{bundled_slf4j_version}

# JAR symlinks in lib directory
Requires:	aopalliance
Requires:	apache-commons-cli
Requires:	apache-commons-codec
Requires:	google-gson
Requires:	google-guice
Requires:	guava
Requires:	httpcomponents-client
Requires:	httpcomponents-core
Requires:	jakarta-annotations
Requires:	jakarta-inject
Requires:	jcl-over-slf4j2
Requires:	jline
Requires:	maven-resolver2
Requires:	maven-wagon
Requires:	objectweb-asm
Requires:	plexus-containers-component-annotations
Requires:	plexus-interactivity
Requires:	plexus-interpolation
Requires:	plexus-sec-dispatcher4
Requires:	plexus-utils4
Requires:	plexus-xml
Requires:	sisu
Requires:	slf4j2
Requires:	stax2-api
Requires:	woodstox-core

%description lib
Core part of Apache Maven that can be used as a library.

%prep
%autosetup -p1 -C

%pom_remove_dep -r :junit-bom
%pom_remove_dep -r :mockito-bom
%pom_remove_plugin -r :maven-enforcer-plugin
%pom_remove_plugin :bom-builder3 apache-maven

%pom_remove_dep :jline-terminal-ffm impl/maven-jline
%pom_remove_dep :jline-terminal-ffm apache-maven
%pom_remove_dep -r :logback-classic

%pom_disable_module maven-executor impl

find -name '*.java' -exec sed -i 's/\r//' {} +
find -name 'pom.xml' -exec sed -i 's/\r//' {} +

# not really used during build, but a precaution
find -name '*.jar' -not -path '*/test/*' -delete
find -name '*.class' -delete
find -name '*.bat' -delete

#sed -i 's:\r::' apache-maven/src/conf/settings.xml

# Downloads dependency licenses from the Internet and aggregates them.
# We already ship the licenses in their respective packages.
rm apache-maven/src/main/appended-resources/META-INF/LICENSE.vm

# Disable plugins which are not useful for us
%pom_remove_plugin -r :apache-rat-plugin
%pom_remove_plugin -r :buildnumber-maven-plugin
sed -i "
/buildNumber=/ {
	s/=.*/=Red Hat %{version}-%{release}/
	s/%{dist}$//
}
/timestamp=/ d
" `find -name build.properties`

%mvn_package :apache-maven __noinstall
%mvn_package ::mdo: __noinstall

%mvn_compat_version : 4.0.0-rc-4

%build
%mvn_build -j -f -- -Dproject.build.sourceEncoding=UTF-8

mkdir m2home
(cd m2home
	gtar --delay-directory-restore -xvf ../apache-maven/target/*tar.gz
)


%install
%mvn_install

export M2_HOME=$(pwd)/m2home/apache-maven-%{xversion}%{?ver_add}

install -d -m 755 %{buildroot}%{homedir}/conf
install -d -m 755 %{buildroot}%{confdir}
install -d -m 755 %{buildroot}%{_datadir}/bash-completion/completions/

cp -a $M2_HOME/{bin,lib,boot} %{buildroot}%{homedir}/

find %{buildroot}%{homedir} -name \*.so -print -delete

install -p -m 644 %{SOURCE2} %{buildroot}%{homedir}/bin/
gzip -9 %{buildroot}%{homedir}/bin/mvn.1
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/mvn
mv $M2_HOME/bin/m2.conf %{buildroot}%{_sysconfdir}/m2.conf
ln -sf %{_sysconfdir}/m2.conf %{buildroot}%{homedir}/bin/m2.conf
mv $M2_HOME/conf/maven.properties %{buildroot}%{confdir}/
ln -sf %{confdir}/maven.properties %{buildroot}%{homedir}/conf/
mv $M2_HOME/conf/settings.xml %{buildroot}%{confdir}/
ln -sf %{confdir}/settings.xml %{buildroot}%{homedir}/conf/settings.xml
mv $M2_HOME/conf/logging %{buildroot}%{confdir}/
ln -sf %{confdir}/logging %{buildroot}%{homedir}/conf

# Ghosts for alternatives
install -d -m 755 %{buildroot}%{_bindir}/
install -d -m 755 %{buildroot}%{_mandir}/man1/
touch %{buildroot}%{_bindir}/{mvn,mvnenc,mvnDebug}
touch %{buildroot}%{_mandir}/man1/{mvn,mvnenc,mvnDebug}.1

# JDK bindings
install -d -m 755 %{buildroot}%{_javaconfdir}/
ln -sf %{_jpbindingdir}/maven.conf %{buildroot}%{_javaconfdir}/maven.conf
echo JAVA_HOME=%{_jvmdir}/jre-21-openjdk >%{buildroot}%{_javaconfdir}/maven-openjdk21.conf
echo JAVA_HOME=%{_jvmdir}/jre-25-openjdk >%{buildroot}%{_javaconfdir}/maven-openjdk25.conf
%jp_binding --verbose --variant openjdk21 --ghost maven.conf --target %{_javaconfdir}/maven-openjdk21.conf --provides %{name}-jdk-binding --requires java-21-openjdk-headless --recommends java-21-openjdk-devel
%jp_binding --verbose --variant openjdk25 --ghost maven.conf --target %{_javaconfdir}/maven-openjdk25.conf --provides %{name}-jdk-binding --requires java-25-openjdk-headless --recommends java-25-openjdk-devel
touch %{buildroot}%{_javaconfdir}/maven-unbound.conf
%jp_binding --verbose --variant unbound --ghost maven.conf --target %{_javaconfdir}/maven-unbound.conf --provides %{name}-jdk-binding

%files lib -f .mfiles
%doc README.md
%license LICENSE NOTICE
%{homedir}
%exclude %{homedir}/bin/mvn*
%dir %{confdir}
%dir %{confdir}/logging
%config %{_javaconfdir}/maven*.conf
%config(noreplace) %{_sysconfdir}/m2.conf
%config(noreplace) %{confdir}/maven.properties
%config(noreplace) %{confdir}/settings.xml
%config(noreplace) %{confdir}/logging/maven.logger.properties

%files
%{homedir}/bin/mvn*
%{_bindir}/mvn
%{_bindir}/mvnenc
%{_bindir}/mvnDebug
%{_datadir}/bash-completion
%{_mandir}/man1/mvn.1.zst
%{_mandir}/man1/mvnenc.1.zst
%{_mandir}/man1/mvnDebug.1.zst
