web:
	doxygen
	rsync -ravK doc/html/ spidey2.bmsi.com:/Public/pymilter

VERSION=1.0
CVSTAG=pysrs-1_0
PKG=pysrs-$(VERSION)
SRCTAR=$(PKG).tar.gz

$(SRCTAR):
	cvs export -r$(CVSTAG) -d $(PKG) pysrs
	tar cvfz $(PKG).tar.gz $(PKG)
	rm -r $(PKG)

cvstar: $(SRCTAR)
