#!/user/bin/env python3
#
# MagiskFrida build process
#
# 1. Checks if project has a tag that matches frida tag
#    Yes -> continue
#    No  -> must tag
# 2. Checks if last commit doesn't have frida tag and is titled 'release'
#    Yes -> must tag
#    No  -> continue
# If tagging, writes new tag to 'NEW_TAG.txt' and builds
# Otherwise, does nothing and builds with placeholder tag
# 3. Deployment will execute only if 'NEW_TAG.txt' is present
#
# NOTE: Requires git
#

import build
import util


def main():
    new_project_tag = util.get_next_project_version()
    build.do_build(new_project_tag, new_project_tag)


if __name__ == "__main__":
    main()
