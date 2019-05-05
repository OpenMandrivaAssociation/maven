# Bootstrap mode "cheats" by using the prebuilt jar files from upstream.
# There's not much of a way around it, given Maven requires Maven to
# build these days.
%bcond_without bootstrap

%{?_javapackages_macros:%_javapackages_macros}
Name:           maven
Version:        3.6.1
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

# 2xx for created non-buildable sources
Source200:      %{name}-script

Patch0005:	0005-Use-generics-in-modello-generated-code.patch

BuildArch:      noarch

%if ! %{with bootstrap}
BuildRequires:  maven-local
BuildRequires:  aether-api >= 1:0
BuildRequires:  aether-connector-basic >= 1:0
BuildRequires:  aether-impl >= 1:0
BuildRequires:  aether-spi >= 1:0
BuildRequires:  aether-util >= 1:0
BuildRequires:  aether-transport-wagon >= 1:0
BuildRequires:  aopalliance
BuildRequires:  apache-commons-cli
BuildRequires:  apache-commons-codec
BuildRequires:  apache-commons-jxpath
BuildRequires:  apache-commons-logging
BuildRequires:  apache-resource-bundles
BuildRequires:  atinject
BuildRequires:  buildnumber-maven-plugin
BuildRequires:  cglib
BuildRequires:  google-guice >= 3.1.6
BuildRequires:  hamcrest
BuildRequires:  httpcomponents-core
BuildRequires:  httpcomponents-client
BuildRequires:  jsr-305
BuildRequires:  junit
BuildRequires:  maven-assembly-plugin
BuildRequires:  maven-compiler-plugin
BuildRequires:  maven-install-plugin
BuildRequires:  maven-jar-plugin
BuildRequires:  maven-javadoc-plugin
BuildRequires:  maven-parent
BuildRequires:  maven-remote-resources-plugin
BuildRequires:  maven-resources-plugin
BuildRequires:  maven-site-plugin
BuildRequires:  maven-surefire-plugin
BuildRequires:  maven-surefire-provider-junit4
BuildRequires:  maven-wagon >= 2.5-2
BuildRequires:	objectweb-asm
BuildRequires:  plexus-cipher
BuildRequires:  plexus-classworlds
BuildRequires:  plexus-containers-component-annotations
BuildRequires:  plexus-containers-component-metadata >= 1.5.5
BuildRequires:  plexus-containers-container-default
BuildRequires:  plexus-interpolation
BuildRequires:  plexus-sec-dispatcher
BuildRequires:  plexus-utils >= 3.0.10
BuildRequires:  sisu-inject >= 1:0
BuildRequires:	sisu-mojos
BuildRequires:  sisu-plexus >= 1:0
BuildRequires:  slf4j
BuildRequires:  xmlunit
BuildRequires:  mvn(ch.qos.logback:logback-classic)
BuildRequires:  mvn(org.mockito:mockito-core)
BuildRequires:	mvn(org.codehaus.modello:modello-maven-plugin)
# Theoretically Maven might be usable with just JRE, but typical Maven
# workflow requires full JDK, wso we require it here.
Requires:       java-devel

# XMvn does generate auto-requires, but explicit requires are still
# needed because some symlinked JARs are not present in Maven POMs or
# their dependency scope prevents them from being added automatically
# by XMvn.  It would be possible to explicitly specify only
# dependencies which are not generated automatically, but adding
# everything seems to be easier.
Requires:       aether-api
Requires:       aether-connector-basic
Requires:       aether-impl
Requires:       aether-spi
Requires:       aether-transport-wagon
Requires:       aether-util
Requires:       aopalliance
Requires:       apache-commons-cli
Requires:       apache-commons-codec
Requires:       apache-commons-logging
Requires:       atinject
Requires:       geronimo-annotation
Requires:       google-guice
Requires:       guava
Requires:       httpcomponents-client
Requires:       httpcomponents-core
Requires:       jsr-305
Requires:       maven-wagon
Requires:	objectweb-asm
Requires:       plexus-cipher
Requires:       plexus-classworlds
Requires:       plexus-containers-component-annotations
Requires:       plexus-interpolation
Requires:       plexus-sec-dispatcher
Requires:       plexus-utils
Requires:       sisu-inject
Requires:       sisu-plexus
Requires:       slf4j

# for noarch->arch change
Obsoletes:      %{name} < 0:%{version}-%{release}

# Temporary fix for broken sisu
Requires:       cdi-api
BuildRequires:  cdi-api

# If XMvn is part of the same RPM transaction then it should be
# installed first to avoid triggering rhbz#1014355.
# Not done in bootstrap mode because we may not have xmvn yet.
Requires(pre):  xmvn
%endif

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

%build

%install
install -d -m 755 %{buildroot}%{_datadir}/%{name}/bin
install -d -m 755 %{buildroot}%{_datadir}/%{name}/conf
install -d -m 755 %{buildroot}%{_datadir}/%{name}/boot
install -d -m 755 %{buildroot}%{_datadir}/%{name}/lib/ext
install -d -m 755 %{buildroot}%{_bindir}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m 755 %{buildroot}%{_datadir}/bash-completion/completions
install -d -m 755 %{buildroot}%{_mandir}/man1

install -p -m 755 %{SOURCE200} %{buildroot}%{_bindir}/mvn
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
%doc LICENSE NOTICE README.txt
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
%else
%setup -q -n apache-%{name}-%{version}%{?ver_add}
%patch0005 -p1

