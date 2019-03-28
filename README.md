# pysrs

A python library and sendmail/Exim socketmap that rewrites MAIL FROM.  Often used with [python milter](http://pythonhosted.org/milter/) to reject forged bounces (that lack a valid SRS signature).

The pysrs rpm now uses the standard daemonize package to replace start.sh on EL6.  This is all moot with EL7 and systemd, of course.

## Note

The srsmilter.py program is experimental, and not intended for production.  It's purpose is to explore whether the milter API supports an SRS application.  The verdict is that it does not at present.  There are fundamental shortcomings in the CHGFROM api and worse problems with recipient handling.

For a functioning SRS system, you must use sendmail, the macros with CF code, and the pysrs.py socket daemon.  Sadly, a postfix solution will need to likewise be very postfix specific - the milter API doesn't cut it.
