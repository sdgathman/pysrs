web:
	doxygen
	rsync -ravK doc/html/ spidey2.bmsi.com:/Public/pymilter

VERSION=1.0.1
PKG=pysrs-$(VERSION)
SRCTAR=$(PKG).tar.gz

$(SRCTAR):
	git archive --format=tar.gz --prefix=$(PKG)/ -o $(SRCTAR) $(PKG)

srctar: $(SRCTAR)
