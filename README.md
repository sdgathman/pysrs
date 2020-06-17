# pysrs

## Python SRS (Sender Rewriting Scheme) library.

As SPF is implemented, MTAs that check SPF must account for any forwarders.
One way to handle forwarding is to have the forwarding MTA rewrite envfrom to a
domain they are authorized to use.

See https://www.open-spf.org/SRS for details.  The Perl reference
implementation and a C implementation are at http://www.libsrs2.org/

This is a python library and sendmail/Exim socketmap that rewrites MAIL FROM.
Often used with [python milter](http://pymilter.org/) to reject
forged bounces (that lack a valid SRS signature).

## Note

The srsmilter.py program is experimental, and not intended for production.
It's purpose is to explore whether the milter API supports an SRS application.
The verdict is that it does not at present.  There are fundamental shortcomings
in the CHGFROM api and worse problems with recipient handling.

For a functioning SRS system, you must use sendmail, the macros with CF code,
and the pysrs.py socket daemon.  Sadly, a postfix solution will need to
likewise be very postfix specific - the milter API doesn't cut it.

