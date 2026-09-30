from django.views import View
from django.shortcuts import render
from datetime import datetime


TOOL_GROUPS = [
    {
        "title": "My tools",
        "tools": [
            {
                "name": "Zinc",
                "url": "https://nextcloud.kitsunehosting.net/",
                "note": "Files",
            },
            {
                "name": "Vaultwarden",
                "url": "https://bitwarden.kitsunehosting.net/",
                "note": "Passwords",
            },
            {
                "name": "Gitea",
                "url": "https://git.kitsunehosting.net/",
                "note": "Git",
            },
        ],
    },
    {
        "title": "Other",
        "tools": [
            {
                "name": "cutopt",
                "url": "https://dotslashgabut.github.io/cutopt.html",
                "note": "Its a handy cutting tool!",
            },
        ],
    },
]


class ToolsView(View):
    def get(self, request, *args, **kwargs):
        context = {"year": datetime.now().year, "tool_groups": TOOL_GROUPS}
        return render(request, "tools.html", context)
