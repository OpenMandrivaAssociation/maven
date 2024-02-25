%bcond_without bootstrap

%global bundled_slf4j_version 1.7.36
%global homedir %{_datadir}/maven%{?maven_version_suffix}
%global confdir %{_sysconfdir}/maven%{?maven_version_suffix}

Name:           maven
Epoch:          1
Version:        3.9.6
Release:        1
Summary:        Java project management and project comprehension tool
# maven itself is Apache-2.0
# bundled slf4j is MIT
License:        Apache-2.0 AND MIT
URL:            https://maven.apache.org/
BuildArch:      noarch
ExclusiveArch:  %{java_arches} noarch

Source0:        https://archive.apache.org/dist/maven/maven-3/%{version}/source/apache-maven-%{version}-src.tar.gz
Source1:        maven-bash-completion
Source2:        mvn.1

Patch1:         0001-Adapt-mvn-script.patch
# Downstream-specific, avoids build-dependency on logback
Patch2:         0002-Invoke-logback-via-reflection.patch
Patch3:         0003-Remove-dependency-on-powermock.patch

%if %{with bootstrap}
BuildRequires:  javapackages-bootstrap
%else
BuildRequires:  maven-local
BuildRequires:  mvn(com.google.guava:failureaccess)
BuildRequires:  mvn(com.google.guava:guava)
BuildRequires:  mvn(com.google.inject:guice)
BuildRequires:  mvn(commons-cli:commons-cli)
BuildRequires:  mvn(commons-io:commons-io)
BuildRequires:  mvn(commons-jxpath:commons-jxpath)
BuildRequires:  mvn(javax.annotation:javax.annotation-api)
BuildRequires:  mvn(javax.inject:javax.inject)
BuildRequires:  mvn(junit:junit)
BuildRequires:  mvn(org.apache.commons:commons-lang3)
BuildRequires:  mvn(org.apache.maven.plugins:maven-assembly-plugin)
BuildRequires:  mvn(org.apache.maven.plugins:maven-dependency-plugin)
BuildRequires:  mvn(org.apache.maven.plugins:maven-enforcer-plugin)
BuildRequires:  mvn(org.apache.maven.plugins:maven-failsafe-plugin)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-api)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-connector-basic)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-impl)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-spi)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-transport-file)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-transport-http)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-transport-wagon)
BuildRequires:  mvn(org.apache.maven.resolver:maven-resolver-util)
BuildRequires:  mvn(org.apache.maven.shared:maven-shared-utils)
BuildRequires:  mvn(org.apache.maven.wagon:wagon-file)
BuildRequires:  mvn(org.apache.maven.wagon:wagon-http)
BuildRequires:  mvn(org.apache.maven.wagon:wagon-provider-api)
BuildRequires:  mvn(org.apache.maven:maven-parent:pom:)
BuildRequires:  mvn(org.codehaus.modello:modello-maven-plugin)
BuildRequires:  mvn(org.codehaus.mojo:build-helper-maven-plugin)
BuildRequires:  mvn(org.codehaus.plexus:plexus-cipher)
BuildRequires:  mvn(org.codehaus.plexus:plexus-classworlds)
BuildRequires:  mvn(org.codehaus.plexus:plexus-component-annotations)
BuildRequires:  mvn(org.codehaus.plexus:plexus-component-metadata)
BuildRequires:  mvn(org.codehaus.plexus:plexus-interpolation)
BuildRequires:  mvn(org.codehaus.plexus:plexus-sec-dispatcher)
BuildRequires:  mvn(org.codehaus.plexus:plexus-utils)
BuildRequires:  mvn(org.eclipse.sisu:org.eclipse.sisu.inject)
BuildRequires:  mvn(org.eclipse.sisu:org.eclipse.sisu.plexus)
BuildRequires:  mvn(org.eclipse.sisu:sisu-maven-plugin)
BuildRequires:  mvn(org.fusesource.jansi:jansi)
BuildRequires:  mvn(org.hamcrest:hamcrest)
BuildRequires:  mvn(org.mockito:mockito-core)
BuildRequires:  mvn(org.slf4j:jcl-over-slf4j)
BuildRequires:  mvn(org.slf4j:slf4j-api)
BuildRequires:  mvn(org.slf4j:slf4j-simple)
BuildRequires:  mvn(org.xmlunit:xmlunit-core)
BuildRequires:  mvn(org.xmlunit:xmlunit-matchers)
%endif

# XXX
#BuildRequires:  mvn(org.slf4j:slf4j-simple::sources:) = %{bundled_slf4j_version}
%if %{without bootstrap}
BuildRequires:  mvn(org.slf4j:slf4j-simple::sources:)
%endif

