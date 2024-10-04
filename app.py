#!/usr/bin/env python3

import os
import subprocess
import sys

import click


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        print(f"File '{file_path}' does not exist.")
        sys.exit(1)


def start_docker_compose(compose_file, detached=False, custom_env=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, '.env')

    compose_file = os.path.abspath(compose_file)

    check_file_exists(env_file)
    check_file_exists(compose_file)

    env_vars = os.environ.copy()
    if custom_env:
        env_vars.update(custom_env)

    cmd = ['docker-compose', '-f', compose_file, 'up', '--build']
    if detached:
        cmd.append('-d')

    result = subprocess.run(cmd, env=env_vars)
    if result.returncode != 0:
        print(f"Error: docker-compose failed with return code {result.returncode}")
        sys.exit(result.returncode)


@click.group()
def cli():
    pass


@cli.command()
def debug():
    # Добавление переменных в env
    custom_env = {
        'PGADMIN_DEFAULT_EMAIL': 'admin@admin.ru',
        'PGADMIN_DEFAULT_PASSWORD': 'admin_password'
    }
    start_docker_compose('infra/nginx/docker-compose.yml', detached=True)
    start_docker_compose('infra/debug/docker-compose.yml', custom_env=custom_env)


@cli.command()
def stage():
    custom_env = {
        'PGADMIN_DEFAULT_EMAIL': 'admin@admin.ru',
        'PGADMIN_DEFAULT_PASSWORD': 'admin_password'
    }
    start_docker_compose('infra/nginx/docker-compose.yml', detached=True)
    start_docker_compose('infra/stage/docker-compose.yml', custom_env=custom_env)


@cli.command()
@click.option('--clean', is_flag=True, help="Удалить висячие образы и тома после остановки контейнеров")
def stop(clean):
    try:
        result = subprocess.run('docker ps -q', shell=True, check=True, capture_output=True, text=True)
        container_ids = result.stdout.strip().split()

        if container_ids:
            container_ids_str = ' '.join(container_ids)
            subprocess.run(f'docker stop {container_ids_str}', shell=True, check=True)
        else:
            print("No running containers to stop.")

        result = subprocess.run('docker ps -a -q', shell=True, check=True, capture_output=True, text=True)
        all_container_ids = result.stdout.strip().split()

        if all_container_ids:
            all_container_ids_str = ' '.join(all_container_ids)
            subprocess.run(f'docker rm {all_container_ids_str}', shell=True, check=True)
        else:
            print("No containers to remove.")

        if clean:
            print("Cleaning up dangling images...")
            subprocess.run('docker image prune -f', shell=True, check=True)
            print("Cleaning up dangling volumes...")
            subprocess.run('docker volume ls -qf dangling=true | grep -E "^[0-9a-f]{64}$" | xargs -r docker volume rm', shell=True, check=True)
            print("Done!")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
