%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
Name:          jabberpy
Version:       0.6
Release:       1%{?dist}
Summary:       Python xmlstream and jabber IM protocol libs

Group:         Development/Libraries
License:       LGPLv2+
URL:           http://sourceforge.net/projects/jabberpy/
Source0:       https://github.com/galtsib/%{name}/archive/%{name}-%{version}-0.tar.gz

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:     noarch

BuildRequires: python-devel
Requires:      python

%description
jabber.py is a Python module for the jabber instant messaging
protocol. jabber.py deals with the xml parsing and socket code,
leaving the programmer to concentrate on developing quality jabber
based applications with Python.

%prep
%setup -q -n %{name}-%{version}-0
chmod -x examples/*.py

%build
%{__python} setup.py  build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --root=$RPM_BUILD_ROOT 

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc examples README
%{python_sitelib}/*


%changelog
* Thu Apr 28 2016 Gennadii Altukhov <galt@redhat.com> 0.6-1
- new package built with tito

