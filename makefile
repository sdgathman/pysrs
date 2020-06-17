web:
	doxygen
	rsync -ravK doc/html/ pymilter.org:/var/www/html/milter/pysrs

VERSION=1.0.3
PKG=pysrs-$(VERSION)
SRCTAR=$(PKG).tar.gz

$(SRCTAR):
	git archive --format=tar.gz --prefix=$(PKG)/ -o $(SRCTAR) $(PKG)

srctar: $(SRCTAR)
