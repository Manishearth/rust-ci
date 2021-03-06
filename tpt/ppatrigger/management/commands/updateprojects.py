import traceback
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from ppatrigger.models import Project
from travisclient import get_repo
from tpt import private_settings
import urllib2
from urllib2 import URLError
from util import varnishutil

# For updating existing projects with new additions
#   * get project description field from Travis CI
#   * check for Cargo.toml presence
#   * create a rustci_token (implicit trigger)
class Command(BaseCommand):
    args = ''
    help = 'Fetch/update project descriptions for all projects'

    def handle(self, *args, **options):

        changed = False
        for project in Project.objects.filter(deleted = False):

            #repo = get_repo(project.username, project.repository)

            #if(repo and 'description' in repo and
            #        repo['description']):
            #    project.description = repo['description']
            #
            #    self.stdout.write(str(project) + ': ' +\
            #            project.description)
            #else:
            #    self.stdout.write('No description found: ' + str(project))


            # Check for Cargo.toml in root of project

            headers = {
                'User-Agent': 'Rust CI'
            }

            url = 'https://api.github.com/repos/%s/%s/contents/Cargo.toml?client_id=%s&client_secret=%s' \
                    % (project.username, project.repository, private_settings.GITHUB_CLIENT_ID,
                            private_settings.GITHUB_CLIENT_SECRET)
            req = urllib2.Request(url, headers = headers)

            try:
                response = urllib2.urlopen(req)

                if project.cargo_support == False:
                    changed = True
                    # Cargo.toml added, ban all project pages
                    varnishutil.ban_cache_groups(Project)

                project.cargo_support = True
                self.stdout.write('Found Cargo.toml: ' + str(project))
            except URLError, e:                
                self.stdout.write('No Cargo.toml found: ' +\
                        str(project) + ' ' + str(e.code))
                #if e.code == 404:
                #    project.cargo_support = False
            
            project.save()

        if changed:
            varnishutil.purge_urls([
                reverse('index'),
                reverse('projects')])


