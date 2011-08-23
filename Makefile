all: apt+chaos 
	@touch apt+chaos/configure
	$(MAKE) -C apt+chaos

quilt apt+chaos: patches/series
	@scripts/quilt.sh -p apt -q -e chaos

clean:
	rm -rf apt+chaos
	rm -f *.rpm *.bz2
