
Name:           maven
Version:        3.0.3
Release:        4
Summary:        Java project management and project comprehension tool

Group:          Development/Java
License:        ASL 2.0 and MIT and BSD
URL:            http://maven.apache.org/
# Source URL is for testing only, final version will be in different place:
# http://www.apache.org/dyn/closer.cgi/maven/source/apache-%{name}-%{version}-src.tar.gz
Source0:        http://www.apache.org/dyn/closer.cgi/maven/source/apache-%{name}-%{version}-src.tar.gz

# custom resolver java files
# source: git clone git://fedorapeople.org/~sochotni/maven-javadir-resolver/
Source100:      JavadirWorkspaceReader.java
Source101:      MavenJPackageDepmap.java

# 2xx for created non-buildable sources
Source200:    %{name}-script
Source201:    %{name}-script-local
Source202:    %{name}-script-rpmbuild

# Other included files
Source250:    repo-metadata.tar.xz

# Patch1XX could be upstreamed probably
# Patch15X are already upstream
Patch150:         0001-Add-plugin-api-deps.patch

# Patch2XX for non-upstreamable patches
Patch200:       0002-Use-custom-resolver.patch

BuildArch:      noarch

BuildRequires:  maven
BuildRequires:  maven-assembly-plugin
BuildRequires:  maven-compiler-plugin
BuildRequires:  maven-install-plugin
BuildRequires:  maven-jar-plugin
BuildRequires:  maven-javadoc-plugin
BuildRequires:  maven-resources-plugin
BuildRequires:  maven-site-plugin
BuildRequires:  maven-surefire-plugin
BuildRequires:  maven-surefire-provider-junit4
BuildRequires:  buildnumber-maven-plugin
BuildRequires:  plexus-containers-component-metadata >= 1.5.5
BuildRequires:  plexus-containers-container-default
BuildRequires:  animal-sniffer >= 1.6-5
BuildRequires:  mojo-parent
BuildRequires:  atinject
BuildRequires:  aether >= 1.11
BuildRequires:  async-http-client
BuildRequires:  sonatype-oss-parent
BuildRequires:  sisu >= 2.1.1-2
BuildRequires:  google-guice >= 3.0
BuildRequires:  hamcrest
BuildRequires:  apache-commons-parent

Requires:       java >= 0:1.6.0
Requires:       plexus-classworlds >= 2.4
Requires:       apache-commons-cli
Requires:       guava
Requires:       hamcrest
Requires:       nekohtml
Requires:       plexus-cipher
Requires:       plexus-containers-component-annotations
Requires:       plexus-containers-container-default
Requires:       plexus-interpolation
Requires:       plexus-sec-dispatcher
Requires:       plexus-utils
Requires:       xbean
Requires:       xerces-j2
Requires:       maven-wagon
Requires:       aether >= 1.11
Requires:       async-http-client
Requires:       sonatype-oss-parent
Requires:       sisu >= 2.1.1-2
Requires:       google-guice >= 3.0
Requires:       atinject
Requires:       animal-sniffer >= 1.6-5
Requires:       mojo-parent
Requires:       hamcrest
Requires:       apache-commons-parent


Requires(post): jpackage-utils
Requires(postun): jpackage-utils


%description
Maven is a software project management and comprehension tool. Based on the
concept of a project object model (POM), Maven can manage a project's build,
reporting and documentation from a central piece of information.

%package        javadoc
Summary:        API documentation for %{name}
Group:          Development/Java
Requires:       jpackage-utils

%description    javadoc
%{summary}.

%prep
%setup -q -n apache-%{name}-%{version}%{?ver_add}
%patch150 -p1
%patch200 -p1

# get custom resolver in place
mkdir -p maven-aether-provider/src/main/java/org/apache/maven/artifact/resolver \
         maven-aether-provider/src/main/java/org/apache/maven/artifact/repository

cp %{SOURCE100} maven-aether-provider/src/main/java/org/apache/maven/artifact/resolver
cp %{SOURCE101} maven-aether-provider/src/main/java/org/apache/maven/artifact/repository

# by adding our things this has become compile dep
sed -i 's:<scope>runtime</scope>::' maven-core/pom.xml

# not really used during build, but a precaution
rm maven-ant-tasks-*.jar

# fix line endings
sed -i 's:\r::' *.txt

# fix for animal-sniffer (we don't generate 1.5 signatures)
sed -i 's:check-java-1.5-compat:check-java-1.6-compat:' pom.xml

