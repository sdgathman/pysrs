divert(-1)
#
# Copyright (c) 2004 Alain Knaff (derived from work by asarian-host.net)
#	All rights reserved.
# Copyright (c) 1988, 1993
#	The Regents of the University of California.  All rights reserved.
#
# By using this file, you agree to the terms and conditions set
# forth in the LICENSE file which can be found at the top level of
# the sendmail distribution.
#
#
divert(0)
VERSIONID(`$Id$')

ifdef(`_MAILER_DEFINED_',,`errprint(`*** WARNING: MAILER() should be before HACK(pysrs)
')')

ifdef(`_ARG_',,`errprint(`*** WARNING: HACK(pysrs,sockname) requires sockname
')')
ifelse(defn(`_ARG_'),`',,`define(`SRS_SOCKET',_ARG_)')

LOCAL_CONFIG
# Forward SRS program map
Kmake_srs socket SRS_SOCKET
# Reverse SRS program map
Kreverse_srs socket SRS_SOCKET
# "To" address is SRS
Kis_srs regex ^<?(SRS[01]|SES)[+=-].*

ifdef(`NO_SRS_FILE', `dnl
# Class of destination mailers not needing SRS
F{noSrsMailers}-o NO_SRS_FILE %[^\#]
')dnl

MAILER_DEFINITIONS

SEnvFromSMTP
R$+		$: $>MakeSrs $1		make SRS

LOCAL_RULESETS

SIsSrs
# Answers YES or NO whether the address in parameter is srs or not
R$*				$: $( is_srs $1 $)
R$@				$@ YES
R$*				$@ NO


SMakeSrs
ifdef(`NO_SRS_FROM_LOCAL',`dnl
#
# Prevent SRS encapsulation if "From" address is local
# (With a local from address, the forwarder mail will pass any SPF checks
# anyways, so why bother with SRS?)
R$* < @ $=w > $*		$@ $1 < @ $2 > $3
R$* < @ $=w . > $*		$@ $1 < @ $2 . > $3
')dnl
ifdef(`NO_SRS_FILE',`dnl
#
# If destination mailer is in non-SRS list, do not apply SRS
# This is intended for handling communication between secondary MX and
# primary MX
R$*				$: $&h $| $1
R$={noSrsMailers} $| $*		$@ $2
R$* $| $*			$: $2
')dnl
R$*				$: $(make_srs $1 $)

SReverseSrs
R$*				$: $1 $>IsSrs $1
R$* NO				$@ $1
R$* YES				$@ $(reverse_srs $1 $)

LOCAL_RULE_0
R$*				$: $>ReverseSrs $1
