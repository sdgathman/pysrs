%define sysvinit pysrs.rc
%define __python python2.6
# set to python26 for EL4,EL5
%define pythonbase python

Summary: Python SRS (Sender Rewriting Scheme) library
Name: %{pythonbase}-pysrs
Version: 1.0
Release: 3
Source0: pysrs-%{version}.tar.gz
Patch0: pysrs-%{version}.patch
License: Python license
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Stuart Gathman (Perl version by Shevek) <stuart@bmsi.com>
Packager: Stuart D. Gathman <stuart@bmsi.com>
Requires: chkconfig, %{pythonbase}, daemonize
Url: http://bmsi.com/python/pysrs.html

%description
Python SRS (Sender Rewriting Scheme) library.
As SPF is implemented, mail forwarders must rewrite envfrom for domains
they are not authorized to send from.

See http://www.openspf.org/SRS for details.
The Perl reference implementation is at http://srs-socketmap.info/

SRS is also useful for detecting forged DSNs (bounces).  SES (Signed
Envelope Sender) is a variation that is more compact for this purpose,
and in conjuction with some kind of replay protection can also be
used as a form of authentication.

%prep
%setup -n pysrs-%{version}
%patch -p1

%build
%{__python} setup.py build

%install
%{__python} setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/etc/mail
cp pysrs.cfg $RPM_BUILD_ROOT/etc/mail
cat >$RPM_BUILD_ROOT/etc/mail/no-srs-mailers <<'EOF'
# no-srs-mailers - list hosts (RHS) we should not SRS encode for when we
# send to them.  E.g. primary MX servers for which we are a secondary.
# NOTE - mailertable can change the RHS for delivery purposes, you
# must match the mailertable RHS in that case.
#
EOF
mkdir -p $RPM_BUILD_ROOT/usr/share/sendmail-cf/hack
cp pysrs.m4 $RPM_BUILD_ROOT/usr/share/sendmail-cf/hack
cp pysrsprog.m4 $RPM_BUILD_ROOT/usr/share/sendmail-cf/hack

# We use same log dir as milter since we also are a sendmail add-on
mkdir -p $RPM_BUILD_ROOT/var/log/milter
mkdir -p $RPM_BUILD_ROOT/var/run/milter
mkdir -p $RPM_BUILD_ROOT/usr/lib/pymilter
mkdir -p $RPM_BUILD_ROOT/etc/rc.d/init.d
cp %{sysvinit} $RPM_BUILD_ROOT/etc/rc.d/init.d/pysrs
ed $RPM_BUILD_ROOT/etc/rc.d/init.d/pysrs <<'EOF'
/^python=/
c
python="%{__python}"
.
w
q
EOF
cp -p pysrs.py $RPM_BUILD_ROOT/usr/lib/pymilter

# logfile rotation
mkdir -p $RPM_BUILD_ROOT/etc/logrotate.d
cat >$RPM_BUILD_ROOT/etc/logrotate.d/pysrs <<'EOF'
/var/log/milter/pysrs.log {
  copytruncate
  compress
}
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
#echo "Syntax of HACK(pysrs) has changed.  Update sendmail.mc."
/sbin/chkconfig --add pysrs

%preun
if [ $1 = 0 ]; then
  /sbin/chkconfig --del pysrs
fi

%files -f INSTALLED_FILES
%doc COPYING LICENSE.python LICENSE.sendmail CHANGES
%defattr(-,root,root)
%config(noreplace) /etc/mail/pysrs.cfg
%config(noreplace) /etc/mail/no-srs-mailers
/etc/logrotate.d/pysrs
/etc/rc.d/init.d/pysrs
/usr/share/sendmail-cf/hack/*
/usr/lib/pymilter/pysrs.py

%changelog
* Wed May 20 2009 Stuart Gathman <stuart@bmsi.com> 1.0-3
- Use daemonize instead of start.sh, which is gone from pymilter

* Wed May 20 2009 Stuart Gathman <stuart@bmsi.com> 1.0-1
- Foundation for python milter envfrom rewriting (in progress)
- Python 2.6
- Depend on pymilter for dirs, even though we don't
  really need it for anything else until envfrom rewriting is done.

* Tue Jan 16 2007 Stuart Gathman <stuart@bmsi.com> 0.30.12-1
- Support logging recipient host, and nosrs in pysrs.cfg
* Wed Feb 15 2006 Stuart Gathman <stuart@bmsi.com> 0.30.11-1
- support SRS signing mode
* Tue Jul 05 2005 Stuart Gathman <stuart@bmsi.com> 0.30.10-1
- support SES
* Sun Sep 19 2004 Stuart Gathman <stuart@bmsi.com> 0.30.9-2
- chkconfig --add pysrs
* Thu Aug 26 2004 Stuart Gathman <stuart@bmsi.com> 0.30.9-1
- Sendmail Socketmap Daemon
* Wed Mar 24 2004 Stuart Gathman <stuart@bmsi.com> 0.30.8-1
- Use HMAC instead of straight sha
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
