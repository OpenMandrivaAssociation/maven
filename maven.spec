%bcond_without bootstrap

%global resolver_version 2.0.24
%global bundled_slf4j_version 2.0.17
# 3.10.1 calls ContainerConfiguration.setVisibilityPredicateSupplierTransformer
# (Sisu 1.1.1+). The indexed system jar is still 0.9.0.M3.MBI.
%global sisu_version 1.1.2
%global sysjar_drops --drop org.codehaus.mojo:animal-sniffer-maven-plugin --drop org.apache.rat:apache-rat-plugin --drop org.apache.maven.plugins:maven-enforcer-plugin --drop org.codehaus.mojo:buildnumber-maven-plugin --drop ch.qos.logback:logback-classic --drop org.powermock:powermock-reflect --drop biz.aQute.bnd:bnd-maven-plugin --drop org.eclipse.jetty:jetty-bom
%if %{with bootstrap}
%global sysjar_bootstrap 1
# Private copy of the bootstrap tree. %build patches its ASM. mvn-jdk27
# points XMvn at that copy: the installed configuration would open the
# unpatched jar. A command-line definition wins.
%{!?_sysjar_mvn:%global _sysjar_mvn %{_builddir}/jpb-root/mvn-jdk27}
# Resolver 2.0.24 is not in the bootstrap set (that set has 2.0.9).
# sisu-root is the 1.1.2 build of inject and plexus. A real package at
# 1.1.2 outranks the installed 0.9.0.M3.MBI record for this build only.
%{!?sysjar_extra:%global sysjar_extra --root / --root %{_builddir}/resolver-root --root %{_builddir}/sisu-root}
# --bootstrap would also read the installed tree. An equal version loaded
# later replaces this patched copy, so name only the private root.
%global __sysjar_mode --bootstrap-root %{_builddir}/jpb-root %{?sysjar_extra} %{?sysjar_drops}
%endif

Name:		maven
Epoch:		1
Version:	3.10.1
Release:	1
Summary:	Java project management and project comprehension tool
# maven itself is Apache-2.0
# maven-slf4j-provider vendors SLF4J simple sources, which are MIT
# lib/ ships Sisu 1.1.2 classes under the frozen 0.9.0.M3.MBI names
License:	Apache-2.0 AND MIT AND EPL-2.0
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
Source7:	toolchain-repo.py
Source8:	https://github.com/eclipse-sisu/sisu-project/archive/refs/tags/releases/%{sisu_version}.tar.gz#/sisu-project-%{sisu_version}.tar.gz

# logback is not installed; call it by reflection so the class is optional
Patch0:		0002-Invoke-logback-via-reflection.patch
# Offline build: no staging repos, no launcher shell tests, no sources-classifier unpack
Patch1:		maven-3.10.1-offline-build.patch

BuildRequires:	python
BuildRequires:	unzip
BuildRequires:	sysjar
# 3.10.1 embedder compiles against jakarta.annotation-api. The bootstrap
# tree only has the old javax.annotation coordinate.
BuildRequires:	mvn(jakarta.annotation:jakarta.annotation-api) = 1.3.5
# Private Sisu 1.1.2 compile. Same jars eclipse-sisu builds against.
BuildRequires:	java-current-devel
BuildRequires:	mvn(com.google.inject:guice)
BuildRequires:	mvn(com.google.inject.extensions:guice-servlet)
BuildRequires:	mvn(com.google.guava:guava)
BuildRequires:	mvn(com.google.guava:failureaccess)
BuildRequires:	mvn(javax.inject:javax.inject)
BuildRequires:	mvn(org.slf4j:slf4j-api) >= 2.0.17
BuildRequires:	mvn(javax.annotation:javax.annotation-api)
BuildRequires:	mvn(javax.enterprise:cdi-api)
BuildRequires:	mvn(javax.servlet:javax.servlet-api)
BuildRequires:	mvn(org.osgi:osgi.core)
BuildRequires:	mvn(org.codehaus.plexus:plexus-utils)
BuildRequires:	mvn(org.codehaus.plexus:plexus-classworlds) >= 2.7.0
BuildRequires:	mvn(org.codehaus.plexus:plexus-component-annotations)
BuildRequires:	mvn(org.ow2.asm:asm)
BuildSystem:	maven
BuildOption:	-Dproject.build.sourceEncoding=UTF-8

