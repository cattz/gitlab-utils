#!/usr/bin/env python3

import os
import gitlab
from atlassian import Confluence
from pprint import pprint
from jinja2 import Environment, BaseLoader
import json

EXCLUDE_USERS: list[int] = [
    1,  # Administrator
    141,  # Santhosh
    1552,  # Davila, Xabier
    1553,  # Shetty, Harish
]

# For Confluence storage formate reference:
# https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html

TEMPLATE = """
<ac:structured-macro  ac:name=\"toc\" />
{% for group, owners in report.items() %}
<h2><a href="https://gitlab.essent.nl/{{ group }}">{{ group }}</a></h2>
<ul>
{% for user in owners -%}
<li>{{ user.name }}, ({{user.username}})</li>
{% endfor -%}
</ul>
{% endfor -%}
"""


def get_gitlab() -> gitlab.Gitlab:
    try:
        TOKEN = os.environ["GITLAB_TOKEN"]
    except KeyError:
        print(
            "[ERROR] Export your GitLab token in the environment variable GITLAB_TOKEN"
        )
        exit(-1)

    return gitlab.Gitlab(url="https://gitlab.essent.nl", private_token=TOKEN)


def get_confluence() -> Confluence:
    try:
        CONFLUENCE_USER = os.environ["CONFLUENCE_USER"]
        CONFLUENCE_TOKEN = os.environ["CONFLUENCE_PASSWORD"]
    except KeyError:
        print(
            "[ERROR] Export your Confluence user and password in the environment "
            "variables CONFLUENCE_USER and CONFLUENCE_PASSWORD"
        )
        exit(-1)

    return Confluence(
        url="https://wiki.essent.nl/confluence",
        username=CONFLUENCE_USER,
        password=CONFLUENCE_TOKEN,
    )


def group_owners_report(gl) -> dict:
    rept = {}
    groups = gl.groups.list(get_all=True)
    for gr in [g for g in groups if g.attributes["parent_id"] is None]:
        # pprint(json.dumps(gr.attributes))
        # exit(0)
        gr_id = gr.attributes["id"]
        gr_path = gr.attributes["full_path"]
        rept[gr_path] = []
        print(f"Checking owners for {gr_path}.")
        group = gl.groups.get(gr_id)
        members = group.members_all.list(get_all=True)
        for member in members:
            if (
                member.attributes["access_level"] == gitlab.const.AccessLevel.OWNER
                and member.attributes["id"] not in EXCLUDE_USERS
                and member.attributes["state"] == "active"
            ):
                rept[gr_path].append(
                    {
                        "name": member.attributes["name"],
                        "username": member.attributes["username"],
                        "id": member.attributes["id"],
                        "web_url": member.attributes["web_url"],
                    }
                )
    return rept


if __name__ == "__main__":
    gl = get_gitlab()
    wiki = get_confluence()
    report = group_owners_report(gl)
    rtemplate = Environment(loader=BaseLoader()).from_string(TEMPLATE)
    # pprint(wiki.get_page_by_id(209199578))
    wiki.update_or_create(
        '209195689',
        "GitLab top level group owners",
        body=rtemplate.render({'report': report}),
        representation='storage',
        full_width=False)
