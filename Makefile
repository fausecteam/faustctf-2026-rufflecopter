SERVICE := rufflecopter
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install

build:
	echo nothing to build

install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)
	cp -r docker-compose.yml db/ $(DESTDIR)$(SERVICEDIR)
	mkdir -p $(DESTDIR)$(SERVICEDIR)/service
	cp -r service/content/ service/src/ service/Cargo.toml service/server.swf service/Dockerfile $(DESTDIR)$(SERVICEDIR)/service
	mkdir -p $(DESTDIR)/etc/systemd/system/faustctf.target.wants/
	ln -s /etc/systemd/system/docker-compose@.service $(DESTDIR)/etc/systemd/system/faustctf.target.wants/docker-compose@$(SERVICE).service