Provides:	bundled(slf4j) = %{bundled_slf4j_version}
Provides:	maven-lib = %{EVRD}
Provides:	maven-jdk-binding = %{EVRD}
Obsoletes:	maven-lib < 1:%{version}-%{release}
Obsoletes:	maven-openjdk21 < 1:%{version}-%{release}
Obsoletes:	maven-openjdk25 < 1:%{version}-%{release}
Obsoletes:	maven-unbound < 1:%{version}-%{release}
# The SRPM is parsed before sysjar is installed, so the sysjar macro is
# not defined yet. This package does not pin a JDK.
Requires:	java-current

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
tar -C %{_builddir} -xzf %{SOURCE8}
cp -a %{_builddir}/sisu-project-releases-%{sisu_version}/LICENSE.txt sisu-EPL-2.0.txt
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
# Compile Sisu %{sisu_version} before the resolver build. The private root
# has to exist before sysjar reads it. A default method on the old interface
# throws UnsupportedOperationException, so both the interface and
# DefaultContainerConfiguration have to be this version.
sisu=%{_builddir}/sisu-project-releases-%{sisu_version}
work=%{_builddir}/sisu-classes
test -d "$sisu/org.eclipse.sisu.inject/src/main/java"
find "$sisu" \( -name '*.jar' -o -name '*.class' \) -delete
rm -rf "$work"
install -d "$work"
sisu_java_home=${JAVA_HOME-}
sisu_path=$PATH
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
CP="%{_javadir}/google-guice.jar"
CP="$CP:%{_javadir}/guice/guice-servlet.jar"
CP="$CP:%{_javadir}/atinject.jar"
CP="$CP:%{_javadir}/osgi-core.jar"
CP="$CP:%{_javadir}/slf4j-api.jar"
CP="$CP:%{_javadir}/jakarta-annotations/jakarta.annotation-api.jar"
CP="$CP:%{_javadir}/cdi-api.jar"
CP="$CP:%{_javadir}/javax.servlet-4.0.1.jar"
CP="$CP:%{_javadir}/plexus-utils.jar"
CP="$CP:%{_javadir}/plexus-classworlds-2.7.0.jar"
CP="$CP:%{_javadir}/plexus-containers/plexus-component-annotations.jar"
CP="$CP:%{_javadir}/guava.jar"
CP="$CP:%{_javadir}/failureaccess.jar"
CP="$CP:%{_javadir}/asm.jar"
for jar in ${CP//:/ }; do
	test -s "$jar"
done
compile_mod() {
	src=$1
	out=$2
	expect=$3
	extra=$4
	mkdir -p "$out"
	find "$src" -name '*.java' \
		! -name 'InjectedTest.java' \
		! -name 'InjectedTestCase.java' \
		! -name 'PlexusTestCase.java' > "$out.list"
	test "$(wc -l < "$out.list")" -eq "$expect"
	javac --release 8 -encoding UTF-8 -Xlint:-options -proc:none \
		-cp "$CP:$extra" -d "$out" @"$out.list"
}
compile_mod "$sisu/org.eclipse.sisu.inject/src/main/java" "$work/inject" 147 ""
compile_mod "$sisu/org.eclipse.sisu.plexus/src/main/java" "$work/plexus" 136 "$work/inject"
javap -v -classpath "$work/plexus" org.codehaus.plexus.DefaultContainerConfiguration | grep -F -q 'major version: 52'
javap -classpath "$work/plexus" org.codehaus.plexus.DefaultContainerConfiguration | grep -F -q setVisibilityPredicateSupplierTransformer
install -d "$work/plexus/META-INF/sisu"
printf '%%s\n' \
	org.codehaus.plexus.component.configurator.BasicComponentConfigurator \
	org.codehaus.plexus.component.configurator.MapOrientedComponentConfigurator \
	> "$work/plexus/META-INF/sisu/javax.inject.Named"
jar_mod() {
	artifact=$1
	classes=$2
	printf 'Manifest-Version: 1.0\nAutomatic-Module-Name: %%s\n\n' "$artifact" > "$work/$artifact.mf"
	jar cfm "$work/$artifact.jar" "$work/$artifact.mf" -C "$classes" .
}
jar_mod org.eclipse.sisu.inject "$work/inject"
jar_mod org.eclipse.sisu.plexus "$work/plexus"
cat > "$work/org.eclipse.sisu.inject.pom" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.eclipse.sisu</groupId>
  <artifactId>org.eclipse.sisu.inject</artifactId>
  <version>1.1.2</version>
  <name>Sisu Inject</name>
  <licenses>
    <license>
      <name>EPL-2.0</name>
      <url>https://www.eclipse.org/legal/epl-2.0/</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.inject</groupId>
      <artifactId>guice</artifactId>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
    </dependency>
  </dependencies>
</project>
EOF
cat > "$work/org.eclipse.sisu.plexus.pom" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.eclipse.sisu</groupId>
  <artifactId>org.eclipse.sisu.plexus</artifactId>
  <version>1.1.2</version>
  <name>Sisu Plexus</name>
  <licenses>
    <license>
      <name>EPL-2.0</name>
      <url>https://www.eclipse.org/legal/epl-2.0/</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.eclipse.sisu</groupId>
      <artifactId>org.eclipse.sisu.inject</artifactId>
      <version>1.1.2</version>
    </dependency>
    <dependency>
      <groupId>com.google.inject</groupId>
      <artifactId>guice</artifactId>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-classworlds</artifactId>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-component-annotations</artifactId>
    </dependency>
    <dependency>
      <groupId>org.codehaus.plexus</groupId>
      <artifactId>plexus-utils</artifactId>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-api</artifactId>
    </dependency>
  </dependencies>
</project>
EOF
rm -rf %{_builddir}/sisu-root
# file-name keeps the buildroot path off the unversioned /usr/share/java
# name. resolve prefers an absolute path that already exists on the system.
sysjar install --buildroot %{_builddir}/sisu-root \
	--file-name "org.eclipse.sisu.inject-%{sisu_version}" \
	--artifact "$work/org.eclipse.sisu.inject.pom:$work/org.eclipse.sisu.inject.jar"
sysjar install --buildroot %{_builddir}/sisu-root \
	--file-name "org.eclipse.sisu.plexus-%{sisu_version}" \
	--artifact "$work/org.eclipse.sisu.plexus.pom:$work/org.eclipse.sisu.plexus.jar"
sisu_plexus=$(sysjar resolve -q --root / --root %{_builddir}/sisu-root org.eclipse.sisu:org.eclipse.sisu.plexus:1.1.2)
case $sisu_plexus in
%{_builddir}/sisu-root/*) ;;
*) echo "sisu 1.1.2 resolved to $sisu_plexus" >&2; exit 1 ;;
esac
python - "%{_builddir}/sisu-root" << 'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]) / "usr/share/sysjar/index/org.eclipse.sisu"
for name in ("org.eclipse.sisu.inject.sysjar", "org.eclipse.sisu.plexus.sysjar"):
    data = json.loads((root / name).read_text())
    if data.get("version") != "1.1.2":
        raise SystemExit(f"{name} version is {data.get('version')}")
PY
export PATH=$sisu_path
if [ -n "$sisu_java_home" ]; then
	export JAVA_HOME=$sisu_java_home
else
	unset JAVA_HOME
fi
# sisu-maven-plugin depends on org.eclipse.sisu.inject, and that
# dependency is the ClassReader which scans JDK classes. Patch the copy
# the metadata points at. The installed tree is not writable here.
jpb=%{_builddir}/jpb-root/usr/share/javapackages-bootstrap
install -d %{_builddir}/jpb-root/usr/share
cp -a %{_datadir}/javapackages-bootstrap "$jpb"
python %{SOURCE6} \
	"$jpb/org.eclipse.sisu.inject.jar" \
	"$jpb/org.eclipse.sisu.inject.jar.jdk"
mv -f "$jpb/org.eclipse.sisu.inject.jar.jdk" \
	"$jpb/org.eclipse.sisu.inject.jar"
python %{SOURCE6} \
	"$jpb/asm.jar" \
	"$jpb/asm.jar.jdk"
mv -f "$jpb/asm.jar.jdk" "$jpb/asm.jar"
sed -i "s|/usr/share/javapackages-bootstrap/|$jpb/|g" \
	"$jpb"/maven-metadata/*.xml
# sysjar stamps the metadata version (2.0.17.MBI). XMvn indexes an
# artifact under compatVersions only. An empty list means SYSTEM, the
# older unversioned jar, so a request for 2.0.17.MBI opened slf4j-api.jar
# (1.7.36) and maven-slf4j-provider could not see the 2.0 SPI. A second
# metadata file repeats each version text as a compat key.
python - "$jpb/maven-metadata" << 'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

meta = Path(sys.argv[1])
dest = meta / "mbi-versions.xml"
root_out = ET.Element("metadata")
arts_out = ET.SubElement(root_out, "artifacts")
seen = set()

def parents_of(root):
    return {child: parent for parent in root.iter() for child in list(parent)}

for path in sorted(meta.glob("*.xml")):
    if path.name == dest.name:
        continue
    tree = ET.parse(path)
    parents = parents_of(tree.getroot())
    for node in tree.getroot().iter("artifact"):
        parent = parents.get(node)
        if parent is None or parent.tag != "artifacts":
            continue
        version = (node.findtext("version") or "").strip()
        compat = node.find("compatVersions")
        if compat is None or not version:
            continue
        have = {(item.text or "").strip() for item in list(compat)}
        if version in have:
            continue
        extension = (node.findtext("extension") or "jar").strip()
        classifier = (node.findtext("classifier") or "").strip()
        key = (
            node.findtext("groupId"),
            node.findtext("artifactId"),
            extension,
            classifier,
            version,
        )
        if key in seen:
            continue
        seen.add(key)
        copy = ET.Element("artifact")
        for tag in ("groupId", "artifactId", "extension", "classifier", "version", "path"):
            text = node.findtext(tag)
            if text:
                ET.SubElement(copy, tag).text = text
        comps = ET.SubElement(copy, "compatVersions")
        ET.SubElement(comps, "version").text = version
        for extra in ("aliases", "dependencies"):
            child = node.find(extra)
            if child is not None:
                copy.append(ET.fromstring(ET.tostring(child)))
        arts_out.append(copy)

if len(arts_out):
    dest.write_bytes(ET.tostring(root_out, encoding="utf-8", xml_declaration=True))
PY
# XMvn, not sysjar, opens that jar. It reads the installed configuration
# and follows the absolute path stored there, which is the unpatched
# copy. A later metadata repository wins when duplicates are not ignored,
# so this configuration names the patched tree and is the only one loaded.
xdg=%{_builddir}/jpb-root/xdg
install -d "$xdg/xmvn" "$xdg/empty"
sed \
	-e "s|/usr/share/javapackages-bootstrap/maven-metadata|$jpb/maven-metadata|" \
	-e 's|<resolverSettings>|<resolverSettings>\n    <ignoreDuplicateMetadata>false</ignoreDuplicateMetadata>|' \
	%{_datadir}/xmvn/configuration.xml > "$xdg/xmvn/configuration.xml"
cat > %{_builddir}/jpb-root/mvn-jdk27 << EOF
#!/bin/sh
export XDG_CONFIG_HOME="$xdg/empty"
export XDG_CONFIG_DIRS="$xdg/empty"
export XDG_DATA_HOME="$xdg/empty"
export XDG_DATA_DIRS="$xdg"
exec "$jpb/bin/mvn" "\$@"
EOF
chmod 755 %{_builddir}/jpb-root/mvn-jdk27
(
	cd %{_builddir}/maven-resolver-%{resolver_version}
	%__sysjar_use_java_home
	export MAVEN_SKIP_RC=1
	%sysjar_mvn -Dmaven.test.skip=true -Dproject.build.sourceEncoding=UTF-8 package
	sysjar install --buildroot %{_builddir}/resolver-root --auto .
)
	# XMvn resolves a request for these coordinates to the unversioned
	# bootstrap jar (Resolver 1.9.22) and never opens the 2.0.24 jar.
	# An exact version in the private metadata is the file it returns.
	python - "$jpb/maven-metadata/resolver-%{resolver_version}.xml" "%{_builddir}/resolver-root" << 'PY'
import json, sys
from pathlib import Path
import xml.etree.ElementTree as ET

dest = Path(sys.argv[1])
buildroot = Path(sys.argv[2])
index = buildroot / "usr/share/sysjar/index/org.apache.maven.resolver"
meta = ET.Element("metadata")
arts = ET.SubElement(meta, "artifacts")

def add_file(data, extension, stored):
    if not stored:
        return
    path = buildroot / stored.lstrip("/")
    if not path.is_file():
        raise SystemExit(f"missing {path}")
    node = ET.SubElement(arts, "artifact")
    ET.SubElement(node, "groupId").text = data["groupId"]
    ET.SubElement(node, "artifactId").text = data["artifactId"]
    if extension != "jar":
        ET.SubElement(node, "extension").text = extension
    if data.get("classifier"):
        ET.SubElement(node, "classifier").text = data["classifier"]
    ET.SubElement(node, "version").text = data["version"]
    ET.SubElement(node, "path").text = str(path)
    compat = ET.SubElement(node, "compatVersions")
    ET.SubElement(compat, "version").text = data["version"]
    if extension != "pom":
        return
    deps = ET.SubElement(node, "dependencies")
    for dep in data.get("dependencies") or []:
        if dep.get("optional") or dep.get("scope") not in (None, "", "compile"):
            continue
        item = ET.SubElement(deps, "dependency")
        ET.SubElement(item, "groupId").text = dep["groupId"]
        ET.SubElement(item, "artifactId").text = dep["artifactId"]
        if dep["groupId"] == "org.apache.maven.resolver":
            ET.SubElement(item, "requestedVersion").text = data["version"]
            ET.SubElement(item, "resolvedVersion").text = data["version"]

for record in sorted(index.glob("*.sysjar")):
    data = json.loads(record.read_text())
    extension = data.get("extension") or "jar"
    if extension == "pom":
        add_file(data, "pom", data.get("pom") or data.get("path") or "")
    else:
        add_file(data, "jar", data.get("jar") or data.get("path") or "")
        if data.get("pom"):
            add_file(data, "pom", data["pom"])

if not len(arts):
    raise SystemExit(f"no resolver artifacts under {index}")
dest.parent.mkdir(parents=True, exist_ok=True)
ET.ElementTree(meta).write(dest, encoding="utf-8", xml_declaration=True)
PY
%endif

%install
install -d %{buildroot}%{_datadir}
tar -C %{buildroot}%{_datadir} -xzf apache-maven/target/apache-maven-%{version}-bin.tar.gz
mv %{buildroot}%{_datadir}/apache-maven-%{version} %{buildroot}%{_datadir}/maven
rm -f %{buildroot}%{_datadir}/maven/bin/*.cmd
# maven-components indexes these frozen names. The bytes are Sisu %{sisu_version}.
# A second copy under the real version would put the same classes on the classpath twice.
sisu_lib=%{buildroot}%{_datadir}/maven/lib
for art in org.eclipse.sisu.inject org.eclipse.sisu.plexus; do
	src="$sisu_lib/${art}-%{sisu_version}.jar"
	dest="$sisu_lib/${art}-0.9.0.M3.MBI.jar"
	if [ ! -s "$src" ]; then
		echo "expected $src" >&2
		ls -l "$sisu_lib"/org.eclipse.sisu.* >&2 || true
		exit 1
	fi
	rm -f "$dest"
	mv -f "$src" "$dest"
done
unexpected=$(find "$sisu_lib" -name 'org.eclipse.sisu.*.jar' \
	! -name 'org.eclipse.sisu.inject-0.9.0.M3.MBI.jar' \
	! -name 'org.eclipse.sisu.plexus-0.9.0.M3.MBI.jar')
if [ -n "$unexpected" ]; then
	echo "unexpected sisu jar in maven lib" >&2
	printf '%%s\n' "$unexpected" >&2
	exit 1
fi

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

%if %{with bootstrap}
# Default lifecycle plugins are not packages. Ship the bootstrap copies
# for sysjar to link into the build repository, and make maven-core ask
# for those versions. The jars are not indexed.
jpb=%{_builddir}/jpb-root/usr/share/javapackages-bootstrap
python %{SOURCE7} \
	"$jpb" \
	%{buildroot}%{_datadir}/maven/lib/maven-core-%{version}.jar \
	%{buildroot}%{_datadir}/maven/toolchain
%endif

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
%license LICENSE NOTICE sisu-EPL-2.0.txt
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
