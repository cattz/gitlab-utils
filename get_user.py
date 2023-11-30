#!/usr/bin/env python3

import os
import gitlab
import json
import pandas as pd

from pprint import pprint

try:
    TOKEN = os.environ['GITLAB_TOKEN']
except KeyError:
    print('[ERROR] Export your GitLab token in the environmnet variable GITLAB_TOKEN')
    exit(-1)

GITLAB = os.environ.get('GITLAB_API', 'https://gitlab.com/api/v4')
headers = {
    'PRIVATE-TOKEN': TOKEN,
    'Content-Type': 'application/json'
}

gl = gitlab.Gitlab(url='https://gitlab.essent.nl', private_token=TOKEN)


def get_users():
    users = [
        1553,  # Harish
        ]
    #     1552,  # xabier
    #     873,   # Emiel (old) 331 projects, 37 groups
    #     842,   # Emiel (blocked)
    #
    # ]
    for us in users:
        user = gl.users.get(id=us)
        user.deactivate()
        with open(f'{us}.json', 'w', encoding='utf-8') as fl:
            fl.write(json.dumps(user.attributes, indent=4))


def all_users_report():
    users = gl.users.list(get_all=True)
    df = pd.DataFrame(
        [user.attributes['id'],
         user.attributes['name'],
         user.attributes['username'],
         user.attributes['created_at'],
         user.attributes['last_sign_in_at'],
         user.attributes['last_activity_on'],
         user.attributes['using_license_seat'],
         user.attributes['state'],
         user.attributes['identities']
        ] for user in users
    )
    df.columns = ['id', 'name', 'usernme', 'created_at', 'last_sign_in',
                  'last_activity', 'using_license', 'state', 'identities']
    df.to_excel('gitlab_users.xlsx')


if __name__ == "__main__":
    all_users_report()