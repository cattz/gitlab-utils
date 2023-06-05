#!/usr/bin/env python3
import yaml
import requests
import os
from argparse import ArgumentParser


HELP = """
This script will create variables in your GitLab project

"""


'''
Example of secrets.yaml structure:

---
star:  # All environments or '*'
  FOO:
    value: some value
    protected: false
    masked: true
  BAR:
    value: some value
    # protected: false default is false
    # masked: true default is true

dev:
  API_TOKEN:
    value: 2311jkhg23jh
    protected: true
    masked: true

tst:
  API_TOKEN:
    value: akdhslgjwq8
    protected: true
    masked: true

acc:
  API_TOKEN:
    value: ewrkjhs284j
    protected: true
    masked: true

prd:
  API_TOKEN:
    value: sdhnsnhfdg939h
    protected: true
    masked: true

'''
try:
    TOKEN = os.environ['GITLAB_TOKEN']
except KeyError:
    print('[ERROR] Export your GitLab token in the environmnet variable GITLAB_TOKEN')
    exit(-1)

GITLAB = os.environ.get('GITLAB_API', 'https://gitlab.com/api/v4')
header = {'PRIVATE-TOKEN': TOKEN}


def get_arguments():
    parser = ArgumentParser(description=HELP)
    parser.add_argument('-s', '--source-variables-file', required=True,
                        help='Yaml file containing the variables')
    parser.add_argument('-p', '--gitlab-target-project', required=True,
                        help='ID of the GitLab project where we want to create the variables')
    parser.add_argument('--delete-variables', required=False, dest='delete_variables', action='store_true',
                        default=False, help='Instead of creating the variables it will delete them, if they exist')
    return parser.parse_args()


def create_variable(var_key, var, environment, prj_code):
    protected = var.get('protected', False)
    masked = var.get('masked', True)
    variable_payload = dict(
        variable_type='env_var',
        protected=protected,
        masked=masked,
        key=var_key,
        value=var['value'],
        environment_scope=environment
    )
    resp = requests.post(
        f'{GITLAB}/projects/{prj_code}/variables',
        headers=header,
        data=variable_payload
    )
    if resp.status_code in (200, 201):
        print(f'Created {var} in project {prj_code}, environment {environment}')
    elif resp.status_code == 400:  # Variable exists
        resp = requests.put(
            f'{GITLAB}/projects/{prj_code}/variables/{var_key}?filter[environment_scope]={environment}',
            headers=header,
            data=variable_payload
        )
        if resp.status_code == 200:
            print(f'Updated {var_key} in project {prj_code}, environment {environment}')
    if resp.status_code not in (200, 201):
        print(
            f'Error updating/creating {var_key} in project {prj_code}, environment {environment}\n{resp}')
        print(f'Returned code   : {resp.status_code}')
        print(f'Returned message: {resp.text}')


def delete_variable(var, environment, prj_code):
    print(f'Deleting variable {var} from {environment}')
    url = f'{GITLAB}/projects/{prj_code}/variables/{var}?filter[environment_scope]={environment}'
    resp = requests.delete(url, headers=header)
    if resp.status_code != 204:
        print('Delete failed.')
        print(url)
        print(resp)
        print(resp.text)


def process_variables(var_file, prj_code, remove):
    with open(var_file, 'r') as vfo:
        variables = yaml.safe_load(vfo)
    for env in variables:
        for var in variables[env]:
            environment = "*" if env == 'star' else env
            if remove:
                delete_variable(var, environment, prj_code)
            else:
                create_variable(var, variables[env][var], environment, prj_code)


if __name__ == '__main__':
    args = get_arguments()
    if args.delete_variables:
        print('This will delete the variables!!!')
        if input('Please confirm [y/N] ').lower() != 'y':
            print('Cancelled....')
            exit(0)
    process_variables(
        args.source_variables_file,
        args.gitlab_target_project,
        args.delete_variables
    )