pushd apache-maven
rm src/bin/*bat
sed -i 's:\r::' src/conf/settings.xml

# Update shell scripts to use unversioned classworlds
sed -i -e s:'-classpath "${M2_HOME}"/boot/plexus-classworlds-\*.jar':'-classpath "${M2_HOME}"/boot/plexus-classworlds.jar':g \
        src/bin/mvn*
popd

%build
mvn-rpmbuild -e install javadoc:aggregate

mkdir m2home
(cd m2home
tar xvf ../apache-maven/target/*tar.gz
chmod -x apache-%{name}-%{version}%{?ver_add}/conf/settings.xml
)


%install
export M2_HOME=$(pwd)/m2home/apache-maven-%{version}%{?ver_add}

# maven2 directory in /usr/share/java
install -dm 755 $RPM_BUILD_ROOT%{_javadir}/%{name}

# put global m2 config into /etc and symlink it later
install -dm 755 $RPM_BUILD_ROOT%{_sysconfdir}
mv $M2_HOME/bin/m2.conf $RPM_BUILD_ROOT%{_sysconfdir}/

###########
# M2_HOME #
###########
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}

#################
# Repo metadata #
#################
install -m 755 %{SOURCE250} $RPM_BUILD_ROOT%{_datadir}/%{name}/


###############
# M2_HOME/bin #
###############
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/bin
cp -a $M2_HOME/bin/* $RPM_BUILD_ROOT%{_datadir}/%{name}/bin

ln -sf %{_sysconfdir}/m2.conf $RPM_BUILD_ROOT%{_datadir}/%{name}/bin/m2.conf


################
# M2_HOME/boot #
################
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/boot

# this dangling symlink will be filled in by Requires
(cd $RPM_BUILD_ROOT%{_datadir}/%{name}/boot
  ln -sf `build-classpath plexus/classworlds` plexus-classworlds.jar
)


################
# M2_HOME/conf #
################
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/conf
cp -a $M2_HOME/conf/* $RPM_BUILD_ROOT%{_datadir}/%{name}/conf/

###############
# M2_HOME/lib #
###############
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/lib

# jdom is needed for our custom resolving code only
(cd $RPM_BUILD_ROOT%{_datadir}/%{name}/lib

  build-jar-repository -s -p . aether/api aether/connector-wagon aether/impl aether/spi aether/util \
                               commons-cli guava google-guice hamcrest/core nekohtml plexus/plexus-cipher \
                               plexus/containers-component-annotations plexus/containers-container-default \
                               plexus/interpolation plexus/plexus-sec-dispatcher plexus/utils \
                               sisu/sisu-inject-bean sisu/sisu-inject-plexus maven-wagon/file \
                               maven-wagon/http-lightweight maven-wagon/http-shared maven-wagon/provider-api \
                               xbean/xbean-reflect xerces-j2 jdom xml-commons-apis atinject
  mkdir ext/
)

################
# M2_HOME/poms #
#*##############
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/poms

########################
# /etc/maven/fragments #
########################
install -dm 755 $RPM_BUILD_ROOT/%{_sysconfdir}/maven/fragments

##############################
# /usr/share/java repository #
##############################
install -dm 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/repository
ln -s %{_javadir} $RPM_BUILD_ROOT%{_datadir}/%{name}/repository/JPP

##################
# javadir/maven #
#*################
install -dm 755 $RPM_BUILD_ROOT%{_javadir}/%{name}

#######################
# javadir/maven/poms #
#*#####################
ln -s %{_datadir}/%{name}/poms $RPM_BUILD_ROOT%{_javadir}/%{name}/poms

############
# /usr/bin #
############
install -dm 755 $RPM_BUILD_ROOT%{_bindir}

# Wrappers
cp -af %{SOURCE200} $RPM_BUILD_ROOT%{_bindir}/mvn3
cp -af %{SOURCE201} $RPM_BUILD_ROOT%{_bindir}/mvn-local
cp -af %{SOURCE202} $RPM_BUILD_ROOT%{_bindir}/mvn-rpmbuild

###################
# Individual jars #
###################

for module in maven-aether-provider maven-artifact maven-compat \
              maven-core maven-embedder maven-model \
              maven-model-builder maven-plugin-api \
              maven-repository-metadata  maven-settings \
              maven-settings-builder;do

    pushd $module
    install -m 644 target/$module-%{version}%{?ver_add}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}/$module.jar
    ln -s %{_javadir}/%{name}/$module.jar $RPM_BUILD_ROOT%{_datadir}/%{name}/lib/$module.jar
    install -m 644 pom.xml $RPM_BUILD_ROOT%{_datadir}/%{name}/poms/JPP.%{name}-$module.pom
    %add_to_maven_depmap org.apache.maven $module %{version} JPP/%{name} $module
    popd
done

# maven pom
install -m 644 pom.xml $RPM_BUILD_ROOT%{_datadir}/%{name}/poms/JPP.%{name}-maven.pom
%add_to_maven_depmap org.apache.maven maven %{version} JPP/%{name} maven

# javadocs
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}
cp -pr target/site/apidocs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}


%post
%update_maven_depmap

%postun
%update_maven_depmap


%files
%defattr(-,root,root,-)
%doc LICENSE.txt NOTICE.txt README.txt
%attr(0755,root,root) %{_bindir}/mvn3
%attr(0755,root,root) %{_bindir}/mvn-local
%attr(0755,root,root) %{_bindir}/mvn-rpmbuild
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/bin
%attr(0755,root,root) %{_datadir}/%{name}/bin/mvn
%attr(0755,root,root) %{_datadir}/%{name}/bin/mvnyjp
%attr(0755,root,root) %{_datadir}/%{name}/bin/mvnDebug
%{_datadir}/%{name}/bin/*.conf
%config(noreplace) %{_sysconfdir}/m2.conf
%{_datadir}/%{name}/boot
%{_datadir}/%{name}/conf
%{_datadir}/%{name}/lib
%{_datadir}/%{name}/poms
%{_datadir}/%{name}/repository
%config %{_mavendepmapfragdir}/%{name}
%{_javadir}/%{name}
%{_datadir}/%{name}/repo-metadata.tar.xz

%files javadoc
%defattr(-,root,root,-)
%doc LICENSE.txt
%{_javadocdir}/%{name}


