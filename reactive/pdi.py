from charmhelpers.core.hookenv import status_set
from charmhelpers.core import hookenv
from charms.reactive.helpers import data_changed
from charmhelpers.core.host import mkdir, adduser, service_start, chownr
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from subprocess import check_call, CalledProcessError, call
from charms.reactive import when, when_not, set_state, remove_state
from shutil import rmtree
import os
import pwd
import stat

@when_not('java.ready')
def update_java_status():
    status_set('blocked', 'Waiting for Java.')


@when_not('pdi.installed')
def install():
    status_set('maintenance', 'Installing PDI')
    adduser('etl')
    au = ArchiveUrlFetchHandler()
    au.install(hookenv.config()['pdi_url'], '/opt/')
    chownr('/opt/data-integration', 'etl', 'etl')
    os.chmod('/opt/data-integration/spoon.sh', stat.S_IEXEC)
    status_set('maintenance', 'PDI Installed')
    set_state('pdi.installed')


@when('java.ready')
@when('pdi.installed')
def check_running(java):
    if data_changed('pdi.url', hookenv.config('pdi_url'))
        stop()
        remove()
        install()

    if data_changed('pdi.config', hookenv.config()):
        restart(None)
    else:
        start()


@when('pdi.installed')
@when('java.updated')
def restart(java):
    status_set('maintenance', 'Configuration has changed, restarting Carte.')
    stop()
    start()
    remove_state('java.updated')

def start():
    currentenv = dict(os.environ)
    port=hookenv.config('carte_port')
    javaopts=hookenv.config('java_opts')

    if javaopts:
        currentenv['JAVA_OPTS']=javaopts

    try:
        check_call(['pgrep', '-f', 'carte.sh'])
    except CalledProcessError:
        check_call(['su', 'etl', '-c', 'sh', '/opt/data-integration/carte.sh', '0.0.0.0', port, '&'], env=currentenv)

    hookenv.open_port(port)
    status_set('active', 'Carte is ready!')

def stop():
    call(['pkill', '-f', 'carte.sh'])

def remove():
    rmtree('/opt/data-integration')