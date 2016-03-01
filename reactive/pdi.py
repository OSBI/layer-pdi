import os
import stat
from shutil import rmtree, chown
from subprocess import check_call, CalledProcessError, call, check_output

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.host import adduser, chownr, mkdir
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charms.reactive import when, when_not, set_state, remove_state, is_state
from charms.reactive.helpers import data_changed
from charmhelpers.core.templating import render
from socket import gethostname;
import charms.leadership


@when_not('java.ready')
def update_java_status():
    status_set('blocked', 'Waiting for Java.')


@when_not('pdi.installed')
def install():
    status_set('maintenance', 'Installing PDI')
    adduser('etl')
    mkdir('/home/etl')
    chownr('/home/etl', 'etl', 'etl', chowntopdir=True)
    os.chmod('/home/etl', 0o755)

    au = ArchiveUrlFetchHandler()
    au.install(hookenv.config()['pdi_url'], '/opt/')
    chownr('/opt/data-integration', 'etl', 'etl', chowntopdir=True)
    st = os.stat('/opt/data-integration/spoon.sh')
    os.chmod('/opt/data-integration/spoon.sh', st.st_mode | stat.S_IEXEC)
    os.chmod('/opt/data-integration/carte.sh', st.st_mode | stat.S_IEXEC)
    os.chmod('/opt/data-integration/encr.sh', st.st_mode | stat.S_IEXEC)
    os.chmod('/opt/data-integration/kitchen.sh', st.st_mode | stat.S_IEXEC)
    os.chmod('/opt/data-integration/pan.sh', st.st_mode | stat.S_IEXEC)
    status_set('maintenance', 'PDI Installed')
    set_state('pdi.installed')


@when('java.ready')
@when('pdi.installed')
def check_running(java):
    if data_changed('pdi.url', hookenv.config('pdi_url')):
        stop()
        remove()
        install()

    if (data_changed('carte_password', hookenv.config())):
        change_carte_password(hookenv.config('carte_password'))

    if data_changed('pdi.config', hookenv.config()) and hookenv.config('run_carte'):
        restart(None)
    elif data_changed('pdi.config', hookenv.config()) and hookenv.config('run_carte') is False:
        stop()
        status_set('active', 'PDI Installed. Carte Server Disabled.')
    elif hookenv.config('run_carte'):
        start()
    elif hookenv.config('run_carte') is False:
        stop()
        status_set('active', 'PDI Installed. Carte Server Disabled.')


@when('pdi.installed')
@when('java.updated')
def restart(java):
    status_set('maintenance', 'Configuration has changed, restarting Carte.')
    stop()
    start()
    remove_state('java.updated')


def start():
    currentenv = dict(os.environ)
    port = hookenv.config('carte_port')
    javaopts = hookenv.config('java_opts')

    if javaopts:
        currentenv['JAVA_OPTS'] = javaopts

    try:
        check_call(['pgrep', '-f', 'carte.sh'])
    except CalledProcessError:
        if is_state('leader.is_leader'):
            check_call(['su', 'etl', '-c', '/opt/data-integration/carte.sh '
                                           '/opt/data-integration/pwd/carte-config-master.xml &'],
                       env=currentenv, cwd="/opt/data-integration")
        else:
            check_call(['su', 'etl', '-c', '/opt/data-integration/carte.sh '
                                           '/opt/data-integration/pwd/carte-config-slave.xml &'],
                       env=currentenv, cwd="/opt/data-integration")


    hookenv.open_port(port)
    status_set('active', 'Carte is ready!')


def stop():
    call(['pkill', '-f', 'carte.sh'])


def remove():
    rmtree('/opt/data-integration')


def change_carte_password(pword):
    process = check_output(['sh', '/opt/data-integration/encr.sh', '-carte', pword])
    encrpword = process.splitlines()[-1]
    with open("/opt/data-integration/pwd/kettle.pwd", "w") as text_file:
        text_file.write("cluster: " + encrpword.decode('utf-8'))
    chown('/opt/data-integration/encr.sh', 'etl', 'etl')


@when('leadership.is_leader')
@when_not('leadership.set.config_file')
def add_leader_config():
    # leadership.leader_set(admin_password=pwgen())
    render('carte-config/master.xml.j2', '/opt/data-integration/pwd/carte-config-master.xml', {
        'carteport': hookenv.config('carte_port'),
        'cartehostname': gethostname()
    })
    leader_set(hostname=gethostname())
    leader_set(port=hookenv.config('carte_port'))
    leader_set(username='cluster')
    leader_set(password=hookenv.config('carte_password'))



@when_not('leadership.is_leader')
@when_not('leadership.set.hostname')
def add_slave_config():
    render('carte-config/slave.xml.j2', '/opt/data-integration/pwd/carte-config-slave.xml', {
        'carteslaveport': hookenv.config('carte_port'),
        'carteslavehostname': gethostname(),
        'cartemasterhostname': leader_get('hostname')
    })