Requires: %{name}-lib = %{epoch}:%{version}-%{release}
Requires: %{name}-jdk-binding = %{epoch}:%{version}-%{release}
Suggests: %{name}-openjdk21 = %{epoch}:%{version}-%{release}

Requires(post): alternatives
Requires(postun): alternatives

%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

%package lib
Summary:        Core part of Maven
# If XMvn is part of the same RPM transaction then it should be
# installed first to avoid triggering rhbz#1014355.
OrderWithRequires: xmvn-minimal

# Maven upstream uses patched version of SLF4J.  They unpack
# slf4j-simple-sources.jar, apply non-upstreamable, Maven-specific
# patch (using a script written in Groovy), compile and package as
# maven-slf4j-provider.jar, together with Maven-specific additions.
Provides:       bundled(slf4j) = %{bundled_slf4j_version}

%description lib
Core part of Apache Maven that can be used as a library.

%package openjdk8
Summary:        OpenJDK 8 binding for Maven
RemovePathPostfixes: -openjdk8
Provides: %{name}-jdk-binding = %{epoch}:%{version}-%{release}
Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: java-1.8.0-openjdk-headless
Recommends: java-1.8.0-openjdk-devel
Conflicts: %{name}-jdk-binding

%description openjdk8
Configures Maven to run with OpenJDK 8.

%package openjdk11
Summary:        OpenJDK 11 binding for Maven
RemovePathPostfixes: -openjdk11
Provides: %{name}-jdk-binding = %{epoch}:%{version}-%{release}
Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: java-11-openjdk-headless
Recommends: java-11-openjdk-devel
Conflicts: %{name}-jdk-binding

%description openjdk11
Configures Maven to run with OpenJDK 11.

%package openjdk17
Summary:        OpenJDK 17 binding for Maven
RemovePathPostfixes: -openjdk17
Provides: %{name}-jdk-binding = %{epoch}:%{version}-%{release}
Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: java-17-openjdk-headless
Recommends: java-17-openjdk-devel
Conflicts: %{name}-jdk-binding

%description openjdk17
Configures Maven to run with OpenJDK 17.

%package openjdk21
Summary:        OpenJDK 21 binding for Maven
RemovePathPostfixes: -openjdk21
Provides: %{name}-jdk-binding = %{epoch}:%{version}-%{release}
Requires: %{name} = %{epoch}:%{version}-%{release}
Requires: java-21-openjdk-headless
Recommends: java-21-openjdk-devel
Conflicts: %{name}-jdk-binding

%description openjdk21
Configures Maven to run with OpenJDK 21.

%{?javadoc_package}

%prep
%setup -q -n apache-maven-%{version}

find -name '*.java' -exec sed -i 's/\r//' {} +
find -name 'pom.xml' -exec sed -i 's/\r//' {} +

%patch -P 1 -p1
%patch -P 2 -p1
%patch -P 3 -p1
sed -i "s/@{maven_version_suffix}/%{?maven_version_suffix}/" apache-maven/src/bin/mvn

# not really used during build, but a precaution
find -name '*.jar' -not -path '*/test/*' -delete
find -name '*.class' -delete
find -name '*.bat' -delete

%pom_remove_dep -r :powermock-reflect

sed -i 's:\r::' apache-maven/src/conf/settings.xml

# Downloads dependency licenses from the Internet and aggregates them.
# We already ship the licenses in their respective packages.
rm apache-maven/src/main/appended-resources/META-INF/LICENSE.vm

# Disable plugins which are not useful for us
%pom_remove_plugin -r :animal-sniffer-maven-plugin
%pom_remove_plugin -r :apache-rat-plugin
%pom_remove_plugin -r :maven-site-plugin
%pom_remove_plugin -r :buildnumber-maven-plugin
sed -i "
/buildNumber=/ {
  s/=.*/=Red Hat %{version}-%{release}/
  s/%{dist}$//
}
/timestamp=/ d
" `find -name build.properties`

%mvn_package :apache-maven __noinstall

%pom_add_dep javax.annotation:javax.annotation-api::provided maven-core

%pom_change_dep :jansi :::runtime maven-embedder
%pom_remove_dep -r :logback-classic

%mvn_alias :maven-resolver-provider :maven-aether-provider

%pom_remove_plugin :plexus-component-metadata maven-model-builder
%pom_add_plugin org.eclipse.sisu:sisu-maven-plugin maven-model-builder

%build
%mvn_build -- -Dproject.build.sourceEncoding=UTF-8

