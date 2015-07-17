# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from fabric.api import run, env, prompt, execute, sudo
import boto
import boto.ec2
import time
from fabric.contrib.project import rsync_project
from fabric.contrib.files import upload_template

env.hosts = ['localhost', ]
env.aws_region = 'us-west-2'
env.key_filename = '~/.ssh/pk-aws.pem'


def host_type():
    run('uname -s')


def get_ec2_connection():
    if 'ec2' not in env:
        conn = boto.ec2.connect_to_region(env.aws_region)
        if conn is not None:
            env.ec2 = conn
            print "Connected to EC2 region {}".format(env.aws_region)
        else:
            msg = "Unable to connect to EC2 region {}"
            raise IOError(msg.format(env.aws_region))
    return env.ec2


def provision_instance(wait_for_running=True, timeout=60, interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    conn = get_ec2_connection()
    instance_type = 't2.micro'
    key_name = 'pk-aws'
    security_group = 'ssh-access'
    image_id = 'ami-8d5b5dbd'

    reservations = conn.run_instances(
        image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group]
    )
    new_instances = [i for i in reservations.instances if i.state == 'pending']
    running_instance = []
    if wait_for_running:
        waited = 0
        while new_instances and (waited < timeout_val):
            time.sleep(wait_val)
            for instance in new_instances:
                state = instance.state
                print "Instance {} is {}".format(instance.id, state)
                if state == 'running':
                    running_instance.append(
                        new_instances.pop(new_instances.index(i))
                    )
                instance.update()
                waited += wait_val


def list_aws_instances(verbose=False, state='all'):
    conn = get_ec2_connection()

    reservations = conn.get_all_reservations()
    instances = []
    for res in reservations:
        for instance in res.instances:
            if state == 'all' or instance.state == state:
                instance = {
                    'id': instance.id,
                    'type': instance.instance_type,
                    'image': instance.image_id,
                    'state': instance.state,
                    'instance': instance,
                }
                instances.append(instance)
    env.instances = instances
    if verbose:
        import pprint
        pprint.pprint(env.instances)


def select_instance(state='running'):
    if env.get('active_instance', False):
        return

    list_aws_instances(state=state)

    prompt_text = "Please select from the following instances:\n"
    instance_template = " {ct}: {state} instance {id}\n"
    for idx, instance in enumerate(env.instances):
        ct = idx + 1
        kwargs = {'ct': ct}
        kwargs.update(instance)
        prompt_text += instance_template.format(**kwargs)
    prompt_text += "Choose an instance: "

    def validation(input):
        choice = int(input)
        if choice not in range(1, len(env.instances) + 1):
            raise ValueError("{} is not a valid instance".format(choice))
        return choice

    choice = prompt(prompt_text, validate=validation)
    env.active_instance = env.instances[choice - 1]['instance']


def stop_instance(wait_for_stopped=True, timeout=60, interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    select_instance()
    instance = env.active_instance
    instance.stop()
    if wait_for_stopped:
        waited = 0
        while instance.state != 'stopped' and (waited < timeout_val):
            time.sleep(wait_val)
            waited += wait_val
            print "Instance {} is {}".format(instance.id, instance.state)
            if instance.state == 'stopped':
                break
            instance.update()


def terminate_instance():
    select_instance('stopped')
    instance = env.active_instance
    instance.terminate()
    print instance.state


def run_command_on_selected_server(command, *args):
    select_instance()
    selected_hosts = [
        'ubuntu@' + env.active_instance.public_dns_name
    ]
    execute(command, hosts=selected_hosts)


def _install_nginx():
    sudo('apt-get install build-essential')
    sudo('apt-get install nginx')
    sudo('/etc/init.d/nginx start')


def install_nginx():
    run_command_on_selected_server(_install_nginx)


def _configure_nginx():
    # Requires that simple_nginx_config is already on the server home.
    sudo('mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default.orig')
    sudo('mv ~/simple_app_nginx.conf /etc/nginx/sites-available/default')
    sudo('/etc/init.d/nginx restart')


def configure_nginx():
    run_command_on_selected_server(_configure_nginx)


def _restart_nginx():
    sudo('/etc/init.d/nginx restart')


def restart_nginx():
    run_command_on_selected_server(_restart_nginx)


def _install_supervisor():
    sudo('apt-get install supervisor')


def install_supervisor():
    run_command_on_selected_server(_install_supervisor)


def _run_supervisor():
    sudo('supervisord -c supervisord.conf')


def run_supervisor():
    run_command_on_selected_server(_run_supervisor)


def _unlink_supervisor():
    sudo('unlink /tmp/supervisor.sock')


# free up resources if we need to kill supervisor
def unlink_supervisor():
    run_command_on_selected_server(_unlink_supervisor)


def _start_app():
    sudo('python bookapp.py')


def _rsync():
    rsync_project(remote_dir='~/', local_dir='./')


def _install_pip():
    sudo('apt-get install python-dev')
    sudo('apt-get install python-pip')
    sudo('pip install -U pip')


# we'll want this later
def _pip_install():
    sudo('pip install -r requirements.txt')


def _install_postgres():
    sudo('apt-get install postgresql')
    sudo('apt-get install libpq-dev')


def _configure_fresh_instance():
    _install_nginx()
    _install_supervisor()
    _rsync()
    context = {'server_name': env.active_instance.public_dns_name}
    upload_template('./nginx_template.conf',
                    '~/simple_app_nginx.conf',
                    context=context)
    _configure_nginx()
    _restart_nginx()
    _install_postgres()
    _install_pip()
    _pip_install()
    _run_supervisor()


def configure_fresh_instance():
    run_command_on_selected_server(_configure_fresh_instance)


def deploy():
    run_command_on_selected_server(_rsync)
    run_command_on_selected_server(_pip_install)
