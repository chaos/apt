Name: apt
Version:
Release:
Source: 

License: GPL
Summary: APT modified for /usr/local
Group: Utilities/System
URL: http://packages.debian.org/apt
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires: dpkg
Requires: gnupg
BuildRequires: quilt
BuildRequires: imake
BuildRequires: dpkg
BuildRequires: curl-devel
BuildRequires: db4-devel

%package utils
Summary: APT utility programs
Group: Utilities/System

%description
Advanced front-end for dpkg (/usr/local version).

%description utils
APT utility programs such as apt-ftparchive,
apt-sortpkgs and apt-extracttemplates.

%prep
%setup

%build
make quilt
cd apt+chaos && %configure
make -j4

%install
mkdir -p $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%_bindir
mkdir -p $RPM_BUILD_ROOT/%_includedir/apt
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/apt/methods
mkdir -p $RPM_BUILD_ROOT/%{_libdir}/dpkg/methods/apt
mkdir -p $RPM_BUILD_ROOT/var/lib/apt/lists/partial
mkdir -p $RPM_BUILD_ROOT/var/lib/apt/periodic
mkdir -p $RPM_BUILD_ROOT/var/log/apt
mkdir -p $RPM_BUILD_ROOT/var/cache/apt/archives/partial
mkdir -p $RPM_BUILD_ROOT/usr/share/locale
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/apt/sources.list.d/

arch=`echo %{_arch} | sed 's/x86_64/amd64/'`
cat <<EOF >$RPM_BUILD_ROOT%{_sysconfdir}/apt/apt.conf 
APT::Architecture "linux-$arch";
Dir "/" {
  Bin::methods  "%{_libdir}/apt/methods";
  State::status "/usr/local/dpkg-db/status";
  Log           "/var/log/apt";
}
EOF

%if 0%{?chaos} < 5
%define repodir RHEL5-debs
%else
%define repodir RHEL6-debs
%endif
echo "deb file:/repo/llnl/ %{repodir}/" \
     >$RPM_BUILD_ROOT%{_sysconfdir}/apt/sources.list


# Install builder key for later inclusion in trusted keys
install -D -m444 buildbot.txt $RPM_BUILD_ROOT/%{_sysconfdir}/apt/buildkey.txt
cp apt-ftparchive.conf $RPM_BUILD_ROOT/%{_sysconfdir}/apt
cp apt-release.conf $RPM_BUILD_ROOT/%{_sysconfdir}/apt

install -D -m755 apt-userinst.sh $RPM_BUILD_ROOT/%{_bindir}/apt-userinst

cd apt+chaos

find bin -type f -name "libapt-pkg*.so*" -exec \
	     cp -a "{}" $RPM_BUILD_ROOT%{_libdir} \;
find bin -type l -name "libapt-pkg*.so*" -exec \
	     cp -a "{}" $RPM_BUILD_ROOT%{_libdir} \;

find bin -type f -name "libapt-inst*.so*" -exec \
	     cp -a "{}" $RPM_BUILD_ROOT%{_libdir} \;
find bin -type l -name "libapt-inst*.so*" -exec \
	     cp -a "{}" $RPM_BUILD_ROOT%{_libdir} \;

#install -m644 include/apt-pkg/*.h $RPM_BUILD_ROOT%{_includedir}/apt

install -m755 bin/apt-* $RPM_BUILD_ROOT%{_bindir}
install bin/methods/* $RPM_BUILD_ROOT%{_libdir}/apt/methods/
install scripts/dselect/* $RPM_BUILD_ROOT%{_libdir}/dpkg/methods/apt
cp -r locale $RPM_BUILD_ROOT/usr/share

for man in doc/*.[158] ; do
    sec=${man##*.}
    mkdir -p $RPM_BUILD_ROOT%{_mandir}/man${sec}
    install $man $RPM_BUILD_ROOT%{_mandir}/man${sec}
done

# remove apt-mark which requires apt-python
rm -f $RPM_BUILD_ROOT%{_bindir}/apt-mark
# remove apt-cdrom which won't be usefule
rm -f $RPM_BUILD_ROOT%{_bindir}/apt-cdrom
rm -f $RPM_BUILD_ROOT%{_mandir}/man8/apt-cdrom*


%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ ! -e %{_sysconfdir}/apt/trusted.gpg ]; then
   tmpfile="/tmp/apt-inst-$$.out";
   %{_bindir}/apt-key add %{_sysconfdir}/apt/buildkey.txt >$tmpfile 2>&1 || \
      echo "apt-key failed!" `cat $tmpfile` >&2
   rm -f $tmpfile
fi

%postun
if [ "$1" = "0" ]; then
   rm -rf /etc/apt/trust*
fi

%define egdir apt+chaos/doc/examples
%files
%defattr(-, root, root)
%doc NEWS 
%doc ChangeLog
%doc %{egdir}/configure-index 
%doc %{egdir}/apt.conf 
%doc %{egdir}/sources.list
%config(noreplace) %{_sysconfdir}/apt/apt.conf
%config(noreplace) %{_sysconfdir}/apt/sources.list
%attr (0444, root, root) %{_sysconfdir}/apt/buildkey.txt
%{_bindir}/apt-get
%{_bindir}/apt-cache
%{_bindir}/apt-key
%{_bindir}/apt-config
%{_bindir}/apt-userinst
%{_libdir}/libapt-pkg*
%{_mandir}/man5/sources.list.5.gz
%{_mandir}/man5/apt.conf.5.gz
%{_mandir}/man5/apt_preferences.5.gz
%{_mandir}/man8/apt.8.gz
%{_mandir}/man8/apt-get.8.gz
%{_mandir}/man8/apt-key.8.gz
%{_mandir}/man8/apt-cache.8.gz
%{_mandir}/man8/apt-config.8.gz
%{_mandir}/man8/apt-secure.8.gz
/usr/share/locale/*
%{_libdir}/apt/methods/*
%{_libdir}/dpkg/methods/*
%dir /var/lib/apt
%dir /var/lib/apt/lists
%dir /var/lib/apt/periodic
%dir /var/lib/apt/lists/partial
%dir /var/cache/apt
%dir /var/cache/apt/archives
%dir /var/cache/apt/archives/partial
%dir /var/log/apt
%dir /etc/apt
%dir /etc/apt/sources.list.d

%files utils
%defattr (-,root,root)
%doc %{egdir}/apt-ftparchive.conf
%{_sysconfdir}/apt/apt-ftparchive.conf
%{_sysconfdir}/apt/apt-release.conf
%{_bindir}/apt-ftparchive
%{_bindir}/apt-sortpkgs
%{_bindir}/apt-extracttemplates
%{_libdir}/libapt-inst*
%{_mandir}/man1/apt-ftparchive.1.gz
%{_mandir}/man1/apt-sortpkgs.1.gz
%{_mandir}/man1/apt-extracttemplates.1.gz

