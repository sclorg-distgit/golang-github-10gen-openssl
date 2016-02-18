%{?scl:%scl_package %{name}}

%if 0%{?fedora} || 0%{?rhel} == 6|| 0%{?rhel} == 7
%global with_devel 1
%global with_bundled 0
%global with_debug 0
%global with_check 1
%global with_unit_test 1
%else
%global with_devel 0
%global with_bundled 0
%global with_debug 0
%global with_check 0
%global with_unit_test 0
%endif

%if 0%{?with_debug}
%global _dwz_low_mem_die_limit 0
%else
%global debug_package   %{nil}
%endif

%global provider        github
%global provider_tld    com
%global project         10gen
%global repo            openssl
# https://github.com/10gen/openssl
%global provider_prefix %{provider}.%{provider_tld}/%{project}/%{repo}
%global import_path     %{provider_prefix}
%global commit          4c6dbafa5ec35b3ffc6a1b1e1fe29c3eba2053ec
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

Name:           %{?scl_prefix}golang-%{provider}-%{project}-%{repo}
Version:        0
Release:        0.7.git%{shortcommit}%{?dist}
Summary:        OpenSSL bindings for Go (forked from github.com/spacemonkeygo/openssl)
License:        ASL 2.0
URL:            https://%{provider_prefix}
Source0:        https://%{provider_prefix}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Patch0:         change-import-path-prefix.patch
Patch1:         use-system-openssl.patch

# e.g. el6 has ppc64 arch without gcc-go, so EA tag is required
ExclusiveArch:  %{?go_arches:%{go_arches}}%{!?go_arches:%{ix86} x86_64 %{arm}}
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%description
%{summary}

%if 0%{?with_devel}
%package devel
Summary:       %{summary}
BuildArch:     noarch

%if 0%{?with_check}
BuildRequires: %{?scl_prefix}golang(github.com/spacemonkeygo/spacelog)
%endif

Requires:      openssl-libs
Requires:      openssl-devel
Requires:      %{?scl_prefix}golang(github.com/spacemonkeygo/spacelog)

Provides:      %{?scl_prefix}golang(%{import_path}) = %{version}-%{release}
Provides:      %{?scl_prefix}golang(%{import_path}/utils) = %{version}-%{release}

%description devel
%{summary}

This package contains library source intended for
building other packages which use import path with
%{import_path} prefix.
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%package unit-test
Summary:         Unit tests for %{name} package
# If go_compiler is not set to 1, there is no virtual provide. Use golang instead.
BuildRequires:  %{?go_compiler:compiler(go-compiler)}%{!?go_compiler:golang}

%if 0%{?with_check}
BuildRequires: openssl-libs
BuildRequires: openssl-devel
%endif
Requires: openssl-libs
Requires: openssl-devel

# test subpackage tests code from devel subpackage
Requires:        %{name}-devel = %{version}-%{release}

%description unit-test
%{summary}

This package contains unit tests for %{project}/%{repo}.
%endif

%prep
%setup -q -n %{repo}-%{commit}
%patch0 -p1
%patch1 -p1

%build
%{?scl:scl enable %{scl} - << "EOF"}

%{?scl:EOF}
%install
%{?scl:scl enable %{scl} - << "EOF"}
# as per commit 'removing code incompatible with openssl 0.9.8e',
# NewGCMDecryptionCipherCtx function no longer exists
rm -rf ciphers_test.go

# source codes for building projects
%if 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# copy *.c files
cp -pav *.c %{buildroot}/%{gopath}/src/%{import_path}/
echo "%%{gopath}/src/%%{import_path}/*.c" >> devel.file-list
# find all *.go but no *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*.go" \! -iname "*_test.go") ; do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> devel.file-list
done
%endif

# testing files for this project
%if 0%{?with_unit_test} && 0%{?with_devel}
install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# find all *_test.go files and generate unit-test.file-list
for file in $(find . -iname "*_test.go"); do
    install -d -p %{buildroot}/%{gopath}/src/%{import_path}/$(dirname $file)
    cp -pav $file %{buildroot}/%{gopath}/src/%{import_path}/$file
    echo "%%{gopath}/src/%%{import_path}/$file" >> unit-test.file-list
done
%endif

%if 0%{?with_devel}
olddir=$(pwd)
pushd %{buildroot}/%{gopath}/src/%{import_path}
for file in $(find . -type d) ; do
    echo "%%dir %%{gopath}/src/%%{import_path}/$file" >> ${olddir}/devel.file-list
done
popd
echo "%%dir %%{gopath}/src/%{provider}.%{provider_tld}/%{project}" >> devel.file-list
echo "%%dir %%{gopath}/src/%{provider}.%{provider_tld}" >> devel.file-list

sort -u -o devel.file-list devel.file-list
%endif

%{?scl:EOF}
%check
%if 0%{?with_check} && 0%{?with_unit_test} && 0%{?with_devel}
%if ! 0%{?with_bundled}
export GOPATH=%{buildroot}/%{gopath}:%{gopath}:/usr/include:/usr/lib64
%else
export GOPATH=%{buildroot}/%{gopath}:$(pwd)/Godeps/_workspace:%{gopath}:/usr/include:/usr/lib64
%endif

%if ! 0%{?gotest:1}
%global gotest go test
%endif

%gotest %{import_path}
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%if 0%{?with_devel}
%files devel -f devel.file-list
%license LICENSE
%doc README.md
%endif

%if 0%{?with_unit_test} && 0%{?with_devel}
%files unit-test -f unit-test.file-list
%license LICENSE
%doc README.md
%endif

%changelog
* Wed Feb 3 2016 Marek Skalicky <mskalick@redhat.com> - 0-0.7.git4c6dbaf
- Fixed directory ownership

* Thu Oct 08 2015 jchaloup <jchaloup@redhat.com> - 0-0.6.git4c6dbaf
- Put back path to header files
  related: #1247160

* Sat Sep 12 2015 jchaloup <jchaloup@redhat.com> - 0-0.5.git4c6dbaf
- Update to spec-2.0
  related: #1247160

* Mon Jul 27 2015 jchaloup <jchaloup@redhat.com> - 0-0.4.git4c6dbaf
- Rebuild all Fedora branches to test modified spec file
  related: #1247160

* Mon Jul 27 2015 jchaloup <jchaloup@redhat.com> - 0-0.3.git4c6dbaf
- Update of spec file to spec-2.0
  resolves: #1247160

* Thu Jun 18 2015 jchaloup <jchaloup@redhat.com> - 0-0.2.git4c6dbaf
- Add missing openssl
  related: #1232234

* Mon Jun 15 2015 Marek Skalicky <mskalick@redhat.com> - 0-0.1.git4c6dbaf
- First package for Fedora
  resolves: #1232234