# not really used during build, but a precaution
rm maven-ant-tasks-*.jar

# Use Eclipse Sisu plugin
sed -i s/org.sonatype.plugins/org.eclipse.sisu/ maven-core/pom.xml

# fix for animal-sniffer (we don't generate 1.5 signatures)
sed -i 's:check-java-1.5-compat:check-java-1.6-compat:' pom.xml

rm -f apache-maven/src/bin/*.bat
sed -i 's:\r::' apache-maven/src/conf/settings.xml

# Update shell scripts to use unversioned classworlds
sed -i -e s:'-classpath "${M2_HOME}"/boot/plexus-classworlds-\*.jar':'-classpath "${M2_HOME}"/boot/plexus-classworlds.jar':g \
        apache-maven/src/bin/mvn*

# Disable animal-sniffer on RHEL
# Temporarily disabled for fedora to solve asm & asm4 clashing on classpath
%pom_remove_plugin :animal-sniffer-maven-plugin
%pom_remove_plugin :apache-rat-plugin

# logback is not really needed by maven in typical use cases, so set
# its scope to provided
%pom_xpath_inject "pom:dependency[pom:artifactId='logback-classic']" "<scope>provided</scope>" maven-embedder


%build
# Put all JARs in standard location, but create symlinks in Maven lib
# directory so that Plexus Classworlds can find them.
%mvn_file ":{*}:jar:" %{name}/@1 %{_datadir}/%{name}/lib/@1

%mvn_build -- -Dproject.build.sourceEncoding=UTF-8

mkdir m2home
(cd m2home
    tar -xvf ../apache-maven/target/*tar.gz
    chmod -R +rwX apache-%{name}-%{version}%{?ver_add}
    chmod -x apache-%{name}-%{version}%{?ver_add}/conf/settings.xml
)


%install
%mvn_install 

export M2_HOME=$(pwd)/m2home/apache-maven-%{version}%{?ver_add}

install -d -m 755 %{buildroot}%{_datadir}/%{name}/bin
install -d -m 755 %{buildroot}%{_datadir}/%{name}/conf
install -d -m 755 %{buildroot}%{_datadir}/%{name}/boot
install -d -m 755 %{buildroot}%{_datadir}/%{name}/lib/ext
install -d -m 755 %{buildroot}%{_bindir}
install -d -m 755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m 755 %{buildroot}%{_datadir}/bash-completion/completions
install -d -m 755 %{buildroot}%{_mandir}/man1

install -p -m 755 %{SOURCE200} %{buildroot}%{_bindir}/mvn
install -p -m 644 %{SOURCE2} %{buildroot}%{_mandir}/man1
install -p -m 644 %{SOURCE1} %{buildroot}%{_datadir}/bash-completion/completions/%{name}
mv $M2_HOME/bin/m2.conf %{buildroot}%{_sysconfdir}
ln -sf %{_sysconfdir}/m2.conf %{buildroot}%{_datadir}/%{name}/bin/m2.conf
mv $M2_HOME/conf/settings.xml %{buildroot}%{_sysconfdir}/%{name}
ln -sf %{_sysconfdir}/%{name}/settings.xml %{buildroot}%{_datadir}/%{name}/conf/settings.xml
mv $M2_HOME/conf/logging %{buildroot}%{_sysconfdir}/%{name}
ln -sf %{_sysconfdir}/%{name}/logging %{buildroot}%{_datadir}/%{name}/conf

cp -a $M2_HOME/bin/* %{buildroot}%{_datadir}/%{name}/bin

ln -sf $(build-classpath plexus/classworlds) \
    %{buildroot}%{_datadir}/%{name}/boot/plexus-classworlds.jar

(cd %{buildroot}%{_datadir}/%{name}/lib
    build-jar-repository -s -p . \
        aether/aether-api \
        aether/aether-connector-basic aether/aether-transport-wagon \
        aether/aether-impl \
        aether/aether-spi \
        aether/aether-util \
        aopalliance \
        cdi-api \
        commons-cli \
        guava \
        atinject \
        geronimo-annotation \
        jsr-305 \
        org.eclipse.sisu.inject \
        org.eclipse.sisu.plexus \
        plexus/plexus-cipher \
        plexus/containers-component-annotations \
        plexus/interpolation \
        plexus/plexus-sec-dispatcher \
        plexus/utils \
        google-guice-no_aop \
        slf4j/api \
        slf4j/simple \
        maven-wagon/file \
        maven-wagon/http-shaded \
        maven-wagon/provider-api \
        \
        httpcomponents/httpclient \
        httpcomponents/httpcore \
        maven-wagon/http-shared4 \
        commons-logging \
        commons-codec \
	objectweb-asm/asm
)

%files -f .mfiles
%doc LICENSE NOTICE README.md
%{_datadir}/%{name}
%{_bindir}/mvn
%dir %{_javadir}/%{name}
%dir %{_sysconfdir}/%{name}
%dir %{_sysconfdir}/%{name}/logging
%config(noreplace) %{_sysconfdir}/m2.conf
%config(noreplace) %{_sysconfdir}/%{name}/settings.xml
%config(noreplace) %{_sysconfdir}/%{name}/logging/simplelogger.properties
%{_datadir}/bash-completion/completions/%{name}
%{_mandir}/man1/mvn.1*

%files javadoc -f .mfiles-javadoc
%doc LICENSE NOTICE
%endif
