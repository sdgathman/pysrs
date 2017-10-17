# pysrs

A python library and sendmail/Exim socketmap that rewrites MAIL FROM.  Often used with [python milter](http://pythonhosted.org/milter/) to reject forged bounces (that lack a valid SRS signature).

The pysrs rpm now uses the standard daemonize package to replace start.sh on EL6.  This is all moot with EL7 and systemd, of course.