mkdir m2home
(cd m2home
    tar --delay-directory-restore -xvf ../apache-maven/target/*tar.gz
)


%install
%mvn_install

export M2_HOME=$(pwd)/m2home/apache-maven-%{version}%{?ver_add}

install -d -m 755 %{buildroot}%{homedir}/conf
install -d -m 755 %{buildroot}%{confdir}
install -d -m 755 %{buildroot}%{_datadir}/bash-completion/completions/

cp -a $M2_HOME/{bin,lib,boot} %{buildroot}%{homedir}/
%if %{without bootstrap}
xmvn-subst -s -R %{buildroot} -s %{buildroot}%{homedir}
%endif

# maven uses this hardcoded path in its launcher to locate jansi so we symlink it
ln -s %{_prefix}/lib/jansi/libjansi.so %{buildroot}%{homedir}/lib/jansi-native/

install -p -m 644 %{SOURCE2} %{buildroot}%{homedir}/bin/
gzip -9 %{buildroot}%{homedir}/bin/mvn.1
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/mvn%{?maven_version_suffix}
mv $M2_HOME/bin/m2.conf %{buildroot}%{_sysconfdir}/m2%{?maven_version_suffix}.conf
ln -sf %{_sysconfdir}/m2%{?maven_version_suffix}.conf %{buildroot}%{homedir}/bin/m2.conf
mv $M2_HOME/conf/settings.xml %{buildroot}%{confdir}/
ln -sf %{confdir}/settings.xml %{buildroot}%{homedir}/conf/settings.xml
mv $M2_HOME/conf/logging %{buildroot}%{confdir}/
ln -sf %{confdir}/logging %{buildroot}%{homedir}/conf

# Ghosts for alternatives
install -d -m 755 %{buildroot}%{_bindir}/
install -d -m 755 %{buildroot}%{_mandir}/man1/
touch %{buildroot}%{_bindir}/{mvn,mvnDebug}
touch %{buildroot}%{_mandir}/man1/{mvn,mvnDebug}.1

# Versioned commands and manpages
%if 0%{?maven_version_suffix:1}
ln -s %{homedir}/bin/mvn %{buildroot}%{_bindir}/mvn%{maven_version_suffix}
ln -s %{homedir}/bin/mvnDebug %{buildroot}%{_bindir}/mvnDebug%{maven_version_suffix}
ln -s %{homedir}/bin/mvn.1.gz %{buildroot}%{_mandir}/man1/mvn%{maven_version_suffix}.1.gz
ln -s %{homedir}/bin/mvnDebug.1.gz %{buildroot}%{_mandir}/man1/mvnDebug%{maven_version_suffix}.1.gz
%endif

# JDK bindings
install -d -m 755 %{buildroot}%{_javaconfdir}/
echo JAVA_HOME=%{_jvmlibdir}/jre-1.8.0-openjdk >%{buildroot}%{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk8
echo JAVA_HOME=%{_jvmlibdir}/jre-11-openjdk >%{buildroot}%{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk11
echo JAVA_HOME=%{_jvmlibdir}/jre-17-openjdk >%{buildroot}%{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk17
echo JAVA_HOME=%{_jvmlibdir}/jre-21-openjdk >%{buildroot}%{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk21


%post
update-alternatives --install %{_bindir}/mvn mvn %{homedir}/bin/mvn %{?maven_alternatives_priority}0 \
--slave %{_bindir}/mvnDebug mvnDebug %{homedir}/bin/mvnDebug \
--slave %{_mandir}/man1/mvn.1.gz mvn1 %{homedir}/bin/mvn.1.gz \
--slave %{_mandir}/man1/mvnDebug.1.gz mvnDebug1 %{homedir}/bin/mvn.1.gz \

%postun
if [[ $1 -eq 0 ]]; then update-alternatives --remove mvn %{homedir}/bin/mvn; fi

%files lib -f .mfiles
%doc README.md
%license LICENSE NOTICE
%{homedir}
%exclude %{homedir}/bin/mvn*
%dir %{confdir}
%dir %{confdir}/logging
%config(noreplace) %{_sysconfdir}/m2%{?maven_version_suffix}.conf
%config(noreplace) %{confdir}/settings.xml
%config(noreplace) %{confdir}/logging/simplelogger.properties

%files
%{homedir}/bin/mvn*
%ghost %{_bindir}/mvn
%ghost %{_bindir}/mvnDebug
%{_datadir}/bash-completion
%ghost %{_mandir}/man1/mvn.1.gz
%ghost %{_mandir}/man1/mvnDebug.1.gz
%if 0%{?maven_version_suffix:1}
%{_bindir}/mvn%{maven_version_suffix}
%{_bindir}/mvnDebug%{maven_version_suffix}
%{_mandir}/man1/mvn%{maven_version_suffix}.1.gz
%{_mandir}/man1/mvnDebug%{maven_version_suffix}.1.gz
%endif

%files openjdk8
%config %{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk8

%files openjdk11
%config %{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk11

%files openjdk17
%config %{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk17

%files openjdk21
%config %{_javaconfdir}/maven%{?maven_version_suffix}.conf-openjdk21

