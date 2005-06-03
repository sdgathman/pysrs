%define name pysrs
%define version 0.30.7
%define release 1

Summary: Python SRS (Sender Rewriting Scheme) library
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
#Patch0: %{name}-%{version}.patch
License: Python license
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Stuart Gathman (Perl version by Shevek) <stuart@bmsi.com>
Packager: Stuart D. Gathman <stuart@bmsi.com>
Url: http://bmsi.com/python/pysrs.html

%description
Python SRS (Sender Rewriting Scheme) library.
As SPF is implemented, mail forwarders must rewrite envfrom for domains
they are not authorized to send from.

See http://spf.pobox.com/srs.html for details.
The Perl reference implementation is at http://www.anarres.org/projects/srs/

%prep
%setup
#%patch -p1

%build
python2.3 setup.py build

%install
python2.3 setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/etc/mail
cp pysrs.cfg $RPM_BUILD_ROOT/etc/mail
cat >$RPM_BUILD_ROOT/etc/mail/no-srs-mailers <<'EOF'
# no-srs-mailers - list domains we should not SRS encode for when we
# send to them.  E.g. primary MX servers for which we are a secondary.
#
EOF
mkdir -p $RPM_BUILD_ROOT/usr/share/sendmail-cf/hack
cp pysrs.m4 $RPM_BUILD_ROOT/usr/share/sendmail-cf/hack

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%config /etc/mail/pysrs.cfg
%config /etc/mail/no-srs-mailers
/usr/share/sendmail-cf/hack/pysrs.m4

%changelog
* Wed Mar 24 2004 Stuart Gathman <stuart@bmsi.com> 0.30.7-1
- Pass SRS_DOMAIN to envfrom2srs.py
* Wed Mar 24 2004 Stuart Gathman <stuart@bmsi.com> 0.30.6-4
- Put SRS rewriting rule at end of EnvFromSMTP in pysrs.m4
* Tue Mar 23 2004 Stuart Gathman <stuart@bmsi.com> 0.30.6-3
- Fix regex for is_srs macro in pysrs.m4
* Tue Mar 23 2004 Stuart Gathman <stuart@bmsi.com> 0.30.6-2
- set alwaysrewrite=True in envfrom2srs.py since pysrs.m4 skips local domains
- Incorporate m4 macro from Alain Knaff for cleaner sendmail support
* Mon Mar 22 2004 Stuart Gathman <stuart@bmsi.com> 0.30.5-1
- Make sendmail map use config in /etc/mail/pysrs.cfg
