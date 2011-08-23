#!/bin/bash
###############################################################################
#  
#  Install packages using APT as non-root by creating a temprorary APT
#   config and cache heirarchy, and passing --force-non-root to Dpkg.
#
#   (Of course, requires writable access to /usr/local, which may be
#    obtained using the dpkg-tmplocal utility)
#
#  Usage: apt-userinst PKG [PKG]...
#
###############################################################################

PROG=$(basename $0)

#  List of directories under basedir which APT requires
#
APT_DIRS="var/lib/apt/lists/partial var/lib/apt/periodic"
APT_DIRS="$APT_DIRS var/cache/apt/archives/partial var/log/apt etc/apt"

declare -r usage=\
"\
Usage: $PROG PKG [PKGS]...\n\
   or  $PROG --fix-broken [PKGS]...\n\
   or  $PROG --local-install [DEBS]...\n\

  -h, --help           Display this message.\n\
  -v, --verbose        Increase output verbosity.\n\
  -n, --dry-run        Pass --dry-run option to apt-get.\n\
  -l, --local-install  Install local packages (i.e. .debs, implies -f)\n\
  -f, --fix-broken     Run apt-get(8) with -f argument to fix up missing\n\
                       dependencies and broken packages in /usr/local.\n"

###############################################################################
#  Functions 
###############################################################################

cleanup ()   { [ -n "$BASE" ] && [ -d $BASE ] && rm -rf $BASE; }
log_msg ()   { echo -e "$PROG: $@";     } 	
log_error () { log_msg "Error: $@";  }
die ()       { log_msg "$@"; cleanup; exit 1; }
usage ()     { echo -e "$usage"; exit 1; }

log_verbose () { [ -n "$verbose" ] && log_msg "$@"; }

#
#  Create directory structure required for APT 
#
create_apt_dirs ()
{
  [ -n "$1" ] || die "Failed to supply basedir to create_apt_dirs"
  for dir in $APT_DIRS; do
    log_verbose "Creating APT dir $dir under $1"
    mkdir -p $1/$dir  || die "failed to create APT dir: $dir"
  done

  log_verbose "Copying apt.conf and sources.list into $1/etc/apt"
  cp /etc/apt/{apt.conf,sources.list} $1/etc/apt || \
     die "failed to copy apt config"
  if [ -f /etc/apt/preferences ]; then
      log_verbose "Copying apt preferences into $1/etc/apt"
      cp /etc/apt/preferences $1/etc/apt
  fi
}

#
#  Import key into basedir/etc/apt 
#
import_key () 
{
  ETCDIR=$1/etc/apt
  [ -z "$verbose" ] && quiet="--quiet"
  log_msg "Importing Builder GPG key"
  gpg --no-options --no-default-keyring $quiet --batch \
      --secret-keyring $ETCDIR/secring.gpg \
      --trustdb-name   $ETCDIR/trustdb.gpg \
      --keyring        $ETCDIR/trusted.gpg \
      --import         /etc/apt/buildkey.txt

}

runcmd ()
{
  log_verbose "Running $@"
  if [ -n "$verbose" ]; then
      $@
  else
      local ERRORS
      ERRORS=$($@ 2>&1 >/dev/null)
      local rc=$?
      if [ $rc -ne 0 ]; then
          log_msg "${ERRORS}"
          return 1
      fi
      return 0
  fi
}

check_files ()
{
  for f in $@; do
    [ -f $f ]                      || die "$f: File not found."
    dpkg-deb -I $f >/dev/null 2>&1 || die "$f: Not a dpkg package."
  done
}

##########################################################################
#  Main script
##########################################################################

longopts="fix-broken,local-install,verbose,dry-run,help"
shortopts="flvhn"
ARGS=`/usr/bin/getopt -uo $shortopts -l $longopts -n $PROG -- $@`
if [ $? -ne 0 ]; then
   usage
fi

set -- $ARGS
while true; do 
   case "$1" in 
    -f|--fix-broken)    fix_broken="-f"; shift   ;;
    -l|--local-install) local_install=1; shift   ;;
    -v|--verbose)       verbose=1;       shift   ;;
    -n|--dry-run)       dry_run=1;       shift   ;;
    -h|--help)          echo -e "$usage"; exit 0 ;;
    --)                 shift; break             ;;
    *)                  die "getopt: unknown opt \"$1\"" ;;
   esac
done

if [ $# -eq 0 ] && [ -z "$fix_broken" ]; then
   log_error "Must supply list of packages unless using --fix-broken\n"
   usage
fi

#
#  Initialize /usr/local if not done already
if [ ! -d /usr/local/dpkg-db ]; then 
   log_msg "Attempting to initialize empty /usr/local"
   log_verbose "Running /usr/sbin/dpkg-initialize"
   /usr/sbin/dpkg-initialize || die "Failed to initialize /usr/local!"
fi

#
#  Create temporary directory for APT working files
#
BASE=$(mktemp -dt ${PROG}.XXXXXXXXXX) || die "mktemp failed"

create_apt_dirs $BASE
import_key $BASE      || die "Failed to import buildbot key"

#
#  Run apt-get update against BASEdir
#
OPTS="-oDir=$BASE -oApt::GPGV::TrustedKeyring=$BASE/etc/apt/trusted.gpg"
log_msg "Running apt-get update..."
runcmd apt-get $OPTS update || die "apt-get update failed"

#
# Dpkg will require /sbin and /usr/sbin in its path
#
PATH=/sbin:/usr/sbin:$PATH
OPTS="$OPTS -oDir::Log=$BASE/var/log/apt -oDPkg::Options::=--force-not-root"
OPTS="$OPTS${dry_run+ -s}"

[ $# -gt 0 ] && log_msg "Attempting to install: $@"

if [ -n "$local_install" -a $# -gt 0 ]; then
   check_files $@
   runcmd dpkg -i --force-not-root,depends $@ || die "dpkg -i failed for $@"
   fix_broken="-f"
   shift $# 
fi

log_msg "Running apt-get ${fix_broken:+$fix_broken }-y install..."
runcmd apt-get $fix_broken -y $OPTS install "$@" || die "apt-get install failed"

cleanup

log_msg "Done."
exit 0

# vi: ts=4 sw=4 expandtab
