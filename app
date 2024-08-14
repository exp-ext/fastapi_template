#!/usr/bin/env python3

import asyncio
import os
import subprocess
import sys
import time

import click
import psycopg2
from dotenv import load_dotenv
from src.conf import static_storage


def check_file_exists(file_path):
    if not os.path.exists(file_path):
        print(f"File '{file_path}' does not exist.")
        sys.exit(1)


def wait_for_postgresql(host, user, password, database):
    while True:
        try:
            connection = psycopg2.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            connection.close()
            print("PostgreSQL is ready!")
            break
        except psycopg2.OperationalError:
            print("Waiting for PostgreSQL to be ready...")
            time.sleep(2)


def wait_for_services(env_file):
    check_file_exists(env_file)
    load_dotenv(env_file)
    services = [
        ('localhost:5432', 'PostgreSQL'),
        ('localhost:6379', 'Redis'),
        ('localhost:5672', 'RabbitMQ')
    ]
    for service, name in services:
        print(f"Waiting for {name}...")
        subprocess.run(['infra/wait-for-it.sh', service, '--timeout=60'])

    wait_for_postgresql(
        host='localhost',
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )


def start_docker_compose(env_file, compose_file):
    check_file_exists(env_file)
    check_file_exists(compose_file)
    load_dotenv(env_file)
    subprocess.run(['docker-compose', '-f', compose_file, '--env-file', env_file, 'up', '--build'])


async def run_static_collection():
    await static_storage.collect_and_upload_static(static_dir="src/static")


@click.group()
def cli():
    pass


@cli.command()
def debug():
    start_docker_compose('infra/.env', 'infra/debug/docker-compose.yml')


@cli.command()
def stage():
    start_docker_compose('infra/.env', 'infra/stage/docker-compose.yml')
    time.sleep(10)
    asyncio.run(run_static_collection())


@cli.command()
def stop():
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

    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
